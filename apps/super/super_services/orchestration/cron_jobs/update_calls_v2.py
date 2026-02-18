import traceback
from super.core.logging.logging import print_log
from super_services.db.services.models.task import (
    RunModel,
    TaskModel,
    CallRetrySmsModel,
)
from super_services.orchestration.task.task_service import TaskService
from super_services.orchestration.webhook.webhook_handler import WebhookHandler
from super.app.call_execution import execute_post_call_workflow
from super_services.db.services.schemas.task import TaskStatusEnum
from super_services.voice.models.config import ModelConfig
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv(override=True)

import asyncio
import requests
import boto3
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class VapiCallUpdater:
    """Handles synchronization of inbound calls with the task system."""

    def __init__(self):
        self.region = os.environ.get("AWS_DEFAULT_REGION")
        self.s3 = boto3.client("s3")
        self.auth_token = os.environ.get("VAPI_AUTH_TOKEN")
        self.base_url = os.environ.get("VAPI_BASE", "https://api.vapi.ai")
        self.webhook_handler = WebhookHandler()
        self.recordings_bucket = "cdr-storage-recs"
        self.recordings_prefix = "media/private/high-call-recordings"
        self.max_retries = 2

    def get_recording_url_by_call_id(self, call_id: str) -> str:
        """Fetch recording URL from S3 by call_id prefix search."""
        search_prefix = f"{self.recordings_prefix}/{call_id}"
        try:
            result = self.s3.list_objects_v2(
                Bucket=self.recordings_bucket, Prefix=search_prefix
            )
            contents = result.get("Contents", [])
            for obj in contents:
                if call_id in obj["Key"] and obj["Key"].endswith(".wav"):
                    download_key = obj["Key"]
                    return f"https://{self.recordings_bucket}.s3.{self.region}.amazonaws.com/{download_key}"
        except Exception as e:
            print_log(f"Error fetching recording for {call_id}: {e}")
        return ""

    def get_assistant_number(self, phone_number_id: str) -> str | None:
        """Fetch assistant phone number from VAPI."""
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }
        number_response = requests.get(
            f"https://api.vapi.ai/phone-number/{phone_number_id}", headers=headers
        )

        if number_response.status_code == 200:
            return number_response.json().get("number", "")
        return None

    def process_transcript(self, transcript):

        import re

        if isinstance(transcript, list):
            return transcript

        elif isinstance(transcript, str):
            messages = []
            pattern = r"(AI|User):\s*(.*?)(?=(AI|User):|$)"
            matches = re.findall(pattern, transcript, re.DOTALL)

            for role, content, _ in matches:
                role_mapped = "assistant" if role == "AI" else "user"
                messages.append({"role": role_mapped, "content": content.strip()})

            return messages

        return []

    def get_call_status(self, reason):

        failure = [
            "call.start.error-get-customer",
            "twilio-reported-customer-misdialed",
            "call.in-progress.error-assistant-did-not-receive-customer-audio",
        ]

        success = ["customer-ended-call"]

        not_connected = [
            "customer-busy",
            "customer-did-not-answer",
            "customer-ended-call-before-warm-transfer",
        ]

        if reason in success:
            return "completed"

        elif reason in not_connected:
            return "not-connected"

        elif reason in failure:
            return "failed"

        return "unknown"

    def _build_output_data(self, call: dict, call_id: str, task=None) -> dict:
        """Build output data dictionary for a call."""
        transcript = self.process_transcript(call.get("transcript", []))
        call_type = (
            "outbound" if call.get("type", "") == "outboundPhoneCall" else "inbound"
        )
        call_status = self.get_call_status(call.get("endedReason", ""))
        # print_log("contact_number -", task.get("task").get("contact_number"), task.get("input").get("contact_number"))
        # print_log("customer - ", task.get("task").get("name"), task.get("input").get("name"))

        contact_number = task.get("input").get("contact_number")

        if isinstance(contact_number,str) and contact_number.startswith("0"):
            contact_number = contact_number[1:]

        output_data = {
            "call_id": call_id,
            "customer": task.get("input").get("name"),
            "contact_number": contact_number,
            "call_end_reason": call.get("endedReason"),
            "recording_url": call.get("recordingUrl"),
            "transcript": transcript,
            "start_time": call.get("startedAt"),
            "end_time": call.get("endedAt"),
            "assistant_number": self.get_assistant_number(call.get("phoneNumberId")),
            "call_summary": call.get("summary"),
            "cost": call.get("cost"),
            "call_type": call_type,
            "call_status": call_status,
            "metadata": {
                "cost": call.get("cost"),
                "type": call.get("type"),
            },
        }

        if not output_data.get("recording_url"):
            output_data["recording_url"] = self.get_recording_url_by_call_id(call_id)

        return output_data

    def mark_pending_for_error(self, task_id, retry_attempt, call_end_reason):
        """Mark task as pending for specific error reasons."""
        new_data = {
            "status": TaskStatusEnum.pending,
            "retry_attempt": int(retry_attempt + 1),
            "output.call_end_reason": call_end_reason,
        }
        TaskModel._get_collection().update_one(
            {
                "task_id": task_id,
            },
            {"$set": new_data},
        )
        print_log(f"Marking task {task_id} as pending due to specific error reason")

    def mark_call_to_schedule(
        self, task_id, retry_attempt, call_end_reason, assignee: str = None
    ):
        from super_services.voice.consumers.voice_task_consumer import (
            _reschedule_to_prefect,
        )

        VAPI_RESCHEDULE_TIME = int(os.environ.get("VAPI_RESCHEDULE_TIME", "15"))  # min
        if assignee and (
            assignee.startswith("bob-card") or assignee.startswith("bobcard")
        ):
            VAPI_RESCHEDULE_TIME = 30
        schedule_time = datetime.now(timezone.utc) + timedelta(
            minutes=VAPI_RESCHEDULE_TIME
        )
        new_data = {
            "status": TaskStatusEnum.scheduled,
            "scheduled_timestamp": int(schedule_time.timestamp()),
            "retry_attempt": int(retry_attempt + 1),
            "output.call_end_reason": call_end_reason,
        }
        TaskModel._get_collection().update_one({"task_id": task_id}, {"$set": new_data})
        _reschedule_to_prefect(task_id, schedule_time)

    def mark_failed_max_retries(self, task_id, call_end_reason, retry_attempt):
        """Mark task as failed after maximum retries."""
        new_data = {
            "status": TaskStatusEnum.failed,
            "output.error": f"Task exceeded maximum retries ({int(retry_attempt + 1)})",
            "output.call_end_reason": call_end_reason,
            "retry_attempt": int(retry_attempt + 1),
        }

        TaskModel._get_collection().update_one(
            {
                "task_id": task_id,
            },
            {"$set": new_data},
        )
        print_log(f"Marking task {task_id} as failed after maximum retries")

    def check_sms_assignee(self, assignee):
        if assignee and (
            assignee.startswith("bob-card") or assignee.startswith("bobcard")
        ):
            return True
        return False

    def _check_and_sent_sms(self, call_end_reason, assignee, task, call):
        from super_services.prefect_setup.deployments.utils import (
            trigger_deployment,
        )

        TEMP_ID = "695b6bb36ca4495d4463e8d6"
        task_service = TaskService()
        task_id = task.get("task_id")
        retry_attempt = int(task.get("retry_attempt", 0))
        contact_number = call.get("customer", {}).get("number")
        if contact_number and contact_number.startswith("+91"):
            if assignee and self.check_sms_assignee(assignee):
                if task_service._is_customer_error(
                    call_end_reason
                ) or task_service._is_retryable_call_error(call_end_reason):
                    contact_number = contact_number.replace("+91", "")
                    print_log(f"Sending SMS to {contact_number} for task {task_id}")
                    assistant_number = self.get_assistant_number(
                        call.get("phoneNumberId")
                    )
                    print_log(f"Assistant number: {assistant_number}")
                    if assistant_number:
                        assistant_number = assistant_number.replace("+91", "0")
                    kargs = {
                        "number": assistant_number,
                        "call_retry": retry_attempt + 1,
                    }
                    parameters = {
                        "task_id": task_id,
                        "data": {
                            "kargs": kargs,
                            "contact_number": contact_number,
                            "temp_id": TEMP_ID,
                        },
                    }
                    flow_name = f"sent_retry_sms-{task_id}"
                    asyncio.run(
                        trigger_deployment("Sent-Retry-SMS", parameters, name=flow_name)
                    )
                    call_details = {}
                    call_keys = ["assistantId", "phoneNumberId", "type", "customer", "updatedAt", "createdAt"]
                    for key in call_keys:
                        call_details[key] = call.get(key)
                    CallRetrySmsModel.save_single_to_db(
                        {
                            "task_id": task_id,
                            "contact_number": contact_number,
                            "temp_id": TEMP_ID,
                            "kargs": kargs,
                            "input_data": {"call": call_details},
                            "status": TaskStatusEnum.processing,
                        }
                    )
                else:
                    print_log("Not a customer error, skipping SMS")
            else:
                print_log("Not a Allowed assignee, skipping SMS")
        else:
            print_log("Not a valid indian contact number")
            return False

    def _update_existing_task(self, task, call: dict, call_id: str) -> bool:
        """Update an existing task with call data."""
        task_service = TaskService()
        if (
            call.get("status") != "ended"
            or call.get("endedReason") == "call.in-progress.sip-completed-call"
        ):
            return False
        call_end_reason = call.get("endedReason", "")
        retry_attempt = task.get("retry_attempt", 0)
        assignee = task.get("assignee", "")

        # Re-pending the call for specific reasons or Failures
        if call_end_reason and task_service._is_retryable_call_error(call_end_reason):
            if retry_attempt < self.max_retries:
                self.mark_pending_for_error(
                    task.get("task_id"), retry_attempt, call_end_reason
                )
                return False
            else:
                self.mark_failed_max_retries(
                    task.get("task_id"), call_end_reason, retry_attempt
                )
                self._check_and_sent_sms(call_end_reason, assignee, task, call)
                return False

        # Reschedule the call for specific reasons
        if call_end_reason and task_service._is_customer_error(call_end_reason):
            if retry_attempt < self.max_retries:
                self.mark_call_to_schedule(
                    task.get("task_id"),
                    retry_attempt,
                    call_end_reason,
                    assignee=assignee,
                )
                return False
            else:
                self.mark_failed_max_retries(
                    task.get("task_id"), call_end_reason, retry_attempt
                )
                self._check_and_sent_sms(call_end_reason, assignee, task, call)
                return False

        output_data = self._build_output_data(call, call_id, task=task)

        task_dict = {
            "task_id": task.get("task_id"),
            "instructions": task.get("task").get("objective", ""),
            "input": task.get("input"),
        }

        asyncio.run(
            execute_post_call_workflow(
                task.get("assignee"),
                ModelConfig(),
                output_data,
                task_dict,
                update_data=True,
            )
        )
        updated_data = {"status": TaskStatusEnum.completed}
        if output_data:
            for key, value in output_data.items():
                updated_data[f"output.{key}"] = value

        print_log("updating task")
        TaskModel._get_collection().update_one(
            {"task_id": task.get("task_id")},
            {"$set": updated_data},
        )
        print_log("sending webhook request")

        asyncio.run(self.webhook_handler.execute(task_id=task.get("task_id")))
        return True

    def get_all_tasks(self):
        """Fetch all tasks from the database."""
        # last_6hr = datetime.now(timezone.utc) - timedelta(hours=24)
        return list(
            TaskModel._get_collection().find(
                {
                    "status": TaskStatusEnum.in_progress,
                    # "created": {"$gte": last_6hr},
                    "output.call_id": {"$exists": True, "$ne": ""},
                }
            )
        )

    def _fetch_call_with_retry(
        self, call_id: str, headers: dict, max_retries: int = 3, timeout: int = 10
    ) -> dict | None:
        """Fetch call data from VAPI with retry logic."""
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/call/{call_id}"
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                )
                if response.status_code == 200:
                    return response.json()
                print_log(
                    f"Failed to fetch call {call_id}, status: {response.status_code}"
                )
            except requests.exceptions.Timeout:
                print_log(
                    f"Timeout fetching call {call_id}, attempt {attempt + 1}/{max_retries}"
                )
            except requests.exceptions.RequestException as e:
                print_log(
                    f"Request error for call {call_id}: {e}, attempt {attempt + 1}/{max_retries}"
                )

            if attempt < max_retries - 1:
                time.sleep(2**attempt)  # Exponential backoff: 1s, 2s, 4s

        return None

    def _fetch_and_process_single_task(self, task, headers: dict) -> bool:
        """Fetch call data and process a single task."""
        call_id = task.get("output", {}).get("call_id")
        if not call_id:
            return False

        call_data = self._fetch_call_with_retry(call_id, headers)
        if not call_data:
            return False

        self._update_existing_task(task, call_data, call_id)
        return True

    def process_tasks(self, tasks):
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(
                    self._fetch_and_process_single_task, task, headers
                ): task
                for task in tasks
            }

            for future in as_completed(futures):
                task = futures[future]
                try:
                    future.result()
                except Exception as e:
                    traceback.print_exc()
                    call_id = task.get("output", {}).get("call_id", "unknown")
                    print_log(f"Error processing task {call_id}: {e}")

    def extract_all_runs(self, tasks):
        runs = []
        for task in tasks:
            run_id = task.get("run_id")
            if run_id and run_id not in runs:
                runs.append(run_id)
        return runs

    def update_runs(self, runs):
        task_service = TaskService()
        for run_id in runs:
            task_service.check_and_update_run_status(run_id=run_id)
            task_service.get_pending_tasks(run_id=run_id)
        return True

    def check_running_flow(self, run_id):
        from super_services.prefect_setup.deployments.utils import (
            trigger_deployment,
            check_flow_runs_filter,
        )

        flow_run_filter = {
            "name": {"like_": f"run-flow-call-{run_id}"},
            "state": {"name": {"any_": ["Running", "Scheduled"]}},
        }
        running_flows = asyncio.run(
            check_flow_runs_filter(flow_run_filter=flow_run_filter)
        )
        task_run_filter = {
            "name": {"like_": f"call-{run_id}-task"},
            "state": {
                "name": {"any_": ["Running", "Scheduled", "AwaitingConcurrencySlot"]}
            },
        }
        runing_tasks = asyncio.run(
            check_flow_runs_filter(flow_run_filter=task_run_filter, limit=30)
        )
        print_log(
            f"Running flows count {len(running_flows)} run_id {run_id} tasks {len(runing_tasks)}"
        )
        if not len(running_flows) and not len(runing_tasks):
            print_log("No running flows found, triggering deployment", run_id)
            asyncio.run(
                trigger_deployment(
                    "Check Reschedule Run",
                    {"job": {"run_id": run_id, "retry": 1, "run_type": "call"}},
                )
            )
        return True

    def check_pending_retry(self, runs):
        for run_id in runs:
            task_count = TaskModel._get_collection().count_documents(
                {"status": TaskStatusEnum.pending, "run_id": run_id}
            )
            print_log("Pending tasks count", task_count, "run_id", run_id)
            if task_count:
                self.check_running_flow(run_id)

    def check_run_cleanup(self, runs):
        from super_services.prefect_setup.deployments.utils import trigger_deployment

        for run_id in runs:
            task_service = TaskService()
            run = task_service.get_run(run_id)
            run_status = run.get("status")
            if run_status in ["completed", "failed", "partially_completed"]:
                print_log("Run cleanup", run_id, run_status)
                asyncio.run(
                    trigger_deployment(
                        "Execute-Run-Cleanup",
                        {"job": {"run_id": run_id, "run_type": "call"}},
                    )
                )

    def check_pending_runs(self, extra_runs):
        task_service = TaskService()

        last_hr = datetime.now(timezone.utc) - timedelta(days=10)
        query = {
            "status": "pending",
            "run_mode": "prefect",
            "created": {"$gte": last_hr},
        }
        runs = list(RunModel._get_collection().find(query))
        print_log("Pending runs count", len(runs))
        for run in runs:
            run_id = run.get("run_id")
            task_service.check_and_update_run_status(run_id=run_id)
            task_service.get_pending_tasks(run_id=run_id)
        run_ids = [run.get("run_id") for run in runs]
        run_ids = list(set(run_ids + extra_runs))
        self.check_pending_retry(run_ids)
        print_log("All pending retries checked")
        self.check_run_cleanup(run_ids)
        return True

    def check_run_concurrency(self):
        from super_services.prefect_setup.deployments.utils import (
            fetch_all_concurrency_list,
            trigger_deployment,
        )

        concurrency_limits = asyncio.run(fetch_all_concurrency_list())
        print_log("Concurrency limits", len(concurrency_limits))
        task_service = TaskService()
        for limit in concurrency_limits:
            tag = limit.tag
            if "run_" in tag:
                run_id = tag.split("run_")[1]
                run = task_service.get_run(run_id)
                run_status = run.get("status")
                if run_status in ["completed", "failed", "partially_completed"]:
                    print_log(
                        "Run cleanup", run_id, run_status, "check_run_concurrency"
                    )
                    asyncio.run(
                        trigger_deployment(
                            "Execute-Run-Cleanup",
                            {"job": {"run_id": run_id, "run_type": "call"}},
                        )
                    )

    def run(self):
        """Main execution method for updating VAPI calls."""
        tasks = self.get_all_tasks()
        print_log("Total tasks fetched", len(tasks))
        runs = self.extract_all_runs(tasks)
        print_log("Total runs fetched", len(runs))
        self.process_tasks(tasks)
        print_log("All tasks processed")
        # self.update_runs(runs)
        # print_log("All runs updated")
        self.check_pending_runs(runs)
        print_log("All pending runs checked")
        self.check_run_concurrency()


def update_vapi_calls():
    """Entry point for the inbound calls cron job."""
    updater = VapiCallUpdater()
    updater.run()


if __name__ == "__main__":
    update_vapi_calls()

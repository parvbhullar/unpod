from super_services.db.services.models.task import RunModel, TaskModel
from super_services.orchestration.webhook.webhook_handler import WebhookHandler
from super.app.call_execution import execute_post_call_workflow
from super_services.db.services.schemas.task import TaskStatusEnum
from super_services.libs.core.db import executeQuery
from super_services.voice.models.config import ModelConfig
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from dateutil import parser

load_dotenv(override=True)

import asyncio
import requests
import boto3
import json
import uuid
import os


class CallUpdater:
    """Handles synchronization of inbound calls with the task system."""

    def __init__(self):
        self.bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
        self.prefix = os.getenv("S3_FILE_PATH", "")
        self.region = os.getenv("AWS_DEFAULT_REGION")
        self.s3 = boto3.client("s3")
        self.auth_token = os.getenv("VAPI_AUTH_TOKEN")
        self.base_url = os.getenv("VAPI_BASE")
        self.state_file = os.getenv("INBOUND_CALLS_EXECUTION_PATH")
        self.webhook_handler = WebhookHandler()

    @staticmethod
    def convert_iso_to_mysql(dt_str: str) -> str | None:
        """Convert ISO datetime string to MySQL format."""
        if not dt_str:
            return None
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def get_last_execution_time(self) -> str | None:
        """Get the last execution time from the state file."""
        if not os.path.exists(self.state_file):
            with open(self.state_file, "w") as f:
                json.dump({"last_run": None}, f)
            return None

        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
                return data.get("last_run")
        except (json.JSONDecodeError, KeyError, ValueError):
            with open(self.state_file, "w") as f:
                json.dump({"last_run": None}, f)
            return None

    def update_last_execution_time(self):
        """Update the state file with the current execution time."""
        print(f"{self.state_file} updating cron run time")
        utc_now = datetime.now(timezone.utc)
        iso_z_format = utc_now.isoformat(timespec="milliseconds").replace("+00:00", "Z")

        with open(self.state_file, "w") as f:
            json.dump({"last_run": iso_z_format}, f)

    def get_call_logs(self, time: str) -> list:
        """Fetch call logs from VAPI API."""
        if time:
            url = f"{self.base_url}/call?updatedAtGt={time}&updatedAtLe={datetime.now() - timedelta(minutes=5)}"
        else:
            url = f"{self.base_url}/call"

        try:
            for i in range(3):
                print("Fetching all call logs")
                try:
                    res = requests.get(
                        url,
                        headers={
                            "Authorization": self.auth_token,
                            "Content-Type": "application/json",
                        },
                        timeout=30,
                    )
                    res.raise_for_status()
                    logs = res.json()
                    print(f"fetched {len(logs)} calls")
                    return logs
                except Exception as e:
                    print(f"failed to fetch call logs for {time} retrying : - {i} Time")
        except Exception as e:
            print(f"failed to fetch logs : - {e}")
            raise

    def get_recordings(self, time) -> dict:
        """Fetch recordings from S3 bucket."""
        paginator = self.s3.get_paginator("list_objects_v2")
        all_recordings = []

        if isinstance(time, str):
            time = parser.parse(time)
        if not time:
            time = datetime.now(timezone.utc) - timedelta(days=10)

        current_execution_time = datetime.now(timezone.utc) - timedelta(minutes=5)

        for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix):
            for obj in page.get("Contents", []):
                if time < obj["LastModified"] < current_execution_time and obj[
                    "Key"
                ].endswith(".wav"):
                    all_recordings.append(obj["Key"])

        call_map = {}
        url_pre = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/"

        for record in all_recordings:
            parts = record.split("/")
            call_map[parts[3][:36]] = url_pre + record

        print(f"Found {len(call_map)} recordings ")
        return call_map

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

    @staticmethod
    def get_pilot(assistant_id: str) -> dict:
        """Fetch pilot data for the given assistant ID."""
        query = """
        SELECT
        handle,
        space_id,
        created_by,
        config
        FROM core_components_pilot
        WHERE config->'voice'->>'vapi_agent_id' = %(assistant_id)s Limit 1;
        """

        print(f"fetching pilot data for {len(assistant_id)} agents")

        params = {"assistant_id": assistant_id}
        res = executeQuery(query, params)

        response = res if res else {}
        handle = res.get("handle") if res else None

        if handle:
            df_params = {"agent_id": handle}
            query2 = """
                SELECT dfv.values
                FROM dynamic_form_values dfv
                JOIN dynamic_forms df
                ON dfv.form_id = df.id
                WHERE dfv.parent_id = %(agent_id)s
                AND df.slug = 'webhook-integration';
            """
            ws = executeQuery(query2, df_params)

            if ws:
                response["webhook"] = ws.get("values", {})

        return response

    def _build_output_data(
        self, call: dict, call_id: str, task=None, recordings: dict = None
    ) -> dict:
        """Build output data dictionary for a call."""
        if task:
            output_data = {
                "call_id": call_id,
                "customer": task.input.get("name"),
                "contact_number": task.input.get("contact_number"),
                "call_end_reason": call.get("endedReason"),
                "recording_url": call.get("recordingUrl"),
                "transcript": call.get("transcript", []),
                "start_time": call.get("startedAt"),
                "end_time": call.get("endedAt"),
                "assistant_number": self.get_assistant_number(
                    call.get("phoneNumberId")
                ),
                "call_summary": call.get("summary"),
                "cost": call.get("cost"),
                "metadata": {
                    "cost": call.get("cost"),
                    "type": call.get("type"),
                },
            }
        else:
            output_data = {
                "call_id": call_id,
                "customer": call.get("customer", {}).get("name"),
                "contact_number": call.get("customer", {}).get("name"),
                "call_end_reason": call.get("endedReason"),
                "transcript": call.get("transcript", []),
                "start_time": call.get("startedAt"),
                "end_time": call.get("endedAt"),
                "assistant_number": self.get_assistant_number(
                    call.get("phoneNumberId")
                ),
                "call_summary": call.get("summary"),
                "cost": call.get("cost"),
                "metadata": {
                    "cost": call.get("cost"),
                    "type": call.get("type"),
                },
            }

        if recordings and not output_data.get("recording_url"):
            output_data["recording_url"] = recordings.get(call_id)

        return output_data

    def _update_existing_task(
        self, task, call: dict, call_id: str, recordings: dict
    ) -> bool:
        """Update an existing task with call data."""
        if (
            call.get("status") != "ended"
            or call.get("endedReason") == "call.in-progress.sip-completed-call"
        ):
            return False

        output_data = self._build_output_data(
            call, call_id, task=task, recordings=recordings
        )

        task_dict = {
            "task_id": task.task_id,
            "instructions": task.task.get("objective", ""),
            "input": task.input,
        }

        workflow_result = asyncio.run(
            execute_post_call_workflow(
                task.assignee, ModelConfig(), output_data, task_dict
            )
        )

        if workflow_result:
            output_data["post_call_data"] = workflow_result

        if not output_data["recording_url"]:
            print(
                f"\n\n\n no recording url for {call_id} {recordings.get(call_id)} \n\n"
            )
            output_data["recording_url"] = recordings.get(call_id)

        new_data = {"status": TaskStatusEnum.completed, "output": output_data}
        TaskModel.update_one({"task_id": task.task_id}, new_data)

        print("updating task")
        print("sending webhook request")

        asyncio.run(self.webhook_handler.execute(task_id=task.task_id))
        return True

    def _create_new_task(self, call: dict, call_id: str, recordings: dict) -> bool:
        """Create a new task for an inbound call."""
        pilot = self.get_pilot(call.get("assistantId"))

        run_id = f"R{uuid.uuid1().hex}"
        tasks = list(TaskModel.find(assignee=pilot.get("handle")))

        if pilot.get("space_id"):
            space_id = pilot.get("space_id")
        elif tasks:
            latest = max(tasks, key=lambda t: t.created)
            space_id = latest.space_id
        else:
            space_id = None

        print(f"creating run for {space_id} with run id {run_id}")

        RunModel.save_single_to_db(
            {
                "run_id": run_id,
                "space_id": str(space_id),
                "batch_count": 1,
                "collection_ref": "",
                "run_mode": "dev",
                "thread_id": "3576856834654",
                "owner_org_id": "",
                "status": TaskStatusEnum.completed,
                "user": "",
            }
        )

        task_id = f"T{uuid.uuid1().hex}"

        data = {
            "task_id": task_id,
            "space_id": str(space_id),
            "user": "",
            "run_id": run_id,
            "thread_id": "3576856834654",
            "collection_ref": "",
            "task": {},
            "assignee": pilot.get("handle", ""),
            "status": TaskStatusEnum.completed,
            "execution_type": "call",
            "provider": "vapi",
            "retry_attempt": 0,
            "last_status_change": datetime.utcnow().isoformat(),
            "input": {
                "vapi_agent_id": call.get("assistantId"),
                "quality": "high",
            },
        }

        output_data = self._build_output_data(call, call_id, recordings=recordings)

        task_dict = {
            "task_id": task_id,
            "instructions": {},
            "input": {},
        }

        workflow_result = asyncio.run(
            execute_post_call_workflow(
                pilot.get("handle"), ModelConfig(), output_data, task_dict
            )
        )

        if workflow_result:
            output_data["post_call_data"] = workflow_result

        output_data["recording_url"] = recordings.get(call_id)
        data["output"] = output_data

        TaskModel.save_single_to_db(data)

        print("Created task with id", task_id)
        print("sending webhook request")

        asyncio.run(self.webhook_handler.execute(task_id=task_id))
        return True

    def process_tasks(self, calls: list, recordings: dict):
        """Process all calls and create/update tasks accordingly."""
        new_tasks = 0
        updated_tasks = 0

        for call in calls:
            call_id = call.get("id")

            if not call_id:
                continue

            tasks = list(
                TaskModel._get_collection().find(
                    {"output.call_id": call_id, "status": TaskStatusEnum.in_progress},
                    sort=[("modified", -1)],
                )
            )

            print(f"{call_id} -> {len(tasks)} tasks")

            if tasks:
                task = TaskModel.get(task_id=tasks[0].get("task_id"))
                if self._update_existing_task(task, call, call_id, recordings):
                    updated_tasks += 1
            else:
                if self._create_new_task(call, call_id, recordings):
                    new_tasks += 1

        print(f"new tasks: {new_tasks}")
        print(f"updated tasks: {updated_tasks}")

    def run(self):
        """Execute the inbound calls flow."""
        time = self.get_last_execution_time()
        calls = self.get_call_logs(time)
        recordings = self.get_recordings(time)
        self.process_tasks(calls, recordings)
        print(f"{len(calls)} calls found for {time}")
        self.update_last_execution_time()


def inbound_calls_flow():
    """Entry point for the inbound calls cron job."""
    updater = CallUpdater()
    updater.run()


if __name__ == "__main__":
    inbound_calls_flow()

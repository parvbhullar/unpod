import asyncio
import os
import traceback
import uuid

# from datetime import datetime
from typing import Dict, Optional, List

# from dateutil import parser
import json

from super.app.providers import CallProviderFactory, VapiProvider
from super.core.logging.logging import print_log
from super_services.db.services.models.task import (
    RunModel,
    TaskModel,
    TaskExecutionLogModel,
    ArtifactModel,
)
from super_services.db.services.repository.wallet import (
    addTaskRequest,
    calculateBit,
    checkWallet,
)
from super_services.db.services.schemas.task import TaskStatusEnum
from super_services.libs.core.jsondecoder import convertFromMongo
from super_services.libs.core.model import updateModelInstance
from super_services.libs.core.db import executeQuery
from super_services.voice.models.config import ModelConfig, MessageCallBack


def run_async_in_thread(fun, *args, **kwargs):
    loop = asyncio.new_event_loop()  # create a new loop
    asyncio.set_event_loop(loop)  # set it for this thread
    result = loop.run_until_complete(fun(*args, **kwargs))
    loop.close()
    return result


class TaskService:
    """Core Task Service for handling task execution and management"""

    def insert_call_log(self, response: Dict, data: Dict, task) -> None:
        """Insert call log data into database"""
        call_type = data.get("call_type", "outbound")

        source = data.get("assistant_number", "NULL")
        destination = data.get("contact_number", "NULL")

        query = f"""
            INSERT INTO metrics_calllog (
            call_status,
            end_reason,
            start_time,
            end_time,
            call_type,
            call_duration,
            source_number,
            destination_number,
            metrics_metadata,
            agent_id,
            bridge_id,
            organization_id,
            space_id,
            creation_time,
            product_types,
            calculated,
            product_id
            )
            VALUES (
            %(call_status)s,
            %(end_reason)s,
            %(start_time)s,
            %(end_time)s,
            %(call_type)s,
            (%(end_time)s::timestamp - %(start_time)s::timestamp),
            %(source)s,
            %(destination)s,
            %(metadata)s,
            (SELECT id FROM core_components_pilot WHERE handle = %(assignee)s LIMIT 1),
            (SELECT tvn.bridge_id
            FROM telephony_voicebridgenumber tvn
            JOIN core_components_telephony_number n ON tvn.number_id = n.id
            WHERE n.number = %(source)s OR n.number = %(destination)s
            LIMIT 1),
            (SELECT space_organization_id FROM space_space WHERE id = %(space_id)s LIMIT 1),
            %(space_id)s,
            NOW(),
            'ai_agents',
            FALSE,
            COALESCE((
                SELECT b.product_id
                FROM telephony_voicebridge b
                JOIN telephony_voicebridgenumber tvn ON tvn.bridge_id = b.id
                JOIN core_components_telephony_number n ON tvn.number_id = n.id
                WHERE n.number = %(source)s OR n.number = %(destination)s
                LIMIT 1
            ), 'unpod.ai')
            );
        """

        if call_type == "outbound":
            source = source
            destination = destination
        else:
            source = destination
            destination = source

        # Handle datetime fields with proper validation and defaults
        from datetime import datetime

        # Get start_time and end_time with proper handling
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        # Convert ISO strings to datetime objects if needed
        if isinstance(start_time, str):
            try:
                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                start_time = None

        if isinstance(end_time, str):
            try:
                end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                end_time = None

        # Provide default values if None
        current_time = datetime.now()
        if start_time is None:
            start_time = current_time
        if end_time is None:
            end_time = current_time

        params = {
            "call_status": response.get("status"),
            "end_reason": data.get("call_end_reason", ""),
            "start_time": start_time,
            "end_time": end_time,
            "call_type": call_type,
            "source": source,
            "destination": destination,
            "metadata": json.dumps(
                {
                    "cost": data.get("cost", 0),
                    "type": data.get("type", "outboundPhoneCall"),
                    "provider": os.getenv(
                        "AGENT_PROVIDER", "call"
                    ),  # Will be dynamic based on provider
                }
            ),
            "assignee": task.assignee,
            "space_id": task.space_id,
            "duration": data.get("duration", 0),
        }

        update_query = f"""
            WITH org_data AS (
                SELECT space_organization_id as org_id
                FROM space_space
                WHERE id = %(space_id)s
                LIMIT 1
            ),
            call_stats AS (
                SELECT
                    COALESCE(COUNT(*), 0) AS total_calls,
                    COALESCE(ROUND(AVG(EXTRACT(EPOCH FROM call_duration))::numeric, 2), 0) AS avg_duration,
                    COALESCE(SUM((metrics_metadata->>'cost')::decimal(10,2)), 0) AS total_cost,
                    COALESCE(ROUND(AVG((metrics_metadata->>'cost')::decimal(10,2))::numeric, 2), 0) AS avg_cost
                FROM metrics_calllog
                WHERE organization_id = (SELECT org_id FROM org_data)
            )
            UPDATE metrics_metrics
            SET value = CASE name
                WHEN 'Number of Calls' THEN (SELECT total_calls FROM call_stats)
                WHEN 'Avg Duration' THEN (SELECT avg_duration FROM call_stats)
                WHEN 'Total Cost' THEN (SELECT total_cost FROM call_stats)
                WHEN 'Avg Cost' THEN (SELECT avg_cost FROM call_stats)
            END
            WHERE organization_id = (SELECT org_id FROM org_data)
            AND name IN ('Number of Calls', 'Avg Duration', 'Total Cost', 'Avg Cost');
        """

        try:
            executeQuery(query, params=params, commit=True)
        except Exception as ex:
            print_log(
                f"Call log insert failed at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "call_log_insert_error",
            )

        try:
            executeQuery(update_query, params=params, commit=True)
        except Exception as ex:
            print_log(
                f"Metrics update failed at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "call_log_metrics_error",
            )
            try:
                executeQuery(update_query, params=params, commit=True)
            except Exception as ex:
                print_log(
                    f"Retrying metrics update failed at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                    "call_log_metrics_error",
                )

    def calculate_and_deduct_cost(self, data: Dict, task) -> None:
        """Calculate and deduct cost for task execution"""
        cost = data.get("cost", 0)
        if not cost:
            return

        usage = data.get("metadata", {}).get("usage", {})

        request_log = {
            "thread_id": task.thread_id,
            "user": task.user_info,
            "org_id": task.user_org_id,
            "pilot": task.assignee,
            "cost": round(float(cost), 3),
            "currency": "USD",
            "tokens": usage,
        }

        request_log["bits"] = calculateBit(request_log["cost"], request_log["currency"])

        print_log(
            f"Request Log for Cost Deduction: {request_log}", "cost_deduction_info"
        )
        try:
            wallet = checkWallet(task.user_info)
            addTaskRequest(**request_log, wallet=wallet)
        except Exception as ex:
            print_log(
                f"Cost deduction failed at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "cost_deduction_error",
            )

    def create_run(
        self,
        space_id: str,
        user: str,
        collection_ref: str,
        batch_count: int = 0,
        run_mode: str = "dev",
        thread_id: Optional[str] = None,
        owner_org_id: Optional[str] = None,
        **run_data,
    ) -> Dict:
        """Create a new run"""
        run_id = f"R{uuid.uuid1().hex}"

        run = RunModel.save_single_to_db(
            {
                "run_id": run_id,
                "space_id": space_id,
                "batch_count": batch_count,
                "collection_ref": collection_ref,
                "run_mode": run_mode,
                "thread_id": thread_id,
                "owner_org_id": owner_org_id,
                "user": user,
                **run_data,
            }
        )
        return run.dict()

    def add_task(
        self,
        run_id: str,
        task_data: Dict,
        assignee: str,
        collection_ref: str,
        thread_id: Optional[str] = None,
        execution_type: Optional[str] = None,
        **task_data_kargs,
    ) -> Dict:
        """Add a task to a run"""
        from datetime import datetime

        task_id = f"T{uuid.uuid1().hex}"

        # Set provider based on execution_type or environment
        provider = "NA"
        if execution_type == "call":
            provider = CallProviderFactory.get_provider_type(task_data)

        task_obj = {
            "task_id": task_id,
            "run_id": run_id,
            "thread_id": thread_id,
            "collection_ref": collection_ref,
            "task": task_data,
            "assignee": assignee,
            "status": TaskStatusEnum.pending,
            "execution_type": execution_type,
            "provider": provider,  # Set provider field
            "retry_attempt": 0,  # Initialize retry attempt
            "last_status_change": datetime.utcnow().isoformat(),  # Set initial timestamp
            **task_data_kargs,
        }
        task = TaskModel.save_single_to_db(task_obj)
        return task.dict()

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatusEnum,
        output: Optional[Dict] = None,
        expected_status: Optional[TaskStatusEnum] = None,
    ) -> Dict:
        """
        Update task status and output with optional atomic compare-and-swap.

        Args:
            task_id: Task identifier
            status: New status to set
            output: Optional output data
            expected_status: If provided, only update if current status matches (atomic CAS)

        Returns:
            Updated task dict or error dict

        IDEMPOTENCY FIX: Supports atomic status transitions to prevent race conditions.
        When expected_status is provided, update only succeeds if current status matches.
        """
        from datetime import datetime

        # Build update data
        update_data = {
            "status": status,
            "last_status_change": datetime.utcnow().isoformat(),
        }
        if output:
            for key, value in output.items():
                update_data[f"output.{key}"] = value

        # Build query with optional status check for atomic CAS
        query = {"task_id": task_id}
        if expected_status is not None:
            # Atomic compare-and-swap: only update if status matches expected
            query["status"] = expected_status
            print_log(
                f"Attempting atomic status update for task {task_id}: {expected_status} → {status}",
                "atomic_status_update_attempt",
            )

        # Perform atomic update
        result = TaskModel._get_collection().update_one(query, {"$set": update_data})

        if result:
            # Fetch updated task to return
            updated_task = TaskModel.get(task_id=task_id)
            if updated_task:
                if expected_status is not None:
                    print_log(
                        f"Atomic status update succeeded for task {task_id}: {expected_status} → {status}",
                        "atomic_status_update_success",
                    )
                return updated_task.dict()

        # Update failed - check why
        task = TaskModel.get(task_id=task_id)
        if not task:
            print_log(
                f"Task {task_id} not found during status update",
                "task_not_found_on_update",
            )
            return {"error": "Task not found"}

        if expected_status is not None and task.status != expected_status:
            # Status mismatch - another worker already updated it
            print_log(
                f"⚠️  DUPLICATE PREVENTED: Atomic status update failed for task {task_id}. "
                f"Expected status {expected_status}, but current status is {task.status}. "
                f"Another worker likely processed this task.",
                "atomic_status_update_failed_duplicate_prevented",
            )
            return {
                "error": "Status mismatch",
                "current_status": task.status,
                "task": task.dict(),
            }

        return {"error": "Update failed"}

    def update_task_status_atomic(
        self,
        task_id: str,
        from_status: TaskStatusEnum,
        to_status: TaskStatusEnum,
        output: Optional[Dict] = None,
    ) -> tuple[bool, Dict]:
        """
        Atomically transition task status with compare-and-swap.

        Args:
            task_id: Task identifier
            from_status: Expected current status
            to_status: New status to set
            output: Optional output data

        Returns:
            Tuple of (success: bool, task_dict or error_dict)

        IDEMPOTENCY FIX: Use this method to ensure only one worker processes a task.
        Returns (True, task_dict) if update succeeded, (False, error_dict) if task
        was already in a different status (indicating another worker took it).
        """
        result = self.update_task_status(
            task_id, to_status, output, expected_status=from_status
        )

        if "error" in result:
            if result["error"] == "Status mismatch":
                # Another worker already took this task
                return False, result
            else:
                # Other error (task not found, etc.)
                return False, result

        # Update succeeded
        return True, result

    def process_task(self, task_id: str, batch_count: int = 1) -> bool:
        try:
            task: TaskModel.Meta.model = TaskModel.get(task_id=task_id)
        except Exception as ex:
            print_log(
                f"Task retrieval failed for {task_id} at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "task_get_error",
            )
            task = None
        try:
            if not task:
                print_log(f"Task {task_id} not found", "task_not_found")
                return {}

            # Skip enqueueing if task is already being handled elsewhere
            if task.status in {
                TaskStatusEnum.in_progress,
                TaskStatusEnum.hold,
                TaskStatusEnum.completed,
                TaskStatusEnum.processing,
            }:
                print_log(
                    f"Task {task_id} already {task.status}, skipping duplicate enqueue",
                    "task_enqueue_skip_existing",
                )
                return task.dict()

            # Read batch_count from Run model instead of using parameter default
            # This ensures bulk batches are routed to bulk queue
            try:
                run = RunModel.find_one(run_id=task.run_id)
                if run and hasattr(run, "batch_count"):
                    batch_count = getattr(run, "batch_count", batch_count)
                    print_log(
                        f"Task {task_id} belongs to run {task.run_id} with batch_count={batch_count}",
                        "task_batch_count_from_run",
                    )
            except Exception as run_ex:
                print_log(
                    f"Failed to fetch run {task.run_id} for batch_count, using default: {str(run_ex)}",
                    "run_fetch_error_batch_count",
                )

            # Check if task has exceeded max retries
            max_retries = int(os.getenv("MAX_CALL_RETRIES", "3"))
            current_retry_attempt = getattr(task, "retry_attempt", 0)

            if current_retry_attempt >= max_retries:
                print_log(
                    f"Task {task_id} has exceeded maximum retries ({max_retries}), marking as permanently failed",
                    "task_max_retries_exceeded",
                )
                self._mark_task_permanently_failed(task)
                self.check_and_update_run_status(task.run_id)
                return task.dict()

            # Create execution log
            exec_id = f"TE{uuid.uuid1().hex}"
            exec_log_data = {
                "task_exec_id": exec_id,
                "task_id": task.task_id,
                "run_id": task.run_id,
                "executor_id": "default",
                "status": TaskStatusEnum.in_progress,
                "input": task.input,
                "output": task.output,
                "space_id": task.space_id,
                "data": {},
            }
            exec_status = TaskExecutionLogModel.save_single_to_db(exec_log_data)

            success = False
            response = {"status": "failed", "data": {}}

            print(f"\nProcessing Task {task.task_id} : {task.execution_type}\n")

            if task.execution_type == "call" and len(task.input) > 0:
                print("Call Execution")

                try:
                    # Execution log already created with in_progress status at line 367
                    # from super.app.call_execution import execute_call

                    quality = task.input.get("quality", "good")

                    # if quality == "high":
                    #     # For high quality, use asyncio run directly
                    #     response = run_async_in_thread(
                    #         execute_call,
                    #         data=task.input,
                    #         task_id=task.task_id,
                    #         agent_id=task.assignee,
                    #         instructions=task.task["objective"],
                    #         model_config=ModelConfig(),
                    #         callback=MessageCallBack(),
                    #     )
                    # else:
                    # For low quality, push the topic to Kafka queue
                    from super_services.voice.consumers.voice_task_consumer import (
                        TaskServiceQueueManager,
                    )

                    TaskServiceQueueManager().add_to_outbound_call_queue(
                        agent_id=task.assignee,
                        task_id=task.task_id,
                        data=task.input,
                        instructions=task.task["objective"],
                        model_config=ModelConfig(),
                        callback=MessageCallBack(),
                        batch_count=batch_count,
                    )
                    response = None
                    # Kafka consumer will pick up and process the call asynchronously and handle the response

                    if response and response.get("data"):
                        data = response.get("data")
                        self.insert_call_log(response, data, task)
                        self.calculate_and_deduct_cost(data, task)
                    elif not response:
                        # Task was queued to Kafka, mark as in_progress and don't process response yet
                        print_log(
                            f"Task {task.task_id} queued for async processing",
                            "task_queued_kafka",
                        )
                        response = {
                            "status": "in_progress",
                            "data": {"message": "Task queued for async processing"},
                        }
                except Exception as ex:
                    print_log(
                        f"Call execution failed for task {task.task_id} at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                        "call_execution_error",
                    )
                    response = {"status": "failed", "data": {}}

                # Classfiacation of call and transcription analysis can be added here

                # from services.task_service.services.classification import (
                #     call_classification,
                # )
                #
                # input = {
                #     "token": task.user["token"],
                #     "data": data,
                # }
                #
                # label =call_classification(input)

            if task.execution_type == "email":
                # TODO : Email Execution Engine
                # Execution log already created with in_progress status at line 367

                response = {
                    "status": "completed",
                    "data": {"email_id": "task@email.com"},
                }

            if task.execution_type == "email_classification" and len(task.input) > 0:
                # Call the classification service
                print("Classification Execution")
                try:
                    # Execution log already created with in_progress status at line 367
                    # TODO import email classification service from messaging service
                    # from services.task_service.services.classification import (
                    #     email_classification,
                    # )
                    #
                    response = {
                        "status": "failed",
                        "data": {"message": "No Logic to process"},
                    }
                except Exception as ex:
                    print_log(
                        f"Email classification failed for task {task.task_id} at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                        "email_classification_error",
                    )
                    response = {"status": "failed", "data": {}}

            if task.execution_type == "dealer" and len(task.input) > 0:
                # Call the dealer service
                print("Dealer App Execution")
                try:
                    # Execution log already created with in_progress status at line 367
                    # from services.task_service.services.dealer_service import (
                    #     dealer_service,
                    # )
                    #
                    # response = dealer_service(task.input)
                    pass
                except Exception as ex:
                    print_log(
                        f"Dealer service failed for task {task.task_id} at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                        "dealer_service_error",
                    )
                    response = {"status": "failed", "data": {}}

            if task.execution_type == "space_call" and len(task.input) > 0:
                # Call the space call service
                print("Space Call Execution")
                try:
                    # Execution log already created with in_progress status at line 367
                    # TODO import and handle the space call service
                    # from services.task_service.services.space_call import space_call
                    #
                    # input_data = task.input
                    # input_data["room"] = "room_" + str(exec_id)
                    # input_data["objective"] = task.task["objective"]
                    # input_data["handle"] = task.assignee
                    # response = space_call(input_data)
                    pass
                except Exception as ex:
                    print_log(
                        f"Space call failed for task {task.task_id} at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                        "space_call_error",
                    )
                    response = {"status": "failed", "data": {}}

            # Handle different response statuses
            if response["status"] == "completed":
                success = True
                task_status = TaskStatusEnum.completed
                exec_status = TaskStatusEnum.completed
                # Reset retry attempt on success
                retry_attempt = 0
                last_failure_reason = None
                print_log(
                    f"Task {task.task_id} completed successfully", "task_completed"
                )
            elif response["status"] == "in_progress":
                # Task was queued to Kafka, keep current retry attempt and set to in_progress
                task_status = TaskStatusEnum.in_progress
                exec_status = TaskStatusEnum.in_progress
                retry_attempt = current_retry_attempt  # Don't increment retry attempt
                last_failure_reason = None  # Clear any previous failure reason
                print_log(
                    f"Task {task.task_id} queued for async processing via Kafka",
                    "task_kafka_queued",
                )
                success = None  # Neither success nor failure - it's pending processing
            else:
                # Task actually failed - Note: The Kafka worker will handle retries
                # Here we just record the failure without incrementing retry_attempt
                success = False
                retry_attempt = (
                    current_retry_attempt  # Keep current, worker will increment
                )
                last_failure_reason = response.get("data", {}).get(
                    "error", "Unknown error"
                )

                if retry_attempt >= max_retries:
                    task_status = TaskStatusEnum.failed
                    print_log(
                        f"Task {task.task_id} permanently failed after {retry_attempt} attempts. Last error: {last_failure_reason}",
                        "task_permanently_failed",
                    )
                else:
                    if task.execution_type in ["email_classification"]:
                        task_status = TaskStatusEnum.failed
                        print_log(
                            f"Task {task.task_id} of type email_classification failed (attempt {retry_attempt}/{max_retries}). No retries will be attempted. Error: {last_failure_reason}",
                            "task_email_classification_failed",
                        )
                    else:
                        task_status = (
                            TaskStatusEnum.pending
                        )  # Keep as pending for retry
                        print_log(
                            f"Task {task.task_id} failed (attempt {retry_attempt}/{max_retries}). Will be retried by worker. Error: {last_failure_reason}",
                            "task_retry_scheduled",
                        )

                exec_status = TaskStatusEnum.failed

            try:
                from datetime import datetime

                update_data = {
                    "status": task_status,
                    "output": response["data"],
                    "retry_attempt": retry_attempt,
                    "last_status_change": datetime.utcnow().isoformat(),  # Update timestamp
                }
                if last_failure_reason:
                    update_data["last_failure_reason"] = last_failure_reason

                updateModelInstance(
                    TaskModel,
                    {"task_id": task.task_id},
                    update_data,
                )
                TaskExecutionLogModel.update_one(
                    {"task_exec_id": exec_id},
                    {"status": exec_status, "output": response["data"]},
                )

                # Check if run should be updated to failed status
                if task_status in [
                    TaskStatusEnum.completed,
                    TaskStatusEnum.failed,
                    TaskStatusEnum.partially_completed,
                ]:
                    self.check_and_update_run_status(task.run_id)
                print_log("Completed _check_and_update_run_status")

            except Exception as ex:
                print_log(
                    f"Task status update failed for {task.task_id} at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                    "task_status_update_error",
                )
            return TaskModel.get(task_id=task_id).dict()
        except Exception as e:
            print_log(
                f"Critical error processing task {task_id} at line {e.__traceback__.tb_lineno}: {str(e)}\n{traceback.format_exc()}",
                "process_task_critical_error",
            )
            if "task" in locals() and task:
                return task.dict()
            else:
                return {
                    "error": f"Task processing failed: {str(e)}",
                    "task_id": task_id,
                }

    def get_run_status(self, run_id: str) -> Dict:
        """Get status of a run and its tasks"""
        run = RunModel.find_one(run_id=run_id)
        if not run:
            return {"error": "Run not found"}

        tasks = list(TaskModel.find(run_id=run_id))
        task_stats = {
            "total": len(tasks),
            "completed": len(
                [t for t in tasks if t.status == TaskStatusEnum.completed]
            ),
            "failed": len([t for t in tasks if t.status == TaskStatusEnum.failed]),
            "pending": len([t for t in tasks if t.status == TaskStatusEnum.pending]),
        }

        return {"run": run, "task_stats": task_stats}

    def add_artifact(
        self,
        file_id: str,
        path: str,
        space_id: str,
        thread_id: Optional[str] = None,
        run_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Dict:
        """Add an artifact"""
        artifact_data = {
            "file_id": file_id,
            "path": path,
            "space_id": space_id,
            "thread_id": thread_id,
            "run_id": run_id,
            "task_id": task_id,
        }
        artifact = ArtifactModel.create(artifact_data)
        return artifact.dict()

    def get_pending_tasks(
        self, run_id: Optional[str] = None, run_status: Optional[str] = None
    ) -> List[Dict]:
        """Get pending tasks for processing"""
        try:
            query = {"status": TaskStatusEnum.pending}
            if run_id:
                query["run_id"] = run_id

            print_log(
                f"Querying pending tasks with: {query}", "get_pending_tasks_query"
            )
            if run_status and run_status == "scheduled":
                query["status"] = TaskStatusEnum.scheduled
                print_log(
                    f"Adjusted query for scheduled run: {query}",
                    "As run status is scheduled",
                    "get_pending_tasks_scheduled_query",
                )

            tasks = TaskModel.find(**query)
            task_list = list(tasks)

            print_log(
                f"Found {len(task_list)} pending tasks for run_id: {run_id}",
                "get_pending_tasks_result",
            )

            # Also check tasks that may need status updates (exclude completed and hold)
            # OPTIMIZATION: Don't fetch completed or hold tasks as they require no action
            if run_id:
                all_tasks = list(
                    TaskModel.find(
                        run_id=run_id,
                        status={
                            "$nin": [
                                TaskStatusEnum.completed,
                                TaskStatusEnum.hold,
                                TaskStatusEnum.scheduled,
                                TaskStatusEnum.in_progress,
                            ]
                        },  # Exclude completed and hold tasks
                    )
                )
                print_log(
                    f"Total actionable tasks for run {run_id}: {len(all_tasks)} (excluding completed and hold)",
                    "get_pending_tasks_total",
                )
                for task in all_tasks:
                    # print_log(
                    #     f"Task {task.task_id}: status={task.status}, execution_type={task.execution_type}",
                    #     "get_pending_tasks_debug",
                    # )
                    try:
                        self.mark_task_status(task)
                    except Exception as ex:
                        print_log(
                            f"Failed to mark task {task.task_id} as permanently failed at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                            "mark_task_failed_error",
                        )

            return [task.dict() for task in task_list]
        except Exception as ex:
            print_log(
                f"Failed to get pending tasks for {run_id} at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "get_pending_tasks_error",
            )
            return []

    def get_query(
        self,
        space_id: Optional[str] = None,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ):
        query = {}
        if space_id:
            query["space_id"] = space_id
        if user_id:
            query["user"] = user_id
        if thread_id:
            query["thread_id"] = thread_id
        return query

    def get_runs(
        self,
        space_id: Optional[str] = None,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get pending runs for processing"""
        try:
            query = self.get_query(space_id, user_id, thread_id)
            if not query:
                return [], 0
            tasks = RunModel._get_collection().find(query, sort=[("_id", -1)])
            count = RunModel._get_collection().count_documents(query)
            return [convertFromMongo(task) for task in tasks], count
        except Exception as ex:
            print_log(
                f"Failed to get runs at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "get_runs_error",
            )
            return [], 0

    def get_tasks(
        self,
        space_id: Optional[str] = None,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get pending tasks for processing"""
        try:
            query = self.get_query(space_id, user_id, thread_id)
            if not query:
                return [], 0
            tasks = TaskModel._get_collection().find(query, sort=[("_id", -1)])
            count = TaskModel._get_collection().count_documents(query)
            return [convertFromMongo(task) for task in tasks], count
        except Exception as ex:
            print_log(
                f"Failed to get tasks at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "get_tasks_error",
            )
            return [], 0

    def get_run_tasks(
        self,
        run_id,
        space_id: Optional[str] = None,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get pending tasks for processing"""
        try:
            query_extra = self.get_query(space_id, user_id, thread_id)
            if not query_extra:
                return [], 0
            query = {"run_id": run_id, **query_extra}
            tasks = TaskModel._get_collection().find(query, sort=[("_id", -1)])
            count = TaskModel._get_collection().count_documents(query)
            return [convertFromMongo(task) for task in tasks], count
        except Exception as ex:
            print_log(
                f"Failed to get run tasks for {run_id} at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "get_run_tasks_error",
            )
            return [], 0

    def _mark_task_permanently_failed(self, task) -> None:
        """Mark a task as permanently failed due to exceeding max retries"""
        try:
            updateModelInstance(
                TaskModel,
                {"task_id": task.task_id},
                {
                    "status": TaskStatusEnum.failed,
                    "output": {
                        "error": f"Task exceeded maximum retries ({getattr(task, 'retry_attempt', 0)})"
                    },
                },
            )
            print_log(
                f"Task {task.task_id} marked as permanently failed",
                "task_permanently_failed",
            )
        except Exception as ex:
            print_log(
                f"Failed to mark task {task.task_id} as permanently failed at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "mark_task_failed_error",
            )

    @staticmethod
    def _is_retryable_call_error(error_message: str) -> bool:
        if not error_message:
            return False

        retryable_errors = [
            "failed to get call status",
            "sip-480-temporarily-unavailable",
            "call.in-progress.error-sip-outbound-call-failed-to-connect",
            "rate-limit",
            "ratelimit",
            "too-many-requests",
            "temporarily-unavailable",
            "providerfault",
            "rate limit exceeded",
            "over concurrency limit",
            "call ended unexpectedly",
            "account not authorized to call",
            "failed to start call",
            "call ended unexpectedly",
        ]

        error_lower = error_message.lower()
        return any(
            retryable_error in error_lower for retryable_error in retryable_errors
        )

    @staticmethod
    def _is_api_error(error_message: str) -> bool:
        if not error_message:
            return False

        api_errors = [
            "failed to get call status",
            "failed to fetch call",
            "api error",
            "connection error",
            "timeout",
            "network error",
        ]

        error_lower = error_message.lower()
        return any(api_error in error_lower for api_error in api_errors)

    @staticmethod
    def _is_customer_error(error_message: str) -> bool:
        if not error_message:
            return False

        customer_errors = [
            "did not answer",
            "customer-did-not-answer",
            "voicemail",
            "busy",
            "call rejected",
            "declined",
            "user busy",
            "not answered",
        ]

        error_lower = error_message.lower()
        return any(customer_error in error_lower for customer_error in customer_errors)

    def mark_task_status(self, task):
        from datetime import datetime, timedelta

        error = task.output.get("error") or task.last_failure_reason or ""
        retry_attempt = getattr(task, "retry_attempt", 0)
        max_retries = int(os.getenv("MAX_CALL_RETRIES", "3"))
        stats = {
            "failed_tasks_retried": 0,
            "failed_tasks_kept": 0,
            "stuck_tasks_retried": 0,
        }
        update_data = None
        message = ""

        if task.status == TaskStatusEnum.completed:
            return  # No action needed for completed tasks

        task_status = None
        result = task.output if task.output else {}
        if task.status == TaskStatusEnum.failed:
            if (
                TaskService._is_retryable_call_error(error)
                and retry_attempt < max_retries
            ):
                # Retry for retryable errors
                task_status = TaskStatusEnum.pending
                stats["failed_tasks_retried"] += 1
                print_log(
                    f"Task {task.task_id} marked as pending for retry (attempt {retry_attempt + 1}/{max_retries}). Error: {error}",
                    "call_recovery_task_retried",
                )
            elif TaskService._is_api_error(error):
                from super.app.call_execution import (
                    execute_post_call_workflow,
                )

                # API Error: Fetch the call status from provider and run post-call workflow
                try:
                    print_log(
                        f"Task {task.task_id} has API error, executing post-call workflow to fetch status",
                        "call_recovery_api_error",
                    )
                    # Ensure task.input is a dict (parse if it's a JSON string)
                    import json

                    task_input = task.input
                    if isinstance(task_input, str):
                        try:
                            task_input = json.loads(task_input)
                        except (json.JSONDecodeError, ValueError):
                            task_input = {}
                    elif not isinstance(task_input, dict):
                        task_input = {}

                    task_dict = {
                        "task_id": task.task_id,
                        "instructions": task.task.get("objective", ""),
                        "input": task_input,
                    }
                    result = task.output if task.output else {}
                    agent_id = task.assignee
                    # print(result)
                    # Fetch call status from provider
                    provider = CallProviderFactory.create_provider(task_input)
                    if isinstance(provider, VapiProvider):
                        result = asyncio.run(provider.update_call_data(task))
                        task.output = result

                    # Execute post-call workflow to get actual call status
                    workflow_result = asyncio.run(
                        execute_post_call_workflow(
                            agent_id, ModelConfig(), result, task_dict
                        )
                    )
                    if workflow_result:
                        task_status = TaskStatusEnum.completed
                        # Only include valid task output fields, exclude 'classification' and other non-model fields
                        update_data = {
                            "status": task_status,
                            "output": workflow_result,  # Store entire workflow result in output field
                            "retry_attempt": retry_attempt + 1,
                            "last_status_change": datetime.utcnow().isoformat(),
                        }
                        print_log(
                            f"Task {task.task_id} post-call workflow completed successfully",
                            "call_recovery_workflow_success",
                        )
                except Exception as ex:
                    print_log(
                        f"Failed to execute post-call workflow for task {task.task_id}: {str(ex)}",
                        "call_recovery_workflow_error",
                    )
                    raise ex
            elif TaskService._is_customer_error(error):
                # Customer Error: Mark as completed with appropriate message
                task_status = TaskStatusEnum.completed
                user_reject_retry = int(os.getenv("USER_REJECT_RETRY", "2"))
                if "did not answer" in error.lower() or "no answer" in error.lower():
                    if retry_attempt < user_reject_retry:
                        task_status = TaskStatusEnum.pending
                        stats["failed_tasks_retried"] += 1
                    message = "Call completed - Customer did not answer"
                elif "voicemail" in error.lower():
                    message = "Call completed - Reached voicemail"
                    if retry_attempt < user_reject_retry:
                        task_status = TaskStatusEnum.pending
                        stats["failed_tasks_retried"] += 1
                elif "busy" in error.lower() or "user busy" in error.lower():
                    message = "Call completed - Customer was busy"
                elif "rejected" in error.lower() or "declined" in error.lower():
                    message = "Call completed - Call was rejected by customer"
                else:
                    message = "Call completed - Customer unavailable"
                print_log(
                    f"Task {task.task_id} has customer error, marking as completed: {message}",
                    "call_recovery_customer_error",
                )
            else:
                stats["failed_tasks_kept"] += 1
                if retry_attempt >= max_retries:
                    # print_log(
                    #     f"Task {task.task_id} kept as failed - max retries reached ({retry_attempt}/{max_retries})",
                    #     "call_recovery_max_retries",
                    # )
                    pass
                else:
                    print_log(
                        f"Task {task.task_id} kept as failed - non-retryable error: {error}",
                        "call_recovery_non_retryable",
                    )
                return  # Keep as failed, no action needed

        if task.status in [TaskStatusEnum.in_progress, TaskStatusEnum.processing]:
            in_progress_hold_minutes = int(os.getenv("IN_PROGRESS_HOLD_MINUTES", "15"))
            one_hour_ago = datetime.utcnow() - timedelta(
                minutes=in_progress_hold_minutes
            )

            # Check if task has been stuck for more than 1 hour
            last_change = getattr(task, "last_status_change", None)
            updated_at = getattr(task, "updated_at", None)

            # Use last_status_change if available, otherwise fall back to updated_at
            timestamp_to_check = last_change or updated_at

            if not timestamp_to_check:
                # If no timestamp, use created_at as fallback
                timestamp_to_check = getattr(task, "created_at", None)

            if timestamp_to_check:
                # Parse timestamp
                if isinstance(timestamp_to_check, str):
                    try:
                        task_time = datetime.fromisoformat(
                            timestamp_to_check.replace("Z", "+00:00")
                        )
                        # Remove timezone info for comparison
                        task_time = task_time.replace(tzinfo=None)
                    except (ValueError, AttributeError):
                        task_time = timestamp_to_check
                        print_log(
                            f"Failed to parse timestamp for task {task.task_id}: {timestamp_to_check}",
                            "task_timestamp_parse_error",
                        )
                else:
                    task_time = timestamp_to_check

                # Check if stuck for more than 1 hour
                if task_time < one_hour_ago:
                    retry_attempt = getattr(task, "retry_attempt", 0)
                    task_status = TaskStatusEnum.pending
                    print_log(
                        f"Task {task.task_id} stuck for >1 hour, marked as pending for retry",
                        "call_recovery_stuck_retried",
                    )
        if not update_data:
            result["message"] = message
            update_data = {
                "status": task_status,
                "retry_attempt": retry_attempt + 1,
                "last_status_change": datetime.utcnow().isoformat(),
                "output": result,
            }
        if task_status:
            TaskModel.update_one({"task_id": task.task_id}, update_data)
            stats["stuck_tasks_retried"] += 1
            print_log(
                f"Task {task.task_id} status updated to {task_status}, retry_attempt={retry_attempt + 1}",
                "call_recovery_task_status_updated",
            )
            # Keep run analytics consistent with recovery-driven status changes
            # self.check_and_update_run_status(task.run_id)
        # else:
        #     print_log(
        #         f"Task {task.task_id} status not changed, remains {task.status}",
        #         "call_recovery_task_status_unchanged",
        #     )

    def recover_call_tasks(self, run_id: Optional[str] = None) -> Dict:
        from datetime import datetime, timedelta

        try:
            stats = {
                "failed_tasks_retried": 0,
                "failed_tasks_kept": 0,
                "stuck_tasks_retried": 0,
                "stuck_tasks_failed": 0,
            }

            # Build query for call provider tasks
            query = {"execution_type": "call"}
            if run_id:
                query["run_id"] = run_id

            # Process failed tasks - OPTIMIZATION: Only fetch tasks eligible for retry
            max_retries = int(os.getenv("MAX_CALL_RETRIES", "3"))
            failed_query = {
                **query,
                "status": TaskStatusEnum.failed,
                "retry_attempt": {
                    "$lt": max_retries
                },  # Exclude tasks that exceeded retry limit
            }
            failed_tasks = list(TaskModel.find(**failed_query))

            print_log(
                f"Found {len(failed_tasks)} failed call tasks eligible for recovery (retry_attempt < {max_retries})",
                "call_recovery_failed_count",
            )

            for task in failed_tasks:
                self.mark_task_status(task)

            # Process stuck in_progress tasks
            in_progress_query = {**query, "status": TaskStatusEnum.in_progress}
            in_progress_tasks = list(TaskModel.find(**in_progress_query))

            print_log(
                f"Found {len(in_progress_tasks)} in_progress call tasks to check",
                "call_recovery_in_progress_count",
            )

            one_hour_ago = datetime.utcnow() - timedelta(hours=1)

            for task in in_progress_tasks:
                self.mark_task_status(task)
            print_log(
                f"call task recovery completed: {stats}",
                "call_recovery_completed",
            )

            return stats

        except Exception as ex:
            print_log(
                f"Failed to recover call tasks at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "call_recovery_error",
            )
            return {}

    def analyze_call_tasks(
        self,
        run_id: Optional[str] = None,
        space_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Dict:
        # from datetime import datetime, timedelta

        try:
            # Build query for call provider tasks
            query = {"execution_type": "call"}
            if run_id:
                query["run_id"] = run_id
            if space_id:
                query["space_id"] = space_id
            if task_id:
                query["task_id"] = task_id

            # Process failed tasks
            query = {**query, "status": TaskStatusEnum.completed}
            tasks = list(TaskModel.find(**query))

            for task in tasks:
                from super.app.call_execution import (
                    execute_post_call_workflow,
                )

                # API Error: Fetch the call status from provider and run post-call workflow
                try:
                    print_log(
                        f"Task {task.task_id} completed, executing post-call workflow for analysis",
                        "call_task_analysis_start",
                    )
                    # Ensure task.input is a dict (parse if it's a JSON string)
                    import json

                    task_input = task.input
                    if isinstance(task_input, str):
                        try:
                            task_input = json.loads(task_input)
                        except (json.JSONDecodeError, ValueError):
                            task_input = {}
                    elif not isinstance(task_input, dict):
                        task_input = {}

                    task_dict = {
                        "task_id": task.task_id,
                        "instructions": task.task.get("objective", ""),
                        "input": task_input,
                    }
                    result = task.output if task.output else {}
                    agent_id = task.assignee
                    # Execute post-call workflow to get actual call status
                    workflow_result = asyncio.run(
                        execute_post_call_workflow(
                            agent_id, ModelConfig(), result, task_dict
                        )
                    )
                    if workflow_result:
                        task_status = TaskStatusEnum.completed
                        # Only include valid task output fields, exclude 'classification' and other non-model fields
                        update_data = {
                            "status": task_status,
                            "output": workflow_result,  # Store entire workflow result in output field
                        }
                        print_log(
                            f"Task {task.task_id} post-call workflow analysis completed successfully",
                            "call_task_workflow_success",
                        )
                except Exception as ex:
                    print_log(
                        f"Failed to execute post-call workflow for task {task.task_id}: {str(ex)}",
                        "call_task_workflow_error",
                    )
                    raise ex

        except Exception as ex:
            print_log(
                f"Failed to recover call tasks at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "call_task_error",
            )

    def calculate_run_analytics(self, tasks: list) -> tuple:
        """
        Calculate call analytics and execution analytics for a run.

        Args:
            tasks: List of tasks for the run

        Returns:
            Tuple of (call_analytics dict, execution_analytics dict)
        """
        # Initialize analytics structures
        call_analytics = {
            "total_calls": 0,
            "interested": 0,
            "call_back": 0,
            "send_details": 0,
            "not_interested": 0,
            "not_connected": 0,
            "failed": 0,
            "quality_metrics": {
                "transcript_available": 0,
                "no_transcript": 0,
                "transcript_rate": 0.0,
                "avg_success_score": 0.0,
                "total_success_score": 0,
                "success_score_count": 0,
            },
        }

        execution_analytics = {
            "total_tasks": len(tasks),
            "completed": 0,
            "failed": 0,
            "pending": 0,
            "in_progress": 0,
            "success_rate": 0.0,
            "completion_rate": 0.0,
            "avg_retry_attempts": 0.0,
            "total_retries": 0,
        }

        # Track call-specific tasks
        call_tasks = [t for t in tasks if t.execution_type == "call"]
        call_analytics["total_calls"] = len(call_tasks)

        # Process each task for analytics
        for task in tasks:
            # Execution analytics
            if task.status == TaskStatusEnum.completed:
                execution_analytics["completed"] += 1
            elif task.status == TaskStatusEnum.failed:
                execution_analytics["failed"] += 1
            elif task.status == TaskStatusEnum.pending:
                execution_analytics["pending"] += 1
            elif task.status == TaskStatusEnum.in_progress:
                execution_analytics["in_progress"] += 1

            # Track retries
            retry_attempt = getattr(task, "retry_attempt", 0)
            execution_analytics["total_retries"] += retry_attempt

            # Call analytics (only for call tasks)
            if task.execution_type == "call":
                output = task.output if task.output else {}

                # Get post_call_data for status and transcript from output level
                post_call_data = output.get("post_call_data", {})
                # Transcript can be a list or string at output level
                transcript = output.get("transcript", [])
                transcript = (
                    transcript
                    if (isinstance(transcript, list) and len(transcript) > 0)
                    or (isinstance(transcript, str) and transcript)
                    else None
                )

                # Track transcript availability
                if transcript:
                    call_analytics["quality_metrics"]["transcript_available"] += 1

                    # Track success score for calls with transcript
                    success_evaluator = post_call_data.get("success_evaluator")
                    if success_evaluator:
                        try:
                            # Convert to float/int and add to total
                            success_score = float(success_evaluator)
                            if 1 <= success_score <= 10:
                                call_analytics["quality_metrics"][
                                    "total_success_score"
                                ] += success_score
                                call_analytics["quality_metrics"][
                                    "success_score_count"
                                ] += 1
                        except (ValueError, TypeError):
                            # Skip invalid success scores
                            pass
                else:
                    call_analytics["quality_metrics"]["no_transcript"] += 1

                # Get call status from post_call_data.summary.status
                call_status = post_call_data.get("summary", {}).get("status", "Unknown")

                # Increment counters based on call status
                if call_status == "InterestedIn" or call_status == "Interested":
                    call_analytics["interested"] += 1
                elif call_status == "Call Back":
                    call_analytics["call_back"] += 1
                elif call_status == "Send Details":
                    call_analytics["send_details"] += 1
                elif call_status == "Not Interested":
                    call_analytics["not_interested"] += 1
                elif call_status == "Not Connected":
                    call_analytics["not_connected"] += 1
                elif task.status == TaskStatusEnum.failed or call_status in [
                    "Error",
                    "Unknown",
                ]:
                    call_analytics["failed"] += 1

        # Calculate percentages and rates
        if execution_analytics["total_tasks"] > 0:
            execution_analytics["success_rate"] = round(
                (execution_analytics["completed"] / execution_analytics["total_tasks"])
                * 100,
                2,
            )
            execution_analytics["completion_rate"] = round(
                (
                    (execution_analytics["completed"] + execution_analytics["failed"])
                    / execution_analytics["total_tasks"]
                )
                * 100,
                2,
            )
            execution_analytics["avg_retry_attempts"] = round(
                execution_analytics["total_retries"]
                / execution_analytics["total_tasks"],
                2,
            )

        if call_analytics["total_calls"] > 0:
            call_analytics["quality_metrics"]["transcript_rate"] = round(
                (
                    call_analytics["quality_metrics"]["transcript_available"]
                    / call_analytics["total_calls"]
                )
                * 100,
                2,
            )

        # Calculate average success score for calls with transcript
        # Average is calculated across all calls with transcript (missing success_evaluator treated as 0)
        if call_analytics["quality_metrics"]["success_score_count"] > 0:
            call_analytics["quality_metrics"]["avg_success_score"] = round(
                call_analytics["quality_metrics"]["total_success_score"]
                / call_analytics["quality_metrics"]["success_score_count"],
                2,
            )

        return call_analytics, execution_analytics

    def check_and_update_run_status(self, run_id: str) -> None:
        """Check if run should be updated to failed status based on task failures"""
        try:
            run = RunModel.find_one(run_id=run_id)
            if not run:
                print_log(
                    f"Run {run_id} not found for status update",
                    "run_not_found_for_status_update",
                )
                return

            # Get all tasks for this run
            tasks = list(TaskModel.find(run_id=run_id))

            if not tasks:
                print_log(f"No tasks found for run {run_id}", "no_tasks_for_run")
                return

            # Calculate task stats
            total_tasks = len(tasks)
            completed_tasks = len(
                [t for t in tasks if t.status == TaskStatusEnum.completed]
            )
            failed_tasks = len([t for t in tasks if t.status == TaskStatusEnum.failed])
            pending_tasks = len(
                [t for t in tasks if t.status == TaskStatusEnum.pending]
            )
            in_progress_tasks = len(
                [t for t in tasks if t.status == TaskStatusEnum.in_progress]
            )

            print_log(
                f"Run {run_id} task stats: {completed_tasks} completed, {failed_tasks} failed, {pending_tasks} pending, {in_progress_tasks} in_progress out of {total_tasks} total",
                "run_task_stats",
            )

            # Determine if run should be updated
            new_run_status = None

            if failed_tasks == total_tasks:
                # All tasks have permanently failed
                new_run_status = TaskStatusEnum.failed
                print_log(
                    f"Run {run_id} all tasks failed, marking run as failed",
                    "run_all_tasks_failed",
                )

            elif completed_tasks == total_tasks:
                # All tasks completed successfully
                new_run_status = TaskStatusEnum.completed
                print_log(
                    f"Run {run_id} all tasks completed, marking run as completed",
                    "run_all_tasks_completed",
                )

            elif (
                completed_tasks + failed_tasks == total_tasks
                and pending_tasks == 0
                and in_progress_tasks == 0
            ):
                # No more pending or in_progress tasks, mix of completed and failed
                new_run_status = TaskStatusEnum.partially_completed
                print_log(
                    f"Run {run_id} has mix of completed and failed tasks, marking as partially completed",
                    "run_partially_completed",
                )

            # Calculate analytics for the run
            call_analytics, execution_analytics = self.calculate_run_analytics(tasks)

            print_log(
                f"Run {run_id} analytics calculated - Call Success: {call_analytics.get('success_rate', 0)}%, Execution Success: {execution_analytics.get('success_rate', 0)}%",
                "run_analytics_calculated",
            )

            # Update run status and analytics if needed
            update_data = {}
            if new_run_status and run.get("status") != new_run_status:
                update_data["status"] = new_run_status

            # Always update analytics
            update_data["call_analytics"] = call_analytics
            update_data["execution_analytics"] = execution_analytics

            if update_data:
                RunModel.update_one({"run_id": run_id}, update_data)
                if "status" in update_data:
                    print_log(
                        f"Updated run {run_id} status from {run.get('status')} to {new_run_status}",
                        "run_status_updated",
                    )
                print_log(
                    f"Updated run {run_id} with analytics",
                    "run_analytics_updated",
                )

        except Exception as ex:
            print_log(
                f"Failed to check and update run status for {run_id} at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "check_run_status_error",
            )

    def update_run_status(
        self,
        run_id: str,
        status: TaskStatusEnum = TaskStatusEnum.failed,
        to_status: TaskStatusEnum = TaskStatusEnum.pending,
    ) -> Dict:
        """Update task status and output"""
        from datetime import datetime

        # Process failed tasks
        try:
            run = RunModel.find_one(run_id=run_id)
            if not run:
                return {"error": "Run not found"}
            s = RunModel.update_one({"run_id": run_id}, {"status": to_status.value})
            print_log(
                f"Updated run {run_id} status from {run.get('status')} to {to_status}",
                "run_status_updated",
            )

            failed_query = {"run_id": run_id, "status": status.value}
            failed_tasks = list(TaskModel.find(**failed_query))
            stats = {
                "task_updated": 0,
            }
            print_log(f"Tasks for run {run_id}: {len(failed_tasks)}", "tasks")
            for task in failed_tasks:
                if task:
                    task_id = task.task_id
                    error = task.output.get("error") or task.last_failure_reason or ""
                    retry_attempt = getattr(task, "retry_attempt", 0)
                    max_retries = int(os.getenv("MAX_CALL_RETRIES", "5"))
                    task_status = to_status
                    # if self._is_retryable_call_error(error):
                    #     # Retry for retryable errors
                    #     task_status = to_status
                    #     stats["failed_tasks_retried"] += 1
                    # elif self._is_api_error(error):
                    #     task_status = to_status
                    #     stats["failed_tasks_retried"] += 1

                    if task_status:
                        stats["task_updated"] += 1
                        update_data = {
                            "status": task_status.value,
                            "retry_attempt": 0,
                            "last_status_change": datetime.utcnow().isoformat(),  # Update timestamp on status change
                        }
                        success = TaskModel.update_one(
                            {"task_id": task_id}, update_data
                        )
                        print_log(
                            f"Updated task {task_id} status from {task.status} to {task_status} is {success}",
                            "task_status_updated",
                        )
            print(f"Task status update completed for run {run_id}: {stats}")
            return stats
        except Exception as ex:
            print_log(
                f"Failed to update task status for run {run_id} at line {ex.__traceback__.tb_lineno}: {str(ex)}\n{traceback.format_exc()}",
                "update_task_status_error",
            )

        return {"error": "Task not found"}

    def upadate_task_raw(self, task_id, from_status, update_data):
        return TaskModel.update_one(
            {"task_id": task_id, "status": from_status}, update_data
        )

    def get_task(self, task_id):
        return TaskModel.find_one(task_id=task_id)

    def get_run(self, run_id):
        return RunModel.find_one(run_id=run_id)

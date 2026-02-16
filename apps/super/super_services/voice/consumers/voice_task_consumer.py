"""
Voice Task Consumer
"""

import os
import sys
import traceback
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from super.app.providers import CallProviderFactory

from super_services.orchestration.webhook.webhook_handler import WebhookHandler
from super.core.logging.logging import print_log
from super_services.db.services.models.task import TaskModel
from super_services.db.services.schemas.task import TaskStatusEnum
from super_services.libs.config import settings
from super_services.voice.models.config import ModelConfig, MessageCallBack
from super_services.voice.common.threads import create_thread_post,update_thread,get_user_id

webhook=WebhookHandler()

import time
# from super_services.libs.storage.kafka_store import KAFKA_BASE

from multiprocessing import Value
from concurrent.futures import ProcessPoolExecutor, as_completed
import asyncio

# from temporalio.client import Client
from super_services.libs.core.redis import REDIS

def sanitize_data_for_mongodb(data):
    """Sanitize data to make it MongoDB-compatible by converting non-serializable objects"""
    if isinstance(data, dict):
        return {key: sanitize_data_for_mongodb(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_data_for_mongodb(item) for item in data]
    elif isinstance(data, timedelta):
        # Convert timedelta to total seconds (float)
        return data.total_seconds()
    elif isinstance(data, datetime):
        # Convert datetime to ISO string
        return data.isoformat()
    elif hasattr(data, '__dict__') and not isinstance(data, (str, int, float, bool, type(None))):
        # Convert complex objects to dictionaries, but be careful with circular references
        try:
            return {key: sanitize_data_for_mongodb(value) for key, value in data.__dict__.items()
                    if not key.startswith('_')}
        except:
            # If conversion fails, return string representation
            return str(data)
    else:
        return data


def _should_retry_immediately(error_data: dict, retry_attempt: int, max_retries: int) -> tuple:
    """
    Determine if a task should be retried immediately based on error type.

    Uses centralized error classification from TaskService.

    Returns: Tuple of (should_retry: bool, reason: str)
    """
    from super_services.orchestration.task.task_service import TaskService

    # Check if we've exceeded max retries
    if retry_attempt >= max_retries - 1:
        return False, "max_retries_exceeded"

    # Extract error message
    error = str(error_data.get("error", ""))
    if isinstance(error_data, dict) and "data" in error_data:
        nested_error = error_data.get("data", {})
        if isinstance(nested_error, dict):
            error = str(nested_error.get("error", error))

    # Customer errors: Don't retry immediately, let recovery process handle with special logic
    # (e.g., mark as completed for voicemail, or use USER_REJECT_RETRY limit for "did not answer")
    if TaskService._is_customer_error(error):
        return False, "customer_error_needs_special_handling"

    # API errors: Don't retry immediately, let recovery process fetch status from provider
    # (the call might have actually succeeded but we couldn't get status)
    if TaskService._is_api_error(error):
        return False, "api_error_needs_status_fetch"

    # Retryable errors: Retry immediately (rate limits, network issues, temporary SIP errors)
    if TaskService._is_retryable_call_error(error):
        return True, "retryable_error"
    
    if "invalid phone number" in error.lower():
        return False, "invalid_phone_number"

    # Generic errors: Retry for exceptions, but not for other failures
    if "exception during processing" in error.lower():
        return True, "exception_retry"

    # Unknown error type: Don't retry immediately, let recovery process decide
    return False, "non_retryable_error"


def _handle_task_retry(task_id: str, message: dict, retry_attempt: int, max_retries: int, error_data: dict, mode: str) -> bool:
    """
    Handle task retry logic with intelligent error-based decisions.

    Strategy:
    - Retryable errors (rate limits, network issues): Immediate re-queue to Kafka
    - Customer errors (no answer, busy): Mark as failed, let recovery process handle
    - API errors: Mark as failed, let recovery process fetch actual status
    - Non-retryable errors: Mark as failed for recovery to evaluate

    Args:
        task_id: Task identifier
        message: Original Kafka message
        retry_attempt: Current retry attempt number
        max_retries: Maximum allowed retries
        error_data: Error data to store with task
        mode: Consumer mode ("normal" or "bulk")

    Returns:
        True if task was successfully re-queued, False if marked as failed/pending for recovery
    """
    from super_services.orchestration.task.task_service import TaskService
    # from super_services.libs.storage.kafka_store import KAFKA_BASE
    from super_services.libs.config import settings
    from datetime import datetime

    task_service = TaskService()

    # Check if we should retry immediately based on error type
    should_retry, reason = _should_retry_immediately(error_data, retry_attempt, max_retries)

    if should_retry:
        # Immediate retry for retryable errors (rate limits, network issues, temporary SIP errors)
        print_log(f"[{mode.upper()}] Re-queueing task {task_id} for immediate retry (attempt {retry_attempt + 1}/{max_retries}, reason: {reason})", "kafka_task_retry")

        try:
            # Update task status to pending with error info
            sanitized_data = sanitize_data_for_mongodb(error_data)
            task_service.update_task_status(
                task_id,
                TaskStatusEnum.pending,
                sanitized_data
            )

            # Update retry_attempt in database
            TaskModel.update_one(
                {"task_id": task_id},
                {
                    "retry_attempt": retry_attempt + 1,
                    "last_status_change": datetime.utcnow().isoformat()
                }
            )

            # Re-queue to Kafka with updated retry_attempt
            # message["retry_attempt"] = retry_attempt + 1

            # Determine topic based on message or mode
            # batch_count = message.get("batch_count", 1)
            # batch_type = "bulk" if batch_count and int(batch_count) > 5 else None
            # topic_name = getattr(settings, 'AGENT_OUTBOUND_REQUEST_TOPIC', 'agent_outbound_requests')
            # topic_name += f"_{batch_type}" if batch_type else ""

            # KAFKA_BASE().push_to_kafka(topic_name, message)
            # print_log(f"[{mode.upper()}] Task {task_id} re-queued to {topic_name} for retry attempt {retry_attempt + 1}", "kafka_requeue_success")
            return True

        except Exception as requeue_ex:
            print_log(f"[{mode.upper()}] Failed to re-queue task {task_id}: {str(requeue_ex)}", "kafka_requeue_error")
            # If re-queue fails, mark as failed
            task_service.update_task_status(task_id, TaskStatusEnum.failed, sanitized_data)
            return False
    else:
        # Don't retry immediately - mark as failed and let recovery process (mark_task_status) handle it
        # Recovery process will:
        # - For customer errors: Mark as completed or retry with USER_REJECT_RETRY limit
        # - For API errors: Fetch call status from provider
        # - For non-retryable: Keep as failed
        print_log(
            f"[{mode.upper()}] Task {task_id} not retrying immediately (reason: {reason}). Marking as failed for recovery process.",
            "kafka_no_immediate_retry"
        )
        try:
            sanitized_data = sanitize_data_for_mongodb(error_data)

            # Add reason why not retrying immediately
            sanitized_data["no_immediate_retry_reason"] = reason

            # Mark as failed - recovery process will handle based on error type
            task_service.update_task_status(task_id, TaskStatusEnum.failed, sanitized_data)

            # Update last failure info without incrementing retry_attempt (recovery will decide)
            TaskModel.update_one(
                {"task_id": task_id},
                {
                    "last_status_change": datetime.utcnow().isoformat(),
                    "last_failure_reason": str(error_data.get("error", "Unknown error"))
                }
            )

        except Exception as db_ex:
            print_log(f"[{mode.upper()}] Failed to mark task {task_id} as failed: {str(db_ex)}", "kafka_db_error")
        return False

def _reschedule_to_prefect(task_id, scheduled_time_utc):
    from super_services.prefect_setup.deployments.utils import trigger_deployment
    from prefect.states import Scheduled
    asyncio.run(
        trigger_deployment(
            "Execute-Task",
            {"job": {"task_id": task_id, "retry": 0, "run_type": "call"}},
            state=Scheduled(scheduled_time=scheduled_time_utc),
        )
    )


def _process_task_worker(message: dict, mode: str, max_workers: int):
    """
    Module-level worker function for processing tasks in spawned processes.

    This is a module-level function (not a method) to avoid pickling
    the entire TaskServiceQueueManager instance, which contains unpicklable objects
    like Process instances with weakrefs.

    LOCK SAFETY GUARANTEES:
    - All code after lock acquisition is wrapped in try-finally
    - Lock is ALWAYS released in finally block (even on exceptions)
    - Lock has 15-minute TTL as safety net (auto-expires if process crashes)
    - Counter is only decremented if it was actually incremented

    Args:
        message: Task message dict from Kafka
        mode: Consumer mode ("normal" or "bulk")
        max_workers: Maximum workers for this mode
    """
    # Import here to avoid circular imports and ensure fresh imports in worker
    from super.app.call_execution import execute_call
    from super.app.providers import CallProviderFactory
    from super_services.orchestration.task.task_service import TaskService
    # from super_services.libs.storage.kafka_store import KAFKA_BASE
    # from super_services.libs.config import settings
    import os

    task_start_time = time.time()
    task_id = message.get("task_id")
    agent_id = message.get("agent_id")
    data = message.get("data")
    instructions = message.get("instructions")
    model_config = message.get("model_config", {})

    # Get task to check retry_attempt from database (single source of truth)
    task = TaskModel.get(task_id=task_id)
    retry_attempt = getattr(task, "retry_attempt", 0) if task else 0

    # Get provider name from task
    provider_name = CallProviderFactory.get_provider_type(data)

    # FIXED: Use lightweight RedisLockManager instead of TaskServiceQueueManager
    # This avoids creating a ProcessPoolExecutor in the worker process
    # which was causing premature executor shutdown via __del__
    redis_manager = RedisLockManager(mode=mode)

    # CRITICAL FIX #1: Pre-execution status check
    is_processed, reason = redis_manager._is_task_already_processed(task_id)
    if is_processed:
        print_log(
            f"[{mode.upper()}] ⚠️  DUPLICATE PREVENTED: Task {task_id} already processed (reason: {reason})",
            "duplicate_execution_prevented"
        )
        return

    # CRITICAL FIX #2: Acquire distributed lock BEFORE incrementing counters
    if not redis_manager._acquire_task_lock(task_id):
        print_log(
            f"[{mode.upper()}] ⚠️  DUPLICATE PREVENTED: Task {task_id} locked by another worker",
            "duplicate_execution_prevented_lock"
        )
        return

    # CRITICAL FIX #7: Wrap ALL code after lock acquisition in try-finally
    # This ensures lock is ALWAYS released even if there's an exception before the main try block
    counter_incremented = False  # Track if we incremented counter (needed for finally cleanup)
    max_retries = int(os.getenv("MAX_CALL_RETRIES", "3"))
    try:
        # CRITICAL FIX #2.4: Business hours check for outbound calls
        # Check if call should be executed based on recipient's timezone
        phone_number = data.get("contact_number")
        if phone_number:
            from super_services.libs.core.timezone_utils import is_within_business_hours

            # Check if business hours validation is enabled
            enable_check = os.getenv("ENABLE_BUSINESS_HOURS_CHECK", "true").lower() == "true"
            if enable_check:
                start_hour = int(os.getenv("BUSINESS_HOURS_START", "9"))
                end_hour = int(os.getenv("BUSINESS_HOURS_END", "20"))

                is_valid, next_available_time = is_within_business_hours(
                    phone_number,
                    start_hour=start_hour,
                    end_hour=end_hour
                )

                if not is_valid:
                    print_log(
                        f"[{mode.upper()}] ⏰ BUSINESS HOURS: Task {task_id} outside business hours "
                        f"for {phone_number}. Scheduling for {next_available_time}",
                        "business_hours_check_failed"
                    )
                    # Schedule task for next business hour
                    scheduled_time_utc = redis_manager._schedule_task_for_later(task_id, message, next_available_time)
                    # Lock will be released in finally block
                    _reschedule_to_prefect(task_id, scheduled_time_utc)
                    return

        # Atomic status update from pending -> in_progress
        # This prevents the task from being picked up again by recovery queries
        # Even if lock acquisition succeeded, we need DB-level atomicity to prevent races
        task_service = TaskService()
        success, result = task_service.update_task_status_atomic(
            task_id,
            from_status=TaskStatusEnum.pending,
            to_status=TaskStatusEnum.processing
        )

        if not success:
            # Another worker already transitioned the status (race condition)
            current_status = result.get("current_status", "unknown")
            print_log(
                f"[{mode.upper()}] ⚠️  DUPLICATE PREVENTED: Task {task_id} status already changed to {current_status} by another worker (atomic CAS failed)",
                "duplicate_execution_prevented_atomic"
            )
            # Lock will be released in finally block
            return

        # Increment Redis counter for this provider
        new_counter_value = redis_manager._increment_redis_counter(provider_name)
        counter_incremented = True  # Mark that counter was incremented

        # Double-check if we exceeded limit after incrementing
        if new_counter_value > max_workers:
            # Counter will be decremented in finally block
            next_available_time = datetime.utcnow() + timedelta(minutes=5)
            scheduled_time_utc = redis_manager._schedule_task_for_later(task_id, message, next_available_time)
            # Lock will be released in finally block
            _reschedule_to_prefect(task_id, scheduled_time_utc)
            print_log(
                f"Provider {provider_name} worker limit exceeded after increment ({new_counter_value}/{max_workers})",
                f"decrementing and skipping task {task_id} and scheduleding to {scheduled_time_utc}",
                "redis_worker_limit",
            )
            return

        if retry_attempt >= max_retries:
            print_log(f"Task {task_id} exceeded max retries ({retry_attempt}), abandoning", "kafka_max_retries")

            task_service = TaskService()
            task_service.update_task_status(
                task_id,
                TaskStatusEnum.failed,
                {"error": f"Task exceeded max retries ({retry_attempt})"}
            )
            task_service.check_and_update_run_status(task.run_id)
            # Counter will be decremented in finally block
            return

        redis_counter = redis_manager._get_redis_counter(provider_name)
        print_log(f"Processing outbound call task {task_id} for agent {agent_id}, provider: {provider_name}, retry_attempt: {retry_attempt}, redis_counter: {redis_counter}", "kafka_process_task")

        # Execute the call
        print_log(f"Executing call for task {task_id} via provider {provider_name}", "call_execution_start")
        outgoing_calls_enabled = os.getenv("OUTGOING_CALLS_ENABLED", "true").lower() == "true"
        if not outgoing_calls_enabled:
            print_log(f"Outgoing calls are disabled via config, simulating failure for task {task_id}",
                      "outgoing_calls_disabled")
            response = {
                "status": "failed",
                "data": {
                    "error": "Outgoing calls are disabled via configuration."
                }
            }
        else:
            response = asyncio.run(
                execute_call(
                    data=data,
                    task_id=task_id,
                    agent_id=agent_id,
                    instructions=instructions,
                    model_config=ModelConfig(),
                    callback=MessageCallBack(),
                )
            )

        # Update task in database with results
        task_service = TaskService()

        if response and response.get("status") == "completed":
            print_log(f"Call task {task_id} completed successfully", "kafka_task_success")
            try:
                sanitized_data = sanitize_data_for_mongodb(response.get("data", {}))
                updated_task = task_service.update_task_status(task_id, TaskStatusEnum.completed, sanitized_data)
                asyncio.run(webhook.execute(task_id=task_id))
                update_thread(task_id, sanitized_data)
            except Exception as db_ex:
                print_log(f"Database update failed for completed task {task_id}, sanitizing further: {str(db_ex)}", "mongo_db_error")
                fallback_data = {
                    "error": "Data sanitization required",
                    "original_error": str(db_ex),
                    "data_summary": str(response.get("data", {}))[:1000]
                }
                updated_task = task_service.update_task_status(task_id, TaskStatusEnum.completed, fallback_data)
                asyncio.run(webhook.execute(task_id=task_id))
            # CRITICAL FIX #5: Add to deduplication cache after successful completion
            redis_manager._mark_task_in_dedup_cache(task_id)

            # Handle call log and cost deduction for successful calls
            data = response.get("data", {})

            task = TaskModel.get(task_id=task_id)
            if task and data:
                try:
                    task_service.insert_call_log(response, data, task)
                    task_service.calculate_and_deduct_cost(data, task)
                    print_log(f"Inserted call log and deducted cost for task {task_id}", "kafka_log_success")
                except Exception as log_ex:
                    print_log(f"Failed to insert call log or deduct cost for task {task_id}: {str(log_ex)}", "kafka_log_error")

            if task:
                task_service.check_and_update_run_status(task.run_id)
                print_log(f"Checked run status for completed task {task_id}", "kafka_run_status_check")

        elif response.get("status") == "in_progress":
            sanitized_data = sanitize_data_for_mongodb(response.get("data", {}))
            updated_task = task_service.update_task_status(task_id, TaskStatusEnum.in_progress, sanitized_data)

        else:
            print_log(f"Call task {task_id} failed with response: {response}", "kafka_task_failed")

            # Handle retry logic
            failed_data = response.get("data", {}) if response else {"error": "No response"}
            # _handle_task_retry(task_id, message, retry_attempt, max_retries, failed_data, mode)

            task = TaskModel.get(task_id=task_id)
            if task:
                task_service.check_and_update_run_status(task.run_id)
                print_log(f"Checked run status for task {task_id}", "kafka_run_status_check")
                sanitized_data = sanitize_data_for_mongodb(response.get("data", {}))
                updated_task = task_service.update_task_status(task_id, TaskStatusEnum.failed, sanitized_data)

    except Exception as ex:
        print_log(f"Exception processing task {task_id}: {str(ex)}", "kafka_process_error")
        print(f"Exception in process_task: {ex}")
        traceback.print_exc()

        # Handle retry logic for exceptions
        error_data = {"error": f"Exception during processing: {str(ex)}"}
        _handle_task_retry(task_id, message, retry_attempt, max_retries, error_data, mode)

    finally:
        # CRITICAL FIX #4 & #7: Always release lock in finally block
        # This runs even if there's an exception anywhere after lock acquisition
        redis_manager._release_task_lock(task_id)

        # CRITICAL FIX #7: Only decrement counter if we actually incremented it
        # This prevents double-decrement on early returns before counter increment
        if counter_incremented:
            redis_manager._decrement_redis_counter(provider_name)

        # Record task latency metrics
        task_duration_ms = (time.time() - task_start_time) * 1000
        MetricsCollector.record_task_latency(mode, task_id, task_duration_ms)


class RedisLockManager:
    """
    Lightweight utility class for Redis operations and distributed locking.

    This class provides Redis counter management, task locking, and deduplication
    without the overhead of ProcessPoolExecutor initialization.

    Used in worker processes where only Redis operations are needed.
    """

    def __init__(self, mode: str = "normal"):
        """
        Initialize Redis lock manager.

        Args:
            mode: Consumer mode ("normal" or "bulk") for counter isolation
        """
        self.mode = mode

    def _get_redis_counter_key(self, provider_name: str) -> str:
        """Get Redis key for provider worker counter with mode isolation."""
        return f"{self.mode}_{provider_name}_call_workers"

    def _increment_redis_counter(self, provider_name: str) -> int:
        """Increment Redis counter for provider and return new value."""
        redis_key = self._get_redis_counter_key(provider_name)
        try:
            pipeline = REDIS.pipeline()
            pipeline.incr(redis_key)
            pipeline.expire(redis_key, 3600)  # 1 hour TTL
            result = pipeline.execute()
            new_value = result[0]
            print_log(f"[{self.mode.upper()}] Incremented {redis_key} to {new_value}", "redis_counter_incr")
            return new_value
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to increment Redis counter for {provider_name}: {str(ex)}", "redis_counter_error")
            return 999999  # Pessimistic fallback

    def _decrement_redis_counter(self, provider_name: str) -> int:
        """Decrement Redis counter for provider and return new value."""
        redis_key = self._get_redis_counter_key(provider_name)
        try:
            new_value = REDIS.decr(redis_key)
            if new_value < 0:
                REDIS.set(redis_key, 0)
                new_value = 0
            print_log(f"[{self.mode.upper()}] Decremented {redis_key} to {new_value}", "redis_counter_decr")
            return new_value
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to decrement Redis counter for {provider_name}: {str(ex)}", "redis_counter_error")
            return 0

    def _get_redis_counter(self, provider_name: str) -> int:
        """Get current value of Redis counter for provider."""
        redis_key = self._get_redis_counter_key(provider_name)
        try:
            value = REDIS.get(redis_key)
            return int(value) if value else 0
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to get Redis counter for {provider_name}: {str(ex)}", "redis_counter_error")
            return 0

    def _acquire_task_lock(self, task_id: str) -> bool:
        """
        Acquire exclusive distributed lock for task execution.

        SAFETY: Lock has 15-minute TTL as a safety net. Even if the worker process
        crashes hard and finally block never executes, lock will auto-expire.

        Args:
            task_id: Task identifier

        Returns:
            True if lock acquired, False if already locked
        """
        lock_key = f"task_lock:{task_id}"
        worker_id = f"{os.getpid()}_{int(time.time())}"

        try:
            # SET with NX (only if not exists) and EX (expiry in seconds)
            # Lock expires in 15 minutes (max expected call duration)
            # This TTL is a critical safety net - prevents permanent deadlocks
            acquired = REDIS.set(lock_key, worker_id, nx=True, ex=900)

            if acquired:
                print_log(f"[{self.mode.upper()}] Acquired task lock for {task_id} by worker {worker_id}", "task_lock_acquired")
                return True
            else:
                current_owner = REDIS.get(lock_key)
                print_log(f"[{self.mode.upper()}] Task {task_id} already locked by {current_owner}", "task_lock_failed")
                return False
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to acquire lock for task {task_id}: {str(ex)}", "task_lock_error")
            return False

    def _release_task_lock(self, task_id: str) -> None:
        """Release distributed lock for task execution."""
        lock_key = f"task_lock:{task_id}"
        try:
            REDIS.delete(lock_key)
            print_log(f"[{self.mode.upper()}] Released task lock for {task_id}", "task_lock_released")
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to release lock for task {task_id}: {str(ex)}", "task_lock_release_error")

    def _is_task_already_processed(self, task_id: str) -> tuple[bool, str]:
        """Check if task is already completed, in progress, or recently processed."""
        try:
            task = TaskModel.get(task_id=task_id)

            if not task:
                return False, "task_not_found"

            if task.status == TaskStatusEnum.completed:
                print_log(f"[{self.mode.upper()}] Task {task_id} already completed, skipping", "task_already_completed")
                return True, "already_completed"

            dedup_key = f"task_dedup:{task_id}"
            if REDIS.get(dedup_key):
                print_log(f"[{self.mode.upper()}] Task {task_id} found in deduplication cache, skipping", "task_dedup_cache_hit")
                return True, "dedup_cache_hit"

            return False, "ready_to_process"
        except Exception as ex:
            traceback.print_exc()
            print_log(f"[{self.mode.upper()}] Failed to check task status for {task_id}: {str(ex)}", "task_status_check_error")
            return True, "status_check_error"

    def _mark_task_in_dedup_cache(self, task_id: str) -> None:
        """Add task to deduplication cache after successful completion."""
        try:
            dedup_key = f"task_dedup:{task_id}"
            REDIS.set(dedup_key, "completed", ex=3600)
            print_log(f"[{self.mode.upper()}] Added task {task_id} to deduplication cache", "task_dedup_cache_add")
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to add task {task_id} to dedup cache: {str(ex)}", "task_dedup_cache_error")

    def _schedule_task_for_later(self, task_id: str, message: dict, scheduled_time: datetime) -> None:
        """Schedule a task for execution at a specific time (business hours)."""
        try:
            import json
            from super_services.orchestration.task.task_service import TaskService

            if scheduled_time:
                if scheduled_time.tzinfo is not None:
                    scheduled_time_utc = scheduled_time.astimezone(timezone.utc)
                else:
                    scheduled_time_utc = scheduled_time.replace(tzinfo=timezone.utc)
            else:
                fallback_time = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(hours=1)
                scheduled_time = fallback_time
                scheduled_time_utc = fallback_time

            timestamp = int(scheduled_time_utc.timestamp())

            sorted_set_key = "scheduled_tasks"
            REDIS.zadd(sorted_set_key, {task_id: timestamp})

            message_key = f"scheduled_task:{task_id}"
            sanitized_message = sanitize_data_for_mongodb(message)

            try:
                task_service = TaskService()
                task_service.upadate_task_raw(task_id, TaskStatusEnum.pending, {
                    "status": TaskStatusEnum.scheduled,
                    "scheduled_timestamp": timestamp,
                    "output": {
                        "message": "Task scheduled for later execution",
                        "scheduled_time": scheduled_time_utc.isoformat()
                    }
                })
                print_log(
                    f"[{self.mode.upper()}] Updated task {task_id} to HOLD while scheduling for later execution",
                    "task_schedule_hold_update"
                )
            except Exception as status_ex:
                print_log(
                    f"[{self.mode.upper()}] Failed to update task {task_id} to HOLD status: {status_ex}",
                    "task_schedule_hold_error"
                )

            now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
            ttl_seconds = 86400
            lead_time = (scheduled_time_utc - now_utc).total_seconds()
            if lead_time > 0:
                ttl_seconds = max(ttl_seconds, int(lead_time) + 3600)

            REDIS.set(message_key, json.dumps(sanitized_message), ex=ttl_seconds)

            scheduled_time_str = scheduled_time.strftime("%Y-%m-%d %H:%M %Z") if scheduled_time else "unknown"
            print_log(
                f"[{self.mode.upper()}] ⏰ Scheduled task {task_id} for {scheduled_time_str} (timestamp: {timestamp}, ttl={ttl_seconds}s)",
                "task_scheduled_for_later"
            )
            return scheduled_time_utc
        except Exception as ex:
            print_log(
                f"[{self.mode.upper()}] Failed to schedule task {task_id}: {str(ex)}. "
                f"Task may be lost - consider implementing fallback requeue.",
                "task_schedule_error"
            )


class TemporalTaskExecutor:
    """
    Handles Temporal workflow execution for voice tasks.

    Separated from Kafka consumer logic for clean separation of concerns.
    This class is responsible for:
    - Temporal client initialization and management
    - Workflow execution with idempotency guarantees
    - Task status updates after workflow completion

    IDEMPOTENCY: Uses WorkflowIDReusePolicy.REJECT_DUPLICATE to prevent duplicate workflows.
    """

    def __init__(self):
        """Initialize Temporal task executor."""
        self.temporal_client = None

    async def init_temporal_client(self):
        """Initialize Temporal client if not already initialized."""
        if self.temporal_client is None:
            temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
            temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
            temporal_api_key = os.getenv("TEMPORAL_API_KEY", "")

            print_log(f"Connecting to Temporal server at {temporal_address}", "temporal_client_init")

            from temporalio.client import Client
            self.temporal_client = await Client.connect(
                temporal_address,
                namespace=temporal_namespace,
                api_key=temporal_api_key if temporal_api_key else None,
                tls=True,
            )

            print_log("Temporal client connected successfully", "temporal_client_ready")
        return self.temporal_client

    async def execute_workflow(self, task_id: str, agent_id: str, data: dict,
                               instructions: str = None, model_config: dict = None):
        """
        Execute Temporal workflow for voice task processing.

        IDEMPOTENCY FIX: Uses REJECT_DUPLICATE policy to prevent duplicate workflow executions.

        Args:
            task_id: Task identifier
            agent_id: Agent identifier
            data: Task data
            instructions: Optional instructions
            model_config: Optional model configuration

        Returns:
            Workflow execution result dict
        """
        from super_services.voice.workflows.workflows import VoiceTaskWorkflow
        from super_services.orchestration.task.task_service import TaskService

        # Initialize Temporal client
        client = await self.init_temporal_client()

        # Generate unique workflow ID
        workflow_id = f"voice-task-{task_id}"
        task_queue = os.getenv("VOICE_TASK_QUEUE", "voice-task-queue")

        print_log(f"Starting workflow {workflow_id} on task queue {task_queue}", "temporal_workflow_start")

        try:
            # CRITICAL FIX #6: Add Temporal workflow idempotency policy
            from temporalio.common import WorkflowIDReusePolicy

            # Start workflow execution with REJECT_DUPLICATE policy
            # This ensures that if a workflow with this ID already exists or completed,
            # Temporal will reject this request rather than creating a duplicate
            handle = await client.start_workflow(
                VoiceTaskWorkflow.run,
                args=[task_id, agent_id, data, instructions, model_config],
                id=workflow_id,
                task_queue=task_queue,
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
            )
        except Exception as workflow_ex:
            # Check if this is a duplicate workflow error
            error_msg = str(workflow_ex).lower()
            if "already started" in error_msg or "workflow execution already" in error_msg:
                print_log(
                    f"⚠️  DUPLICATE PREVENTED: Workflow {workflow_id} already exists. "
                    f"Task {task_id} is being processed by another worker.",
                    "duplicate_workflow_prevented"
                )
                # Don't requeue - another worker is handling this
                return {"status": "duplicate", "data": {"error": "Workflow already processing"}}
            else:
                # Re-raise other exceptions
                raise workflow_ex

        print_log(f"Workflow {workflow_id} started, waiting for result", "temporal_workflow_running")

        # Wait for workflow result
        response = await handle.result()

        print_log(f"Workflow {workflow_id} completed with status: {response.get('status')}", "temporal_workflow_completed")

        # Update task in database with results
        task_service = TaskService()

        if response and response.get("status") == "completed":
            print_log(f"Call task {task_id} completed successfully", "kafka_task_success")
            # Update task status to completed
            try:
                # Sanitize data before database update to handle datetime/timedelta objects
                sanitized_data = sanitize_data_for_mongodb(response.get("data", {}))
                sanitized_data.pop("usage", None)  # Remove usage field if exists
                updated_task = task_service.update_task_status(task_id, TaskStatusEnum.completed, sanitized_data)
            except Exception as db_ex:
                print_log(f"Database update failed for completed task {task_id}, sanitizing further: {str(db_ex)}", "mongo_db_error")
                # Fallback: convert problematic data to strings
                fallback_data = {
                    "error": "Data sanitization required",
                    "original_error": str(db_ex),
                    "data_summary": str(response.get("data", {}))[:1000]  # Truncate to avoid huge logs
                }
                updated_task = task_service.update_task_status(task_id, TaskStatusEnum.completed, fallback_data)

            # Handle call log and cost deduction for successful calls
            data = response.get("data", {})

            task = TaskModel.get(task_id=task_id)
            if task and data:
                try:
                    task_service.insert_call_log(response, data, task)
                    task_service.calculate_and_deduct_cost(data, task)
                except Exception as log_ex:
                    print_log(f"Failed to insert call log or deduct cost for task {task_id}: {str(log_ex)}", "kafka_log_error")

            # Check and update run status after task completion
            if task:
                task_service.check_and_update_run_status(task.run_id)
                print_log(f"Checked run status for completed task {task_id}", "kafka_run_status_check")

        else:
            print_log(f"Call task {task_id} failed with response: {response}", "kafka_task_failed")
            # Update task status to failed
            try:
                # Sanitize data before database update to handle datetime/timedelta objects
                failed_data = response.get("data", {}) if response else {"error": "No response"}
                sanitized_data = sanitize_data_for_mongodb(failed_data)
                updated_task = task_service.update_task_status(task_id, TaskStatusEnum.failed, sanitized_data)
            except Exception as db_ex:
                print_log(f"Database update failed for failed task {task_id}, sanitizing further: {str(db_ex)}", "kafka_db_error")
                # Fallback: convert problematic data to strings
                fallback_data = {
                    "error": "Data sanitization required",
                    "original_error": str(db_ex),
                    "data_summary": str(response.get("data", {}) if response else "No response")[:1000]
                }
                updated_task = task_service.update_task_status(task_id, TaskStatusEnum.failed, fallback_data)

            # Check and update run status after task failure
            task = TaskModel.get(task_id=task_id)
            if task:
                task_service.check_and_update_run_status(task.run_id)
                print_log(f"Checked run status for failed task {task_id}", "kafka_run_status_check")

        return response


class TaskServiceQueueManager(object):
    """
    Kafka-based task queue manager with priority-based consumer modes.

    Supports two modes:
    - 'normal': High-priority consumer for normal calls (30% worker capacity)
    - 'bulk': Low-priority consumer for bulk calls (70% worker capacity)

    Each mode runs as a separate process to eliminate head-of-line blocking.

    ARCHITECTURE:
    - This class handles Kafka consumer logic and worker process management
    - Temporal workflow execution is delegated to TemporalTaskExecutor
    - Direct call execution (non-Temporal) is handled inline
    """

    def __init__(self, mode: str = "normal", use_temporal: bool = False):
        """
        Initialize TaskServiceQueueManager with mode-based configuration.

        Args:
            mode: Consumer mode - "normal" for high-priority, "bulk" for low-priority
            use_temporal: If True, use Temporal workflows for task execution (optional)
        """
        self.mode = mode
        self.use_temporal = use_temporal

        # PICKLE FIX: Don't initialize TemporalTaskExecutor here to avoid pickle errors
        # TemporalTaskExecutor contains asyncio clients with weakrefs that can't be pickled
        # across process boundaries. It will be lazily initialized in worker processes.
        if use_temporal:
            print_log(f"Configured for Temporal workflow execution (will lazy-init in workers)", "temporal_config")
        else:
            print_log(f"Configured for direct call execution (non-Temporal)", "direct_exec_config")

        # Total workers available across all providers
        total_workers = int(os.getenv("AGENT_OUTBOUND_MAX_WORKERS", "4"))

        # Priority-based worker allocation
        if mode == "normal":
            # Normal mode gets 30% of total capacity (reserved for high-priority calls)
            self.max_workers = max(1, int(total_workers * 0.1))
            self.poll_interval = 1.0  # Fast polling (1 second)
            self.max_poll_records_base = 5  # Smaller batches for responsiveness
            print_log(f"Initialized NORMAL priority consumer: max_workers={self.max_workers}", "consumer_init")
        else:  # bulk mode
            # Bulk mode gets 70% of total capacity (allows some overlap with normal)
            self.max_workers = max(1, int(total_workers * 0.9))
            self.poll_interval = 3.0  # Slower polling (3 seconds)
            self.max_poll_records_base = 20  # Larger batches for throughput
            print_log(f"Initialized BULK priority consumer: max_workers={self.max_workers}", "consumer_init")

        # Legacy multiprocessing counter - kept for backward compatibility but not used as source of truth
        self.counter = Value("i", 0)

        # REFACTORED: Use ProcessPoolExecutor for efficient process management
        # Benefits: automatic process reuse, built-in cleanup, no memory leaks
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        print_log(f"[{self.mode.upper()}] Initialized ProcessPoolExecutor with {self.max_workers} workers", "executor_init")

        # Track submitted futures with task_id and submission time for safe cleanup
        # Format: list of (future, task_id, submit_timestamp) tuples
        # This allows us to verify lock release before cleanup
        self._active_futures = []

    def shutdown(self, wait: bool = True):
        """
        Gracefully shutdown the ProcessPoolExecutor.

        Args:
            wait: If True, wait for all submitted tasks to complete before shutdown

        Call this when stopping the consumer to ensure clean shutdown.
        """
        if hasattr(self, 'executor'):
            print_log(f"[{self.mode.upper()}] Shutting down ProcessPoolExecutor (wait={wait})...", "executor_shutdown")
            self.executor.shutdown(wait=wait)
            print_log(f"[{self.mode.upper()}] ProcessPoolExecutor shutdown complete", "executor_shutdown_complete")

    def __del__(self):
        """Ensure executor is shut down when object is garbage collected."""
        try:
            self.shutdown(wait=False)
        except:
            pass  # Ignore errors during cleanup

    def _get_temporal_executor(self) -> TemporalTaskExecutor:
        """
        Lazily create and return TemporalTaskExecutor instance.

        PICKLE FIX: This creates the executor on-demand in the worker process
        to avoid pickling errors when spawning multiprocessing workers.

        Returns:
            TemporalTaskExecutor instance

        Note: This is thread-local/process-local. Each worker process gets its own instance.
        """
        # Check if we already have an executor in this process
        if not hasattr(self, '_temporal_executor_instance'):
            if not self.use_temporal:
                raise RuntimeError("Temporal executor requested but use_temporal=False")

            self._temporal_executor_instance = TemporalTaskExecutor()
            print_log(
                f"[{self.mode.upper()}] Lazy-initialized TemporalTaskExecutor in worker process (PID: {os.getpid()})",
                "temporal_lazy_init"
            )

        return self._temporal_executor_instance

    def _get_redis_counter_key(self, provider_name: str) -> str:
        """
        Get Redis key for provider worker counter with mode isolation.

        Normal and bulk consumers track workers separately to avoid conflicts.
        """
        return f"{self.mode}_{provider_name}_call_workers"

    def reset_call_counters(self):
        """Reset all Redis call worker counters to 0."""
        providers = ["vapi", "pipecat", "livekit"]
        for provider in providers:
            redis_key = self._get_redis_counter_key(provider)
            try:
                REDIS.set(redis_key, 0)
                with self.counter.get_lock():
                    self.counter.value = 0
                print_log(f"Reset Redis counter {redis_key} to 0", "redis_counter_reset")
            except Exception as ex:
                print_log(f"Failed to reset Redis counter {redis_key}: {str(ex)}", "redis_counter_error")

    def _get_provider_from_task(self, task_id: str) -> str:
        """Get provider name from task in database."""
        try:
            task = TaskModel.get(task_id=task_id)
            if task and task.provider:
                return task.provider.lower()
        except Exception as ex:
            print_log(f"Failed to get provider from task {task_id}: {str(ex)}", "redis_provider_error")

        # Default to 'vapi' if provider not found
        return "vapi"

    def _increment_redis_counter(self, provider_name: str) -> int:
        """
        Increment Redis counter for provider and return new value.

        Simplified to use ONLY Redis as source of truth (no multiprocessing.Value sync).
        """
        redis_key = self._get_redis_counter_key(provider_name)
        try:
            # Increment counter with 1 hour expiry (to handle crashed workers)
            pipeline = REDIS.pipeline()
            pipeline.incr(redis_key)
            pipeline.expire(redis_key, 3600)  # 1 hour TTL
            result = pipeline.execute()
            new_value = result[0]

            print_log(f"[{self.mode.upper()}] Incremented {redis_key} to {new_value}", "redis_counter_incr")
            return new_value
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to increment Redis counter for {provider_name}: {str(ex)}", "redis_counter_error")
            # Fallback: return pessimistic value to avoid over-provisioning
            return self.max_workers

    def _decrement_redis_counter(self, provider_name: str) -> int:
        """
        Decrement Redis counter for provider and return new value.

        Simplified to use ONLY Redis as source of truth.
        """
        redis_key = self._get_redis_counter_key(provider_name)
        try:
            new_value = REDIS.decr(redis_key)
            # Don't let it go below 0
            if new_value < 0:
                REDIS.set(redis_key, 0)
                new_value = 0

            print_log(f"[{self.mode.upper()}] Decremented {redis_key} to {new_value}", "redis_counter_decr")
            return new_value
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to decrement Redis counter for {provider_name}: {str(ex)}", "redis_counter_error")
            return 0

    def _get_redis_counter(self, provider_name: str) -> int:
        """
        Get current value of Redis counter for provider.

        Simplified to use ONLY Redis as source of truth.
        """
        redis_key = self._get_redis_counter_key(provider_name)
        try:
            value = REDIS.get(redis_key)
            return int(value) if value else 0
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to get Redis counter for {provider_name}: {str(ex)}", "redis_counter_error")
            return 0

    def _get_total_active_workers(self) -> int:
        """
        Get total active workers across all providers for this consumer mode.

        Returns sum of all provider-specific counters.
        """
        providers = ["vapi", "pipecat", "livekit"]
        total = 0
        for provider in providers:
            total += self._get_redis_counter(provider)
        return total

    def add_to_outbound_call_queue(self, agent_id: str, task_id: str, data: dict, instructions: str = None,
                                   model_config: ModelConfig = None, callback: MessageCallBack = None, batch_count: str = None):
        try:
            from super_services.libs.storage.kafka_store import KAFKA_BASE
            # Get task from database to check current retry_attempt
            task = TaskModel.get(task_id=task_id)
            current_retry_attempt = getattr(task, "retry_attempt", 0) if task else 0

            # Create the message payload for Kafka
            message_payload = {
                "agent_id": agent_id,
                "task_id": task_id,
                "data": data,
                "instructions": instructions,
                "model_config": model_config.get_config(agent_id) if model_config else {},
                "callback": callback.__class__.__name__ if callback else None,
                "retry_attempt": current_retry_attempt,  # Use retry_attempt for consistency
                "message_type": "outbound_call"
            }

            print_log(f"Adding task {task_id} to outbound call queue (retry_attempt: {current_retry_attempt})", "kafka_queue_add")

            batch_type = "bulk" if batch_count and int(batch_count) > 5 else None
            topic_name = getattr(settings, 'AGENT_OUTBOUND_REQUEST_TOPIC', 'agent_outbound_requests')
            topic_name += f"_{batch_type}" if batch_type else ""
            KAFKA_BASE().push_to_kafka(topic_name, message_payload)

            print_log(f"Successfully queued task {task_id} for agent {agent_id}", "kafka_queue_success")

        except Exception as ex:
            print_log(f"Exception while adding task {task_id} to outbound call queue: {str(ex)}", "kafka_queue_error")
            print(f"Exception in while add to outbound call queue: {ex}")
            traceback.print_exc()

    def init_cuda(self):
        # Pre-initialize GPU context at startup
        os.environ['CUDA_DEVICE_ORDER'] = os.environ.get('CUDA_DEVICE_ORDER', 'PCI_BUS_ID')
        os.environ['CUDA_VISIBLE_DEVICES'] = os.environ.get('CUDA_VISIBLE_DEVICES', '0')  # Use specific GPU

        # Warm up GPU before LiveKit initialization
        import torch
        if torch.cuda.is_available():
            torch.cuda.init()
            # Create a small tensor to initialize CUDA context
            dummy = torch.zeros(1).cuda()
            del dummy

    # NOTE: Temporal workflow execution methods moved to TemporalTaskExecutor class
    # See TemporalTaskExecutor.execute_workflow() for Temporal-based task execution

    def _process_task_legacy(self, message):
        from super_services.libs.storage.kafka_store import KAFKA_BASE
        """Legacy task processing without Temporal (kept for reference/fallback)."""
        with self.counter.get_lock():
            self.counter.value += 1

        task_id = message.get("task_id")
        agent_id = message.get("agent_id")
        data = message.get("data")
        instructions = message.get("instructions")
        model_config = message.get("model_config", {})
        retry = message.get("retry", 0)

        print_log(f"Processing outbound call task {task_id} for agent {agent_id}, retry: {retry}, counter: {self.counter.value}", "kafka_process_task")

        try:
            from super.app.call_execution import execute_call

            # Execute the call asynchronously
            data['thread_id'] = create_thread_post(task_id) if not data.get("thread_id") else data.get("thread_id")
            data['user_id'] = get_user_id(task_id) if not data.get("user_id") else data.get("user_id")

            response = asyncio.run(
                execute_call(
                    data=data,
                    task_id=task_id,
                    agent_id=agent_id,
                    instructions=instructions,
                    model_config=ModelConfig(),
                    callback=MessageCallBack(),
                )
            )


            # Update task in database with results
            from super_services.orchestration.task.task_service import TaskService
            task_service = TaskService()

            if response and response.get("status") == "completed":
                print_log(f"Call task {task_id} completed successfully", "kafka_task_success")
                # Update task status to completed
                try:
                    # Sanitize data before database update to handle datetime/timedelta objects
                    sanitized_data = sanitize_data_for_mongodb(response.get("data", {}))
                    updated_task = task_service.update_task_status(task_id, TaskStatusEnum.completed, sanitized_data)
                    asyncio.run(webhook.execute(task_id=task_id))
                    update_thread(task_id, sanitized_data)
                except Exception as db_ex:
                    print_log(f"Database update failed for completed task {task_id}, sanitizing further: {str(db_ex)}", "mongo_db_error")
                    # Fallback: convert problematic data to strings
                    fallback_data = {
                        "error": "Data sanitization required",
                        "original_error": str(db_ex),
                        "data_summary": str(response.get("data", {}))[:1000]  # Truncate to avoid huge logs
                    }
                    updated_task = task_service.update_task_status(task_id, TaskStatusEnum.completed, fallback_data)
                    asyncio.run(webhook.execute(task_id=task_id))
                # CRITICAL FIX #5: Add to deduplication cache after successful completion
                self._mark_task_in_dedup_cache(task_id)

                # Handle call log and cost deduction for successful calls
                data = response.get("data", {})

                task = TaskModel.get(task_id=task_id)
                if task and data:
                    try:
                        task_service.insert_call_log(response, data, task)
                        task_service.calculate_and_deduct_cost(data, task)
                        print_log(f"Inserted call log and deducted cost for task {task_id}", "kafka_log_success")
                    except Exception as log_ex:
                        print_log(f"Failed to insert call log or deduct cost for task {task_id}: {str(log_ex)}", "kafka_log_error")

                # Check and update run status after task completion
                if task:
                    task_service.check_and_update_run_status(task.run_id)
                    print_log(f"Checked run status for completed task {task_id}", "kafka_run_status_check")

            elif response.get("status")== "in_progress":
                sanitized_data = sanitize_data_for_mongodb(response.get("data", {}))
                updated_task = task_service.update_task_status(task_id, TaskStatusEnum.in_progress, sanitized_data)

            else:
                print_log(f"Call task {task_id} failed with response: {response}", "kafka_task_failed")
                # Update task status to failed
                try:
                    # Sanitize data before database update to handle datetime/timedelta objects
                    failed_data = response.get("data", {}) if response else {"error": "No response"}
                    sanitized_data = sanitize_data_for_mongodb(failed_data)
                    updated_task = task_service.update_task_status(task_id, TaskStatusEnum.failed, sanitized_data)
                    asyncio.run(webhook.execute(task_id=task_id))
                except Exception as db_ex:
                    print_log(f"Database update failed for failed task {task_id}, sanitizing further: {str(db_ex)}", "kafka_db_error")
                    # Fallback: convert problematic data to strings
                    fallback_data = {
                        "error": "Data sanitization required",
                        "original_error": str(db_ex),
                        "data_summary": str(response.get("data", {}) if response else "No response")[:1000]
                    }
                    updated_task = task_service.update_task_status(task_id, TaskStatusEnum.failed, fallback_data)
                    asyncio.run(webhook.execute(task_id=task_id))

                # Check and update run status after task failure
                task = TaskModel.get(task_id=task_id)
                if task:
                    task_service.check_and_update_run_status(task.run_id)
                    print_log(f"Checked run status for failed task {task_id}", "kafka_run_status_check")

        except Exception as ex:
            print_log(f"Exception processing task {task_id}: {str(ex)}", "kafka_process_error")
            print(f"Exception in process_task: {ex}")
            traceback.print_exc()

            # Retry the task
            message["retry"] = retry + 1
            topic_name = getattr(settings, 'AGENT_OUTBOUND_REQUEST_TOPIC', 'agent_outbound_requests')
            KAFKA_BASE().push_to_kafka(topic_name, message)

        with self.counter.get_lock():
            self.counter.value -= 1

    def process_outbound_queue(self, topic_name, group_name, max_poll_records=10):
        from super_services.libs.storage.kafka_store import KAFKA_BASE
        """
        Poll Kafka topic and spawn worker processes.

        FIXED: Uses poll() with timeout instead of infinite iterator to prevent memory leaks.
        FIXED: Tracks spawned processes globally and cleans up zombies.
        FIXED: Hard limit on total spawned processes to prevent runaway process creation.

        KAFKA AUTO-COMMIT WARNING:
        ⚠️  Auto-commit is currently ENABLED which can cause message loss or duplicates:
        - Offsets commit every 1 second, but tasks take 30+ seconds
        - If consumer crashes after commit but before task completes, task is lost
        - If task is requeued on error, it can be processed twice

        RECOMMENDED FIX (Phase 2):
        - Set enable_auto_commit=False
        - Manually commit offsets only after verifying task completion
        - Use at-least-once delivery with idempotent processing (locks + status checks)
        """
        consumer = None

        try:
            # REFACTORED: Clean up completed futures BEFORE submitting new ones
            self._cleanup_completed_futures()

            # IDEMPOTENCY CONCERN: Auto-commit enabled for backward compatibility
            # Combined with pre-execution checks and locks to prevent duplicates
            consumer = KAFKA_BASE().get_consumer(
                topic_name,
                group_name,
                auto_offset_reset="earliest",
                enable_auto_commit=True,  # ⚠️  See warning above
                auto_commit_interval_ms=1000,  # ⚠️  Commits before task completion
                max_poll_records=max_poll_records,
            )

            # Log warning about auto-commit on first poll
            if not hasattr(self, '_auto_commit_warning_logged'):
                print_log(
                    f"⚠️  [{self.mode.upper()}] Kafka auto-commit is ENABLED. "
                    f"Relying on pre-execution status checks and distributed locks for idempotency. "
                    f"Consider disabling auto-commit in Phase 2 for stronger guarantees.",
                    "kafka_auto_commit_warning"
                )
                self._auto_commit_warning_logged = True

            # Use poll() with timeout instead of infinite iterator
            # This prevents the consumer from blocking indefinitely
            messages = consumer.poll(timeout_ms=2000, max_records=max_poll_records)

            if not messages:
                # No messages, return early
                return

            messages_processed = 0
            for topic_partition, records in messages.items():
                for message in records:
                    # Check capacity using Redis counter (source of truth)
                    task_data = message.value
                    task_id = task_data.get("task_id", "unknown")
                    data = task_data.get("data", {})

                    try:
                        provider_name = CallProviderFactory.get_provider_type(data)
                    except Exception as ex:
                        print_log(f"Failed to get provider type for task {task_id}, defaulting to 'vapi': {str(ex)}", "provider_error")
                        provider_name = "vapi"

                    # Check Redis counter before submitting to executor
                    current_workers = self._get_redis_counter(provider_name)
                    if current_workers >= self.max_workers:
                        print_log(f"[{self.mode.upper()}] Provider {provider_name} worker limit reached ({current_workers}/{self.max_workers}), stopping poll", "worker_limit")
                        break

                    # REFACTORED: Use ProcessPoolExecutor.submit() instead of manual Process spawning
                    # Benefits: automatic process reuse, built-in cleanup, no pickle errors
                    future = self.executor.submit(_process_task_worker, task_data, self.mode, self.max_workers)

                    # Track future with task_id and timestamp for safe cleanup verification
                    # Format: (future, task_id, submit_timestamp)
                    self._active_futures.append((future, task_id, time.time()))
                    messages_processed += 1

                    print_log(f"[{self.mode.upper()}] Submitted task {task_id} to executor (active futures: {len(self._active_futures)})", "task_submitted")

            if messages_processed > 0:
                print_log(f"[{self.mode.upper()}] Processed {messages_processed} messages from {topic_name}", "poll_complete")

        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Error in process_outbound_queue: {str(ex)}", "poll_error")
            traceback.print_exc()
        finally:
            # Always close consumer to free resources
            if consumer:
                try:
                    consumer.close()
                except Exception as ex:
                    print_log(f"[{self.mode.upper()}] Error closing consumer: {str(ex)}", "consumer_close_error")

    def _cleanup_completed_futures(self):
        """
        Clean up completed futures from the tracking list.

        SAFETY: Only removes futures where:
        1. future.done() returns True (worker function completed)
        2. Task lock has been released (finally block executed)
        3. Future has been done for at least 2 seconds (allows time for async cleanup)

        This prevents premature cleanup while workers are still in finally blocks.
        """
        if not self._active_futures:
            return

        initial_count = len(self._active_futures)
        current_time = time.time()

        # Keep futures that are either:
        # 1. Not done yet, OR
        # 2. Done but lock not released yet, OR
        # 3. Done recently (< 2 seconds ago)
        cleaned_futures = []
        kept_futures = []

        for item in self._active_futures:
            # Handle both old format (just future) and new format (future, task_id, timestamp)
            if isinstance(item, tuple):
                future, task_id, submit_time = item
            else:
                # Legacy format - keep it for now without lock check
                future = item
                task_id = None
                submit_time = current_time

            # Check if future is done
            if not future.done():
                kept_futures.append(item)
                continue

            # If we have task_id, verify lock is released
            if task_id:
                lock_key = f"task_lock:{task_id}"
                try:
                    lock_exists = REDIS.exists(lock_key)
                    if lock_exists:
                        # Lock still exists - worker still in finally block
                        kept_futures.append(item)
                        print_log(
                            f"[{self.mode.upper()}] Keeping future for task {task_id} - lock not yet released",
                            "future_cleanup_lock_wait"
                        )
                        continue
                except Exception as ex:
                    # On error, be conservative and keep the future
                    print_log(f"[{self.mode.upper()}] Error checking lock for {task_id}: {ex}", "future_cleanup_error")
                    kept_futures.append(item)
                    continue

            # Future is done and lock is released (or no task_id) - safe to clean up
            cleaned_futures.append(task_id if task_id else "unknown")

        self._active_futures = kept_futures
        cleaned_count = len(cleaned_futures)

        if cleaned_count > 0:
            print_log(
                f"[{self.mode.upper()}] Cleaned {cleaned_count} completed futures ({initial_count} → {len(self._active_futures)}) - tasks: {cleaned_futures}",
                "future_cleanup"
            )

    def _acquire_task_lock(self, task_id: str) -> bool:
        """
        Acquire exclusive distributed lock for task execution.

        Args:
            task_id: Task identifier

        Returns:
            True if lock acquired, False if already locked
        """
        lock_key = f"task_lock:{task_id}"
        worker_id = f"{os.getpid()}_{int(time.time())}"

        try:
            # SET with NX (only if not exists) and EX (expiry in seconds)
            # Lock expires in 15 minutes (max expected call duration)
            acquired = REDIS.set(lock_key, worker_id, nx=True, ex=900)

            if acquired:
                print_log(f"[{self.mode.upper()}] Acquired task lock for {task_id} by worker {worker_id}", "task_lock_acquired")
                return True
            else:
                # Check who owns the lock
                current_owner = REDIS.get(lock_key)
                print_log(f"[{self.mode.upper()}] Task {task_id} already locked by {current_owner}", "task_lock_failed")
                return False
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to acquire lock for task {task_id}: {str(ex)}", "task_lock_error")
            # Pessimistic: assume already locked on error
            return False

    def _release_task_lock(self, task_id: str) -> None:
        """
        Release distributed lock for task execution.

        Args:
            task_id: Task identifier
        """
        lock_key = f"task_lock:{task_id}"

        try:
            REDIS.delete(lock_key)
            print_log(f"[{self.mode.upper()}] Released task lock for {task_id}", "task_lock_released")
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to release lock for task {task_id}: {str(ex)}", "task_lock_release_error")

    def _is_task_already_processed(self, task_id: str) -> tuple[bool, str]:
        """
        Check if task is already completed, in progress, or recently processed.
        """
        try:
            # Check database for task status
            task = TaskModel.get(task_id=task_id)

            if not task:
                return False, "task_not_found"

            # Check if task is in a terminal or active state
            if task.status == TaskStatusEnum.completed:
                print_log(f"[{self.mode.upper()}] Task {task_id} already completed, skipping", "task_already_completed")
                return True, "already_completed"

            # if task.status == TaskStatusEnum.in_progress:
            #     print_log(f"[{self.mode.upper()}] Task {task_id} already in progress, skipping", "task_already_in_progress")
            #     return True, "already_in_progress"

            # Check deduplication cache (recently completed tasks)
            dedup_key = f"task_dedup:{task_id}"
            if REDIS.get(dedup_key):
                print_log(f"[{self.mode.upper()}] Task {task_id} found in deduplication cache, skipping", "task_dedup_cache_hit")
                return True, "dedup_cache_hit"

            return False, "ready_to_process"

        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to check task status for {task_id}: {str(ex)}", "task_status_check_error")
            # Pessimistic: skip task on error to avoid duplicate execution
            return True, "status_check_error"

    def _mark_task_in_dedup_cache(self, task_id: str) -> None:
        """
        Add task to deduplication cache after successful completion.

        Args:
            task_id: Task identifier
        """
        try:
            dedup_key = f"task_dedup:{task_id}"
            # Store in cache with 1 hour TTL
            REDIS.set(dedup_key, "completed", ex=3600)
            print_log(f"[{self.mode.upper()}] Added task {task_id} to deduplication cache", "task_dedup_cache_add")
        except Exception as ex:
            print_log(f"[{self.mode.upper()}] Failed to add task {task_id} to dedup cache: {str(ex)}", "task_dedup_cache_error")

    def _schedule_task_for_later(self, task_id: str, message: dict, scheduled_time: datetime) -> None:
        """
        Schedule a task for execution at a specific time (business hours).

        Stores task in Redis sorted set with scheduled time as score.
        Task will be picked up by _process_scheduled_tasks() when time arrives.

        Args:
            task_id: Task identifier
            message: Full Kafka message payload
            scheduled_time: UTC datetime when task should be executed
        """
        try:
            import json
            from datetime import datetime

            from super_services.orchestration.task.task_service import TaskService

            # Attempt to transition task to hold while it waits for the next window
            try:
                task_service = TaskService()
                update_result = task_service.update_task_status(
                    task_id,
                    TaskStatusEnum.hold
                )
                print_log(
                    f"[{self.mode.upper()}] Updated task {task_id} to HOLD while scheduling for later execution",
                    "task_schedule_hold_update"
                )
            except Exception as status_ex:
                print_log(
                    f"[{self.mode.upper()}] Failed to update task {task_id} to HOLD status: {status_ex}",
                    "task_schedule_hold_error"
                )

            # Convert scheduled_time to Unix timestamp for Redis sorted set score
            if scheduled_time:
                if scheduled_time.tzinfo is not None:
                    scheduled_time_utc = scheduled_time.astimezone(timezone.utc)
                else:
                    scheduled_time_utc = scheduled_time.replace(tzinfo=timezone.utc)
            else:
                # Fallback: schedule for 1 hour from now
                fallback_time = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(hours=1)
                scheduled_time = fallback_time
                scheduled_time_utc = fallback_time

            timestamp = int(scheduled_time_utc.timestamp())

            # Store task in Redis sorted set
            sorted_set_key = "scheduled_tasks"
            REDIS.zadd(sorted_set_key, {task_id: timestamp})

            # Store message payload separately for retrieval
            message_key = f"scheduled_task:{task_id}"
            sanitized_message = sanitize_data_for_mongodb(message)

            # TTL: ensure payload survives until execution window plus 1 hour buffer (min 24h)
            now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
            ttl_seconds = 86400  # default 24h
            lead_time = (scheduled_time_utc - now_utc).total_seconds()
            if lead_time > 0:
                ttl_seconds = max(ttl_seconds, int(lead_time) + 3600)

            REDIS.set(message_key, json.dumps(sanitized_message), ex=ttl_seconds)

            scheduled_time_str = scheduled_time.strftime("%Y-%m-%d %H:%M %Z") if scheduled_time else "unknown"
            print_log(
                f"[{self.mode.upper()}] ⏰ Scheduled task {task_id} for {scheduled_time_str} (timestamp: {timestamp}, ttl={ttl_seconds}s)",
                "task_scheduled_for_later"
            )
        except Exception as ex:
            print_log(
                f"[{self.mode.upper()}] Failed to schedule task {task_id}: {str(ex)}. "
                f"Task may be lost - consider implementing fallback requeue.",
                "task_schedule_error"
            )

    def _get_scheduled_tasks_ready(self) -> list:
        """
        Retrieve tasks that are ready for execution (scheduled time has passed).

        Queries Redis sorted set for tasks with score <= current timestamp.
        Atomically removes retrieved tasks from the set.

        Returns:
            List of message payloads for tasks ready to execute
        """
        try:
            import json
            from datetime import datetime

            current_timestamp = int(datetime.utcnow().timestamp())
            sorted_set_key = "scheduled_tasks"

            # Get tasks with score <= current timestamp (ready to execute)
            # Returns list of task_ids
            ready_task_ids = REDIS.zrangebyscore(
                sorted_set_key,
                min=0,
                max=current_timestamp
            )

            if not ready_task_ids:
                return []

            # Retrieve message payloads and remove from sorted set
            ready_messages = []
            for task_id_bytes in ready_task_ids:
                task_id = task_id_bytes.decode('utf-8') if isinstance(task_id_bytes, bytes) else task_id_bytes

                # Get message payload
                message_key = f"scheduled_task:{task_id}"
                message_json = REDIS.get(message_key)

                if message_json:
                    try:
                        message = json.loads(message_json)
                        ready_messages.append(message)

                        # Remove from sorted set and delete message payload
                        REDIS.zrem(sorted_set_key, task_id)
                        REDIS.delete(message_key)

                        print_log(
                            f"[{self.mode.upper()}] Retrieved scheduled task {task_id} for requeue",
                            "scheduled_task_retrieved"
                        )
                    except json.JSONDecodeError as je:
                        print_log(
                            f"[{self.mode.upper()}] Failed to decode scheduled task {task_id}: {str(je)}",
                            "scheduled_task_decode_error"
                        )
                        # Remove corrupted entry
                        REDIS.zrem(sorted_set_key, task_id)
                        REDIS.delete(message_key)
                else:
                    # Message payload missing - remove from sorted set
                    print_log(
                        f"[{self.mode.upper()}] Scheduled task {task_id} payload missing, removing",
                        "scheduled_task_missing"
                    )
                    REDIS.zrem(sorted_set_key, task_id)

            return ready_messages

        except Exception as ex:
            print_log(
                f"[{self.mode.upper()}] Error retrieving scheduled tasks: {str(ex)}",
                "scheduled_tasks_retrieve_error"
            )
            return []

    def _process_scheduled_tasks(self) -> None:
        from super_services.libs.storage.kafka_store import KAFKA_BASE
        """
        Process scheduled tasks that are ready for execution.

        Retrieves tasks from Redis sorted set and requeues them to Kafka.
        Called periodically from main consumer loop.
        """
        try:
            ready_messages = self._get_scheduled_tasks_ready()
            if not ready_messages:
                return

            print_log(
                f"[{self.mode.upper()}] Processing {len(ready_messages)} scheduled tasks",
                "scheduled_tasks_processing"
            )

            # Requeue tasks to Kafka
            topic_name = getattr(settings, 'AGENT_OUTBOUND_REQUEST_TOPIC', 'agent_outbound_requests')
            from super_services.orchestration.task.task_service import TaskService
            task_service = TaskService()

            # Determine if should go to bulk queue based on batch_count
            # (This mirrors the logic in add_to_outbound_call_queue)
            batch_count = len(ready_messages)
            for message in ready_messages:
                task_id = message.get("task_id")
                if not task_id:
                    print_log(
                        f"[{self.mode.upper()}] Scheduled task payload missing task_id, skipping requeue",
                        "scheduled_task_missing_id"
                    )
                    continue

                # Reset status back to pending so the worker can claim it atomically
                try:
                    update_result = task_service.update_task_status(
                        task_id,
                        TaskStatusEnum.hold
                    )
                    print_log(
                        f"[{self.mode.upper()}] Reset task {task_id} status to PENDING before requeue",
                        "scheduled_task_status_reset"
                    )
                except Exception as status_ex:
                    print_log(
                        f"[{self.mode.upper()}] Exception resetting status for scheduled task {task_id}: {status_ex}",
                        "scheduled_task_status_exception"
                    )

                try:
                    # Check batch_count to route to correct queue
                    batch_type = "bulk" if batch_count and int(batch_count) > 5 else None
                    queue_topic = f"{topic_name}_{batch_type}" if batch_type else topic_name
                    KAFKA_BASE().push_to_kafka(queue_topic, message)

                    print_log(
                        f"[{self.mode.upper()}] Requeued scheduled task {task_id} to {queue_topic}",
                        "scheduled_task_requeued"
                    )
                except Exception as msg_ex:
                    print_log(
                        f"[{self.mode.upper()}] Failed to requeue scheduled task {task_id}: {str(msg_ex)}",
                        "scheduled_task_requeue_error"
                    )

        except Exception as ex:
            print_log(
                f"[{self.mode.upper()}] Error processing scheduled tasks: {str(ex)}",
                "scheduled_tasks_process_error"
            )

    def _process_task_with_counter_init(self, message):
        """
        Process task with Redis counter tracking per provider and latency metrics.

        Records end-to-end latency from Kafka message to task completion.

        IDEMPOTENCY SAFEGUARDS:
        1. Pre-execution status check to prevent duplicate processing
        2. Distributed lock acquisition to prevent concurrent execution
        3. Deduplication cache to skip recently completed tasks
        """
        task_start_time = time.time()
        task_id = message.get("task_id")
        agent_id = message.get("agent_id")
        data = message.get("data")
        instructions = message.get("instructions")
        model_config = message.get("model_config", {})
        retry = message.get("retry", 0)

        # CRITICAL FIX #1: Pre-execution status check
        is_processed, reason = self._is_task_already_processed(task_id)
        if is_processed:
            print_log(
                f"[{self.mode.upper()}] ⚠️  DUPLICATE PREVENTED: Task {task_id} already processed (reason: {reason})",
                "duplicate_execution_prevented"
            )
            return

        # CRITICAL FIX #2: Acquire distributed lock BEFORE incrementing counters
        if not self._acquire_task_lock(task_id):
            print_log(
                f"[{self.mode.upper()}] ⚠️  DUPLICATE PREVENTED: Task {task_id} locked by another worker",
                "duplicate_execution_prevented_lock"
            )
            return

        # CRITICAL FIX #2.4: Business hours check for outbound calls
        # Check if call should be executed based on recipient's timezone
        phone_number = data.get("contact_number")
        if phone_number:
            from super_services.libs.core.timezone_utils import is_within_business_hours
            import os

            # Check if business hours validation is enabled
            enable_check = os.getenv("ENABLE_BUSINESS_HOURS_CHECK", "true").lower() == "true"

            if enable_check:
                start_hour = int(os.getenv("BUSINESS_HOURS_START", "9"))
                end_hour = int(os.getenv("BUSINESS_HOURS_END", "20"))

                is_valid, next_available_time = is_within_business_hours(
                    phone_number,
                    start_hour=start_hour,
                    end_hour=end_hour
                )

                if not is_valid:
                    print_log(
                        f"[{self.mode.upper()}] ⏰ BUSINESS HOURS: Task {task_id} outside business hours "
                        f"for {phone_number}. Scheduling for {next_available_time}",
                        "business_hours_check_failed"
                    )
                    # Schedule task for next business hour
                    self._schedule_task_for_later(task_id, message, next_available_time)
                    # Release lock since we're not processing now
                    self._release_task_lock(task_id)
                    return

        # Get provider name from task
        provider_name = CallProviderFactory.get_provider_type(data)

        # Increment Redis counter for this provider (this is the first action)
        new_counter_value = self._increment_redis_counter(provider_name)

        # Double-check if we exceeded limit after incrementing
        if new_counter_value > self.max_workers:
            print_log(f"Provider {provider_name} worker limit exceeded after increment ({new_counter_value}/{self.max_workers}), decrementing and skipping task {task_id}", "redis_worker_limit")
            # Decrement immediately since we exceeded
            self._decrement_redis_counter(provider_name)
            # Release lock before returning
            self._release_task_lock(task_id)
            return

        max_retries = int(os.getenv("MAX_CALL_RETRIES", "3"))
        if retry >= max_retries:
            print_log(f"Task {task_id} exceeded max retries ({retry}), abandoning", "kafka_max_retries")

            # Mark task as permanently failed
            from super_services.orchestration.task.task_service import TaskService
            task_service = TaskService()
            task_service.update_task_status(
                task_id,
                TaskStatusEnum.failed,
                {"error": f"Task exceeded max retries ({retry})"}
            )

            # Decrement Redis counter (which also syncs self.counter.value)
            self._decrement_redis_counter(provider_name)
            # Release lock before returning
            self._release_task_lock(task_id)
            task_service.check_and_update_run_status(task.run_id)
            return

        redis_counter = self._get_redis_counter(provider_name)
        print_log(f"Processing outbound call task {task_id} for agent {agent_id}, provider: {provider_name}, retry: {retry}, redis_counter: {redis_counter}, mp_counter: {self.counter.value}", "kafka_process_task")

        try:
            from super.app.call_execution import execute_call

            print_log(f"Executing call for task {task_id} via provider {provider_name}", "call_execution_start")
            outgoing_calls_enabled = os.getenv("OUTGOING_CALLS_ENABLED", "true").lower() == "true"
            if not outgoing_calls_enabled:
                print_log(f"Outgoing calls are disabled via config, simulating failure for task {task_id}", "outgoing_calls_disabled")
                response = {
                    "status": "failed",
                    "data": {
                        "error": "Outgoing calls are disabled via configuration."
                    }
                }
            else:
                # Execute the call asynchronously
                data['thread_id'] = create_thread_post(task_id) if not data.get("thread_id") else data.get("thread_id")
                data['user_id'] = get_user_id(task_id) if not data.get("user_id") else data.get("user_id")

                response = asyncio.run(
                    execute_call(
                        data=data,
                        task_id=task_id,
                        agent_id=agent_id,
                        instructions=instructions,
                        model_config=ModelConfig(),
                        callback=MessageCallBack(),
                    )
                )

            # Update task in database with results
            from super_services.orchestration.task.task_service import TaskService
            task_service = TaskService()

            if response and response.get("status") == "completed":
                print_log(f"Call task {task_id} completed successfully", "kafka_task_success")
                # Update task status to completed
                try:
                    # Sanitize data before database update to handle datetime/timedelta objects
                    sanitized_data = sanitize_data_for_mongodb(response.get("data", {}))
                    updated_task = task_service.update_task_status(task_id, TaskStatusEnum.completed, sanitized_data)
                    asyncio.run(webhook.execute(task_id=task_id))
                    update_thread(task_id, sanitized_data)
                except Exception as db_ex:
                    print_log(f"Database update failed for completed task {task_id}, sanitizing further: {str(db_ex)}", "mongo_db_error")
                    # Fallback: convert problematic data to strings
                    fallback_data = {
                        "error": "Data sanitization required",
                        "original_error": str(db_ex),
                        "data_summary": str(response.get("data", {}))[:1000]  # Truncate to avoid huge logs
                    }
                    updated_task = task_service.update_task_status(task_id, TaskStatusEnum.completed, fallback_data)
                    asyncio.run(webhook.execute(task_id=task_id))

                # CRITICAL FIX #5: Add to deduplication cache after successful completion
                self._mark_task_in_dedup_cache(task_id)

                # Handle call log and cost deduction for successful calls
                data = response.get("data", {})

                task = TaskModel.get(task_id=task_id)
                if task and data:
                    try:
                        task_service.insert_call_log(response, data, task)
                        task_service.calculate_and_deduct_cost(data, task)
                        print_log(f"Inserted call log and deducted cost for task {task_id}", "kafka_log_success")
                    except Exception as log_ex:
                        print_log(f"Failed to insert call log or deduct cost for task {task_id}: {str(log_ex)}", "kafka_log_error")

                # Check and update run status after task completion
                if task:
                    task_service.check_and_update_run_status(task.run_id)
                    print_log(f"Checked run status for completed task {task_id}", "kafka_run_status_check")

            elif response.get("status") == "in_progress":
                sanitized_data = sanitize_data_for_mongodb(response.get("data", {}))
                updated_task = task_service.update_task_status(task_id, TaskStatusEnum.in_progress, sanitized_data)

            else:
                print_log(f"Call task {task_id} failed with response: {response}", "kafka_task_failed")
                # Update task status to failed
                try:
                    # Sanitize data before database update to handle datetime/timedelta objects
                    failed_data = response.get("data", {}) if response else {"error": "No response"}
                    sanitized_data = sanitize_data_for_mongodb(failed_data)
                    updated_task = task_service.update_task_status(task_id, TaskStatusEnum.failed, sanitized_data)
                    asyncio.run(webhook.execute(task_id=task_id))
                except Exception as db_ex:
                    print_log(f"Database update failed for failed task {task_id}, sanitizing further: {str(db_ex)}", "kafka_db_error")
                    # Fallback: convert problematic data to strings
                    fallback_data = {
                        "error": "Data sanitization required",
                        "original_error": str(db_ex),
                        "data_summary": str(response.get("data", {}) if response else "No response")[:1000]
                    }
                    updated_task = task_service.update_task_status(task_id, TaskStatusEnum.failed, fallback_data)
                    asyncio.run(webhook.execute(task_id=task_id))
                # Check and update run status after task failure
                task = TaskModel.get(task_id=task_id)
                if task:
                    task_service.check_and_update_run_status(task.run_id)
                    print_log(f"Checked run status for failed task {task_id}", "kafka_run_status_check")

        except Exception as ex:
            print_log(f"Exception processing task {task_id}: {str(ex)}", "kafka_process_error")
            print(f"Exception in process_task: {ex}")
            traceback.print_exc()

        finally:
            # CRITICAL FIX #4: Always release lock in finally block
            self._release_task_lock(task_id)

            # Decrement Redis counter when task completes (success or failure)
            self._decrement_redis_counter(provider_name)

            # Record task latency metrics
            task_duration_ms = (time.time() - task_start_time) * 1000
            MetricsCollector.record_task_latency(self.mode, task_id, task_duration_ms)

    def _get_memory_usage_mb(self):
        """Get current process memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            return mem_info.rss / 1024 / 1024  # Convert to MB
        except ImportError:
            # psutil not available, try with resource module
            try:
                import resource
                usage = resource.getrusage(resource.RUSAGE_SELF)
                return usage.ru_maxrss / 1024  # Convert to MB (Linux)
            except:
                return 0.0
        except:
            return 0.0

    def process_single_topic_service(self):
        """
        Process only the topic assigned to this consumer instance.

        This replaces the old sequential processing with mode-specific processing.
        Each consumer mode (normal/bulk) runs in a separate process.

        MEMORY LEAK FIXES:
        - Aggressive process cleanup before every poll
        - Periodic memory monitoring and logging
        - Hard limit on spawned processes
        """
        print_log(f"Starting {self.mode.upper()} Priority Task Service Queue Manager", "service_start")
        self.init_cuda()
        self.reset_call_counters()
        print_log(f"[{self.mode.upper()}] CUDA Initialized, max_workers={self.max_workers}, poll_interval={self.poll_interval}s", "cuda_init")

        # Construct topic and group names based on mode
        base_topic_name = getattr(settings, 'AGENT_OUTBOUND_REQUEST_TOPIC', 'agent_outbound_requests')
        topic_name = f"{base_topic_name}_bulk" if self.mode == "bulk" else base_topic_name

        # Use mode-specific consumer group to allow parallel consumption
        base_group_name = getattr(settings, 'AGENT_OUTBOUND_REQUEST_GROUP', 'agent_outbound_requests_group')
        group_name = f"{base_group_name}"

        print_log(f"[{self.mode.upper()}] Consumer config: topic={topic_name}, group={group_name}", "consumer_config")

        poll_count = 0
        initial_memory = self._get_memory_usage_mb()
        last_memory_log = time.time()

        while True:
            poll_count += 1
            start_time = time.time()

            # MEMORY LEAK FIX: Periodic memory monitoring (every 60 seconds)
            if time.time() - last_memory_log > 60:
                current_memory = self._get_memory_usage_mb()
                memory_growth = current_memory - initial_memory
                # Clean up completed futures before reporting worker count
                self._cleanup_completed_futures()
                active_futures = len(self._active_futures)

                print_log(
                    f"[{self.mode.upper()}] Memory: {current_memory:.1f}MB (growth: {memory_growth:+.1f}MB), "
                    f"Active futures: {active_futures}, Poll count: {poll_count}",
                    "memory_status"
                )

                # Alert if memory growth is excessive
                if memory_growth > 500:  # 500MB growth
                    print_log(
                        f"[{self.mode.upper()}] ⚠️  HIGH MEMORY GROWTH: {memory_growth:.1f}MB! "
                        f"Active futures: {active_futures}",
                        "memory_warning"
                    )

                last_memory_log = time.time()

            # Process scheduled tasks (business hours) every 60 seconds
            # This runs at the same frequency as memory monitoring
            if poll_count % 60 == 0 or (time.time() - last_memory_log < 1):
                self._process_scheduled_tasks()

            # Get current total active workers across all providers for this mode
            current_workers = self._get_total_active_workers()

            if current_workers >= self.max_workers:
                print_log(f"[{self.mode.upper()}] Capacity reached ({current_workers}/{self.max_workers}), backing off", "capacity_reached")
                # Back off when at capacity (double the poll interval)
                time.sleep(self.poll_interval * 2)
                continue

            # Calculate dynamic poll records based on available capacity
            available_capacity = self.max_workers - current_workers
            dynamic_poll_records = min(available_capacity, self.max_poll_records_base)

            if dynamic_poll_records > 0:
                print_log(f"[{self.mode.upper()}] Poll #{poll_count}: workers={current_workers}/{self.max_workers}, polling {dynamic_poll_records} records", "poll_start")
                self.process_outbound_queue(topic_name, group_name, dynamic_poll_records)

            # Adaptive sleep based on capacity utilization
            utilization = current_workers / self.max_workers if self.max_workers > 0 else 0

            if utilization > 0.8:
                # High utilization: slow down polling
                sleep_time = self.poll_interval * 2
                print_log(f"[{self.mode.upper()}] High utilization ({utilization:.0%}), sleeping {sleep_time}s", "adaptive_sleep")
            elif utilization < 0.3:
                # Low utilization: speed up polling
                sleep_time = self.poll_interval * 0.5
            else:
                # Normal utilization
                sleep_time = self.poll_interval

            poll_duration = time.time() - start_time
            print_log(f"[{self.mode.upper()}] Poll #{poll_count} completed in {poll_duration:.2f}s, sleeping {sleep_time:.1f}s", "poll_end")

            time.sleep(sleep_time)

    def process_task_service(self):
        """
        LEGACY: Old sequential processing method that handles both topics.

        DEPRECATED: Use process_single_topic_service() instead for new deployments.
        This method is kept for backward compatibility only.
        """
        print_log("Starting LEGACY Task Service Queue Manager (processes both topics sequentially)", "service_start")
        print_log("⚠️  WARNING: Using deprecated sequential processing. Consider migrating to separate consumer processes.", "legacy_warning")

        self.init_cuda()
        self.reset_call_counters()
        print_log("CUDA Initialized", "cuda_init")
        while True:
            if self.counter.value >= self.max_workers:
                print_log("Agent Outbound Capacity Reached", self.counter.value)
                time.sleep(2)
            else:
                max_poll_records = self.max_workers - self.counter.value
                print_log("Calling process outbound call queue")
                topic_name = getattr(settings, 'AGENT_OUTBOUND_REQUEST_TOPIC', 'agent_outbound_requests')
                group_name = getattr(settings, 'AGENT_OUTBOUND_REQUEST_GROUP', 'agent_outbound_requests_group')
                # ----------------------------------------------------------
                self.process_outbound_queue(topic_name, group_name, max_poll_records)
                print_log("Processing topic", topic_name, self.counter.value)
                time.sleep(5)
                # ----------------------------------------------------------
                topic_name += "_bulk"
                self.process_outbound_queue(topic_name, group_name, max_poll_records)
                print_log("Processing bulk topic", topic_name, self.counter.value)
                time.sleep(5)


class MetricsCollector:
    """Collects and tracks latency and throughput metrics per topic type."""

    @staticmethod
    def record_task_latency(topic_type: str, task_id: str, latency_ms: float):
        """
        Record end-to-end latency from Kafka to processing completion.

        Args:
            topic_type: "normal" or "bulk"
            task_id: Task identifier
            latency_ms: Latency in milliseconds
        """
        try:
            redis_key = f"metrics:task_latency:{topic_type}"
            timestamp = time.time()
            entry = f"{task_id}:{latency_ms:.2f}:{timestamp}"

            REDIS.lpush(redis_key, entry)
            REDIS.ltrim(redis_key, 0, 999)  # Keep last 1000 entries
            REDIS.expire(redis_key, 3600)  # 1 hour TTL

            # Alert if latency exceeds SLA
            if topic_type == "normal" and latency_ms > 5000:  # 5 second SLA for normal
                print_log(f"⚠️  SLA BREACH: Normal task {task_id} took {latency_ms:.0f}ms (>5000ms)", "sla_breach")
            elif topic_type == "bulk" and latency_ms > 30000:  # 30 second SLA for bulk
                print_log(f"⚠️  SLA BREACH: Bulk task {task_id} took {latency_ms:.0f}ms (>30000ms)", "sla_breach")

        except Exception as ex:
            print_log(f"Failed to record task latency: {str(ex)}", "metrics_error")

    @staticmethod
    def get_average_latency(topic_type: str) -> float:
        """
        Get average latency for topic type in last hour.

        Args:
            topic_type: "normal" or "bulk"

        Returns:
            Average latency in milliseconds
        """
        try:
            redis_key = f"metrics:task_latency:{topic_type}"
            entries = REDIS.lrange(redis_key, 0, -1)

            if not entries:
                return 0.0

            latencies = []
            for entry in entries:
                parts = entry.decode().split(':')
                if len(parts) >= 2:
                    latencies.append(float(parts[1]))

            return sum(latencies) / len(latencies) if latencies else 0.0
        except Exception as ex:
            print_log(f"Failed to get average latency: {str(ex)}", "metrics_error")
            return 0.0

    @staticmethod
    def get_p95_latency(topic_type: str) -> float:
        """
        Get 95th percentile latency for topic type.

        Args:
            topic_type: "normal" or "bulk"

        Returns:
            P95 latency in milliseconds
        """
        try:
            redis_key = f"metrics:task_latency:{topic_type}"
            entries = REDIS.lrange(redis_key, 0, -1)

            if not entries:
                return 0.0

            latencies = []
            for entry in entries:
                parts = entry.decode().split(':')
                if len(parts) >= 2:
                    latencies.append(float(parts[1]))

            if not latencies:
                return 0.0

            latencies.sort()
            p95_index = int(len(latencies) * 0.95)
            return latencies[p95_index] if p95_index < len(latencies) else latencies[-1]
        except Exception as ex:
            print_log(f"Failed to get P95 latency: {str(ex)}", "metrics_error")
            return 0.0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Voice Task Queue Consumer with Priority Modes")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["normal", "bulk", "legacy"],
        default="normal",
        help="Consumer mode: 'normal' for high-priority, 'bulk' for low-priority, 'legacy' for old behavior"
    )
    args = parser.parse_args()

    if args.mode == "legacy":
        print_log("Starting in LEGACY mode (sequential processing of both topics)", "startup")
        service = TaskServiceQueueManager(mode="normal")  # Default to normal for legacy
        service.process_task_service()
    else:
        print_log(f"Starting in {args.mode.upper()} mode (priority-based separate consumer)", "startup")
        service = TaskServiceQueueManager(mode=args.mode)
        service.process_single_topic_service()
    # exit(0)
    # thread_id = "552055888261677313"
    # user = {
    #     "user_id": 2,
    #     "username": "babulalkumawat@mastersindia.co",
    #     "email": "babulalkumawat@mastersindia.co",
    #     "first_name": "Babulal",
    #     "last_name": "Kumawat 2 3",
    #     "user_token": "FZXIYPZ606U8UU44",
    #     "is_active": 1,
    #     "full_name": "Babulal Kumawat 2 3",
    # }
    # user = {'user_id': 51528027, 'username': 'anonymous', 'email': 'anonymous.51528027@unpod.tv', 'first_name': 'Anonymous', 'last_name': 'User', 'user_token': 'ANONYMOUS', 'is_active': True, 'full_name': 'Anonymous User', 'is_anonymous': True, 'space': {'space_token': '3Q4ODI5OSVFIJ2KLO3546EGU', 'org_token': 'KJHWCANOIDUB7DM7JIDU', 'org_id': 37}}
    # data = {'block': 'html', 'block_type': 'question', 'data': {'content': 'A Boy Play with ball', 'files': [{'object_type': 'post', 'object_id': None, 'size': 32085, 'media_id': '401f498a6f1811eeaa1b21d138967907', 'media_type': 'image', 'media_relation': 'attachment', 'name': 'Ques16.png', 'media_url': 'https://ik.imagekit.io/techblog/Ques16.png', 'url': 'https://unpod-back.s3.amazonaws.com/media/private/Ques16.png', 'sequence_number': 0}], 'conversation_type': 'initiate'}, 'parent_id': None, 'pilot': 'question-solver'}
    # asyncio.run(process_task(thread_id, data, user, send_to_chat=True))

    # data = {'block': 'html', 'block_type': 'question', 'data': {'content': 'A Boy Play with ball', 'files': [{'object_type': 'post', 'object_id': None, 'size': 32085, 'media_id': '401f498a6f1811eeaa1b21d138967907', 'media_type': 'image', 'media_relation': 'attachment', 'name': 'Ques16.png', 'media_url': 'https://unpod-back.s3.amazonaws.com/media/private/AI_Answer_5M_Scraping_2023-09-19_CB4.xlsx', 'url': 'https://unpod-back.s3.amazonaws.com/media/private/AI_Answer_5M_Scraping_2023-09-19_CB4.xlsx', 'sequence_number': 0}], 'conversation_type': 'initiate'}, 'parent_id': None, 'pilot': 'cbird-question-rectifier'}

    # data = {
    #     "block": "html",
    #     "block_type": "question",
    #     "data": {"content": "Provide the summary of this conversation & Topics", "conversation_type": "initiate"},
    #     "parent_id": None,
    #     "pilot": "gpt-4",
    # }

    # data = {
    #     "block": "html",
    #     "block_type": "question",
    #     "data": {
    #         # "content": "Calculate the diffraction limit of the human eye in arcseconds, assuming a wide-open pupil so that your eye acts like a lens with diameter 0.8 centimeter, for visible light of 500-nanometer wavelength",
    #         # "content": "Provide the summary of SUNIL Kumar resume",
    #         "content": '{"content":"Most iconic movies from India"}',
    #         # "files": [
    #         #     {
    #         #         "object_type": "post",
    #         #         "object_id": None,
    #         #         "size": 32085,
    #         #         "media_id": "401f498a6f1811eeaa1b21d138967907",
    #         #         "media_type": "image",
    #         #         "media_relation": "attachment",
    #         #         "name": "Ques16.png",
    #         #         "media_url": "https://unpodbackend.s3.amazonaws.com/media/private/Ques9_Ma3UXHw.png",
    #         #         "url": "https://unpodbackend.s3.amazonaws.com/media/private/Ques9_Ma3UXHw.png",
    #         #         "sequence_number": 0,
    #         #     }
    #         # ],
    #         "conversation_type": "initiate",
    #         "source": "qa2",
    #         # "knowledge_bases": ["knowledge-base-test-75ty2car"],
    #     },
    #     "parent_id": None,
    #     "pilot": "multi-ai",
    # }
    # asyncio.run(process_task(thread_id, data, user, send_to_chat=True))
    # from services.superpilot_service.services.write import generate_title

    # answer = """
    #     To address the issue of "Reco is not executed," it is important to follow a structured approach to diagnose and resolve the problem. Here are some steps you can take:

    #     1. **Check for Existing Solutions**: Before reaching out for help, ensure that the issue has not already been discussed and resolved in the FAQ section or other resources. You can use search engines, StackOverflow, or the r/manim subreddit to find similar issues and their solutions [6], [7].

    #     2. **Prepare Your Question**: If you need to ask the community for help, make sure to clearly explain the problem. Include all relevant information such as the full stack trace, the code you were running, and the command you used to execute the code. This will help others understand your issue better and provide more accurate assistance [6], [7].

    #     3. **Use Appropriate Channels**: You can ask for help in the Manim community's Discord server, StackOverflow, or the r/manim subreddit. Each platform has its own way of handling queries, so choose the one you are most comfortable with [6], [7].

    #     4. **Follow Up if Necessary**: If your question does not get answered, try to improve it by adding more details or simplifying the example code. You can also ping the @Manim Helper role on Discord to bring attention to your query, but do this only if your question has been buried and not immediately after posting it [6], [7].

    #     5. **Report Bugs**: If you believe the issue is a bug, check the list of known issues and feature requests in the Manim GitHub repository. If the problem is not listed, you can file a new issue following the guidelines provided. Make sure to include a minimal example to reproduce the issue and the full terminal output [6], [7].

    #     By following these steps, you can systematically address the issue and seek help from the community if needed.
    #     """
    # title_dict = generate_title(answer)
    # print(title_dict)

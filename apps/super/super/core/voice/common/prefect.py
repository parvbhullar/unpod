from super_services.prefect_setup.deployments.utils import (
    trigger_deployment,
)
import uuid
from datetime import datetime
from super_services.libs.core.redis import REDIS


def _set_cached_config(key: str) -> None:
    try:
        cache_key = f"{key}"
        REDIS.setex(cache_key, 100, "scheduled")
    except Exception:
        pass


def _get_cached_config(key: str):
    """Get config from Redis cache."""
    try:
        cache_key = f"{key}"
        data = REDIS.get(cache_key)
        if data:
            return data
    except Exception:
        pass
    return None


def create_entry(coll: str, data: dict):
    """
    Create a document in MongoDB using a fresh connection.

    This avoids issues with MongomanticClient shared state across worker processes.
    """

    print(f"{'='*50}\n\n creating entry {coll} \n\n{'='*50}")
    from pymongo import MongoClient
    from super_services.libs.config import settings

    client = MongoClient(settings.MONGO_DSN)
    try:
        db = client[settings.MONGO_DB]
        collection = db[coll]
        result = collection.insert_one(data)

        # Get count for verification
        count = collection.count_documents({})
        return result.inserted_id, count
    finally:
        client.close()


def normalise_user_state(user_state):
    try:
        if user_state.start_time and hasattr(user_state.start_time, "isoformat"):
            user_state.start_time = user_state.start_time.isoformat()
        if user_state.end_time and hasattr(user_state.end_time, "isoformat"):
            user_state.end_time = user_state.end_time.isoformat()
    except Exception as e:
        pass
    return user_state


def generate_perf_log_id() -> str:
    """Generate a unique perf log ID."""
    return f"PL{uuid.uuid1().hex}"


async def store_perf_logs(user_state) -> None:
    """
    Store performance logs to MongoDB collection.

    Args:
        user_state: UserState with perf_logs array
    """
    try:
        extra_data = getattr(user_state, "extra_data", {}) or {}
        perf_logs = extra_data.get("perf_logs")
        if not perf_logs:
            return

        from super_services.libs.core.datetime import get_datetime_now

        # Calculate total init time from perf_logs
        total_init_time_ms = None
        if perf_logs:
            total_init_time_ms = sum(
                entry.get("duration_ms", 0)
                for entry in perf_logs
                if entry.get("name")
                in [
                    "lk_lite_execute_total",
                    "total_entrypoint",
                ]
            )

        model_config = user_state.model_config or {}

        create_data = {
            "session_id": str(user_state.thread_id) if user_state.thread_id else None,
            "room_name": user_state.room_name,
            "call_type": extra_data.get("call_type"),
            "agent_id": model_config.get("agent_id"),
            "perf_logs": perf_logs,
            "total_init_time_ms": total_init_time_ms,
            "contact_number": user_state.contact_number,
            "user_name": user_state.user_name,
            "space_id": model_config.get("space_id"),
            "task_id": user_state.task_id,
            "metadata": {
                "call_status": user_state.call_status,
                "language": user_state.language,
            },
            "created": get_datetime_now(utc=True),
            "modified": get_datetime_now(utc=True),
        }
        from bson import ObjectId

        create_data["_id"] = ObjectId()
        create_data["perf_log_id"] = generate_perf_log_id()

        # Use fresh MongoDB connection to avoid MongomanticClient shared state issues
        inserted_id, total_count = create_entry("call_perf_logs", create_data)

        print(
            f"[PERF_LOG] Stored perf logs for session {user_state.thread_id}: "
            f"{len(perf_logs)} entries, total={total_init_time_ms:.0f}ms, "
            f"perf_log_id={create_data['perf_log_id']}, "
            f"mongo_id={inserted_id}"
        )
        print(f"[PERF_LOG] Total documents in call_perf_logs: {total_count}")

    except Exception as e:
        import traceback

        print(f"[PERF_LOG] Error storing perf logs: {e}")
        print(f"[PERF_LOG] Traceback: {traceback.format_exc()}")


def get_providers(model_config):
    if not model_config:
        return {}

    if not isinstance(model_config, dict):
        return {}

    data = {
        "stt_provider": model_config.get("stt_provider"),
        "tts_provider": model_config.get("tts_provider"),
        "llm_provider": model_config.get("llm_provider"),
        "tts_model": model_config.get("tts_model"),
        "llm_model": model_config.get("llm_model"),
        "stt_model": model_config.get("stt_model"),
    }

    return data


async def trigger_post_call(user_state, res):
    try:
        # from super_services.orchestration.cron_jobs.post_call import (
        #     post_call_flow,
        #     FlowJob,
        # )
        #
        # job = FlowJob(user_state.task_id, res, user_state)
        # await post_call_flow(job)

        user_state = normalise_user_state(user_state)

        try:
            if not isinstance(user_state.extra_data, dict):
                user_state.extra_data = {}

            latency_metrics = user_state.extra_data.get("latency_metrics", [])

            if latency_metrics:
                data = {
                    "metrics": latency_metrics,
                    "agent_id": user_state.model_config.get("agent_id"),
                    "created_at": datetime.utcnow().isoformat(),
                    "providers": get_providers(user_state.model_config),
                    "thread_id": user_state.thread_id,
                    "provider": user_state.extra_data.get("provider", "livekit"),
                }

                create_entry("agent_latency_metrics", data)

        except Exception as e:
            print(f"[latency_metrics] Exception: {e}")

        key = _get_cached_config(f"prefect:{user_state.task_id}")

        if key:
            print("task already in processing skipping flow ")
            return

        _set_cached_config(f"prefect:{user_state.task_id}")

        await trigger_deployment(
            "Post-Call-Flow",
            {
                "job": {
                    "task_id": user_state.task_id,
                    "call_result": res,
                    "user_state": user_state,
                }
            },
        )

    except Exception as e:
        print(f"Error triggering Post-Call-Flow deployment: {e}")

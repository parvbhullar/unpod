from super_services.prefect_setup.deployments.utils import (
    trigger_deployment,
)
import uuid


def create_entry(coll: str, data: dict):
    """
    Create a document in MongoDB using a fresh connection.

    This avoids issues with MongomanticClient shared state across worker processes.
    """
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


def generate_latency_log_id() -> str:
    """Generate a unique latency log ID."""
    return f"LL{uuid.uuid1().hex}"


async def store_latency_metrics(
    user_state,
    agent_num: int,
    turn_count: int,
    cumulative_stt: float,
    cumulative_llm: float,
    cumulative_tts: float,
    cumulative_total: float,
    realtime_total: float,
) -> None:
    """
    Store latency metrics to MongoDB collection 'latency_metrics'.

    Called on call end for each agent in the room.

    Args:
        user_state: UserState with room/agent info
        agent_num: Agent number in multi-agent scenarios
        turn_count: Total number of turns
        cumulative_stt: Cumulative STT latency in seconds
        cumulative_llm: Cumulative LLM TTFT in seconds
        cumulative_tts: Cumulative TTS TTFB in seconds
        cumulative_total: Cumulative total latency
        realtime_total: Cumulative realtime model TTFT
    """
    try:
        from super_services.libs.core.datetime import get_datetime_now
        from bson import ObjectId
        from super.core.voice.common.common import get_system_metrics

        model_config = user_state.model_config or {}

        # Calculate averages (avoid division by zero)
        avg_stt = cumulative_stt / turn_count if turn_count > 0 else 0.0
        avg_llm = cumulative_llm / turn_count if turn_count > 0 else 0.0
        avg_tts = cumulative_tts / turn_count if turn_count > 0 else 0.0
        avg_total = cumulative_total / turn_count if turn_count > 0 else 0.0
        avg_realtime = realtime_total / turn_count if turn_count > 0 else 0.0

        # Capture current system metrics
        current_system_metrics = get_system_metrics()
        print(f"[LATENCY_LOG] Current system metrics: {current_system_metrics}")

        # Get system metrics logs from user_state if available
        system_metrics_logs = []
        if user_state.extra_data and "system_metrics_logs" in user_state.extra_data:
            system_metrics_logs = user_state.extra_data["system_metrics_logs"]
        print(f"[LATENCY_LOG] System metrics logs count: {len(system_metrics_logs)}, logs: {system_metrics_logs}")

        # Get latency metrics logs from user_state if available (per-agent latencies captured on disconnect)
        latency_metrics_logs = []
        if user_state.extra_data and "latency_metrics_logs" in user_state.extra_data:
            latency_metrics_logs = user_state.extra_data["latency_metrics_logs"]
        print(f"[LATENCY_LOG] Latency metrics logs count: {len(latency_metrics_logs)}, logs: {latency_metrics_logs}")

        create_data = {
            "_id": ObjectId(),
            "latency_log_id": generate_latency_log_id(),
            "room_name": user_state.room_name,
            "agent_id": model_config.get("agent_id"),
            "agent_num": agent_num,
            "thread_id": str(user_state.thread_id) if user_state.thread_id else None,
            "task_id": user_state.task_id,
            "space_id": model_config.get("space_id"),
            "user_name": user_state.user_name,
            "contact_number": user_state.contact_number,
            "turn_count": turn_count,
            "system_metrics": current_system_metrics,
            "system_metrics_logs": system_metrics_logs,
            "latency_metrics_logs": latency_metrics_logs,
            "created": get_datetime_now(utc=True),
            "modified": get_datetime_now(utc=True),
        }

        # Use fresh MongoDB connection
        inserted_id, total_count = create_entry("latency_metrics", create_data)

        print(
            f"[LATENCY_LOG] Stored latency metrics for room={user_state.room_name}, "
            f"agent_id={model_config.get('agent_id')}, agent_num={agent_num}: "
            f"turns={turn_count}, avg_total={avg_total:.3f}s, "
            f"latency_log_id={create_data['latency_log_id']}, "
            f"mongo_id={inserted_id}"
        )
        print(f"[LATENCY_LOG] Total documents in latency_metrics: {total_count}")

    except Exception as e:
        import traceback

        print(f"[LATENCY_LOG] Error storing latency metrics: {e}")
        print(f"[LATENCY_LOG] Traceback: {traceback.format_exc()}")


async def trigger_post_call(user_state, res):
    try:

        # from super_services.orchestration.cron_jobs.post_call import post_call_flow, FlowJob

        # job=FlowJob(
        #     user_state.task_id,
        #     res,
        #     user_state
        # )   
        # await post_call_flow(job)

        user_state = normalise_user_state(user_state)

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

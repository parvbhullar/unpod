from time import perf_counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from super.core.voice.schema import UserState

import requests
from super_services.db.services.schemas.task import TaskStatusEnum
import json
from super.core.voice.common.services import save_execution_log
from super_services.libs.core.db import executeQuery


def create_default_usage(model_config):
    return {
        "llm_provider": model_config.get("llm_provider", ""),
        "llm_model": model_config.get("llm_model", ""),
        "tts_provider": model_config.get("tts_provider", ""),
        "tts_model": model_config.get("tts_model", ""),
        "stt_provider": model_config.get("stt_provider", ""),
        "stt_model": model_config.get("stt_model", ""),
        "llm_prompt_tokens": 0,
        "llm_completion_tokens": 0,
        "tts_characters_count": 0,
        "stt_audio_duration": 0,
        "costs": {"llm_cost": 0, "stt_cost": 0, "tts_cost": 0},
        "total_cost": 0,
    }


def add_perf_log(
    user_state: "UserState",
    name: str,
    duration_ms: float,
    start_time_ms: float = None,
) -> None:
    """
    Add a performance log entry to user_state.extra_data['perf_logs'].

    Args:
        user_state: UserState instance to add the log to
        name: Name of the checkpoint (e.g., "config_lookup", "pipecat_init")
        duration_ms: Duration in milliseconds
        start_time_ms: Optional absolute start time in ms (from perf_counter)
    """
    if user_state.extra_data is None:
        user_state.extra_data = {}

    if "perf_logs" not in user_state.extra_data:
        user_state.extra_data["perf_logs"] = []

    entry = {
        "name": name,
        "duration_ms": round(duration_ms, 2),
    }

    if start_time_ms is not None:
        entry["timestamp_ms"] = round(start_time_ms, 2)

    user_state.extra_data["perf_logs"].append(entry)


class PerfTimer:
    """
    Context manager for timing code blocks and adding to perf_logs.

    Usage:
        with PerfTimer(user_state, "config_lookup"):
            config = await get_config()
    """

    def __init__(self, user_state: "UserState", name: str):
        self.user_state = user_state
        self.name = name
        self.start = None

    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (perf_counter() - self.start) * 1000
        add_perf_log(self.user_state, self.name, duration_ms)
        return False

    async def __aenter__(self):
        self.start = perf_counter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (perf_counter() - self.start) * 1000
        add_perf_log(self.user_state, self.name, duration_ms)
        return False


async def build_call_result(user_state):
    from super.core.voice.providers.base import CallResult
    from datetime import datetime

    try:
        duration = (
            int((user_state.end_time - user_state.start_time).total_seconds())
            if user_state.end_time
            and user_state.start_time
            and isinstance(user_state.start_time, datetime)
            and isinstance(user_state.end_time, datetime)
            else 0
        )
    except Exception as e:
        print(str(e))
        duration = 0

    # Build data dict with quality metrics if available
    data = {
        "type": user_state.extra_data.get("call_type"),
        "transcript": user_state.transcript,
        "cost": user_state.usage.get("total_cost", 0.0),
    }

    # Include quality metrics for conversation intelligence (Gap #3)
    quality_metrics = user_state.extra_data.get("quality_metrics")
    if quality_metrics:
        data["quality_metrics"] = quality_metrics

    conversation_userdata = user_state.extra_data.get("conversation_userdata")
    if conversation_userdata:
        data["conversation_userdata"] = conversation_userdata

    call_result = CallResult(
        status="completed",
        call_status=user_state.call_status,
        call_id=user_state.thread_id,
        customer=user_state.user_name,
        contact_number=user_state.contact_number,
        transcript=user_state.transcript,
        duration=duration,
        recording_url=user_state.recording_url,
        call_start=str(user_state.start_time),
        call_end=str(user_state.end_time),
        call_end_reason=user_state.end_reason if user_state.end_reason else None,
        assistant_number="",
        data=data,
    )

    return call_result


async def get_webhook_plan(agent_id):
    query = """
        SELECT dfv.values
        FROM dynamic_form_values dfv
        JOIN dynamic_forms df
            ON dfv.form_id = df.id
        WHERE dfv.parent_id =  %(agent)s
            AND df.slug = 'webhook-integration';
        """

    params = {"agent": agent_id}

    res = executeQuery(query=query, params=params)

    try:
        if isinstance(res.get("values"), str):
            res = json.loads(res.get("values"))
        else:
            res = res.get("values")
    except Exception as e:
        res = {}

    return res or {}


def get_headers(webhook_plan):
    headers = {
        "Content-Type": "application/json",
    }
    # Explicit null and type check to prevent AttributeError
    if webhook_plan is None or not isinstance(webhook_plan, dict):
        return headers

    webhook_headers = webhook_plan.get("headers") or {}

    if isinstance(webhook_headers, dict):
        headers.update(webhook_headers)
    elif isinstance(webhook_headers, list):
        for item in webhook_headers:
            if isinstance(item, dict) and "header_name" in item and "header_value" in item:
                headers[item["header_name"]] = item["header_value"]

    return headers


async def send_web_notification(
    status, event, user_state, description: str = None, payload_data: dict = None
):
    # Safely access model_config to prevent AttributeError
    model_config = getattr(user_state, "model_config", None)
    if not model_config or not isinstance(model_config, dict):
        print("No model_config found in user_state, skipping webhook notification")
        return

    agent = model_config.get("agent_id")
    if not agent:
        print("No agent_id found in model_config, skipping webhook notification")
        return

    plan = await get_webhook_plan(agent)
    if not plan:
        print("No webhook plan found")
        return

    headers = get_headers(plan)

    url = plan.get("webhook_url")

    task_id = user_state.task_id
    if not plan.get("enable_webhook", False):
        await save_execution_log(
            task_id,
            "web-notification",
            TaskStatusEnum.failed,
            {"status": "web notifications disabled"},
        )
        return

    if not url:
        await save_execution_log(
            task_id,
            "web-notification",
            TaskStatusEnum.failed,
            {"status": "webhoook dont have any url"},
        )
        return

    payload = {
        "event": event,
        "status": status,
        "data": {
            "call_id": user_state.thread_id,
            "task_id": user_state.task_id,
            "contact_number": user_state.contact_number,
            "contact_name": user_state.user_name,
            "config": user_state.model_config,
            "transcript": user_state.transcript,
            "room": user_state.room_name,
            "usage": user_state.usage,
            "start_time": str(user_state.start_time),
            "end_time": str(user_state.end_time),
            "call_type": user_state.extra_data.get("call_type")
            if user_state.extra_data
            else "unknown",
        },
    }

    if payload_data:
        payload.update(payload_data)

    for i in range(3):
        try:
            res = requests.post(url, json=payload, headers=headers)
            if res.status_code == 200:
                print("webhook request successful")
                await save_execution_log(
                    task_id,
                    "web-notification",
                    TaskStatusEnum.completed,
                    {"status": "completed", "description": description},
                )
                return "Success"
            else:
                print("webhook request failed %s", res)
                continue

        except Exception as e:
            await save_execution_log(
                task_id,
                "web-notification",
                TaskStatusEnum.failed,
                {"status": f"failed due to exception {str(e)}"},
            )
            print("webhook request failed", str(e))
            return "Failed to process webhook request"

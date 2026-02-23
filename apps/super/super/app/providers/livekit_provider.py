import os

import json
import logging
from typing import Dict, Any, Optional
from livekit import api

from super_services.libs.core.utils import get_env_name
from super.core.voice.providers.base import CallProvider, CallResult
from super.core.callback.base import BaseCallback
from super.core.configuration import BaseModelConfig
from super.core.voice.schema import UserState
from datetime import datetime
import uuid
from super.core.voice.common.services import save_execution_log
from super_services.db.services.schemas.task import TaskStatusEnum


logger = logging.getLogger("voice-agent")

class LiveKitProvider(CallProvider):
    """LiveKit call provider implementation"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.default_agent_name = (
            config.get("agent_name", "voice-agent-test")
            if config
            else "voice-agent-test"
        )

    def get_provider_name(self) -> str:
        return "livekit"

    def supports_async(self) -> bool:
        return True

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return "room" in data

    async def execute_call(
        self,
        agent_id: str,
        task_id: str,
        data: Dict[str, Any],
        instructions: Optional[str] = None,
        model_config: BaseModelConfig = None,
        callback: BaseCallback = None,
        call_type: str = "outbound",
    ) -> CallResult:
        """Execute a LiveKit call"""

        self._callback = callback
        self._model_config = model_config
        user_name = data.get("name")

        if instructions:
            data["objective"] = instructions
        else:
            data["objective"] = "Say Hi This your voice assistant from Unpod"
        data["agent_id"] = agent_id

        try:
            config = model_config.get_config(agent_id)

        except Exception as e:
            config = model_config.get_config("", id="1")

        user_state = UserState(
            user_name=data.get("contact_name") or data.get("name") or "User",
            space_name=data.get("space_name"),
            contact_number=data.get("contact_number"),
            token=data.get("token"),
            language="English",
            thread_id=data.get("thread_id", task_id),
            user={},
            persona=config.get("persona"),
            system_prompt=config.get("system_prompt"),
            first_message=config.get("first_message"),
            config=config,
            knowledge_base=config.get("knowledge_base", []),
            start_time=datetime.now(),
            usage={},
            transcript=[],
            recording_url="",
        )

        data["task_id"] = task_id
        metadata = {"data": data, "model_config": config, "call_type": "outbound"}

        try:
            logger.info("Starting outbound call")
            metadata = json.dumps(metadata)

            # Generate unique room ID using contact number and UUID
            # This ensures each call gets its own isolated room
            contact_number = data.get("contact_number", "")
            # Sanitize phone number for room name (remove non-alphanumeric chars)
            sanitized_number = "".join(c for c in contact_number if c.isalnum())[-10:]
            unique_id = str(uuid.uuid4())[:8]
            room_name = f"call_{sanitized_number}_{unique_id}" if sanitized_number else f"call_{unique_id}"
            env = get_env_name()
            agent_name = os.environ.get("AGENT_NAME", f"unpod-{env}-general-agent-v3")

            lkapi = api.LiveKitAPI()

            await self.create_explicit_dispatch(lkapi, agent_name, room_name, metadata)
            await lkapi.aclose()

            start = user_state.start_time
            end = user_state.end_time

            await save_execution_log(
                task_id,
                "call-dispatch",
                TaskStatusEnum.completed,
                {"status": "livekit call dispatched"},
            )

            return CallResult(
                status="in_progress",
                call_id="",
                call_status=user_state.call_status,
                call_end_reason="Provider call dispatched successfully",
                customer=user_state.user_name,
                contact_number=user_state.contact_number,
                transcript=user_state.transcript,
                duration=(
                    (user_state.end_time - user_state.start_time)
                    if user_state.end_time and user_state.start_time
                    else None
                ),
                recording_url=user_state.recording_url,
                call_start=start,
                call_end=end,
                data={
                    "usage": user_state.usage,
                    "transcript": user_state.transcript,
                    "call_type": "outbound",
                    "cost": user_state.usage.get("total_cost", 0),
                    "type": "outbound",
                    "thread_id": user_state.thread_id,
                    "room_name": room_name,
                },
            )

        except Exception as e:
            return CallResult(
                status="failed",
                call_id="",
                customer=user_state.user_name,
                call_status=user_state.call_status,
                contact_number=user_state.contact_number,
                transcript=user_state.transcript,
                recording_url=user_state.recording_url,
                error=str(e),
                data={
                    "usage": user_state.usage,
                    "transcript": user_state.transcript,
                    "call_type": "outbound",
                    "cost": 0,
                    "type": "outbound",
                    "error": str(e),
                },
            )

    async def create_explicit_dispatch(
        self, lkapi, agent_name: str, room_name: str, metadata: str
    ):
        print(f"Creating explicit dispatch  for agent {agent_name}")
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=agent_name, room=room_name, metadata=metadata
            )
        )
        logger.info("created dispatch")
        print("created dispatch")

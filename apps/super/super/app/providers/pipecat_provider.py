from typing import Dict, Any, Optional
from super.core.callback.base import BaseCallback
from super.core.configuration import BaseModelConfig
from super.core.logging import logging
from super.core.voice.providers.base import CallProvider, CallResult
from super.core.voice.pipecat.handler import PipecatVoiceHandler
from super.core.voice.schema import UserState
import uuid
from datetime import datetime
from super.core.voice.observers.metrics import CustomMetricObserver
import os
import jwt
import time


class PipecatProvider(CallProvider):
    """Pipecat call provider implementation"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._callback = None
        self._model_config = None
        self._logger = logging.get_logger("calls_orc.pipecat_provider")

    def get_provider_name(self) -> str:
        return "pipecat"

    def supports_async(self) -> bool:
        """Pipecat provider supports async operations"""
        return True

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return "contact_number" in data

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
        """Execute a PIPECAT call"""
        self._callback = callback
        self._model_config = model_config

        if instructions:
            data["objective"] = instructions
        else:
            data["objective"] = "Say Hi This your voice assistant from Unpod"
        data["agent_id"] = agent_id

        try:
            config = model_config.get_config(agent_id)

        except Exception as e:
            config = model_config.get_config("", id="1")

        # self._logger.info(f"PipecatProvider: Starting call by agent: {agent_id} with config: {config}")

        user_state = UserState(
            user_name=data.get("contact_name") or data.get("name") or "User",
            space_name=data.get("space_name") or config.get("space_name"),
            contact_number=data.get("contact_number"),
            token=data.get("token") or config.get("space_token"),
            language="English",
            thread_id=str(data.get("thread_id")) or str(uuid.uuid4()),
            user={
                "user_id": data.get("user_id", str(uuid.uuid4())),
            },
            persona=config.get("persona"),
            system_prompt=config.get("system_prompt"),
            first_message=config.get("first_message"),
            model_config=config,
            config=config,
            knowledge_base=config.get("knowledge_base", []),
            start_time=datetime.now(),
            usage=self.create_default_usage(config),
            transcript=[],
            recording_url="",
        )

        voice_agent = PipecatVoiceHandler(
            session_id=user_state.thread_id,
            user_state=user_state,
            callback=self._callback,
            model_config=config,
            observer=CustomMetricObserver,
        )
        try:
            if call_type == "inbound":
                await voice_agent.initialize_inbound_call(
                    data.get("room_name"),
                    config,
                    CustomMetricObserver,
                    data.get("contact_number"),
                    user_state,
                )
            else:
                await voice_agent.initialize_outbound_call(
                    data, user_state, phone_number=user_state.contact_number
                )

            try:
                start = user_state.start_time.isoformat()
                end = user_state.end_time.isoformat()
            except Exception as e:
                start = "NULL"
                end = "NULL"

            # Get turn_metrics from observer if available
            turn_metrics = None
            if hasattr(voice_agent, 'observer_instance') and hasattr(voice_agent.observer_instance, 'get_all_turn_metrics'):
                turn_metrics = voice_agent.observer_instance.get_all_turn_metrics()
                if turn_metrics:
                    print(f"📊 Retrieved turn_metrics for {len(turn_metrics)} turns from observer")

            result = CallResult(
                status="completed",
                call_status=user_state.call_status,
                call_id=user_state.thread_id,
                customer=user_state.user_name,
                contact_number=user_state.contact_number,
                transcript=user_state.transcript,
                duration=(user_state.end_time - user_state.start_time)
                if user_state.end_time and user_state.start_time
                else "0",
                recording_url=user_state.recording_url,
                call_start=start,
                call_end=end,
                call_end_reason=user_state.end_reason
                if user_state.end_reason
                else None,
                assistant_number=self.get_assistant_number(),
                data={
                    "usage": self.get_usage(user_state.usage),
                    "transcript": user_state.transcript,
                    "call_type": "outbound",
                    "cost": user_state.usage.get("total_cost", 0.0),
                    "type": "outboundPhoneCall",
                    "turn_metrics": turn_metrics,
                },
            )

            if user_state.call_error and user_state.call_status == "failed":
                result.error = user_state.call_error
                result.status = "failed"

            return result

        except Exception as e:
            return CallResult(
                status="failed",
                call_id="",
                call_status=user_state.call_status,
                customer=user_state.user_name,
                contact_number=user_state.contact_number,
                transcript=user_state.transcript,
                recording_url=user_state.recording_url,
                assistant_number=self.get_assistant_number(),
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

    def create_default_usage(self, model_config):
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


    def get_assistant_number(self) -> str:
        now = int(time.time())
        _token_expiry = now + 3500
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")

        payload = {
            "iss": api_key,
            "exp": now + 3600,
            "iat": now,
            "video": {"ingressAdmin": True},
            "sip": {"call": True, "admin": True},
        }
        token = jwt.encode(payload, api_secret, algorithm="HS256")
        token = token if isinstance(token, str) else token.decode("utf-8")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {"sip_trunk_id": os.getenv("SIP_OUTBOUND_TRUNK_ID")}
        import requests

        base_url = os.getenv("LIVEKIT_URL").replace("wss://", "")
        res = requests.post(
            f"https://{base_url}/twirp/livekit.SIP/GetSIPOutboundTrunk",
            headers=headers,
            json=payload,
        )

        return res.json().get("trunk", {}).get("numbers", [""])[0]

    def get_usage(self, usage):
        data = {
            "llm_prompt_tokens": usage.get("llm_prompt_tokens", 0),
            "llm_completion_tokens": usage.get("llm_completion_tokens", 0),
            "tts_characters_count": usage.get("tts_characters_count", 0),
            "stt_audio_duration": usage.get("stt_audio_duration", 0),
        }

        return data

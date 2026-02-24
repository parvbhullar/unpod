import asyncio
import atexit
import gc
import json
import logging
import os
import signal
import threading
from typing import Any, Dict, Optional, Set
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from super.core.logging import logging as app_logging
from super.core.callback.base import BaseCallback
from super.core.configuration import BaseModelConfig
from super.core.context.schema import Message, User, Role
from super.core.handler.config import (
    HandlerConfiguration,
    RoleConfiguration,
    ExecutionNature,
)
from super.core.plugin.base import PluginLocation, PluginStorageFormat
from super.core.voice.base import BaseVoiceHandler
from super.core.voice.services.livekit_services import (
    DEFAULT_TTS_PROVIDER,
    DEFAULT_TTS_VOICE,
)
from super.core.voice.services import livekit_services

# from super.core.voice.managers.prompt_manager import PromptManager
from super.core.voice.schema import (
    UserState,
    CallSession,
    AgentConfig,
    TransportType,
    Modality,
)
from super.core.voice.common.common import create_default_usage

from super.core.voice.common.common import create_default_usage, add_perf_log

from dotenv import load_dotenv

# from pydantic import Field
from time import perf_counter
import traceback
from super.core.voice.observers.metrics import CustomMetricObserver
from super_services.voice.models.config import MessageCallBack
from super.core.voice.livekit.lite_handler import LiveKitLiteHandler
from super.core.voice.pipecat.handler import PipecatVoiceHandler
from super.core.voice.pipecat.lite_handler import LiteVoiceHandler
from super.core.voice.common.common import build_call_result
from super.core.voice.common.prefect import trigger_post_call
from super.core.voice.schema import CallStatusEnum
from super.core.voice.workflows.pre_call import PreCallWorkFlow
from super.core.voice.common.common import send_web_notification
import random


load_dotenv(override=True)



from livekit import agents, rtc, api
from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    AutoSubscribe,
)

from super_services.libs.core.timezone_utils import normalize_phone_number

class VoiceAgentHandler(BaseVoiceHandler, ABC):
    """A LiveKit-based handler for voice conversations with same interface as livekitVoiceHandler."""

    default_configuration = HandlerConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.voice.voice_agent_handler.VoiceAgentHandler",
        ),
        role=RoleConfiguration(
            name="voice_agent_handler",
            role=(
                "A handler to handle voice conversations using either of Livekit/Pipecat."
            ),
            cycle_count=0,
            max_task_cycle_count=3,
        ),
        execution_nature=ExecutionNature.AUTO,
    )

    def __init__(
        self,
        session_id: str = None,
        callback: BaseCallback = None,
        model_config: BaseModelConfig = None,
        configuration: HandlerConfiguration = default_configuration,
        logger: logging.Logger = app_logging.get_logger("livekit.voice.handler"),
        agent_name: str = "voice_test_agent-2",
        handler_type: Optional[str] = None,
    ) -> None:
        super().__init__(
            session_id=session_id,
            callback=callback,
            configuration=configuration,
            logger=logger,
        )
        self._session_id = session_id
        self._callback = callback or None
        self._logger = logger
        self._configuration = configuration
        self.config = model_config or None
        self.user_state = None
        self.agent_name = agent_name
        self._job_context: Optional[JobContext] = None
        self._transport_type = TransportType.LIVEKIT
        self.agent_config = AgentConfig(
            agent_name=session_id or "SuperVoiceAgent",
            model_config=model_config,
            callback=callback,
        )
        self._agent = None

    async def execute(self, objective: str | Message = "", *args, **kwargs) -> Any:
        """Run worker execution from async contexts."""
        self._logger.info("execute() called; delegating to execute_agent()")
        return await asyncio.to_thread(self.execute_agent)


    async def _init_variables(self, user_state: UserState):
        """Initialize variables - same interface as livekit handler"""
        self._logger.info("Initializing variables...")
        if not self.config:
            self.config = user_state.model_config
        self.session_id = str(user_state.thread_id)
        self._room_name = user_state.room_name or f"room-{user_state.thread_id}"

    def _send_callback(self, message: Message, thread_id: str):
        """Send a message through the callback if one is configured."""
        if self._callback:
            self._callback.send(message, thread_id=thread_id)


    async def run_agent(
        self,
        ctx: agents.JobContext,
        user_state: UserState,
        _agent,
        retry: int = 3,
    ):
        try:
            await _agent.execute_with_context(ctx)
        except Exception as e:
            self._logger.error(f"Error starting agent session: {e}")
            ctx.shutdown()



    async def manage_call(
        self,
        ctx: agents.JobContext,
        participant: rtc.RemoteParticipant,
        user_state: UserState,
        _agent,
        call_type: str = "outbound",
    ):
        if call_type == "inbound":
            self._logger.info("inbound call - starting agent directly")
            await self.run_agent(ctx, user_state, _agent)
            return

        self.user_state = user_state

        start_time = perf_counter()
        dialing_timeout_seconds = 45  # Allow up to 45 seconds for call to connect

        self._logger.info("dialing")

        while perf_counter() - start_time < dialing_timeout_seconds:
            elapsed = perf_counter() - start_time
            call_status = participant.attributes.get("sip.callStatus")

            if call_status == "dialing":
                # Log progress every 5 seconds
                if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                    self._logger.debug(f"Still dialing... {int(elapsed)}s elapsed")
                # Only fail if we've been dialing for the full timeout
                # (handled by while loop condition)

            if call_status == "active":
                self._logger.info("user has picked up")

                user_state.call_status = CallStatusEnum.CONNECTED
                await self.run_agent(ctx, user_state, _agent)
                return

            elif call_status == "automation":
                pass
            elif participant.disconnect_reason == rtc.DisconnectReason.USER_REJECTED:
                self._logger.info("user rejected the call, exiting job")

                user_state.call_status = CallStatusEnum.CANCELLED

                ctx.shutdown()
                break

            elif participant.disconnect_reason == rtc.DisconnectReason.USER_UNAVAILABLE:
                if _agent:
                    await _agent.end_ongoing_agent()

                self._logger.info("user did not pick up, exiting job")

                user_state.end_time = user_state.start_time
                user_state.call_status = CallStatusEnum.NOT_CONNECTED

                # res = await build_call_result(user_state)
                # await trigger_post_call(user_state=user_state, res=res)


                ctx.shutdown()
                break

            elif participant.disconnect_reason == rtc.DisconnectReason.ROOM_CLOSED:
                if _agent:
                    await _agent.end_ongoing_agent()

                self._logger.info(
                    f"User has disconnected: {participant.disconnect_reason}"
                )

                user_state.call_status = CallStatusEnum.COMPLETED


                # res = await build_call_result(user_state)
                # await trigger_post_call(user_state=user_state, res=res)

                ctx.shutdown()
                break

            elif participant.disconnect_reason == rtc.DisconnectReason.UNKNOWN_REASON:
                if _agent:
                    await _agent.end_ongoing_agent()

                self._logger.info(
                    f"User has disconnected: {participant.disconnect_reason}"
                )


                user_state.call_status = CallStatusEnum.FAILED



                ctx.shutdown()
                break
            await asyncio.sleep(0.1)

        # If we exit the loop without connecting, it's a timeout
        if participant.attributes.get("sip.callStatus") == "dialing":
            self._logger.info(
                "SIP Failed - dialing timeout after %ds", dialing_timeout_seconds
            )

            user_state.end_time = user_state.start_time
            user_state.call_status = CallStatusEnum.FAILED
        ctx.shutdown()

    async def _create_assistant(
        self, user_state, ctx: JobContext, handler_class, handler_name
    ):

        try:
            handler_config = (
                dict(user_state.model_config) if user_state.model_config else {}
            )
            if "agent_name" not in handler_config:
                handler_config["agent_name"] = self.agent_name

            self._agent = handler_class(
                session_id=user_state.thread_id,
                user_state=user_state,
                callback=MessageCallBack(),
                model_config=handler_config,
                observer=CustomMetricObserver,
            )

            started = await self._agent.preload_agent(user_state, CustomMetricObserver)

            if started:
                return True
            else:
                return False

        except Exception as e:
            traceback.print_exc()
            print(f"unable to initiate agent {str(e)}")

    async def _get_handler_classes(self, ctx: JobContext):
        from super.core.voice.testing_agents.vanilla_handler import VanillaAgenHandler
        handler_class = VanillaAgenHandler
        handler_name = "VanillaAgenHandler"

        return handler_class, handler_name

    def get_trunk_id(self, user_state):
        config = user_state.model_config
        telephony = config.get("telephony") if isinstance(config, dict) else []

        if not telephony:
            return os.getenv("SIP_OUTBOUND_TRUNK_ID")

        num = random.choice(telephony)

        if not isinstance(num, dict):
            return os.getenv("SIP_OUTBOUND_TRUNK_ID")

        if num.get("association", {}).get("trunk_id"):
            print(f"\n\n selected number {num.get('number')}  for call \n\n ")
            return num.get("association", {}).get("trunk_id")
        else:
            return os.getenv("SIP_OUTBOUND_TRUNK_ID")

    async def _create_sip_participant_in_room(
            self, ctx: JobContext, data: Dict[str, Any], user_state: UserState
        ) -> Optional[rtc.RemoteParticipant]:
            """Create SIP participant inside the room - based on sip_lifecycle.py"""
            try:
                # trunk_id = data.get("trunk_id", os.getenv("SIP_OUTBOUND_TRUNK_ID"))
                phone_number = normalize_phone_number(user_state.contact_number)
                trunk_id = self.get_trunk_id(user_state)
                room_name = ctx.room.name
                identity = f"idt_{phone_number}"

                if not user_state.extra_data and not isinstance(
                    user_state.extra_data, dict
                ):
                    user_state.extra_data = {}

                user_state.extra_data["trunk_id"] = trunk_id
                user_state.extra_data["identity"] = identity

                self._logger.info(
                    f"Creating SIP participant: trunk={trunk_id}, phone={phone_number}, room={room_name}"
                )
                if not phone_number:
                    return await ctx.wait_for_participant()

                for i in range(2):
                    # Check if participant already connected
                    existing = [
                        p
                        for p in ctx.room.remote_participants.values()
                        if p.identity == identity
                    ]
                    if existing:
                        self._logger.info(
                            f"SIP participant already in room: {existing[0].identity}"
                        )
                        return existing[0]

                    try:
                        await ctx.api.sip.create_sip_participant(
                            api.CreateSIPParticipantRequest(
                                sip_trunk_id=trunk_id,
                                sip_call_to=phone_number,
                                room_name=room_name,
                                participant_identity=identity,
                                participant_name=user_state.user_name,
                                krisp_enabled=True,
                            )
                        )
                        participant = await ctx.wait_for_participant(identity=identity)

                        return participant

                    except Exception as e:
                        self._logger.error(
                            f"Failed to create SIP participant attempt {i+1}/2: "
                            f"{type(e).__name__}: {e}"
                        )
                        # Participant may have connected despite API error
                        connected = [
                            p
                            for p in ctx.room.remote_participants.values()
                            if p.identity == identity
                        ]
                        if connected:
                            self._logger.info(
                                f"SIP participant connected despite API error: "
                                f"{connected[0].identity}"
                            )
                            return connected[0]
                        trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")

            except Exception as e:
                self._logger.error(f"Error creating SIP participant: {e}")
                import traceback

                self._logger.error(traceback.format_exc())
                return None

    async def _get_config_with_cache(
        self, agent_handle: Optional[str] = None, space_token: Optional[str] = None
    ) -> Optional[Dict]:
        from super_services.voice.models.config import ModelConfig
        config_loader = ModelConfig()
        config = None
        config = config_loader.get_config(agent_handle)

        return config if config else {}

    async def entrypoint(self, ctx: JobContext):
        _entrypoint_start = perf_counter()

        try:
            lk_url = os.getenv("LIVEKIT_URL", "")
            lk_key = os.getenv("LIVEKIT_API_KEY", "")
            lk_secret = os.getenv("LIVEKIT_API_SECRET", "")

            _get_handlers = asyncio.create_task(
                self._get_handler_classes(ctx=ctx), name="handler_class"
            )

            await ctx.connect()
            self._job_context = ctx

            metadata = json.loads(ctx.job.metadata) if ctx.job.metadata else {}

            extra_data = {}
            extra_data = {}

            user_data=metadata.get('data',{})

            agent_id=metadata.get("data",{}).get("agent_id","gamestop-iu3kqyk3rf4x")
            model_config=await self._get_config_with_cache(agent_id)

            user_state = UserState(
                user_name=user_data.get("contact_name", "User"),
                space_name=user_data.get("space_name", "Unpod AI"),
                contact_number=user_data.get("contact_number"),
                token=user_data.get("token", ""),
                language=model_config.get("language", "English"),
                thread_id=str(user_data.get("thread_id", "")),
                user=user_data.get("user", {}),
                model_config=model_config,
                persona=model_config.get("persona"),
                system_prompt=model_config.get("script"),
                first_message=model_config.get("first_message"),
                knowledge_base=model_config.get("knowledge_base", []),
                start_time=datetime.utcnow(),
                usage=create_default_usage(model_config),
                transcript=[],
                room_name=ctx.room.name,
                task_id=user_data.get("task_id", ""),
                extra_data={},
            )
            self.user_state = user_state

            handler_class, handler_name = await _get_handlers

            await self._create_assistant(
                user_state, ctx, handler_class, handler_name
            )

            participant = await self._create_sip_participant_in_room(
                ctx=ctx, data=user_data, user_state=user_state
            )
            if asyncio.iscoroutine(participant):
                participant = await participant

            if participant:
                await self.manage_call(
                    ctx, participant, user_state, self._agent, "outbound"
                )
            else:
                pass

        except Exception as e:
            error_str = str(e)
            self._logger.error(f"Error in entrypoint: {e}")
            self._logger.error(traceback.format_exc())

            # Provide specific guidance for common errors
            if "401" in error_str or "Unauthorized" in error_str:
                self._logger.error(
                    "[401 ERROR] This typically means:\n"
                    "  1. LIVEKIT_API_KEY or LIVEKIT_API_SECRET environment variables are not set\n"
                    "  2. The API credentials don't match the LiveKit Cloud project\n"
                    "  3. The agent worker is using different credentials than the dispatch\n"
                    "Please verify environment variables are correctly set."
                )
            elif "signal failure" in error_str.lower():
                self._logger.error(
                    "[SIGNAL FAILURE] Connection to LiveKit server failed. Check:\n"
                    "  1. LIVEKIT_URL is correct and reachable\n"
                    "  2. Network connectivity to LiveKit Cloud\n"
                    "  3. WebSocket port is not blocked"
                )

            if hasattr(self, "user_state") and self.user_state is not None:
              pass
            raise e

    async def entrypoint_console(self,ctx:JobContext):

        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        metadata = json.loads(ctx.job.metadata) if ctx.job.metadata else {}

        _get_handlers = asyncio.create_task(
            self._get_handler_classes(ctx=ctx), name="handler_class"
        )

        extra_data = {}
        extra_data = {}

        user_data = metadata.get('data', {})

        agent_id = metadata.get("data", {}).get("agent_id", "gamestop-iu3kqyk3rf4x")
        model_config = await self._get_config_with_cache(agent_id)

        user_state = UserState(
            user_name=user_data.get("contact_name", "User"),
            space_name=user_data.get("space_name", "Unpod AI"),
            contact_number=user_data.get("contact_number"),
            token=user_data.get("token", ""),
            language=model_config.get("language", "English"),
            thread_id=str(user_data.get("thread_id", "")),
            user=user_data.get("user", {}),
            model_config=model_config,
            persona=model_config.get("persona"),
            system_prompt=model_config.get("script"),
            first_message=model_config.get("first_message"),
            knowledge_base=model_config.get("knowledge_base", []),
            start_time=datetime.utcnow(),
            usage=create_default_usage(model_config),
            transcript=[],
            room_name=ctx.room.name,
            task_id=user_data.get("task_id", ""),
            extra_data={},
        )
        self.user_state = user_state

        handler_class, handler_name = await _get_handlers

        await self._create_assistant(
            user_state, ctx, handler_class, handler_name
        )
        try:
            await self.run_agent(ctx,user_state, self._agent)
        except Exception as e:
            pass

    def execute_agent(self):
        """Execute agent worker - synchronous wrapper for cli.run_app"""
        try:
            livekit_services._ensure_livekit_plugins_loaded(self._logger)
            try:
                cli.run_app(
                    WorkerOptions(
                        entrypoint_fnc=self.entrypoint,
                        agent_name=self.agent_name,
                        initialize_process_timeout=float(
                            os.getenv("LK_PROCESS_TIMEOUT", "60.0")
                        ),
                    )
                )
            finally:
                # Ensure cleanup on normal exit
               pass

        except Exception as e:
            self._logger.error(f"Error in execute_agent: {e}")
            raise e


if __name__ == "__main__":
    from super_services.libs.core.utils import get_env_name
    from super_services.voice.models.config import ModelConfig
    env = get_env_name()
    AGENT_NAME = os.environ.get("AGENT_NAME", f"unpod-{env}-general-agent-v3")

    voice_agent = VoiceAgentHandler(
        callback=MessageCallBack(), model_config=ModelConfig(), agent_name=AGENT_NAME, handler_type=os.environ.get("WORKER_HANDLER", "livekit")
    )
    voice_agent.execute_agent()

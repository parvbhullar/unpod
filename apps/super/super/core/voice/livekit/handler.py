import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional, Annotated
from abc import ABC
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
from super.core.voice.managers.prompt_manager import PromptManager
from super.core.voice.schema import UserState, CallSession, AgentConfig, TransportType
from super.core.voice.common.common import create_default_usage
from super.core.voice.services.livekit_services import (
    DEFAULT_TTS_PROVIDER,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_VOICE,
)
from dotenv import load_dotenv
from pydantic import Field
from time import perf_counter
import traceback

# Import LiveKit SDK
try:
    from livekit import agents, rtc, api
    from livekit.agents import (
        JobContext,
        WorkerOptions,
        cli,
        # AutoSubscribe,
        metrics,
        MetricsCollectedEvent,
    )
    from livekit.agents.voice import (
        Agent,
        AgentSession,
        RunContext,
        ConversationItemAddedEvent,
        # room_io,
        UserInputTranscribedEvent,
        AgentStateChangedEvent,
    )
    from livekit.agents.llm import function_tool
    from livekit.plugins import silero
    from livekit.plugins import openai, google
    from openai.types.beta.realtime.session import TurnDetection
    from livekit.plugins.turn_detector.multilingual import MultilingualModel

    from livekit.plugins import (
        deepgram,
        openai,
        groq,
        elevenlabs,
        speechmatics,
        playai,
        google,
        sarvam,
        aws,
        gladia,
        lmnt,
        cartesia,
    )

    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False

load_dotenv(override=True)


class LiveKitVoiceAgent(Agent):
    """LiveKit Agent instance that extends the base Agent class"""

    def __init__(
        self,
        handler: "LiveKitVoiceHandler",
        user_state: UserState,
        job_context: JobContext,
    ):
        # Get config from user_state
        model_config = user_state.model_config or {}
        self._session = None
        self._session_id = str(user_state.thread_id)
        self.model_config = model_config
        self.handler = handler
        self.user_state = user_state
        self.job_context = job_context
        self._logger = handler._logger
        self._callback = None
        self._tool_calling = True

        self.agent_config = AgentConfig(
            agent_name=self._session_id or "SuperVoiceAgent",
            model_config=model_config,
        )
        self.prompt_manager = PromptManager(
            config=self.model_config or {},
            agent_config=self.agent_config,
            session_id=self._session_id,
            tool_calling=self._tool_calling,
            logger=self._logger,
        )
        self.pipecat_agent = None
        self.prompt_manager.user_state = (
            self.user_state
        )  # Update user_state for template replacement
        # self.prompt_manager.input_data = self.input_data  # Pass input_data for template replacement
        self.prompt_manager.update_config(self.model_config)
        self.prompt_manager.update_session_id(self._session_id)
        super().__init__(instructions=self.prompt_manager._create_assistant_prompt())

    def message_callback(
        self, transcribed_text: str, role: str, user_state: UserState
    ) -> None:
        """Handle message callbacks - same interface as livekit handler"""
        thread_id = str(user_state.thread_id)
        if "Call Status" in transcribed_text and role == "system":
            msg = Message.add_notification(transcribed_text.replace("Call Status:", ""))
            self._send_callback(msg, thread_id=thread_id)
        elif "EOF" in transcribed_text and role == "system":
            user_state.end_time = datetime.utcnow()
            usage = self.create_usage(user_state)
            msg = Message.add_task_end_message(
                "Voice Execution Completed",
                id=thread_id,
                data={
                    "start_time": user_state.start_time.isoformat()
                    if user_state.start_time
                    else None,
                    "end_time": user_state.end_time.isoformat()
                    if user_state.end_time
                    else None,
                    "usage": usage,
                    "recording_url": user_state.recording_url,
                    "transcript": user_state.transcript or [],
                },
            )
            self._send_callback(msg, thread_id=thread_id)

    def _send_callback(self, message: Message, thread_id: str):
        """Send a message through the callback if one is configured."""
        if self._callback:
            self._callback.send(message, thread_id=thread_id)

    def get_agent_session(self, ctx: agents.JobContext):
        # from livekit.agents import AgentSession

        llm_provider = self.model_config.get("llm_provider", "openai")
        speaking_plan = self.model_config.get("speaking_plan", {})
        mode = self.model_config.get(
            "mode", os.getenv("AGENT_INFRA_MODE", "realtime")
        )  # inference / realtime

        userdata = {
            "token": self.user_state.token,
            "knowledge_base": self.user_state.knowledge_base,
            "ctx_room": ctx.room,
        }

        llm_model = self._create_llm_service()
        stt_model = self._create_stt_service()
        tts_model = self._create_tts_service()

        # Set up VAD
        vad = silero.VAD.load(
            min_silence_duration=speaking_plan.get("min_silence_duration", 0.2),
            activation_threshold=0.3,
        )

        # Initialize based on LLM provider
        if mode == "inference":
            # Auto-select compatible model for languages not supported by nova-3
            model_config = self.model_config
            stt_model_name = model_config.get("stt_model")
            stt_language = model_config.get("stt_language")
            stt_provider = model_config.get("stt_provider")

            if stt_provider == "deepgram":
                nova_2_only_languages = [
                    "hi",
                    "ta",
                    "kn",
                    "te",
                    "ml",
                ]  # Hindi, Tamil, Kannada, Telugu, Malayalam
                if stt_model_name == "nova-3-general":
                    self._logger.warning(
                        f"nova-3-general doesn't support language '{stt_language}'. Using nova-2-general instead."
                    )
                    stt_model_name = "nova-2"

            print(
                f"inference mode : \n stt : {stt_provider}/{stt_model_name}:{stt_language}  \n llm : {llm_provider}/{model_config.get('llm_model')} \n tts : {model_config.get('tts_provider')}/{model_config.get('tts_model')}:{model_config.get('tts_voice')}"
            )
            session = AgentSession(
                userdata=userdata,
                stt="deepgram/nova-3:multi",  # f"{stt_provider}/{stt_model_name}:{stt_language}",
                llm="openai/gpt-5-mini",
                # llm=inference.LLM(
                #         model="openai/gpt-5-mini",
                #         provider="openai",
                #         extra_kwargs={
                #             "reasoning_effort": "low"
                #         }
                #     ), #f"{llm_provider.lower()}/{model_config.get('llm_model')}",
                tts=f"{DEFAULT_TTS_PROVIDER}/{DEFAULT_TTS_MODEL}:{DEFAULT_TTS_VOICE}",
                min_interruption_duration=speaking_plan.get(
                    "min_interruption_duration", 0.3
                ),
                min_interruption_words=speaking_plan.get("min_interruption_words", 4),
                vad=vad,
                turn_detection=MultilingualModel(),
            )
            return session
        if llm_provider == "openai-realtime":
            return AgentSession(
                userdata=userdata,
                llm=openai.realtime.RealtimeModel(
                    temperature=0.7,
                    turn_detection=TurnDetection(
                        type="semantic_vad",
                        eagerness="medium",
                        create_response=True,
                        interrupt_response=True,
                    ),
                ),
                vad=vad,
            )
        elif llm_provider == "gemini-realtime":
            return AgentSession(
                userdata=userdata,
                llm=google.beta.realtime.RealtimeModel(
                    model="gemini-2.0-flash-exp",
                    voice="Puck",
                    temperature=0.3,
                ),
                vad=vad,
            )
        else:
            # Standard pipeline with separate STT, LLM, TTS
            return AgentSession(
                userdata=userdata,
                stt=stt_model,
                llm=llm_model,
                tts=tts_model,
                vad=vad,
                turn_detection=MultilingualModel(),
            )

    async def build_call_result(self, user_state):
        from super.core.voice.providers.base import CallResult

        call_result = CallResult(
            status="completed",
            call_id=user_state.thread_id,
            customer=user_state.user_name,
            contact_number=user_state.contact_number,
            transcript=user_state.transcript,
            duration=(user_state.end_time - user_state.start_time)
            if user_state.end_time and user_state.start_time
            else "0",
            recording_url=user_state.recording_url,
            call_start=user_state.start_time,
            call_end=user_state.end_time,
            call_end_reason=user_state.end_reason if user_state.end_reason else None,
            data={
                "type": user_state.extra_data.get("call_type"),
                "transcript": user_state.transcript,
                "cost": user_state.usage.get("total_cost", 0.0),
            },
        )

        return call_result

    async def run_agent(
        self,
        ctx: agents.JobContext,
        user_state: UserState,
        pipecat_agent,
        retry: int = 3,
    ):
        try:
            if pipecat_agent:
                event = await self.handler._event_client.get()

                print(f"\n\n\n{user_state.thread_id}: {event}\n\n\n")
                await pipecat_agent.execute()
                res = await self.build_call_result(user_state)

                from super_services.prefect_setup.deployments.utils import (
                    trigger_deployment,
                )

                asyncio.run(
                    trigger_deployment(
                        "Post-Call-Flow",
                        {
                            "job": {
                                "task_id": user_state.task_id,
                                "call_result": res,
                                "user_state": user_state,
                            }
                        },
                    )
                )

                # print(f"{'='*50}\n\n pipecat agent executed successfully \n {user_state} \n\n {'='*50}")

            else:
                self._session = self.get_agent_session(ctx=ctx)
                for i in range(retry):
                    self._logger.info(f"starting agent session, attempt {i + 1}")
                    try:
                        from livekit.agents.voice import room_io
                        from livekit.plugins import noise_cancellation

                        await self._session.start(
                            room=ctx.room,
                            agent=self,
                            room_input_options=room_io.RoomInputOptions(
                                noise_cancellation=noise_cancellation.BVC()
                            ),
                        )
                        break
                    except Exception as e:
                        continue

        except Exception as e:
            self._logger.error(f"Error starting agent session: {e}")
            self.message_callback("EOF\n", role="system", user_state=user_state)
            ctx.shutdown()
            return

    async def manage_call(
        self,
        ctx: agents.JobContext,
        participant: rtc.RemoteParticipant,
        user_state: UserState,
        pipecat_agent,
        call_type: str = "outbound",
    ):
        if call_type == "inbound":
            self._logger.info("inbound call - starting agent directly")
            await self.run_agent(ctx, user_state, pipecat_agent)
            return

        self.user_state = user_state

        start_time = perf_counter()
        dialing_timeout_seconds = 45  # Allow up to 45 seconds for call to connect

        self._logger.info("dialing")
        self.message_callback(
            f"Call Status:Dialing\n", role="system", user_state=user_state
        )

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
                self.message_callback(
                    f"Call Status:User has picked up\n",
                    role="system",
                    user_state=user_state,
                )
                await self.run_agent(ctx, user_state, pipecat_agent)
                return

            elif call_status == "automation":
                pass
            elif participant.disconnect_reason == rtc.DisconnectReason.USER_REJECTED:
                if pipecat_agent:
                    await pipecat_agent.end_ongoing_agent()

                self._logger.info("user rejected the call, exiting job")
                self.message_callback(
                    f"Call Status:User rejected the call\n",
                    role="system",
                    user_state=user_state,
                )
                self.message_callback("EOF\n", role="system", user_state=user_state)
                ctx.shutdown()
                break

            elif participant.disconnect_reason == rtc.DisconnectReason.USER_UNAVAILABLE:
                if pipecat_agent:
                    await pipecat_agent.end_ongoing_agent()

                self._logger.info("user did not pick up, exiting job")
                self.message_callback(
                    f"Call Status:User did not pick up\n",
                    role="system",
                    user_state=user_state,
                )
                self.message_callback("EOF\n", role="system", user_state=user_state)
                ctx.shutdown()
                break

            elif participant.disconnect_reason == rtc.DisconnectReason.ROOM_CLOSED:
                if pipecat_agent:
                    await pipecat_agent.end_ongoing_agent()

                self._logger.info(
                    f"User has disconnected: {participant.disconnect_reason}"
                )
                self.message_callback(
                    f"Call Status:User has hanged up\n",
                    role="system",
                    user_state=user_state,
                )
                self.message_callback("EOF\n", role="system", user_state=user_state)
                ctx.shutdown()
                break
            elif participant.disconnect_reason == rtc.DisconnectReason.UNKNOWN_REASON:
                if pipecat_agent:
                    await pipecat_agent.end_ongoing_agent()

                self._logger.info(
                    f"User has disconnected: {participant.disconnect_reason}"
                )
                self.message_callback(
                    f"Call Status:User has hanged up\n",
                    role="system",
                    user_state=user_state,
                )
                self.message_callback("EOF\n", role="system", user_state=user_state)
                ctx.shutdown()
                break
            await asyncio.sleep(0.1)

        # If we exit the loop without connecting, it's a timeout
        if participant.attributes.get("sip.callStatus") == "dialing":
            self._logger.info(
                "SIP Failed - dialing timeout after %ds", dialing_timeout_seconds
            )
            self.message_callback(
                f"Call Status:SIP Failed\n",
                role="system",
                user_state=user_state,
            )
            self.message_callback("EOF\n", role="system", user_state=user_state)
        ctx.shutdown()

    def _create_llm_service(self):
        """Create LLM service based on config - following configurable_agent.py pattern"""
        llm_provider = self.model_config.get("llm_provider", "openai")
        llm_model = self.model_config.get("llm_model", "gpt-4o")
        self._logger.info(
            f"LLM provider: {llm_provider}, llm_model: {self.model_config.get('llm_model')}"
        )

        try:
            if llm_provider == "openai":
                return openai.LLM(
                    model=llm_model, temperature=0.3, parallel_tool_calls=True
                )
            elif llm_provider == "groq":
                return groq.LLM(
                    model=llm_model, temperature=0.3, parallel_tool_calls=True
                )
            elif llm_provider == "anthropic":
                return openai.LLM(
                    model=llm_model, temperature=0.3, parallel_tool_calls=True
                )
            elif llm_provider == "gemini" or llm_provider == "google":
                return google.LLM(model=llm_model, temperature=0.3)
            else:
                return openai.LLM(
                    model="gpt-4o", temperature=0.3, parallel_tool_calls=True
                )
        except Exception as e:
            self._logger.error(f"Failed to create LLM service: {e}")
            return None

    def _create_stt_service(self, context=""):
        """Create STT service based on config - following configurable_agent.py pattern"""

        stt_provider = self.model_config.get("stt_provider", "openai")
        stt_model = self.model_config.get("stt_model", "whisper-1")
        stt_language = self.model_config.get("language", "en")
        try:
            if stt_provider == "deepgram":
                return deepgram.STT(model=stt_model, language=stt_language)
            elif stt_provider == "openai":
                return openai.STT(model=stt_model, language=stt_language)
            elif stt_provider == "groq":
                return groq.STT(model=stt_model)
            elif stt_provider == "speechmatics":
                return speechmatics.STT()
            elif stt_provider == "sarvam":
                return sarvam.STT(language="hi-IN", model=stt_model)
            elif stt_provider == "google":
                return google.STT(
                    spoken_punctuation=False,
                    credentials_file="/home/dev/Downloads/Arshpreet/cred.json",
                )
            elif stt_provider == "aws":
                return aws.STT(language=stt_language)
            elif stt_provider == "gladia":
                return gladia.STT(
                    translation_enabled=True,
                    languages=stt_language,
                    translation_target_languages=stt_language,
                    api_key=os.getenv("GLADIA_API_KEY"),
                )

            else:
                return deepgram.STT()
        except Exception as e:
            self._logger.error(f"Failed to create STT service: {e}")
            return None

    def _create_tts_service(self):
        """Create TTS service based on config - following configurable_agent.py pattern"""

        tts_provider = self.model_config.get("tts_provider", DEFAULT_TTS_PROVIDER)
        tts_model = self.model_config.get("tts_model", DEFAULT_TTS_MODEL)
        tts_voice = self.model_config.get("tts_voice", DEFAULT_TTS_VOICE)

        try:
            if tts_provider == "deepgram":
                return deepgram.TTS(model=tts_model)
            elif tts_provider == "openai":
                return openai.TTS(model=tts_model, voice=tts_voice)
            elif tts_provider == "groq":
                return groq.TTS(model=tts_model)
            elif tts_provider == "elevenlabs":
                return elevenlabs.TTS(voice_id=tts_voice, model=tts_model)
            elif tts_provider == "PlayHT":
                return playai.TTS(model="play3.0-mini")
            elif tts_provider == "sarvam":
                return sarvam.TTS(target_language_code="hi-IN", speaker=tts_voice)
            elif tts_provider == "google":
                return google.TTS(
                    credentials_file="/home/dev/Downloads/Arshpreet/cred.json"
                )
            elif tts_provider == "aws":
                return aws.TTS(
                    voice=tts_voice,
                    speech_engine="generative",
                    language=self.model_config.get("language", "en"),
                )
            elif tts_provider == "lmnt":
                return lmnt.TTS(
                    voice="leah",
                )
            elif tts_provider == "cartesia":
                return cartesia.TTS(
                    model=tts_model or DEFAULT_TTS_MODEL,
                    voice=tts_voice,
                )
            else:
                # Default fallback
                return self._create_fallback_tts()

        except Exception as e:
            self._logger.error(f"Failed to create TTS service: {e}")
            return self._create_fallback_tts()

    def _create_fallback_tts(self):
        """Create fallback TTS service using default provider."""
        try:
            from livekit.agents import inference

            fallback_model = os.getenv("FALLBACK_TTS_MODEL", DEFAULT_TTS_MODEL)
            fallback_voice = os.getenv("FALLBACK_TTS_VOICE", DEFAULT_TTS_VOICE)
            self._logger.warning(
                f"Using fallback TTS: {DEFAULT_TTS_PROVIDER} {fallback_model} ({fallback_voice})"
            )
            return inference.TTS(
                model=f"{DEFAULT_TTS_PROVIDER}/{fallback_model}",
                voice=fallback_voice,
            )
        except Exception as e:
            self._logger.error(f"Fallback TTS also failed: {e}")
            return None

    @function_tool(
        name="get_docs",
        description="Get documents from knowledge base to answer user queries.",
    )
    async def get_docs(
        self,
        context: RunContext,
        query: Annotated[str, Field(description="Query to get relevant documents")],
        kb_name: Annotated[str, Field(description="Knowledge Base Name")],
    ):
        """Get documents from knowledge base"""
        try:
            kn_bases = []
            token = self.user_state.token
            kn_list = self.user_state.knowledge_base

            if len(kn_list) >= 0:
                kn_bases = [
                    item["token"] for item in kn_list if item["name"] == kb_name
                ]
            kn_bases.append(token)
            self._logger.info(f"getting docs for with query {query}")
            ref_docs = await self.handler._get_index(query, kn_bases)
            self._logger.info("Updating Chat Context with Docs")
            return None, json.dumps(ref_docs)

        except Exception as e:
            self._logger.error(f"Error getting docs: {e}")
            return None, json.dumps(
                {
                    "error": str(e),
                    "message": "Unable to get your relevant information",
                }
            )

    def create_usage(self, user_state: UserState) -> dict:
        """Create serializable usage data from user_state - same interface as livekit handler"""
        usage_data = {}

        if (
            hasattr(user_state, "usage")
            and user_state.usage
            and hasattr(user_state.usage, "get_summary")
        ):
            summary = user_state.usage.get_summary()
            usage_data = {
                "llm_prompt_tokens": getattr(summary, "llm_prompt_tokens", 0),
                "llm_completion_tokens": getattr(summary, "llm_completion_tokens", 0),
                "tts_characters_count": getattr(summary, "tts_characters_count", 0),
                "stt_audio_duration": getattr(summary, "stt_audio_duration", 0),
            }


class LiveKitVoiceHandler(BaseVoiceHandler, ABC):
    """A LiveKit-based handler for voice conversations with same interface as livekitVoiceHandler."""

    default_configuration = HandlerConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.voice.livekit.LiveKitVoiceHandler",
        ),
        role=RoleConfiguration(
            name="livekit_voice_handler",
            role=("A handler to handle voice conversations using LiveKit."),
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
        self._execution_nature = configuration.execution_nature
        self.config = model_config or None
        self.user_state = None

        self._transport_type = TransportType.LIVEKIT
        self.agent_config = AgentConfig(
            agent_name=session_id or "SuperVoiceAgent",
            model_config=model_config,
            callback=callback,
        )
        self.agent_name = agent_name
        self.pipecat_agent = None
        # LiveKit components
        self.active_sessions: Dict[str, CallSession] = {}
        self._agent: Optional[LiveKitVoiceAgent] = None
        self._job_context: Optional[JobContext] = None
        self._agent_session: Optional[AgentSession] = None
        self._event_client = None

    def message_callback(
        self, transcribed_text: str, role: str, user_state: UserState
    ) -> None:
        """Handle message callbacks - same interface as livekit handler"""
        thread_id = str(user_state.thread_id)
        if "Call Status" in transcribed_text and role == "system":
            msg = Message.add_notification(transcribed_text.replace("Call Status:", ""))
            self._send_callback(msg, thread_id=thread_id)
        elif "EOF" in transcribed_text and role == "system":
            user_state.end_time = datetime.utcnow()
            usage = self.create_usage(user_state)
            msg = Message.add_task_end_message(
                "Voice Execution Completed",
                id=thread_id,
                data={
                    "start_time": user_state.start_time.isoformat()
                    if user_state.start_time
                    else None,
                    "end_time": user_state.end_time.isoformat()
                    if user_state.end_time
                    else None,
                    "usage": usage,
                    "recording_url": user_state.recording_url,
                    "transcript": user_state.transcript or [],
                },
            )
            self._send_callback(msg, thread_id=thread_id)

    async def _get_index(self, query: str, kn_bases: list = None) -> dict:
        """Fetch documents from knowledge base - same as livekit handler"""
        import html
        import requests

        payload = {"query": query, "kn_bases": kn_bases}
        response = requests.post(os.getenv("DOC_SEARCH_URL", ""), json=payload)
        if response.status_code != 200:
            return {
                "error": str(response.status_code),
                "message": "Internal error retrieving information.",
            }
        docs = response.json()["data"]["search_response_summary"]["top_sections"]
        doc_list = [
            {f"Context {i}": html.unescape(doc["combined_content"])}
            for i, doc in enumerate(docs)
            if (
                doc["score"] >= 0.8
                and len(doc["content"]) > 0
                and doc["recency_bias"] > 0.95
            )
        ]
        self._logger.info(f"Retrieved information:")
        return {"Reference Docs": doc_list[:3]}

    def _send_callback(self, message: Message, thread_id: str):
        """Send a message through the callback if one is configured."""
        if self._callback:
            self._callback.send(message, thread_id=thread_id)

    async def execute(self, user_state: UserState, *args, **kwargs) -> Any:
        """Execute the handler step - same interface as livekit handler"""
        if not LIVEKIT_AVAILABLE:
            raise Exception("LiveKit is not available. Please install livekit package.")

        data = kwargs.get("data", {})
        self._logger.info(
            "LiveKit execution - worker will be started via initialize_outbound_call"
        )

    async def manage_call(
        self,
        ctx: JobContext,
        participant: rtc.RemoteParticipant,
        user_state: UserState,
        session: AgentSession,
    ) -> None:
        """Manage call status - based on sip_lifecycle.py"""
        from time import perf_counter

        start_time = perf_counter()
        dialing_timeout_seconds = 45  # Allow up to 45 seconds for call to connect

        self._logger.info("Monitoring call status...")
        self.message_callback(
            f"Call Status:Dialing\n",
            role="system",
            user_state=user_state,
        )

        while perf_counter() - start_time < dialing_timeout_seconds:
            elapsed = perf_counter() - start_time
            call_status = participant.attributes.get("sip.callStatus", "unknown")

            if call_status == "dialing":
                # Log progress every 5 seconds
                if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                    self._logger.debug(f"Still dialing... {int(elapsed)}s elapsed")
                # Only fail if we've been dialing for the full timeout
                # (handled by while loop condition)

            if call_status == "active":
                self._logger.info("Call is active - user picked up")
                self.message_callback(
                    f"Call Status:User has picked up\n",
                    role="system",
                    user_state=user_state,
                )
                # Say first message
                first_message = (
                    user_state.first_message or "Hello! How can I help you today?"
                )
                if "{{name}}" in first_message:
                    first_message = first_message.replace(
                        "{{name}}", user_state.user_name
                    )
                await session.generate_reply(instructions=first_message)
                return

            elif (
                call_status == "hangup"
                or participant.disconnect_reason == rtc.DisconnectReason.USER_REJECTED
            ):
                self._logger.info("Call ended - user rejected")
                self.message_callback(
                    f"Call Status:User rejected the call\n",
                    role="system",
                    user_state=user_state,
                )
                self.message_callback("EOF\n", role="system", user_state=user_state)
                return

            await asyncio.sleep(0.1)

        # Timeout - call didn't connect within timeout
        self._logger.info(
            "SIP Failed - dialing timeout after %ds", dialing_timeout_seconds
        )
        self.message_callback(
            f"Call Status:SIP Failed\n",
            role="system",
            user_state=user_state,
        )
        self.message_callback("EOF\n", role="system", user_state=user_state)

    async def _init_variables(self, user_state: UserState):
        """Initialize variables - same interface as livekit handler"""
        self._logger.info("Initializing variables...")
        if not self.config:
            self.config = user_state.model_config
        self.session_id = str(user_state.thread_id)
        self._room_name = user_state.room_name or f"room-{user_state.thread_id}"

    async def initialize_outbound_call(
        self, data: Dict, user_state: UserState, *args, **kwargs
    ) -> Any:
        """Initialize outbound call using agent dispatch pattern"""
        self.user_state = user_state
        self.data = data

        if not LIVEKIT_AVAILABLE:
            raise Exception("LiveKit is not available. Please install livekit package.")

        await self._init_variables(user_state)

        # Use dispatch pattern instead of direct worker execution
        await self._dispatch_agent(data, user_state)

    async def _dispatch_agent(self, data: Dict, user_state: UserState):
        """Dispatch agent to handle the call - based on space_call.py"""
        try:
            self._logger.info(
                f"Dispatching LiveKit agent for user {user_state.user_name}"
            )

            room_name = self._room_name
            agent_name = (
                self.agent_name
            )  # Use self.agent_name instead of agent_config.agent_name

            # Create LiveKit API client
            lkapi = api.LiveKitAPI()

            # Step 1: Create SIP participant FIRST (initiates the outbound call)
            trunk_id = data.get("trunk_id", os.getenv("SIP_OUTBOUND_TRUNK_ID"))
            phone_number = self._format_phone_number(user_state.contact_number)

            if not phone_number:
                raise ValueError(
                    f"Invalid phone number format: {user_state.contact_number}"
                )

            identity = f"sip_{user_state.thread_id}"

            self._logger.info(
                f"Creating SIP participant BEFORE dispatch: trunk={trunk_id}, phone={phone_number}, room={room_name}"
            )

            # Create SIP participant - this initiates the outbound call
            try:
                await lkapi.sip.create_sip_participant(
                    api.CreateSIPParticipantRequest(
                        sip_trunk_id=trunk_id,
                        sip_call_to=phone_number,
                        room_name=room_name,
                        participant_identity=identity,
                        participant_name=user_state.user_name,
                        krisp_enabled=True,
                    )
                )
                self._logger.info(
                    f"SIP participant created successfully - call initiated to {phone_number}"
                )

            except Exception as e:
                self._logger.error(f"Error creating SIP participant: {e}")
                await lkapi.aclose()
                raise e

            # Step 2: Prepare metadata for the agent
            metadata = {
                "token": user_state.token,
                "contact_name": user_state.user_name,
                "space_name": user_state.space_name,
                "contact_number": user_state.contact_number,
                "language": user_state.language,
                "thread_id": str(user_state.thread_id),
                "user": user_state.user or {},
                "model_config": user_state.model_config,
                "persona": user_state.persona,
                "script": user_state.system_prompt,
                "first_message": user_state.first_message,
                "knowledge_base": user_state.knowledge_base,
                "trunk_id": trunk_id,  # Pass trunk_id in metadata
            }

            # Step 3: Create explicit dispatch (agent will join the room with SIP participant)
            self._logger.info(
                f"Creating dispatch for room: {room_name}, agent: {agent_name}"
            )
            dispatch = await lkapi.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    agent_name=agent_name, room=room_name, metadata=json.dumps(metadata)
                )
            )

            self._logger.info(f"Agent dispatch created: {dispatch}")
            self.message_callback(
                f"Call Status:Outbound call initiated and agent dispatched\n",
                role="system",
                user_state=user_state,
            )

            await lkapi.aclose()

        except Exception as e:
            self._logger.error(f"Error dispatching agent: {e}")
            import traceback

            self._logger.error(traceback.format_exc())
            self.message_callback("EOF\n", role="system", user_state=user_state)
            raise e

    async def _create_pipecat_assistant(self, user_state, ctx: JobContext):
        # provider = os.environ.get("AGENT_PROVIDER", "pipecat")
        # if provider != "pipecat":
        #     return False
        import time

        _start = time.time()
        print(f"[TIMING] _create_pipecat_assistant START")

        from super.core.voice.pipecat.handler import PipecatVoiceHandler

        print(
            f"[TIMING] PipecatVoiceHandler import: {(time.time() - _start) * 1000:.0f}ms"
        )

        from super.core.voice.observers.metrics import (
            CustomMetricObserver,
        )

        print(
            f"[TIMING] CustomMetricObserver import: {(time.time() - _start) * 1000:.0f}ms"
        )

        from super_services.voice.models.config import MessageCallBack

        print(f"[TIMING] MessageCallBack import: {(time.time() - _start) * 1000:.0f}ms")

        try:
            _ctor_start = time.time()
            self.pipecat_agent = PipecatVoiceHandler(
                session_id=user_state.thread_id,
                user_state=user_state,
                callback=MessageCallBack(),
                model_config=user_state.model_config,
                observer=CustomMetricObserver,
            )
            print(
                f"[TIMING] PipecatVoiceHandler constructor: {(time.time() - _ctor_start) * 1000:.0f}ms"
            )

            _preload_start = time.time()
            started = await self.pipecat_agent.preload_agent(
                user_state, CustomMetricObserver
            )
            print(
                f"[TIMING] preload_agent: {(time.time() - _preload_start) * 1000:.0f}ms"
            )

            if started:
                return True
            else:
                return False

        except Exception as e:
            traceback.print_exc()
            print(f"unable to initiate agent {str(e)}")

    async def get_agent_number(self, ctx: JobContext):
        async with api.LiveKitAPI() as lkapi:
            from livekit.api import ListParticipantsRequest

            participants = await lkapi.room.list_participants(
                ListParticipantsRequest(room=ctx.room.name)
            )

        for participant in participants.participants:
            if participant.attributes["sip.trunkPhoneNumber"]:
                return participant.attributes["sip.trunkPhoneNumber"]

        return None

    async def create_task_run(self, pilot_data, user_state):
        from super.core.voice.schema import TaskData
        from super.core.voice.common.services import create_task_and_thread

        # Ensure space_id and user_id are strings (may come as int from SDK)
        space_id = pilot_data.get("space_id")
        user_id = pilot_data.get("user_id")

        task_data = TaskData(
            assignee=pilot_data.get("pilot") or "unknown",
            space_id=str(space_id) if space_id is not None else "",
            user_id=str(user_id) if user_id is not None else "",
            input={
                "name": user_state.user_name,
                "contact_number": user_state.contact_number,
                "token": user_state.token,
                "quality": "good",
            },
            execution_type="call",
        )

        data = await create_task_and_thread(task_data)

        return data

    async def _get_event_cliet(self, ctx: JobContext):
        loop = asyncio.get_event_loop()

        from livekit.rtc._ffi_client import FfiClient

        client = FfiClient.instance.queue.subscribe(loop)

        self._event_client = client

    # Entrypoint for agent worker execution (from sip_lifecycle.py)
    async def entrypoint(self, ctx: JobContext):
        """Entrypoint for LiveKit agent worker - based on sip_lifecycle.py"""
        try:
            await ctx.connect()
            self._logger.info("Connected to LiveKit room")
            self._job_context = ctx
            await self._get_event_cliet(ctx)
            # Parse metadata
            metadata = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
            user_data = metadata.get("data", {})
            model_config = metadata.get("model_config", {})
            pilot_data = None

            self._logger.info(f"Agent Job metadata: {metadata}")

            # Handle SDK calls with agent_handle or space_token at root level
            if not model_config and (
                metadata.get("agent_handle") or metadata.get("space_token")
            ):
                from super.core.voice.common.pilot import (
                    get_pilot_handle_by_space_token,
                )
                from super_services.voice.models.config import ModelConfig

                config_loader = ModelConfig()
                agent_handle = metadata.get("agent_handle")

                # Try agent_handle first
                if agent_handle:
                    self._logger.info(
                        f"Looking up config for agent_handle: {agent_handle}"
                    )
                    model_config = config_loader.get_config(agent_handle)

                # Fallback to space_token if agent_handle not found
                if not model_config:
                    space_token = metadata.get("space_token") or metadata.get("token")
                    if space_token:
                        self._logger.info(
                            f"agent_handle not found, trying space_token: {space_token}"
                        )
                        agent_handle = get_pilot_handle_by_space_token(space_token)
                        if agent_handle:
                            self._logger.info(
                                f"Found pilot handle from space_token: {agent_handle}"
                            )
                            model_config = config_loader.get_config(agent_handle)

                if not model_config:
                    self._logger.error(
                        f"No config found for agent_handle: {metadata.get('agent_handle')} or space_token: {metadata.get('space_token')}"
                    )
                    return

                # Use root-level metadata as user_data for SDK calls
                user_data = {
                    "token": metadata.get("token") or metadata.get("space_token"),
                    "space_name": metadata.get("space_name"),
                    "space_slug": metadata.get("space_slug"),
                    "contact_name": metadata.get("contact_name"),
                    "user": metadata.get("user", {}),
                }
                print(
                    f"{'=' * 50}\nSDK call with agent_handle: {agent_handle}\n{'=' * 50}"
                )

            # Inbound phone call - lookup pilot by phone number
            elif not model_config:
                from super.core.voice.common.pilot import get_pilot_and_space_for_number
                from super_services.voice.models.config import ModelConfig

                agent_number = await self.get_agent_number(ctx)
                pilot_data = await get_pilot_and_space_for_number(agent_number)
                if pilot_data:
                    slug = pilot_data.get("pilot")
                    model_config = ModelConfig().get_config(slug)
                    if not model_config:
                        self._logger.error(f"No config found for pilot: {slug}")
                        return
                    print(
                        f"{'=' * 50}\nInbound call for number: {str(agent_number)} with handle: {model_config.get('agent_id')}\n{'=' * 50}"
                    )
                else:
                    self._logger.error(f"No pilot found for number: {agent_number}")
                    return

            self._logger.info(f"Call data: {metadata}")

            # Reconstruct user_state from metadata
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

            # Create Pipecat assistant if needed
            started = await self._create_pipecat_assistant(user_state, ctx)

            call_type = (
                "outbound" if metadata.get("call_type") == "outbound" else "inbound"
            )

            # Create SIP participant
            if metadata.get("call_type") == "outbound":
                participant = await self._create_sip_participant_in_room(
                    ctx=ctx, data=user_data, user_state=user_state
                )
                user_state.extra_data = {
                    "call_type": "outbound",
                }
            else:
                participant = await ctx.wait_for_participant()
                if pilot_data:
                    from super.core.voice.common.pilot import get_space_token

                    user_state.contact_number = participant.identity.replace(
                        "sip_0", ""
                    )
                    user_state.token = get_space_token(pilot_data.get("space_id"))
                    user_state.user_name = participant.identity

                    task_data = await self.create_task_run(pilot_data, user_state)
                    thread_id = task_data.get("thread_id", "")

                    user_state.thread_id = thread_id
                    user_state.task_id = task_data.get("task_id", "")
                    user_state.extra_data = {"call_type": "inbound", "extra": task_data}

            if participant:
                user_state.participant = participant
                self._logger.info(f"SIP participant created: {participant}")
                agent = LiveKitVoiceAgent(self, user_state, ctx)
                self._agent = agent

                # if participant.kind in [rtc.ParticipantKind.PARTICIPANT_KIND_SIP, rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD] :
                await self._agent.manage_call(
                    ctx, participant, user_state, self.pipecat_agent, call_type
                )
            else:
                self._logger.error("Failed to create SIP participant")
                self.message_callback("EOF\n", role="system", user_state=user_state)

        except Exception as e:
            self._logger.error(f"Error in entrypoint: {e}")
            import traceback

            self._logger.error(traceback.format_exc())
            if hasattr(self, "user_state") and self.user_state is not None:
                self.message_callback(
                    "EOF\n", role="system", user_state=self.user_state
                )
            raise e

    def execute_agent_worker(self):
        """Execute agent worker - based on sip_lifecycle.py"""
        try:
            self._logger.info(
                f"Starting LiveKit agent worker: {self.agent_config.agent_name}"
            )

            # Run the worker using cli.run_app
            cli.run_app(
                WorkerOptions(
                    entrypoint_fnc=self.entrypoint,
                    agent_name=self.agent_config.agent_name,
                )
            )

        except Exception as e:
            self._logger.error(f"Error in agent worker: {e}")
            raise e

    async def _create_sip_participant_in_room(
        self, ctx: JobContext, data: Dict[str, Any], user_state: UserState
    ) -> Optional[rtc.RemoteParticipant]:
        """Create SIP participant inside the room - based on sip_lifecycle.py"""
        try:
            trunk_id = data.get("trunk_id", os.getenv("SIP_OUTBOUND_TRUNK_ID"))
            phone_number = self._format_phone_number(user_state.contact_number)

            room_name = ctx.room.name
            identity = f"idt_{phone_number}"

            self._logger.info(
                f"Creating SIP participant: trunk={trunk_id}, phone={phone_number}, room={room_name}"
            )
            if not phone_number:
                return ctx.wait_for_participant()

            # Create SIP participant using ctx.api
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

            # Wait for participant to connect
            participant = await ctx.wait_for_participant(identity=identity)
            self._logger.info(f"SIP participant connected: {participant.identity}")
            return participant

        except Exception as e:
            self._logger.error(f"Error creating SIP participant: {e}")
            import traceback

            self._logger.error(traceback.format_exc())
            return None

    async def _on_participant_attributes_changed(
        self,
        changed_attributes: dict,
        participant: rtc.Participant,
        user_state: UserState,
        session: AgentSession,
    ):
        """Handle participant attribute changes - based on sip_lifecycle.py"""
        self._logger.info(
            f"Participant {participant.identity} attributes changed: {changed_attributes}"
        )

        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            if "sip.callStatus" in changed_attributes:
                call_status = changed_attributes["sip.callStatus"]
                self._logger.info(f"SIP Call Status updated: {call_status}")

                if call_status == "active":
                    self._logger.info("Call is now active and connected")
                elif call_status == "hangup":
                    self._logger.info("Call has been ended by participant")
                    self.message_callback(
                        f"Call Status:User hung up\n",
                        role="system",
                        user_state=user_state,
                    )
                    self.message_callback("EOF\n", role="system", user_state=user_state)

    def _setup_event_handlers(
        self, session: AgentSession, user_state: UserState, ctx: JobContext
    ):
        """Set up event handlers for metrics and transcripts"""

        @session.on("metrics_collected")
        def _on_metrics_collected(ev: MetricsCollectedEvent):
            if not hasattr(user_state, "usage"):
                user_state.usage = metrics.UsageCollector()
            user_state.usage.collect(ev.metrics)
            metrics.log_metrics(ev.metrics)

        @session.on("agent_state_changed")
        def agent_state_changed(state: AgentStateChangedEvent):
            self._logger.info(f"Agent state changed: {state.new_state}")

            if state.new_state == "speaking":

                @session.on("conversation_item_added")
                def conversation(msg: ConversationItemAddedEvent):
                    if msg.item.role == "assistant":
                        agent_text = msg.item.content[0] if msg.item.content else ""
                        if agent_text:
                            transcript_entry = {
                                "role": "assistant",
                                "content": agent_text,
                                "timestamp": str(datetime.now()),
                            }
                            user_state.transcript.append(transcript_entry)
                            self.message_callback(
                                agent_text, role="system", user_state=user_state
                            )

        @session.on("user_input_transcribed")
        def on_user_input_transcribed(ev: UserInputTranscribedEvent):
            if ev.is_final:
                transcript_text = ev.transcript
                if transcript_text:
                    transcript_entry = {
                        "role": "user",
                        "content": transcript_text,
                        "timestamp": str(datetime.now()),
                    }
                    user_state.transcript.append(transcript_entry)
                    self.message_callback(
                        transcript_text, role="user", user_state=user_state
                    )

        @ctx.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            self._logger.info(f"Participant disconnected: {participant.identity}")
            self.message_callback(
                f"Call Status:User Left the call\n",
                role="system",
                user_state=user_state,
            )
            self.message_callback("EOF\n", role="system", user_state=user_state)

        @ctx.room.on("connection_state_changed")
        def on_connection_state_changed(state):
            self._logger.info(f"Room connection state changed: {state}")
            # state: 0=DISCONNECTED, 1=CONNECTED, 2=RECONNECTING
            if state == 0:  # DISCONNECTED
                self._logger.warning(
                    "Room disconnected - waiting for reconnection attempt"
                )

        @ctx.room.on("reconnecting")
        def on_reconnecting():
            self._logger.warning(
                "Room reconnecting... agent will resume when connected"
            )

        @ctx.room.on("reconnected")
        def on_reconnected():
            self._logger.info("Room reconnected - agent resumed")

    def _format_phone_number(self, phone_number: str) -> Optional[str]:
        """Format and validate phone number for SIP calling - same as livekit handler"""
        if not phone_number:
            return None

        # Remove any non-digit characters except + at the beginning
        cleaned = "".join(
            c
            for c in phone_number
            if c.isdigit() or (c == "+" and phone_number.index(c) == 0)
        )

        # If no + at start, assume it needs country code
        if not cleaned.startswith("+"):
            if len(cleaned) == 10:
                cleaned = "+91" + cleaned
            elif len(cleaned) >= 7:
                default_country_code = os.getenv("DEFAULT_COUNTRY_CODE", "+91")
                cleaned = default_country_code + cleaned

        # Validate minimum and maximum length
        if len(cleaned) < 8 or len(cleaned) > 16:
            self._logger.warning(f"Phone number length invalid: {cleaned}")
            return None

        return cleaned

    def _find_trunk_for_outbound(self, number: str) -> Optional[str]:
        """Find appropriate trunk for outbound call - same as livekit handler"""
        return os.getenv("SIP_OUTBOUND_TRUNK_ID")

    def create_usage(self, user_state: UserState) -> dict:
        """Create serializable usage data from user_state - same interface as livekit handler"""
        usage_data = {}

        if (
            hasattr(user_state, "usage")
            and user_state.usage
            and hasattr(user_state.usage, "get_summary")
        ):
            summary = user_state.usage.get_summary()
            usage_data = {
                "llm_prompt_tokens": getattr(summary, "llm_prompt_tokens", 0),
                "llm_completion_tokens": getattr(summary, "llm_completion_tokens", 0),
                "tts_characters_count": getattr(summary, "tts_characters_count", 0),
                "stt_audio_duration": getattr(summary, "stt_audio_duration", 0),
            }

        # Calculate call duration in seconds (serializable)
        if user_state.start_time and user_state.end_time:
            duration_seconds = (
                user_state.end_time - user_state.start_time
            ).total_seconds()
            usage_data["call_duration_seconds"] = duration_seconds

        return usage_data

    def dump(self) -> dict:
        role_config = self._configuration.role
        dump = {
            "id": role_config.id,
            "name": role_config.name,
            "role": role_config.role,
        }
        return dump

    def dump_user(self) -> User:
        """Dump user info for callbacks"""
        dump = self.dump()
        return User.add_user(
            name=dump["name"],
            role=Role.ASSISTANT,
            _id=dump["id"],
            data=dump,
        )

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self._configuration.__str__()

    def name(self) -> str:
        """The name of the ability."""
        return self._configuration.role.id

    def execute_agent(self):
        """Execute agent worker - synchronous wrapper for cli.run_app"""
        try:
            outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
            if not outbound_trunk_id or not outbound_trunk_id.startswith("ST_"):
                raise ValueError(
                    "SIP_OUTBOUND_TRUNK_ID is not set. Please follow the guide at https://docs.livekit.io/agents/quickstarts/outbound-calls/ to set it up."
                )

            self._logger.info(f"Starting LiveKit agent worker: {self.agent_name}")

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
                pass

        except Exception as e:
            self._logger.error(f"Error in execute_agent: {e}")
            raise e

"""
LiveKit Lite Voice Handler - Plugin-based voice processing using LiveKit agents SDK.

A lightweight handler for LiveKit native voice pipelines with plugin architecture.
Similar to LiteVoiceHandler but uses LiveKit's AgentSession instead of Pipecat pipelines.

Key features:
- LiveKit native AgentSession (not Pipecat)
- Support for inference, realtime, and standard modes
- Plugin system for optional features (transcript, filler responses)
- Same event interface as LiteVoiceHandler for compatibility
"""

import asyncio
import json
import logging
import os
import time
import uuid
from abc import ABC
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Optional

from pydantic import Field
from dotenv import load_dotenv

from super.core.callback.base import BaseCallback
from super.core.configuration import BaseModelConfig
from super.core.context.schema import Event, Message, Role, User
from super.core.handler.config import (
    ExecutionNature,
    HandlerConfiguration,
    RoleConfiguration,
)
from super.core.logging import logging as app_logging
from super.core.plugin.base import PluginLocation, PluginStorageFormat
from super.core.voice.base import BaseVoiceHandler
from super.core.voice.plugins import PluginRegistry
from super.core.voice.managers.prompt_manager import PromptManager
from super.core.voice.schema import AgentConfig, CallSession, UserState, Modality

# Conversation Intelligence imports
try:
    from super.core.voice.livekit.conversation_state import DynamicConversationState
    CONVERSATION_INTELLIGENCE_AVAILABLE = True
except ImportError:
    CONVERSATION_INTELLIGENCE_AVAILABLE = False
    DynamicConversationState = None

# Import LiveKitLiteAgent from dedicated module
from super.core.voice.livekit.livekit_lite_agent import LiveKitLiteAgent

from super.core.voice.services.livekit_services import (
    LiveKitServiceFactory,
    BackgroundAudioPlayer,
    # LiveKitServiceMode,
)
from super.core.voice.services import livekit_services
from super.core.voice.common.services import save_execution_log

from super.core.voice.schema import CallStatusEnum
from super.core.voice.common.common import add_perf_log
from time import perf_counter
from super.core.voice.common.common import build_call_result
from super.core.voice.common.prefect import trigger_post_call

if TYPE_CHECKING:
    from livekit.agents import JobContext, llm
    from livekit.agents.voice import AgentSession

load_dotenv(override=True)
from livekit.agents import ChatContext, ChatMessage
from super_services.db.services.models.task import TaskModel

# from super.core.voice.managers.knowledge_base import KnowledgeBaseManager

# Check LiveKit availability
try:
    from livekit import rtc
    from livekit.agents import JobContext, MetricsCollectedEvent
    from livekit.agents.voice import (
        Agent,
        AgentSession,
        RunContext,
        ConversationItemAddedEvent,
        UserInputTranscribedEvent,
        AgentStateChangedEvent,
    )
    from livekit.agents import llm, stt
    from livekit.agents.llm import function_tool

    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False
    JobContext = Any
    AgentSession = Any
    stt = Any

# LiveKit data channel topic constants
TOPIC_LK_CHAT = "lk.chat"  # Main chat topic for responses
TOPIC_LK_STREAM = "lk.stream"  # Streaming chunks topic


class LiveKitLiteHandler(BaseVoiceHandler, ABC):
    """
    Lightweight LiveKit voice handler with plugin architecture.

    Uses LiveKit's native AgentSession for voice processing while maintaining
    compatibility with the plugin system and event interface from LiteVoiceHandler.

    Supports three modes:
    - inference: String-based service references for LiveKit Cloud
    - realtime: Native realtime models (OpenAI/Gemini)
    - standard: Separate STT/LLM/TTS service objects
    """

    default_configuration = HandlerConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.voice.livekit_lite_handler.LiveKitLiteHandler",
        ),
        role=RoleConfiguration(
            name="livekit_lite_handler",
            role="A lightweight handler for LiveKit voice conversations.",
            cycle_count=0,
            max_task_cycle_count=3,
        ),
        execution_nature=ExecutionNature.AUTO,
    )

    def __init__(
        self,
        session_id: Optional[str] = None,
        user_state: Optional[UserState] = None,
        callback: Optional[BaseCallback] = None,
        model_config: Optional[BaseModelConfig] = None,
        configuration: HandlerConfiguration = default_configuration,
        observer: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(
            session_id=session_id,
            callback=callback,
            configuration=configuration,
            logger=logger or app_logging.get_logger("livekit.lite.handler"),
        )

        self._session_id = session_id or (
            str(user_state.thread_id) if user_state else None
        )
        self._callback = callback
        self._logger = logger or app_logging.get_logger("livekit.lite.handler")
        self._configuration = configuration

        # User state and config - ensure config is never None
        self.user_state = user_state
        self.config = (
            model_config or (user_state.model_config if user_state else None) or {}
        )

        # Log config for STT/TTS debugging
        self._logger.info(
            f"[LITE_HANDLER_INIT] Config received - "
            f"stt_provider={self.config.get('stt_provider') if isinstance(self.config, dict) else 'N/A'}, "
            f"stt_model={self.config.get('stt_model') if isinstance(self.config, dict) else 'N/A'}, "
            f"tts_provider={self.config.get('tts_provider') if isinstance(self.config, dict) else 'N/A'}, "
            f"tts_model={self.config.get('tts_model') if isinstance(self.config, dict) else 'N/A'}"
        )

        # Observer for metrics
        self.observer = observer

        # Room name
        self._room_name: Optional[str] = None

        # Agent config
        self.agent_config = AgentConfig(
            agent_name=session_id or "LiveKitLiteAgent",
            model_config=model_config,
        )

        # Plugin registry
        self.plugins = PluginRegistry(logger=self._logger.getChild("plugins"))

        # Service factory (lazy initialized)
        self._service_factory: Optional[LiveKitServiceFactory] = None

        # Prompt manager (lazy initialized)
        self._prompt_manager: Optional[PromptManager] = None

        # LiveKit session and agent
        self._session: Optional[AgentSession] = None
        self._agent: Optional[LiveKitLiteAgent] = None

        # Active sessions tracking
        self.active_sessions: Dict[str, CallSession] = {}

        # RAG processor configuration
        # Enables synchronous context enrichment before LLM (reduces latency by 500-2000ms)
        self.use_rag_processor = self.config.get(
            "use_rag_processor",
            os.getenv("USE_RAG_PROCESSOR", "false").lower() == "true",
        )

        # State flags
        self._is_shutting_down = False
        self._services_initialized = False
        self._first_response_sent = asyncio.Event()
        self._kb_ready = asyncio.Event()

        # Realtime mode detection
        # In full realtime mode, TTS is not available - realtime LLM handles audio natively
        self._is_realtime_mode = self.config.get("llm_realtime", False)
        self._mixed_realtime_mode = self.config.get("mixed_realtime_mode", False)
        # Full realtime = realtime mode without mixed mode (no TTS available)
        self._is_full_realtime = self._is_realtime_mode and not self._mixed_realtime_mode

        # Agent/user references for callbacks
        self.agent: Optional[User] = None

        # Event bridge for transcript publishing and state management
        self._event_bridge: Optional[Any] = None

        # LiveKit job context (set during execute_with_context)
        self._job_context: Optional[Any] = None

        # Background audio player (initialized during execute_with_context)
        self._background_audio: Optional[Any] = None

        # Multi-participant STT tracking
        self._participant_stt_tasks: Dict[str, asyncio.Task] = {}
        self._participant_stt_streams: Dict[str, Any] = {}

        # Idle timeout configuration (seconds)
        self._idle_timeout_seconds: float = float(
            self.config.get("idle_timeout_seconds", 30.0)
            if isinstance(self.config, dict)
            else 30.0
        )
        self._idle_warning_1_seconds: float = self._idle_timeout_seconds * 0.5  # 15s
        self._idle_warning_2_seconds: float = self._idle_timeout_seconds * 0.83  # 25s
        self._last_activity_time: float = time.time()
        self._idle_warning_count: int = 0
        self._idle_monitor_task: Optional[asyncio.Task] = None
        self._idle_monitor_running: bool = False
        self._sending_idle_warning: bool = False
        self._agent_state: str = "listening"

        self._logger.info(f"LiveKitLiteHandler created (session={self._session_id})")

    @property
    def prompt_manager(self) -> PromptManager:
        """Lazy-initialized prompt manager."""
        if self._prompt_manager is None:
            self._prompt_manager = PromptManager(
                config=self.config or {},
                agent_config=self.agent_config,
                session_id=self._session_id,
                tool_calling=self.config.get("tool_calling", True),
                logger=self._logger.getChild("prompt"),
            )
            if self.user_state:
                self._prompt_manager.user_state = self.user_state
        return self._prompt_manager

    @property
    def service_factory(self) -> LiveKitServiceFactory:
        """Lazy-initialized service factory."""
        if self._service_factory is None:
            self._service_factory = LiveKitServiceFactory(
                config=self.config,
                logger=self._logger.getChild("services"),
            )
        return self._service_factory

    @property
    def use_conversation_intelligence(self) -> bool:
        """
        Check if dynamic conversation intelligence is enabled.

        Uses the 4-phase model: greeting -> presenting -> reflecting -> closing
        Enabled via config: use_conversation_intelligence: true
        Requires CONVERSATION_INTELLIGENCE_AVAILABLE to be True.
        """
        if not CONVERSATION_INTELLIGENCE_AVAILABLE:
            return False
        return self.config.get("use_conversation_intelligence", True)

    def _add_users(self) -> None:
        """Create agent and user references."""
        import uuid

        self.agent = User.add_user(
            name=self.config.get("agent_id", ""),
            role=Role.ASSISTANT,
        )

        if self.user_state:
            # Extract user_id from dict, handling both 'id' and 'user_id' keys
            # and converting to string since the value may be an int
            user_id = str(uuid.uuid4())
            if isinstance(self.user_state.user, dict):
                raw_id = self.user_state.user.get(
                    "id", self.user_state.user.get("user_id")
                )
                if raw_id is not None:
                    user_id = str(raw_id)

            self.user_state.user = User.add_user(
                name=self.user_state.user_name,
                role=Role.USER,
                _id=user_id,
            )

    async def preload_agent(
        self,
        user_state: UserState,
        observer: Optional[Any] = None,
    ) -> bool:
        """
        Minimal preload - only essential initialization.

        Target: <200ms startup time.

        Args:
            user_state: User state for the session
            observer: Optional observer for metrics

        Returns:
            True if preload successful
        """
        preload_start = perf_counter()
        self._logger.info("Starting LiveKit lite preload...")

        try:
            # Update state
            self.user_state = user_state
            self.config = user_state.model_config or self.config
            self._room_name = user_state.room_name
            self.observer = observer

            # Create users
            users_start = perf_counter()
            self._add_users()
            add_perf_log(
                user_state,
                "lk_lite_add_users",
                (perf_counter() - users_start) * 1000,
            )

            # Activate plugins from config (filler, transcript, etc.)
            plugins_start = perf_counter()
            await self.plugins.activate_from_config(self, self.config)
            add_perf_log(
                user_state,
                "lk_lite_plugins_activation",
                (perf_counter() - plugins_start) * 1000,
            )

            # Start background KB warmup (non-blocking)
            # With preloaded embeddings from ServiceCache, KB init is fast (~50-100ms)
            # so we start immediately instead of waiting for first response
            if self.use_rag_processor and self._kb_enabled():
                asyncio.create_task(
                    self._background_kb_warmup(immediate=True),
                    name=f"{self._session_id}-kb-warmup",
                )

            self._services_initialized = True
            elapsed = (perf_counter() - preload_start) * 1000
            add_perf_log(user_state, "lk_lite_preload_total", elapsed)
            self._logger.info(f"LiveKit lite preload complete in {elapsed:.0f}ms")
            return True

        except Exception as e:
            self._logger.error(f"Preload failed: {e}")
            return False

    def _kb_enabled(self) -> bool:
        """Check if knowledge base is configured."""
        if not self.config:
            return False
        return bool(self.config.get("knowledge_base"))

    async def _background_kb_warmup(self, immediate: bool = True) -> None:
        """
        Warm up KB in background.

        With preloaded embeddings from ServiceCache, KB init is now fast (~50-100ms)
        so we can start immediately instead of waiting for first response.

        Args:
            immediate: If True, start KB warmup immediately without waiting
                      for first response. Default: False for backward compat.
        """
        try:
            if not immediate:
                # Legacy behavior: wait for first response
                await asyncio.wait_for(
                    self._first_response_sent.wait(),
                    timeout=30.0,
                )
                await asyncio.sleep(0.5)

            if self._kb_enabled():
                _start = asyncio.get_event_loop().time()

                from super.core.voice.managers.knowledge_base import (
                    KnowledgeBaseManager,
                )

                kb_manager = KnowledgeBaseManager(
                    logger=self._logger.getChild("kb"),
                    session_id=self._session_id,
                    user_state=self.user_state,
                    config=self.config,
                )

                # Initialize index (uses preloaded embeddings from ServiceCache)
                await kb_manager._init_context_retrieval()

                # Preload documents from remote service (if configured)
                await kb_manager._preload_knowledge_base_documents(self.user_state)

                self._kb_manager = kb_manager
                self._kb_ready.set()

                elapsed_ms = (asyncio.get_event_loop().time() - _start) * 1000
                self._logger.info(
                    f"Background KB warmup complete in {elapsed_ms:.0f}ms "
                    f"(immediate={immediate})"
                )

        except asyncio.TimeoutError:
            self._logger.warning("KB warmup timeout - first response not sent")
            self._kb_ready.set()
        except Exception as e:
            self._logger.warning(f"KB warmup failed: {e}")
            self._kb_ready.set()

    async def create_agent_session(
        self,
        ctx: JobContext,
        userdata: Optional[Dict[str, Any]] = None,
    ) -> AgentSession:
        """
        Create AgentSession using the service factory.

        Supports two modalities:
        - text_audio (default): Full voice mode with STT/TTS
        - text: Text-only hybrid mode without STT/TTS

        Args:
            ctx: LiveKit job context
            userdata: Optional userdata to attach to session

        Returns:
            Configured AgentSession
        """
        userdata = userdata or {}

        # Use dict userdata for session
        userdata.update(
            {
                "token": self.user_state.token,
                "knowledge_base": self.user_state.knowledge_base,
                "ctx_room": ctx.room,
            }
        )
        # Check modality from user_state
        # Compare as strings since modality can be str or Modality enum
        modality = getattr(self.user_state, "modality", Modality.TEXT_AUDIO)
        modality_str = str(modality) if modality else "text_audio"

        self._logger.info(f"[MODALITY] User state modality: {modality_str}")

        if modality_str == "text" or modality == Modality.TEXT:
            self._logger.info("[MODALITY] Creating TEXT-ONLY session (no STT/TTS)")
            return await self.service_factory.create_text_session(userdata=userdata)

        # Default: full voice mode with STT/TTS
        self._logger.info("[MODALITY] Creating TEXT_AUDIO session (full voice)")

        return await self.service_factory.create_session(
            userdata=userdata, user_state=self.user_state
        )

    async def _persist_session_quality_metrics(self, reason: str = "session_end") -> None:
        """
        Persist quality metrics and call summary from DynamicConversationState when session ends.

        This ensures metrics are captured regardless of how the session ends
        (user hangup, room disconnect, error, etc.), not just when the
        end_call tool is explicitly invoked.

        Args:
            reason: Why the session is ending (e.g., "session_disconnect", "error")
        """
        try:
            # Only applies to stage-based conversation mode
            if not self.use_conversation_intelligence:
                return

            # Get agent's conversation state
            agent = getattr(self, "_agent", None)
            if not agent:
                self._logger.debug("No agent available for quality metrics persistence")
                return

            conv_state = getattr(agent, "_conv_state", None)
            if not conv_state:
                self._logger.debug("No DynamicConversationState found in agent")
                return

            # Update conv_state with actual metadata values (may have been empty at init time)
            # These values are now definitely available at call-end time
            if self.user_state:
                conv_state.task_id = getattr(self.user_state, "task_id", "") or ""
            conv_state.session_id = self._session_id or ""
            conv_state.agent_handle = self.config.get("agent_name", "") or ""
            self._logger.info(
                f"[SESSION_END] Metadata updated: task_id={conv_state.task_id}, "
                f"session_id={conv_state.session_id}, agent={conv_state.agent_handle}"
            )

            # Log quality summary
            self._logger.info(conv_state.get_quality_log_line())

            # Get metrics for detailed logging
            metrics = conv_state.get_quality_metrics()
            progress = metrics.get("content_progress", {})
            self._logger.info(
                f"[SESSION_END] reason={reason} | "
                f"phase={metrics.get('current_phase', 'unknown')} | "
                f"content={progress.get('delivered', 0)}/{progress.get('total', 0)} | "
                f"objective={'achieved' if metrics.get('objective_achieved') else metrics.get('objective_outcome', 'pending')} | "
                f"score={metrics['scores']['overall']}"
            )

            # Build and log call summary dashboard
            call_summary_text = conv_state.build_call_summary(end_reason=reason)
            self._logger.info(f"\n{call_summary_text}")

            # Get call summary as dictionary for database storage
            call_summary_dict = conv_state.get_call_summary_dict(end_reason=reason)

            # Add quality metrics and call summary to user_state.extra_data for post-call analytics
            if self.user_state:
                if not isinstance(self.user_state.extra_data, dict):
                    self.user_state.extra_data = {}
                self.user_state.extra_data["quality_metrics"] = metrics
                self.user_state.extra_data["conversation_state"] = conv_state.to_dict()
                self.user_state.extra_data["call_summary"] = call_summary_dict
                self._logger.debug("Quality metrics and call summary added to user_state.extra_data")

            # Save call summary to database using TaskModel
            task_id = self.user_state.task_id if self.user_state else None
            if task_id:
                # 1. Save to TaskExecutionLog for audit trail
                await save_execution_log(
                    task_id=task_id,
                    step="call_summary",
                    status="completed",
                    output=call_summary_dict,
                )
                self._logger.info(f"[CALL_SUMMARY] Saved to execution log | task_id={task_id}")

                # 2. Update TaskModel.output with call summary for quick access
                try:
                    TaskModel.update_one(
                        {"task_id": task_id},
                        {"$set": {"output.call_summary": call_summary_dict}},
                    )
                    self._logger.info(f"[CALL_SUMMARY] Updated task output | task_id={task_id}")
                except Exception as db_error:
                    self._logger.error(f"[CALL_SUMMARY] Failed to update task: {db_error}")
            else:
                self._logger.warning("[CALL_SUMMARY] No task_id available, skipping DB storage")

            # Persist to JSONL file
            filepath = conv_state.persist_quality_metrics(reason=reason)
            if filepath:
                self._logger.info(f"Quality metrics persisted to: {filepath}")
            else:
                self._logger.warning("Failed to persist quality metrics")

        except Exception as e:
            self._logger.error(f"Error persisting session quality metrics: {e}")

    async def _record_agent_response_for_quality(self, content: str) -> None:
        """
        Record agent response for quality metrics anti-pattern detection.

        This captures agent responses for detecting:
        - Question-only turns (ending with just a question)
        - Clarification requests (excessive clarification)
        - Content repetition (saying the same thing twice)

        Args:
            content: The agent's response text
        """
        try:
            agent = getattr(self, "_agent", None)
            if not agent:
                return

            conv_state = getattr(agent, "_conv_state", None)
            if not conv_state:
                return

            # Record the response and get anti-pattern detection result
            result = conv_state.record_agent_response(
                response_text=content,
                phase="conversation",  # Simplified - no phase tracking
                turn=conv_state.turn_count,
            )

            # Log any detected issues
            issues = result.get("issues", [])
            if issues:
                self._logger.warning(
                    f"[QUALITY_ANTIPATTERN] turn={conv_state.turn_count} "
                    f"repair={conv_state.in_repair} issues={issues}"
                )

        except Exception as e:
            self._logger.debug(f"Error recording agent response for quality: {e}")

    def create_agent(self, ctx) -> "Agent":
        """Create the LiveKit agent (state built internally by agent)."""
        instructions = self.prompt_manager._create_assistant_prompt()

        agent = LiveKitLiteAgent(
            handler=self,
            user_state=self.user_state,
            instructions=instructions,
            ctx=ctx,
            config=self.config,
        )

        # Log registered tools for debugging
        try:
            if hasattr(agent, "_tools") and agent._tools:
                tool_names = [getattr(t, "name", str(t)) for t in agent._tools]
                self._logger.info(
                    f"[TOOLS] Registered tools ({len(agent._tools)}): {tool_names}"
                )
            else:
                self._logger.warning("[TOOLS] No tools found in agent._tools!")
        except Exception as e:
            self._logger.error(f"[TOOLS] Could not list tools: {e}")

        return agent

    async def _start_participant_transcription(
        self,
        participant: "rtc.RemoteParticipant",
        room: "rtc.Room",
    ) -> None:
        """
        Start transcribing a participant's audio for logging purposes.

        This captures transcripts from all participants (e.g., after handover)
        so their conversation can be saved, without the agent responding.
        """
        participant_identity = participant.identity

        # Skip if already tracking this participant
        if participant_identity in self._participant_stt_tasks:
            self._logger.debug(
                f"Already transcribing participant: {participant_identity}"
            )
            return

        # Skip the local participant (agent)
        if participant_identity == room.local_participant.identity:
            return

        self._logger.info(
            f"Starting transcription for participant: {participant_identity}"
        )

        async def _transcribe_participant():
            """Transcribe a participant's audio stream."""
            try:
                self._logger.info(
                    f"[STT] Creating STT instance for {participant_identity}"
                )
                # Create STT instance
                stt_instance = self.service_factory.create_stt()
                if not stt_instance:
                    self._logger.warning(
                        f"[STT] Failed to create STT for {participant_identity}"
                    )
                    return

                self._logger.info(
                    f"[STT] STT instance created for {participant_identity}: {type(stt_instance)}"
                )

                # Check if STT supports streaming, if not wrap with StreamAdapter
                if not stt_instance.capabilities.streaming:
                    self._logger.info(
                        f"[STT] STT does not support streaming, wrapping with StreamAdapter for {participant_identity}"
                    )
                    try:
                        from livekit.plugins.silero import VAD

                        vad = VAD.load()
                        stt_instance = stt.StreamAdapter(stt=stt_instance, vad=vad)
                        self._logger.info(
                            f"[STT] StreamAdapter created successfully for {participant_identity}"
                        )
                    except Exception as e:
                        self._logger.error(
                            f"[STT] Failed to create StreamAdapter, falling back to Deepgram: {e}"
                        )
                        # Fallback to Deepgram which supports streaming natively
                        try:
                            from livekit.plugins import deepgram

                            stt_instance = deepgram.STT(
                                model="nova-3", language="multi"
                            )
                            self._logger.info(
                                f"[STT] Using Deepgram STT fallback for {participant_identity}"
                            )
                        except Exception as fallback_error:
                            self._logger.error(
                                f"[STT] Deepgram fallback also failed: {fallback_error}"
                            )
                            return

                # Find audio track - check for any audio track, not just SOURCE_MICROPHONE
                # SIP participants may have audio tracks with different source types
                audio_track = None
                self._logger.info(
                    f"[STT] Looking for audio track. Publications: {list(participant.track_publications.keys())}"
                )
                for pub in participant.track_publications.values():
                    self._logger.debug(
                        f"[STT] Checking publication: source={pub.source}, track={pub.track}, kind={pub.kind if hasattr(pub, 'kind') else 'N/A'}"
                    )
                    # Accept audio tracks from microphone or unknown source (SIP participants)
                    if pub.track and pub.source in (
                        rtc.TrackSource.SOURCE_MICROPHONE,
                        rtc.TrackSource.SOURCE_UNKNOWN,
                    ):
                        audio_track = pub.track
                        self._logger.info(
                            f"[STT] Found audio track for {participant_identity} (source={pub.source})"
                        )
                        break

                if not audio_track:
                    self._logger.info(
                        f"[STT] No audio track yet for {participant_identity}, waiting for track_subscribed..."
                    )
                    # Wait for track
                    track_ready = asyncio.Event()

                    def on_track_subscribed(track, publication, p):
                        nonlocal audio_track
                        self._logger.debug(
                            f"[STT] track_subscribed event: participant={p.identity}, source={publication.source}"
                        )
                        # Accept audio tracks from microphone or unknown source (SIP participants)
                        if (
                            p.identity == participant_identity
                            and publication.source
                            in (
                                rtc.TrackSource.SOURCE_MICROPHONE,
                                rtc.TrackSource.SOURCE_UNKNOWN,
                            )
                        ):
                            audio_track = track
                            self._logger.info(
                                f"[STT] Audio track received for {participant_identity} (source={publication.source})"
                            )
                            track_ready.set()

                    room.on("track_subscribed", on_track_subscribed)
                    try:
                        await asyncio.wait_for(track_ready.wait(), timeout=30.0)
                    except asyncio.TimeoutError:
                        self._logger.warning(
                            f"[STT] Timeout waiting for audio from {participant_identity}"
                        )
                        return
                    finally:
                        room.off("track_subscribed", on_track_subscribed)

                if not audio_track:
                    self._logger.warning(
                        f"[STT] No audio track available for {participant_identity}"
                    )
                    return

                self._logger.info(
                    f"[STT] Starting audio stream transcription for: {participant_identity}"
                )

                audio_stream = rtc.AudioStream(audio_track)
                stt_stream = stt_instance.stream()
                self._participant_stt_streams[participant_identity] = stt_stream

                async def forward_audio():
                    frame_count = 0
                    async for event in audio_stream:
                        if hasattr(event, "frame"):
                            stt_stream.push_frame(event.frame)
                            frame_count += 1
                            if frame_count % 100 == 0:
                                self._logger.debug(
                                    f"[STT] Forwarded {frame_count} audio frames for {participant_identity}"
                                )

                async def process_transcripts():
                    async for event in stt_stream:
                        if event.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                            transcript = (
                                event.alternatives[0].text if event.alternatives else ""
                            )
                            if transcript.strip():
                                self._logger.info(
                                    f"[TRANSCRIPT] [{participant_identity}]: {transcript}"
                                )
                                self.user_state.transcript.append(
                                    {
                                        "role": "user",
                                        "content": transcript,
                                        "timestamp": str(datetime.now()),
                                        "participant": participant_identity,
                                    }
                                )

                                await self.plugins.broadcast_event(
                                    f"user_speaking_{participant_identity}", transcript
                                )
                        elif event.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
                            transcript = (
                                event.alternatives[0].text if event.alternatives else ""
                            )
                            if transcript.strip():
                                self._logger.debug(
                                    f"[STT] [{participant_identity}] interim: {transcript}"
                                )

                self._logger.info(
                    f"[STT] Starting forward_audio and process_transcripts for {participant_identity}"
                )
                await asyncio.gather(forward_audio(), process_transcripts())

            except asyncio.CancelledError:
                self._logger.info(
                    f"[STT] Transcription stopped for {participant_identity}"
                )
            except Exception as e:
                import traceback

                self._logger.error(
                    f"[STT] Transcription error for {participant_identity}: {e}\n{traceback.format_exc()}"
                )
            finally:
                if participant_identity in self._participant_stt_streams:
                    stream = self._participant_stt_streams.pop(participant_identity)
                    if hasattr(stream, "aclose"):
                        await stream.aclose()

        task = asyncio.create_task(_transcribe_participant())
        self._participant_stt_tasks[participant_identity] = task

    async def _stop_participant_transcription(self, participant_identity: str) -> None:
        """Stop transcription when a participant disconnects."""
        if participant_identity in self._participant_stt_tasks:
            self._logger.info(f"Stopping transcription for: {participant_identity}")
            task = self._participant_stt_tasks.pop(participant_identity)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def _setup_session_events(self, session: AgentSession) -> None:
        """Set up event handlers for the session."""

        # Define async handlers
        async def _handle_user_input(event: UserInputTranscribedEvent):
            """Handle user transcription."""
            # Skip processing if shutting down
            if self._is_shutting_down:
                return

            content = event.transcript
            if not content:
                return

            if not event.is_final:
                 return

            # Reset idle timer on user activity
            self._reset_idle_timer()

            # Note: Goodbye detection is now handled by the end_call tool
            # The LLM decides when to end the call based on conversation context

            self.user_state.transcript.append(
                {
                    "role": "user",
                    "content": content,
                    "timestamp": str(datetime.now()),
                    "participant": self.user_state.extra_data.get("identity"),
                }
            )

            # Ensure user is a User object (defensive check)
            user = self.user_state.user
            if isinstance(user, dict):
                import uuid
                raw_id = user.get("id", user.get("user_id"))
                user_id = str(raw_id) if raw_id is not None else str(uuid.uuid4())
                user = User.add_user(
                    name=self.user_state.user_name,
                    role=Role.USER,
                    _id=user_id,
                )
                self.user_state.user = user

            # Send callback
            msg = Message.create(
                content,
                user=user,
                event=Event.USER_MESSAGE,
            )
            self._send_callback(msg, thread_id=str(self.user_state.thread_id))

            # Notify plugins
            await self.plugins.broadcast_event("on_user_speech", content)

        async def _handle_conversation_item(event: ConversationItemAddedEvent):
            """Handle conversation items in voice mode.

            Handles both user and assistant messages:
            - User messages: Reset idle timer, check goodbye intent (for inference mode)
            - Assistant messages: Send parallel text response via data channel

            In VOICE_TEXT mode, this sends parallel text/data response via the
            data channel in the same format as TEXT mode for consistency:
            - StreamBlock: {event: "stream", id, pilot, data: {content, chunk_index, is_final}}
            - ResponseBlock: {event: "block_response", id, pilot, execution_type, data: {...}}
            """
            # Skip processing if shutting down
            if self._is_shutting_down:
                return

            item = event.item

            # Extract text content from ChatMessage.content (list of str|ImageContent|AudioContent)
            content = ""
            if hasattr(item, "content") and item.content:
                text_parts = [c for c in item.content if isinstance(c, str)]
                content = " ".join(text_parts)
            if not content:
                return

            # Handle user conversation items (captures user speech in inference mode)
            if item.role == "user":
                self._logger.info(
                    f"[CONVERSATION_ITEM] User message captured: "
                    f"thread_id={self.user_state.thread_id}, content_len={len(content)}"
                )

                # Reset idle timer on user activity
                self._reset_idle_timer()

                # Note: Goodbye detection is now handled by the end_call tool
                # The LLM decides when to end the call based on conversation context

                # Store transcript
                # self.user_state.transcript.append(
                #     {
                #         "role": "user",
                #         "content": content,
                #         "timestamp": str(datetime.now()),
                #     }
                # )

                # Send callback for user message
                msg = Message.create(
                    content,
                    user=self.user_state.user,
                    event=Event.USER_MESSAGE,
                )
                self._send_callback(msg, thread_id=str(self.user_state.thread_id))

                # Notify plugins
                await self.plugins.broadcast_event("on_user_speech", content)
                return

            # Handle assistant conversation items
            if item.role == "assistant":
                # Reset idle timer - agent responding counts as activity
                # Skip reset during idle warnings to allow escalation
                if not self._sending_idle_warning:
                    self._reset_idle_timer()

                # Record agent response for anti-pattern detection (Gap #2 fix)
                if self.use_conversation_intelligence and session.userdata:
                    try:
                        userdata = session.userdata
                        if hasattr(userdata, 'record_agent_response'):
                            result = userdata.record_agent_response(
                                response_text=content,
                                stage=userdata.current_stage,
                                turn=userdata.turn_count,
                            )
                            if result.get("issues"):
                                self._logger.warning(
                                    f"[ANTI_PATTERN] Detected: {result['issues']} "
                                    f"in stage={userdata.current_stage}, turn={userdata.turn_count}"
                                )
                    except Exception as e:
                        self._logger.debug(f"Could not record agent response: {e}")

                # Delegate to overridable method for response handling
                await self._handle_voice_response(content)

        async def _handle_state_changed(event: AgentStateChangedEvent):
            """Handle agent state changes."""
            state = event.new_state
            self._agent_state = state
            self._logger.debug(f"Agent state changed: {state}")

            # Reset idle timer when agent finishes speaking (transitions to listening)
            # This ensures timer starts AFTER the agent has finished speaking
            if state == "listening" and not self._sending_idle_warning:
                self._reset_idle_timer()

        async def _handle_metrics(event: MetricsCollectedEvent):
            """Handle metrics collection."""
            await handle_metrics(event)
            if self.observer and hasattr(self.observer, "on_metrics"):
                await self.observer.on_metrics(event)

        # Register sync wrappers that create tasks for async handlers
        @session.on("user_input_transcribed")
        def on_user_input(event: UserInputTranscribedEvent):
            asyncio.create_task(_handle_user_input(event))

        @session.on("conversation_item_added")
        def on_conversation_item(event: ConversationItemAddedEvent):
            asyncio.create_task(_handle_conversation_item(event))

        @session.on("agent_state_changed")
        def on_state_changed(event: AgentStateChangedEvent):
            asyncio.create_task(_handle_state_changed(event))

        @session.on("metrics_collected")
        def on_metrics(event: MetricsCollectedEvent):
            asyncio.create_task(_handle_metrics(event))

        llm_met = None
        tts_met = None
        eou_met = None
        stt_met = None
        turn_count = 0
        cumulative_stt = 0.0
        cumulative_llm = 0.0
        cumulative_tts = 0.0
        cumulative_total = 0
        real_time_model_met = 0
        realtime_total = 0
        completion_tokens = 0
        prompt_tokens = 0

        async def handle_metrics(ev):
            from livekit.agents import metrics

            nonlocal llm_met, tts_met, eou_met

            nonlocal turn_count, cumulative_stt, cumulative_llm, cumulative_tts, cumulative_total, stt_met, real_time_model_met, realtime_total,prompt_tokens,completion_tokens

            metrics.log_metrics(ev.metrics)

            if type(ev.metrics) == metrics.EOUMetrics:
                eou_met = ev.metrics
            elif type(ev.metrics) == metrics.LLMMetrics:
                llm_met = ev.metrics
                completion_tokens = llm_met.completion_tokens
                prompt_tokens = llm_met.prompt_tokens
            elif type(ev.metrics) == metrics.TTSMetrics:
                tts_met = ev.metrics
            elif type(ev.metrics) == metrics.STTMetrics:
                stt_met = ev.metrics
            elif type(ev.metrics) == metrics.RealtimeModelMetrics:
                if ev.metrics.ttft > 0:
                    real_time_model_met = ev.metrics.ttft
                    print(f"\n\n Realtime : {ev.metrics} \n\n ")

            if real_time_model_met:
                turn_count += 1
                realtime_total += real_time_model_met

                latency_data = self.user_state.extra_data.get("latency_metrics", [])
                latency_data.append({"realtime_latency":real_time_model_met, "realtime_avg":realtime_total / turn_count})
                print(
                    f"\n\n real_time_model_met avg : {realtime_total / turn_count} \n\n "
                )

                real_time_model_met = None

            if eou_met and llm_met and tts_met:
                stt_latency = eou_met.end_of_utterance_delay
                llm_latency = llm_met.ttft
                tts_latency = tts_met.ttfb

                current_turn_total = stt_latency + llm_latency + tts_latency

                turn_count += 1
                cumulative_stt += stt_latency
                cumulative_llm += llm_latency
                cumulative_tts += tts_latency
                cumulative_total += current_turn_total

                avg_stt = cumulative_stt / turn_count
                avg_llm = cumulative_llm / turn_count
                avg_tts = cumulative_tts / turn_count
                avg__current_total = cumulative_total / turn_count
                # avg_total = (avg_stt + avg_llm + avg_tts)/turn_count

                self.add_latency_chart(turn_count,llm_latency,tts_latency,stt_latency,current_turn_total,avg_llm,avg_stt,avg_tts,avg__current_total,prompt_tokens,completion_tokens)

                print(f"\n{'=' * 60}")
                print(f"Turn #{turn_count} Metrics:")
                # print(f"  Current - STT: {stt_latency:.2f}ms | LLM: {llm_latency:.2f}ms | TTS: {tts_latency:.2f}ms")
                # print(f"  Current Turn Total (avg): {current_turn_total:.2f}ms")
                print(f"\nRunning Averages (across all {turn_count} turns):")
                print(
                    f"Avg STT: {avg_stt:.2f}s | Avg LLM: {avg_llm:.2f}s | Avg TTS: {avg_tts:.2f}s"
                )
                print(f"\n Avg of current total{avg__current_total:.2f} s")
                # print(f"  Overall Avg Total: {avg_total:.2f}s")
                print(f"{'=' * 60}\n")

                eou_met = None
                llm_met = None
                tts_met = None
                stt_met = None
                prompt_tokens=0
                completion_tokens=0

    def add_latency_chart(self,turn_count,llm_latency,tts_latency,stt_latency,current_turn_total,avg_llm,avg_stt,avg_tts,avg__current_total,prompt_tokens,completion_tokens):
        if not isinstance(self.user_state.extra_data,dict):
            self.user_state.extra_data = {}

        latency_data = self.user_state.extra_data.get("latency_metrics",[])
        provider_data = self.user_state.extra_data.get("service_modes")

        latency_entry = {
            "turn_count":turn_count,
            "llm_latency": llm_latency,
            "tts_latency": tts_latency,
            "stt_latency": stt_latency,
            "total_latency": current_turn_total,
            "avg_llm_latency": avg_llm,
            "avg_stt_latency": avg_stt,
            "avg_tts_latency": avg_tts,
            "avg_total_latency": avg__current_total,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }

        if provider_data:
            try:
                latency_entry['stt_provider']=provider_data.stt_provider
                latency_entry['tts_provider']=provider_data.tts_provider
                latency_entry['llm_provider']=provider_data.llm_provider
                latency_entry['llm_type']=provider_data.llm_type
                latency_entry['stt_type']=provider_data.stt_type
                latency_entry['tts_type']=provider_data.tts_type

            except Exception as e:
                pass


        latency_data.append(latency_entry)

        self.user_state.extra_data["latency_metrics"] = latency_data



    def _parse_block_message(
        self, raw_message: str
    ) -> tuple[str, dict | None, list[dict] | None]:
        """
        Parse incoming message, extracting content and files from block JSON.

        Args:
            raw_message: Raw message text (may be JSON block or plain text)

        Returns:
            Tuple of (extracted_content, block_data or None, files list or None)
        """
        if not raw_message or not raw_message.strip():
            return "", None, None

        # Try to parse as JSON block
        if raw_message.strip().startswith("{"):
            try:
                block_data = json.loads(raw_message)

                # Check if this is a block event
                if isinstance(block_data, dict) and block_data.get("event") == "block":
                    raw_data = block_data.get("data")
                    if raw_data is None or not isinstance(raw_data, dict):
                        return raw_message, None, None
                    data = raw_data

                    inner_data = data.get("data") or {}
                    if not isinstance(inner_data, dict):
                        inner_data = {}

                    # Extract content from nested data structure
                    content = inner_data.get("content") or data.get("content") or ""

                    # Extract attached files from inner data
                    files = inner_data.get("files", [])

                    self._logger.info(
                        f"[TEXT_MODE] Parsed block message: "
                        f"block_type={data.get('block_type')}, "
                        f"content_type={data.get('content_type')}, "
                        f"content_length={len(content)}, "
                        f"files_count={len(files)}"
                    )

                    return content, block_data, files if files else None

            except json.JSONDecodeError:
                # Not valid JSON, treat as plain text
                pass

        # Return as plain text
        return raw_message, None, None

    async def _download_file_from_s3(self, file_info: dict) -> str | None:
        """
        Download a file from S3 to a local temporary location.

        Args:
            file_info: File metadata dict with 'url' or 'media_url' keys

        Returns:
            Local file path if successful, None otherwise
        """
        try:
            from super_services.libs.core.s3 import s3_path_split, download_file
            import tempfile
            import os

            # Get S3 URL (prefer 'url' which is the S3 path, fallback to 'media_url')
            file_url = file_info.get("url") or file_info.get("media_url")
            if not file_url:
                self._logger.warning("No URL found in file info")
                return None

            # Parse S3 URL to get bucket and key
            bucket_name, file_key = s3_path_split(file_url)

            # Extract filename from the key
            file_name = file_key.split("/")[-1]
            name, ext = os.path.splitext(file_name)

            # Create temp directory if needed
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"voice_input_{name}{ext}")

            # Download file from S3
            local_path = download_file(bucket_name, file_key, output_path)

            self._logger.info(
                f"[FILE_PROCESSING] Downloaded file from S3: {file_name} -> {local_path}"
            )
            return local_path

        except Exception as e:
            self._logger.error(
                f"[FILE_PROCESSING] Failed to download file from S3: {e}"
            )
            return None

    async def _process_attached_files(self, files: list[dict]) -> list[dict]:
        """
        Process attached files - download from S3 and prepare for LLM context.

        Args:
            files: List of file metadata dicts

        Returns:
            List of processed file info dicts with local paths
        """
        processed_files = []

        for file_info in files:
            media_type = file_info.get("media_type", "unknown")
            file_name = file_info.get("name", "unknown")

            self._logger.info(
                f"[FILE_PROCESSING] Processing file: {file_name} (type: {media_type})"
            )

            # Download file from S3
            local_path = await self._download_file_from_s3(file_info)

            if local_path:
                processed_files.append(
                    {
                        "name": file_name,
                        "media_type": media_type,
                        "local_path": local_path,
                        "original_url": file_info.get("url"),
                        "media_url": file_info.get("media_url"),
                    }
                )

        return processed_files

    def _create_text_input_handler(self) -> Any:
        """
        Create a text input handler for the lk.chat topic.

        For text-only mode, we generate LLM response and send it back via
        send_text() on the lk.chat topic instead of using TTS.

        Returns:
            Callback function for TextInputOptions.text_input_cb
        """
        from livekit.agents import room_io

        def custom_text_input_handler(
            session: "AgentSession", event: room_io.TextInputEvent
        ) -> None:
            """
            Handle text input from lk.chat topic.

            For text-only mode:
            - Receive text via event.text
            - Parse JSON block if present to extract content
            - Generate LLM response
            - Send response back via send_text() on lk.chat topic
            """
            raw_message = event.text
            self._logger.info(
                f"[CUSTOM_HANDLER] Received text input: {raw_message[:200]}..."
            )

            if not raw_message or not raw_message.strip():
                return

            # Parse message - extract content and files from block JSON if present
            message, block_data, files = self._parse_block_message(raw_message)

            if not message or not message.strip():
                self._logger.warning(
                    "[CUSTOM_HANDLER] No content extracted from message, skipping"
                )
                return

            self._logger.info(f"[CUSTOM_HANDLER] Extracted content: {message[:100]}...")

            # Process attached files if present (async task)
            if files:
                self._logger.info(
                    f"[CUSTOM_HANDLER] Found {len(files)} attached file(s), processing..."
                )

                # Process files and generate response in async task
                async def process_files_and_generate() -> None:
                    # Send notification: Processing files
                    self._send_callback(
                        Message.add_notification("Processing attached files..."),
                        thread_id=str(self.user_state.thread_id),
                    )

                    processed = await self._process_attached_files(files)
                    if processed:
                        self._logger.info(
                            f"[CUSTOM_HANDLER] Processed {len(processed)} file(s)"
                        )
                        # Send notification: Files processed
                        self._send_callback(
                            Message.add_notification(
                                f"Loaded {len(processed)} file(s) for analysis"
                            ),
                            thread_id=str(self.user_state.thread_id),
                        )

                    # Send notification: Generating response
                    self._send_callback(
                        Message.add_notification("Analyzing content..."),
                        thread_id=str(self.user_state.thread_id),
                    )

                    await self._generate_and_send_text_response(
                        session, message, block_data, processed_files=processed
                    )

                asyncio.create_task(process_files_and_generate())
                return  # Exit early - response generation handled in async task

            # Store transcript
            print(
                f"{'='*100}\n\n appending in  custom_text_input_handler \n\n {'='*100} "
            )

            self.user_state.transcript.append(
                {
                    "role": "user",
                    "content": message,
                    "timestamp": str(datetime.now()),
                    "participant": self.user_state.extra_data.get("identity"),
                }
            )

            # Send callback for user message
            msg = Message.create(
                message,
                user=self.user_state.user,
                event=Event.USER_MESSAGE,
            )
            self._send_callback(msg, thread_id=str(self.user_state.thread_id))

            # Notify plugins (fire and forget)
            asyncio.create_task(self.plugins.broadcast_event("on_user_speech", message))

            # Handle commands (optional - can be extended)
            if message.startswith("/"):
                if message == "/help":
                    asyncio.create_task(
                        self._send_text_response(
                            session, "Available commands: /help, /status"
                        )
                    )
                    return
                elif message == "/status":
                    asyncio.create_task(
                        self._send_text_response(session, "Agent is running normally")
                    )
                    return

            # Generate response and send as text
            # Pass block_data for additional context if needed
            asyncio.create_task(
                self._generate_and_send_text_response(session, message, block_data)
            )

        return custom_text_input_handler

    def _build_response_block(
        self,
        response_text: str,
        block_data: dict | None = None,
        message_id: str | None = None,
        cards: dict | None = None,
    ) -> dict:
        """
        Build response block dict matching BlockModelSchema structure.

        The response block follows the BlockModelSchema pattern:
        - block: BlockEnum (html, text, media, etc.)
        - block_type: BlockTypeEnum (pilot_response, reply, etc.)
        - data: Dict containing content and cards

        Supports two modes:
        - Text response (with optional cards): response_text is non-empty
        - Card-only block: response_text is empty, cards provided

        Args:
            response_text: The LLM response text (can be empty for card-only blocks)
            block_data: Original block data from input (for context)
            message_id: Unique ID for correlating with streaming chunks
            cards: Optional single card object (e.g., {"type": "provider", "items": [...]})

        Returns:
            Dict formatted as response block (for use with publish_data)
        """
        # Extract context from original block if available
        pilot = "multi-ai"
        execution_type = "contact"
        focus = "my_space"

        if block_data:
            pilot = block_data.get("pilot", pilot)
            data = block_data.get("data", {})
            execution_type = data.get("execution_type", execution_type)
            inner_data = data.get("data", {})
            focus = inner_data.get("focus", focus)

        # Build data dict following BlockModelSchema pattern
        data_content: dict = {}

        # Include content only if provided (allows card-only blocks)
        if response_text:
            data_content["content"] = response_text
            data_content["focus"] = focus

        # Include cards inside data dict
        if cards:
            data_content["cards"] = cards

        # Set block_type based on content presence
        block_type = "pilot_response" if response_text else "card_block"

        response_block = {
            "event": "block_response",
            "id": message_id or str(uuid.uuid4())[:12],
            "pilot": pilot,
            "execution_type": execution_type,
            "block": "html",  # BlockEnum.html
            "block_type": block_type,
            "data": data_content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return response_block

    async def _send_streaming_text(
        self,
        text_chunk: str,
        message_id: str | None = None,
        chunk_index: int = 0,
        block_data: dict | None = None,
    ) -> None:
        """
        Send a streaming text chunk as structured JSON via TOPIC_LK_STREAM topic.

        Args:
            text_chunk: Text chunk to send for real-time display
            message_id: Unique ID for correlating chunks with final response
            chunk_index: Index of this chunk in the stream sequence
            block_data: Original block data for context (pilot, focus, etc.)
        """
        try:
            if not text_chunk:
                return

            room = self._job_context.room if self._job_context else None
            if not room:
                self._logger.error(
                    "[TEXT_MODE] No room available to send streaming text"
                )
                return

            # Extract context from block_data if available
            pilot = "multi-ai"
            focus = "my_space"
            if block_data:
                pilot = block_data.get("pilot", pilot)
                data = block_data.get("data", {})
                inner_data = data.get("data", {})
                focus = inner_data.get("focus", focus)

            # Build structured streaming block format
            stream_block = {
                "event": "stream",
                "id": message_id or str(uuid.uuid4())[:12],
                "pilot": pilot,
                "data": {
                    "content": text_chunk,
                    "chunk_index": chunk_index,
                    "is_final": False,
                    "focus": focus,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Publish via data channel with dedicated streaming topic
            payload = json.dumps(stream_block, ensure_ascii=False).encode("utf-8")
            await room.local_participant.publish_data(
                payload,
                reliable=True,
                topic=TOPIC_LK_STREAM,
            )

        except Exception as e:
            self._logger.error(f"[TEXT_MODE] Failed to send streaming text: {e}")

    async def _handle_voice_response(self, content: str) -> None:
        """
        Handle voice mode assistant response.

        Called when conversation_item_added fires for assistant. Override this
        method in subclasses to customize response handling (e.g., add cards).

        Args:
            content: The assistant's response text
        """
        # Generate message ID for this voice response
        message_id = str(uuid.uuid4())[:12]

        # Store transcript with message_id
        # self.user_state.transcript.append(
        #     {
        #         "role": "assistant",
        #         "content": content,
        #         "timestamp": str(datetime.now()),
        #         "message_id": message_id,
        #     }
        # )

        # Send callback for internal processing
        msg = Message.create(
            content,
            user=self.agent,
            event=Event.AGENT_MESSAGE,
        )
        self._send_callback(msg, thread_id=str(self.user_state.thread_id))

        # Send parallel text response via data channel (VOICE mode)
        # Uses same format as TEXT mode for consistency (TOPIC_LK_CHAT topic)
        try:
            await self._send_data_response(content, None, message_id)
            self._logger.debug(
                f"[VOICE_MODE] Sent text response via {TOPIC_LK_CHAT} (id={message_id})"
            )
        except Exception as e:
            self._logger.warning(f"[VOICE_MODE] Failed to send text response: {e}")

        # Signal first response sent
        if not self._first_response_sent.is_set():
            self._first_response_sent.set()

        # Record agent response for quality metrics (Gap #2 fix)
        await self._record_agent_response_for_quality(content)

        # Notify plugins
        await self.plugins.broadcast_event("on_agent_speech", content)

    async def _send_data_response(
        self,
        response_text: str,
        block_data: dict | None = None,
        message_id: str | None = None,
        cards: dict | None = None,
    ) -> None:
        """
        Send final response as JSON block via data channel (event bridge).

        Args:
            response_text: Full response text
            block_data: Original block data for context
            message_id: Unique ID for correlating with streaming chunks
            cards: Optional single card object
        """
        try:
            if not response_text:
                return

            if not self._event_bridge:
                self._logger.error(
                    "[TEXT_MODE] No event bridge available for data response"
                )
                return

            # Build response block dict with message_id for correlation
            self._logger.debug(
                f"[CARDS_DEBUG] Building response block: "
                f"card_type={cards.get('type') if cards else None}, message_id={message_id}"
            )
            response_block = self._build_response_block(
                response_text, block_data, message_id, cards
            )

            # Log the response block structure
            data_cards = response_block.get("data", {}).get("cards")
            self._logger.info(
                f"[CARDS_DEBUG] Response block built: "
                f"has_cards={data_cards is not None}, "
                f"card_type={data_cards.get('type') if data_cards else None}"
            )

            # Send via event bridge data channel
            success = await self._event_bridge.publish_data(
                data=response_block,
                topic=TOPIC_LK_CHAT,
                reliable=True,
            )

            if success:
                self._logger.info(
                    f"[BLOCK_SENT] Published to {TOPIC_LK_CHAT} (id={message_id}): "
                    f"cards_in_block={len(data_cards) if data_cards else 0}, "
                    f"text={response_text[:80]}..."
                )
            else:
                self._logger.error("[TEXT_MODE] Failed to publish data response")

            self.user_state.transcript.append(
                {
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": str(datetime.now()),
                    "message_id": message_id,
                }
            )

            # Send callback for agent message
            msg = Message.create(
                response_text,
                user=self.agent,
                event=Event.AGENT_MESSAGE,
            )
            self._send_callback(msg, thread_id=str(self.user_state.thread_id))

            # Notify plugins
            await self.plugins.broadcast_event("on_agent_speech", response_text)

        except Exception as e:
            self._logger.error(f"[TEXT_MODE] Failed to send data response: {e}")

    async def _build_multimodal_content(
        self,
        text_message: str,
        processed_files: list[dict],
    ) -> list:
        """
        Build multimodal content for LiveKit LLM chat context.

        Creates a list of content parts compatible with LiveKit's ChatMessage.
        Content must be list[str | ImageContent | AudioContent].

        Args:
            text_message: The text part of the message
            processed_files: List of processed file info dicts with local paths

        Returns:
            List of content parts (str or ImageContent) for LiveKit LLM
        """
        from livekit.agents.llm.chat_context import ImageContent
        import base64
        import mimetypes

        content_parts: list = []

        # Add text content first (as plain string for LiveKit)
        if text_message:
            content_parts.append(text_message)

        # Process each file
        for file_info in processed_files:
            media_type = file_info.get("media_type", "unknown")
            local_path = file_info.get("local_path")
            file_name = file_info.get("name", "unknown")

            if not local_path:
                continue

            try:
                if media_type == "image":
                    # Read and encode image as base64 data URL
                    with open(local_path, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode("utf-8")

                    # Detect MIME type
                    mime_type, _ = mimetypes.guess_type(local_path)
                    if not mime_type:
                        mime_type = "image/png"  # Default fallback

                    # Create LiveKit ImageContent with data URL
                    image_content = ImageContent(
                        image=f"data:{mime_type};base64,{image_data}",
                        mime_type=mime_type,
                        inference_detail="auto",
                    )
                    content_parts.append(image_content)
                    self._logger.info(
                        f"[MULTIMODAL] Added image: {file_name} ({mime_type})"
                    )

                elif media_type in ("document", "pdf", "file"):
                    # For documents, add as text reference
                    content_parts.append(f"[Attached file: {file_name}]")
                    self._logger.info(
                        f"[MULTIMODAL] Added document reference: {file_name}"
                    )

                else:
                    # Unknown type - add as text reference
                    content_parts.append(
                        f"[Attached file: {file_name} (type: {media_type})]"
                    )
                    self._logger.info(
                        f"[MULTIMODAL] Added file reference: {file_name} ({media_type})"
                    )

            except Exception as e:
                self._logger.error(
                    f"[MULTIMODAL] Failed to process file {file_name}: {e}"
                )

        return content_parts

    async def _generate_and_send_text_response(
        self,
        session: "AgentSession",
        user_message: str,
        block_data: dict | None = None,
        stream_response: bool = True,
        processed_files: list[dict] | None = None,
    ) -> None:
        """
        Generate LLM response with streaming text and final data block.

        Flow:
        - Streaming chunks: Sent as structured JSON via TOPIC_LK_STREAM topic
        - Final response: Sent as JSON block via TOPIC_LK_CHAT topic

        All chunks and the final response share the same message_id for correlation.

        Args:
            session: AgentSession instance
            user_message: User's input message
            block_data: Optional parsed block data for response formatting
            stream_response: If True, send streaming chunks; if False, wait for full
            processed_files: Optional list of processed file info dicts with local paths
        """
        # Generate unique message ID for correlating stream chunks with final response
        message_id = str(uuid.uuid4())[:12]

        try:
            self._logger.info(
                f"[CUSTOM_HANDLER] Generating response for: {user_message[:100]}... "
                f"(message_id={message_id})"
            )

            # Get the agent's chat context and generate response
            if self._agent and hasattr(self._agent, "chat_ctx"):
                # Add user message to chat context
                chat_ctx = self._agent.chat_ctx.copy()

                # Build message content - multimodal if files are present
                if processed_files:
                    # Build multimodal content with images/files
                    content_parts = await self._build_multimodal_content(
                        user_message, processed_files
                    )
                    chat_ctx.add_message(role="user", content=content_parts)
                    self._logger.info(
                        f"[CUSTOM_HANDLER] Added multimodal message with "
                        f"{len(processed_files)} file(s)"
                    )
                else:
                    chat_ctx.add_message(role="user", content=user_message)

                # Token-aware context truncation before LLM call
                if hasattr(self._agent, "_truncate_context_to_limit"):
                    chat_ctx.messages = self._agent._truncate_context_to_limit(
                        chat_ctx.messages
                    )

                # Get LLM from session or create from service factory
                llm = getattr(session, "_llm", None)
                if llm is None:
                    # Create LLM from service factory (sync method)
                    llm = self.service_factory.create_llm()
                    self._logger.info(
                        f"[CUSTOM_HANDLER] Created LLM from service factory: {type(llm)}"
                    )

                if llm:
                    # Generate response using LLM with streaming
                    response_text = ""
                    chunk_index = 0
                    stream = llm.chat(chat_ctx=chat_ctx)
                    try:
                        async for chunk in stream:
                            if chunk.delta and chunk.delta.content:
                                chunk_content = chunk.delta.content
                                response_text += chunk_content

                                # Send streaming chunk with correlation ID
                                if stream_response and chunk_content:
                                    await self._send_streaming_text(
                                        chunk_content,
                                        message_id=message_id,
                                        chunk_index=chunk_index,
                                        block_data=block_data,
                                    )
                                    chunk_index += 1
                    finally:
                        await stream.aclose()

                    self._logger.info(
                        f"[CUSTOM_HANDLER] Generated response ({len(response_text)} chars, "
                        f"{chunk_index} chunks): {response_text[:100]}..."
                    )

                    if response_text:
                        # Send final response with same message_id for correlation
                        await self._send_data_response(
                            response_text, block_data, message_id
                        )

                        # Update agent's chat context with the response
                        # Must use copy() and update_chat_ctx() since chat_ctx is read-only
                        chat_ctx.add_message(role="assistant", content=response_text)
                        await self._agent.update_chat_ctx(chat_ctx)
                    else:
                        self._logger.warning(
                            "[CUSTOM_HANDLER] LLM returned empty response"
                        )
                else:
                    self._logger.error(
                        "[CUSTOM_HANDLER] No LLM available for text generation"
                    )
            else:
                self._logger.error(
                    "[CUSTOM_HANDLER] Agent or chat context not available"
                )

        except Exception as e:
            self._logger.error(f"[CUSTOM_HANDLER] Error generating text response: {e}")
            import traceback

            self._logger.error(traceback.format_exc())

    def _setup_data_channel_handler(
        self,
        _ctx: "JobContext",
        session: "AgentSession",
        is_text_only: bool = False,
    ) -> None:
        """
        Set up data channel and text stream handlers for custom protocols.

        Uses the event_bridge's on_topic() system to avoid duplicate
        on("data_received") handler registration. The event_bridge already
        handles the data_received event and routes to topic listeners.

        Topics handled here:
        - user_action: User interactions with UI cards
        - superkik.* topics: Custom SuperKik protocol messages (via wildcard)
        - lk.chat: Text input in TEXT-ONLY mode (fallback for text streams)

        Note: Output topics (TOPIC_LK_STREAM, TOPIC_LK_CHAT) are filtered by event_bridge

        Args:
            ctx: LiveKit JobContext
            session: AgentSession instance
            is_text_only: Whether this is TEXT-ONLY mode
        """
        self._logger.info(
            "[DATA_CHANNEL] Setting up custom topic listeners via event_bridge"
        )

        if not self._event_bridge:
            self._logger.warning(
                "[DATA_CHANNEL] No event_bridge available, skipping topic registration"
            )
            return

        # Store session reference for use in handlers
        self._session = session

        # Handler for user_action topic
        async def handle_user_action_event(event: Dict[str, Any]) -> None:
            """Handle user_action topic via event_bridge."""
            try:
                data = event.get("data", {})
                self._logger.info(
                    f"[DATA_CHANNEL] user_action received: {str(data)[:200]}..."
                )
                await self._handle_user_action(data, session)
            except Exception as e:
                self._logger.error(f"[DATA_CHANNEL] Error handling user_action: {e}")

        # Handler for lk.chat topic (fallback for text streams in TEXT-ONLY mode)
        async def handle_lk_chat_event(event: Dict[str, Any]) -> None:
            """
            Handle lk.chat topic via event_bridge (fallback for text streams).

            This handles text input that arrives via text streams but bypasses
            LiveKit's TextInputOptions due to participant identity mismatch.
            """
            try:
                data = event.get("data", {})
                raw_data = event.get("raw_data", b"")
                participant = event.get("participant_identity", "unknown")

                # Get raw text - either from raw_data or from data dict
                if isinstance(raw_data, bytes) and raw_data:
                    raw_message = raw_data.decode("utf-8")
                elif data.get("raw"):
                    # Plain text wrapped by event_bridge
                    raw_message = data.get("text", "")
                else:
                    # JSON data - serialize back to string
                    raw_message = json.dumps(data) if data else ""

                self._logger.info(
                    f"[TEXT_STREAM_FALLBACK] lk.chat received from '{participant}': "
                    f"{raw_message[:200]}..."
                )

                if not raw_message or not raw_message.strip():
                    return

                # Parse message - extract content and files from block JSON
                message, block_data, files = self._parse_block_message(raw_message)

                if not message or not message.strip():
                    self._logger.warning(
                        "[TEXT_STREAM_FALLBACK] No content extracted, skipping"
                    )
                    return

                self._logger.info(
                    f"[TEXT_STREAM_FALLBACK] Extracted content: {message[:100]}..."
                )

                self.user_state.transcript.append(
                    {
                        "role": "user",
                        "content": message,
                        "timestamp": str(datetime.now()),
                        "participant": self.user_state.extra_data.get("identity"),
                    }
                )

                # Send callback for user message
                msg = Message.create(
                    message,
                    user=self.user_state.user,
                    event=Event.USER_MESSAGE,
                )
                self._send_callback(msg, thread_id=str(self.user_state.thread_id))

                # Notify plugins
                asyncio.create_task(
                    self.plugins.broadcast_event("on_user_speech", message)
                )

                # Generate and send response
                asyncio.create_task(
                    self._generate_and_send_text_response(session, message, block_data)
                )

            except Exception as e:
                self._logger.error(
                    f"[TEXT_STREAM_FALLBACK] Error handling lk.chat: {e}"
                )
                import traceback

                self._logger.error(traceback.format_exc())

        # Handler for all data (catches superkik.* input topics)
        async def handle_all_data_event(event: Dict[str, Any]) -> None:
            """Handle all data events, routing superkik.* input topics."""
            try:
                topic = event.get("topic", "")
                data = event.get("data", {})

                # Only handle superkik.* input topics here
                # Note: Output topics (superkik.cards, superkik.preferences, superkik.session)
                # are already filtered by event_bridge._HANDLED_TOPICS
                if topic.startswith("superkik."):
                    self._logger.info(
                        f"[DATA_CHANNEL] superkik message on '{topic}': {str(data)[:200]}..."
                    )
                    await self._handle_superkik_message(topic, data, session)
            except Exception as e:
                self._logger.error(f"[DATA_CHANNEL] Error in data handler: {e}")

        # Register topic-specific listener for user_action
        self._event_bridge.on_topic("user_action", handle_user_action_event)
        self._logger.debug("[DATA_CHANNEL] Registered listener for 'user_action' topic")

        # Register global data listener to catch superkik.* topics
        # (event_bridge doesn't support wildcard topics, so we use global listener)
        self._event_bridge.on_data_received(handle_all_data_event)
        self._logger.debug(
            "[DATA_CHANNEL] Registered global data listener for superkik.* topics"
        )

        # For TEXT-ONLY mode, register fallback handler for lk.chat
        # This catches text stream messages that bypass TextInputOptions
        if is_text_only:
            self._event_bridge.on_topic(TOPIC_LK_CHAT, handle_lk_chat_event)
            self._logger.info(
                f"[DATA_CHANNEL] Registered fallback listener for '{TOPIC_LK_CHAT}' "
                "(TEXT-ONLY mode)"
            )

            # Register text stream handlers to receive text stream messages
            # Note: lk.chat may already be registered by RoomIO, which is fine
            self._event_bridge.register_text_stream_handlers(
                topics=[TOPIC_LK_CHAT, "user_action"]
            )
        else:
            # VOICE mode: Register handler to capture file attachments from lk.chat
            # This allows users to send files while speaking
            async def handle_voice_mode_attachments(event: Dict[str, Any]) -> None:
                """
                Handle lk.chat messages in VOICE mode to capture file attachments.

                In voice mode, the voice pipeline handles speech transcription,
                but file attachments come through the data channel via lk.chat.
                This handler extracts those files and stores them in user_state
                so tools like process_csv_for_calls can access them.
                """
                try:
                    data = event.get("data", {})
                    raw_data = event.get("raw_data", b"")

                    # Get raw message
                    if isinstance(raw_data, bytes) and raw_data:
                        raw_message = raw_data.decode("utf-8")
                    elif data.get("raw"):
                        raw_message = data.get("text", "")
                    else:
                        raw_message = json.dumps(data) if data else ""

                    if not raw_message or not raw_message.strip():
                        return

                    # Parse message to extract files
                    message, block_data, files = self._parse_block_message(raw_message)

                    if files:
                        self._logger.info(
                            f"[VOICE_MODE] Found {len(files)} file attachment(s) "
                            f"in lk.chat message"
                        )

                        # Process and store files in user_state
                        processed_files = await self._process_attached_files(files)
                        if processed_files:
                            # Store in user_state.files for tool access
                            self.user_state.files.extend(processed_files)
                            self._logger.info(
                                f"[VOICE_MODE] Stored {len(processed_files)} file(s) "
                                f"in user_state.files"
                            )

                            # Inject context about attached files into the agent's chat
                            # This helps the agent know there are files attached
                            if self._agent:
                                file_descriptions = []
                                for f in processed_files:
                                    name = f.get("name", "unknown")
                                    media_type = f.get("media_type", "unknown")
                                    file_descriptions.append(f"- {name} ({media_type})")

                                file_context = (
                                    f"[ATTACHED FILES]\n"
                                    f"The user has attached the following file(s):\n"
                                    f"{chr(10).join(file_descriptions)}\n"
                                    f"Use appropriate tools to process these files "
                                    f"based on the user's request."
                                )

                                try:
                                    chat_ctx = self._agent.chat_ctx.copy()
                                    chat_ctx.add_message(
                                        role="system",
                                        content=file_context,
                                    )
                                    await self._agent.update_chat_ctx(chat_ctx)
                                    self._logger.info(
                                        "[VOICE_MODE] Injected file context into "
                                        "agent chat"
                                    )
                                except Exception as ctx_err:
                                    self._logger.warning(
                                        f"[VOICE_MODE] Failed to inject file context: "
                                        f"{ctx_err}"
                                    )

                    # Also handle text message if present (hybrid voice+text)
                    if message and message.strip():
                        self._logger.info(
                            f"[VOICE_MODE] Text message with attachment: "
                            f"{message[:100]}..."
                        )
                        # Store transcript entry
                        self.user_state.transcript.append(
                            {
                                "role": "user",
                                "content": message,
                                "timestamp": str(datetime.now()),
                                "participant": self.user_state.extra_data.get(
                                    "identity"
                                ),
                            }
                        )

                except Exception as e:
                    self._logger.error(
                        f"[VOICE_MODE] Error handling file attachment: {e}"
                    )
                    import traceback

                    self._logger.error(traceback.format_exc())

            # Register handler for lk.chat in voice mode
            self._event_bridge.on_topic(TOPIC_LK_CHAT, handle_voice_mode_attachments)
            self._event_bridge.register_text_stream_handlers(
                topics=[TOPIC_LK_CHAT, "user_action"]
            )
            self._logger.info(
                f"[DATA_CHANNEL] Registered file attachment listener for "
                f"'{TOPIC_LK_CHAT}' (VOICE mode)"
            )

        self._logger.info(
            "[DATA_CHANNEL] Custom topic listeners registered via event_bridge"
        )

    async def _handle_user_action(
        self, data: Dict[str, Any], session: "AgentSession"
    ) -> None:
        """
        Handle user action messages from frontend.

        Args:
            data: Action data dict with 'action' key and parameters
            session: AgentSession instance
        """
        action = data.get("action", "")
        self._logger.info(f"[USER_ACTION] Received action: {action}")
        # Override in subclasses for specific action handling

    async def _handle_superkik_message(
        self, topic: str, data: Dict[str, Any], session: "AgentSession"
    ) -> None:
        """
        Handle SuperKik protocol messages.

        Args:
            topic: Full topic name (e.g., "superkik.preferences")
            data: Message data
            session: AgentSession instance
        """
        self._logger.debug(f"[SUPERKIK] Received on {topic}: {str(data)[:100]}...")
        # Override in subclasses (SuperKikHandler) for specific handling

    async def execute(self, *args, **kwargs) -> Any:
        """Execute the handler (compatibility method for Pipecat interface)."""
        self._logger.warning(
            "LiveKit handler execute() called without context. "
            "Use execute_with_context(ctx) for LiveKit native execution."
        )

    async def _connect_room_if_needed(self, ctx: "JobContext") -> bool:
        """Connect to room only when not already connected."""
        room = getattr(ctx, "room", None)
        state = getattr(room, "connection_state", None)
        connected_states = {1}

        rtc_connection_state = getattr(rtc, "ConnectionState", None)
        if rtc_connection_state:
            connected_states.update(
                {
                    getattr(rtc_connection_state, "CONN_CONNECTED", None),
                    getattr(rtc_connection_state, "CONNECTED", None),
                }
            )
            connected_states.discard(None)

        if state in connected_states:
            self._logger.info("Room already connected, skipping duplicate connect")
            return False

        await ctx.connect()
        self._logger.info("Connected to room")
        return True

    async def execute_with_context(self, ctx: "JobContext") -> Any:
        """
        Execute the LiveKit voice handler with job context.

        This is the main entry point for LiveKit native execution.
        Creates and runs an AgentSession with the configured services.

        Args:
            ctx: LiveKit JobContext
        """
        try:
            self._logger.info(
                f"Starting LiveKit session for {self.user_state.user_name}"
            )

            agent_handler_start = perf_counter()

            # Store context for later use
            self._job_context = ctx

            # Ensure LiveKit plugins are registered on the main thread
            livekit_services._ensure_livekit_plugins_loaded(self._logger)

            # Create the agent session using service factory
            session_start_at = perf_counter()

            session = await self.create_agent_session(ctx)
            self._session = session
            session_duration = (perf_counter() - session_start_at) * 1000
            add_perf_log(self.user_state, "lk_lite_session_create", session_duration)
            self._logger.info(
                f"\n\n[TIMING] for session timing  : {session_duration:.0f}ms\n\n"
            )

            agent_create_start = perf_counter()
            # Create the agent with instructions
            agent = self.create_agent(ctx)
            self._agent = agent
            agent_create_duration = (perf_counter() - agent_create_start) * 1000
            add_perf_log(self.user_state, "lk_lite_agent_create", agent_create_duration)
            self._logger.info(
                f"\n\n [TIMING] for agent create time  : {agent_create_duration:.0f}ms\n\n"
            )
            # Set up session event handlers
            event_start = perf_counter()

            self._setup_session_events(session)

            # Notify plugins of call start
            await self.plugins.broadcast_event("on_call_start")

            # Check modality for room options and handler configuration
            modality = getattr(self.user_state, "modality", Modality.TEXT_AUDIO)
            modality_str = str(modality) if modality else "text_audio"
            is_text_only = modality_str == "text" or modality == Modality.TEXT
            self._logger.info(
                f"[MODALITY] Session mode: modality={modality}, "
                f"modality_str={modality_str}, is_text_only={is_text_only}, "
                f"Modality.TEXT={Modality.TEXT}, modality==Modality.TEXT={modality == Modality.TEXT}"
            )

            event_duration = (perf_counter() - event_start) * 1000
            add_perf_log(self.user_state, "lk_lite_events_setup", event_duration)
            self._logger.info(
                f"\n\n [TIMING] for events broadcast : {event_duration:.0f}ms\n\n"
            )

            # Start the session with new RoomOptions API (replaces deprecated room_input_options)

            other_process_start = perf_counter()

            try:
                from livekit.agents.voice import room_io

                # Build room options based on modality
                room_opts_kwargs = {}

                if is_text_only:
                    # Text-only mode: disable audio input/output
                    # Per LiveKit docs: https://docs.livekit.io/agents/multimodality/text/
                    self._logger.info(
                        "[TEXT_MODE] Configuring room options with audio disabled"
                    )
                    room_opts_kwargs["audio_input"] = False
                    room_opts_kwargs["audio_output"] = False

                    # Set up text input handler via TextInputOptions
                    # This handles the 'lk.chat' topic messages
                    # Pattern from LiveKit reference: /Users/parvbhullar/Downloads/agent.py
                    text_input_handler = self._create_text_input_handler()
                    room_opts_kwargs["text_input"] = room_io.TextInputOptions(
                        text_input_cb=text_input_handler
                    )
                    self._logger.info(
                        f"[TEXT_MODE] TextInputOptions configured with handler: {text_input_handler}"
                    )
                else:
                    # Voice mode: enable audio with optional noise cancellation
                    self._logger.info("[VOICE_MODE] Using voice mode with STT/TTS")
                    # Try to enable noise cancellation if available
                    # BVC requires LiveKit Cloud authentication - gracefully skip if not available
                    try:
                        from livekit.plugins import noise_cancellation

                        # Check if this is a SIP/telephony call for optimized noise cancellation
                        is_telephony = self.config.get("call_type") in (
                            "inbound",
                            "outbound",
                        )
                        if is_telephony and hasattr(noise_cancellation, "BVCTelephony"):
                            nc = noise_cancellation.BVCTelephony()
                            self._logger.info(
                                "Using BVCTelephony noise cancellation for telephony call"
                            )
                        else:
                            nc = noise_cancellation.BVC()
                            self._logger.info("Using BVC noise cancellation")

                        room_opts_kwargs["audio_input"] = room_io.AudioInputOptions(
                            noise_cancellation=nc,
                        )
                    except ImportError:
                        self._logger.warning(
                            "Noise cancellation plugin not available - continuing without it"
                        )
                    except Exception as nc_error:
                        self._logger.warning(
                            f"Noise cancellation setup failed (likely not authenticated with LiveKit Cloud): {nc_error}. "
                            "Continuing without noise cancellation."
                        )

                # Create room options
                # Set close_on_disconnect=False to keep the agent in the room during handover
                # When handover is enabled, we don't want the session to close when the original
                # caller disconnects - the agent should stay to facilitate the transferred call
                handover_enabled = (
                    self.user_state.model_config.get("handover_enabled", False)
                    if self.user_state
                    else False
                )
                room_opts_kwargs["close_on_disconnect"] = not handover_enabled

                if handover_enabled:
                    self._logger.info(
                        "[HANDOVER] close_on_disconnect=False - agent will stay in room during handover"
                    )

                room_options = room_io.RoomOptions(**room_opts_kwargs)

                await self._session.start(
                    room=ctx.room,
                    agent=agent,
                    room_options=room_options,
                )
                self._logger.info(
                    f"LiveKit session started successfully with RoomOptions (modality={modality})"
                )

                # Connect to the room - this enables text stream handling
                # Per LiveKit reference: must be called after session.start()
                await self._connect_room_if_needed(ctx)

                chat_context_data = None
                if self.user_state and self.user_state.extra_data:
                    if isinstance(self.user_state.extra_data, dict):
                        chat_context_data = (
                            self.user_state.extra_data.get("data", {})
                            .get("pre_call_result", {})
                            .get("chat_context")
                        )

                    elif isinstance(self.user_state.extra_data, str):
                        chat_context_data = self.user_state.extra_data

                if not chat_context_data and self.config:
                    chat_context_data = self.config.get("chat_context")

                print(f"{'=' * 100}\n\n  updating chat context \n\n{'=' * 100}")
                if chat_context_data:
                    await agent.load_previous_conversations(chat_context_data)

                other_process_duration = (perf_counter() - other_process_start) * 1000
                add_perf_log(
                    self.user_state, "lk_lite_session_start", other_process_duration
                )
                self._logger.info(
                    f"\n\n [TIMING] for extra process   : {other_process_duration:.0f}ms\n\n"
                )
                total_execution = (perf_counter() - agent_handler_start) * 1000
                add_perf_log(self.user_state, "lk_lite_execute_total", total_execution)
                self._logger.info(
                    f"\n\n [TIMING] for agent execution : {total_execution:.0f}ms\n\n"
                )
            except Exception as e:
                self.user_state.call_status = CallStatusEnum.FAILED
                self._logger.error(f"Failed to start LiveKit session: {e}")
                import traceback

                self._logger.error(traceback.format_exc())
                raise

            # Start background audio if configured (only for voice mode)
            # Reuse is_text_only computed above for consistency
            if not is_text_only:
                await self._start_background_audio(ctx.room, session)

            # Set up data channel handler for custom topics (user_action, superkik.*)
            # In TEXT-ONLY mode, also registers fallback for lk.chat text streams
            self._setup_data_channel_handler(ctx, session, is_text_only=is_text_only)

            # Send first message (skip for stage-based agents - they handle greeting in on_enter)
            if not self.use_conversation_intelligence:
                first_message = self.config.get(
                    "first_message",
                    "Hello! How can I help you today?",
                )
                first_message = self.prompt_manager._replace_template_params(first_message)
                await session.generate_reply(instructions=first_message)
            else:
                self._logger.info(
                    "[STAGE_AGENTS] Skipping first_message - agent on_enter() handles greeting"
                )

            # Send start callback
            self._send_callback(
                Message.create("CALL STARTED", role="system", event=Event.TASK_START),
                thread_id=str(self.user_state.thread_id),
            )

            self._logger.info(
                "LiveKit session started successfully, waiting for completion..."
            )

            # Start idle timeout monitoring
            await self._start_idle_monitor()

            # Wait for the room to disconnect or session to end
            # This keeps the agent running until the call completes
            disconnect_event = asyncio.Event()

            # Track the main user identity (first non-agent, non-SIP participant)
            # This is used to determine when to end the session
            main_user_identity: Optional[str] = None

            # Identify main user from current remote participants
            for identity, participant in ctx.room.remote_participants.items():
                if (
                    identity != ctx.room.local_participant.identity
                    and participant.kind != rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                ):
                    main_user_identity = identity
                    self._logger.info(f"Identified main user: {main_user_identity}")
                    break

            @ctx.room.on("disconnected")
            def on_room_disconnected():
                self._logger.info("Room disconnected, ending session")
                disconnect_event.set()

            @ctx.room.on("participant_connected")
            def on_participant_connected(participant):
                nonlocal main_user_identity
                # Track main user if not yet identified (for late joiners)
                if (
                    main_user_identity is None
                    and participant.identity != ctx.room.local_participant.identity
                    and participant.kind != rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                ):
                    main_user_identity = participant.identity
                    self._logger.info(f"Main user joined (late): {main_user_identity}")
                else:
                    self._logger.info(
                        f"Participant connected: {participant.identity} "
                        f"(kind: {participant.kind}, main_user: {main_user_identity})"
                    )

            @ctx.room.on("participant_disconnected")
            def on_participant_disconnected(participant):
                nonlocal main_user_identity
                self._logger.info(
                    f"Participant {participant.identity} disconnected "
                    f"(kind: {participant.kind}, main_user: {main_user_identity})"
                )

                # Stop transcription for this participant
                asyncio.create_task(
                    self._stop_participant_transcription(participant.identity)
                )

                # Skip if it's the agent disconnecting
                if participant.identity == ctx.room.local_participant.identity:
                    self._logger.warning("Agent participant disconnected unexpectedly")
                    return

                # Check if handover is in progress or active
                handover_initiated = (
                    self.user_state
                    and isinstance(self.user_state.extra_data, dict)
                    and self.user_state.extra_data.get("handover_initiated", False)
                )
                is_handover_active = (
                    self.user_state
                    and isinstance(self.user_state.extra_data, dict)
                    and self.user_state.extra_data.get("is_handed_over_call", False)
                )
                handover_participant_identity = (
                    self.user_state.extra_data.get("handover_participant_identity")
                    if (handover_initiated or is_handover_active)
                    else None
                )

                # Handle handover scenarios
                if handover_initiated or is_handover_active:
                    self._logger.info(
                        f"[HANDOVER] Participant disconnected. "
                        f"Disconnected: {participant.identity}, Handover participant: {handover_participant_identity}, "
                        f"Handover initiated: {handover_initiated}, Handover active: {is_handover_active}"
                    )

                    # If the handover participant disconnects - IGNORE, don't end session
                    if participant.identity == handover_participant_identity:
                        self._logger.info(
                            f"[HANDOVER] Handover participant {participant.identity} disconnected - ignoring, session continues"
                        )
                        return

                    # If the original caller (first user) disconnects - end the session
                    self._logger.info(
                        f"[HANDOVER] Original caller {participant.identity} disconnected, ending session"
                    )
                    disconnect_event.set()
                    return

                # SIP participant disconnected - don't end session
                # The main user is still connected and may want to continue
                if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                    self._logger.info(
                        f"SIP participant {participant.identity} disconnected, "
                        "main user session continues"
                    )
                    return

                # Check if this is the main user disconnecting
                # Only end session when the MAIN USER disconnects, not other participants
                if main_user_identity and participant.identity == main_user_identity:
                    self._logger.info(
                        f"Main user {participant.identity} disconnected, ending session"
                    )
                    disconnect_event.set()
                elif not main_user_identity:
                    # Fallback: if main user wasn't tracked, any STANDARD participant
                    # disconnecting ends the session (legacy behavior)
                    if (
                        participant.kind
                        == rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD
                    ):
                        self._logger.info(
                            f"User {participant.identity} disconnected (no main user tracked), "
                            "ending session"
                        )
                        disconnect_event.set()
                else:
                    # Some other participant disconnected (not main user, not SIP)
                    self._logger.info(
                        f"Participant {participant.identity} disconnected, "
                        f"but main user {main_user_identity} still connected"
                    )

            # Wait for disconnect event
            await disconnect_event.wait()
            self._logger.info("Session completed, cleaning up...")

            # Persist quality metrics before cleanup (Gap #1 fix)
            await self._persist_session_quality_metrics(reason="session_disconnect")

            # Stop idle monitor
            await self._stop_idle_monitor()

            # Notify plugins of call end
            await self.plugins.broadcast_event("on_call_end")

        except Exception as e:
            self.user_state.call_status = CallStatusEnum.FAILED
            self._logger.error(f"LiveKit session error: {e}")
            import traceback

            self._logger.error(traceback.format_exc())
            raise

    async def _get_index(self, query: str, kn_bases: List[str] = None) -> dict:
        """Fetch documents from knowledge base using KnowledgeBaseManager."""
        try:
            # Use cached KB manager if available
            kb_manager = getattr(self, "_kb_manager", None)

            if kb_manager is None:
                from super.core.voice.managers.knowledge_base import (
                    KnowledgeBaseManager,
                )

                kb_manager = KnowledgeBaseManager(
                    logger=self._logger,
                    session_id=self._session_id,
                    user_state=self._user_state,
                    config=self.config,
                )
                await kb_manager._init_context_retrieval()
                self._kb_manager = kb_manager

            # Search documents
            docs = await kb_manager._search_documents(query, k=3)

            if not docs:
                # Fallback to remote fetch if local search returns nothing
                if kn_bases:
                    docs = await kb_manager._fetch_remote_documents(query, kn_bases)
                    if docs:
                        await kb_manager._cache_documents(docs)

            if docs:
                doc_list = [
                    {f"Context {i}": doc.content}
                    for i, doc in enumerate(docs)
                    if doc.content and len(doc.content) > 0
                ]
                self._logger.info(f"Retrieved {len(doc_list)} documents")
                return {"Reference Docs": doc_list[:3]}

            self._logger.info("No documents found for query")
            return {"Reference Docs": []}

        except Exception as e:
            self._logger.error(f"Error in _get_index: {e}")
            return {
                "error": str(e),
                "message": "Internal error retrieving information.",
            }

    def _send_callback(self, message: Message, thread_id: str) -> None:
        """Send a message through the callback if one is configured."""
        if self._callback:
            self._callback.send(message, thread_id=thread_id)

    def message_callback(
        self,
        transcribed_text: str,
        role: str,
        user_state: UserState,
    ) -> None:
        """Handle message callbacks - same interface as livekit handler."""
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

    def create_usage(self, user_state: UserState) -> dict:
        """Create serializable usage data from user_state."""
        usage_data = {}

        if hasattr(user_state, "usage") and user_state.usage:
            if hasattr(user_state.usage, "get_summary"):
                summary = user_state.usage.get_summary()
                usage_data = {
                    "llm_prompt_tokens": getattr(summary, "llm_prompt_tokens", 0),
                    "llm_completion_tokens": getattr(
                        summary, "llm_completion_tokens", 0
                    ),
                    "tts_characters_count": getattr(summary, "tts_characters_count", 0),
                    "stt_audio_duration": getattr(summary, "stt_audio_duration", 0),
                }

        return usage_data

    async def end_call(self, reason: str = "completed") -> str:
        """End the current call gracefully."""
        self._logger.info(f"Ending call: {reason}")
        self._is_shutting_down = True

        try:
            # Log quality metrics if using conversation stages
            if self.use_conversation_intelligence and self._session:
                try:
                    userdata = self._session.userdata
                    if hasattr(userdata, 'get_quality_metrics'):
                        quality_metrics = userdata.get_quality_metrics()
                        self._logger.info(userdata.get_quality_log_line())
                        self._logger.info(
                            f"[CONV_END] reason={reason} | "
                            f"intent={quality_metrics.get('intent', 'none')} | "
                            f"stages={quality_metrics['stages_completed']}/5 | "
                            f"score={quality_metrics['scores']['overall']}"
                        )
                except Exception as qe:
                    self._logger.debug(f"Could not log quality metrics: {qe}")

            # Stop idle monitor
            await self._stop_idle_monitor()

            # Stop background audio if running
            await self._stop_background_audio()

            # Notify plugins
            await self.plugins.broadcast_event("on_call_end")

            # Clean up plugins
            await self.plugins.cleanup_all()

            # Send end callback
            self._send_callback(
                Message.create("CALL ENDED", role="system", event=Event.TASK_END),
                thread_id=str(self.user_state.thread_id),
            )

            self._logger.info("Call ended successfully")
            return f"Call ended: {reason}"

        except Exception as e:
            self._logger.error(f"Error ending call: {e}")
            return f"Error: {e}"

    async def end_ongoing_agent(self) -> None:
        """Stop the agent (compatibility method)."""
        await self.end_call("agent_stopped")

    async def get_docs(self, query: Any, params: Any = None) -> str:
        """
        Get documents from knowledge base.

        Args:
            query: Search query (string or dict)
            params: Optional function call params

        Returns:
            JSON string with results
        """
        if isinstance(query, dict):
            query_str = query.get("query", "")
        else:
            query_str = str(query)

        if not query_str:
            return json.dumps({"error": "Empty query"})

        try:
            await asyncio.wait_for(self._kb_ready.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            self._logger.warning("KB not ready, attempting query anyway")

        kb_manager = getattr(self, "_kb_manager", None)
        if kb_manager is None:
            return json.dumps({"error": "Knowledge base not initialized"})

        try:
            result = await kb_manager.get_docs(
                params=params,
                query=query_str,
                user_state=self.user_state,
            )
            return result
        except Exception as e:
            self._logger.error(f"KB query failed: {e}")
            return json.dumps({"error": str(e)})

    def get_plugin_metrics(self) -> Dict[str, dict]:
        """Get metrics from all plugins."""
        return self.plugins.get_all_metrics()

    def set_plugin_enabled(self, name: str, enabled: bool) -> bool:
        """Enable or disable a plugin at runtime."""
        return self.plugins.set_plugin_enabled(name, enabled)

    # -------------------------------------------------------------------------
    # Background Audio Methods
    # -------------------------------------------------------------------------

    async def _start_background_audio(
        self,
        room: Any,
        session: "AgentSession",
    ) -> None:
        """
        Start background audio player if configured.

        Background audio plays ambient sounds (office ambience) and thinking sounds
        (keyboard typing) to make the agent feel more realistic vs silence.

        Config options (under 'background_audio' key):
        - enabled: Enable/disable background audio (default: False)
        - ambient_sound: BuiltinAudioClip name or file path (default: OFFICE_AMBIENCE)
        - ambient_volume: Volume 0.0-1.0 (default: 0.8)
        - thinking_sound: BuiltinAudioClip name(s) or file path(s) (default: KEYBOARD_TYPING)
        - thinking_volume: Volume 0.0-1.0 (default: 0.7)

        Args:
            room: LiveKit Room instance
            session: AgentSession instance
        """
        try:
            # Check if background audio is available
            if BackgroundAudioPlayer is None:
                self._logger.debug("BackgroundAudioPlayer not available")
                return

            # Create background audio player via service factory
            self._background_audio = self.service_factory.create_background_audio()

            if self._background_audio is None:
                self._logger.debug("Background audio not enabled or failed to create")
                return

            # Start the background audio player
            await self._background_audio.start(room=room, agent_session=session)
            self._logger.info("Background audio started successfully")

        except Exception as e:
            self._logger.warning(f"Failed to start background audio: {e}")
            self._background_audio = None

    async def _stop_background_audio(self) -> None:
        """Stop background audio player if running."""
        if self._background_audio is None:
            return

        try:
            # Properly close the background audio player using aclose()
            # This cancels playback tasks, unpublishes track, and cleans up resources
            if hasattr(self._background_audio, "aclose"):
                await self._background_audio.aclose()
                self._logger.debug("Background audio stopped and closed via aclose()")
            else:
                self._logger.debug(
                    "Background audio player lacks aclose(), clearing reference"
                )
        except Exception as e:
            self._logger.warning(f"Error stopping background audio: {e}")
        finally:
            self._background_audio = None

    # -------------------------------------------------------------------------
    # Event Bridge Methods (for compatibility with LiteVoiceHandler interface)
    # -------------------------------------------------------------------------

    def set_event_bridge(self, event_bridge: Any) -> None:
        """
        Set LiveKit event bridge for transcript publishing and state management.

        Args:
            event_bridge: LiveKitEventBridge instance
        """
        self._event_bridge = event_bridge
        self._logger.info("Event bridge set")

    async def set_agent_state(self, state: str) -> bool:
        """
        Set agent state via event bridge.

        Valid states: "initializing", "listening", "thinking", "speaking"

        Args:
            state: New agent state

        Returns:
            True if state was updated
        """
        if hasattr(self, "_event_bridge") and self._event_bridge:
            return await self._event_bridge.set_agent_state(state)
        return False

    async def listening(self) -> None:
        """Set agent state to listening."""
        await self.set_agent_state("listening")

    async def thinking(self) -> None:
        """Set agent state to thinking."""
        await self.set_agent_state("thinking")

    async def speaking(self) -> None:
        """Set agent state to speaking."""
        await self.set_agent_state("speaking")

    async def initializing(self) -> None:
        """Set agent state to initializing."""
        await self.set_agent_state("initializing")

    async def _publish_transcript(
        self,
        role: str,
        content: str,
        is_final: bool = True,
    ) -> bool:
        """
        Publish transcript to LiveKit via event bridge.

        Args:
            role: Speaker role ("user" or "assistant")
            content: Transcript text
            is_final: Whether this is a final transcript

        Returns:
            True if published successfully
        """
        if not hasattr(self, "_event_bridge") or not self._event_bridge or not content:
            return False

        try:
            result = await self._event_bridge.emit_transcript(
                role=role,
                content=content,
                is_final=is_final,
            )
            return result is not None
        except Exception as e:
            self._logger.error(f"Transcript publish failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # Idle Timeout Monitoring
    # -------------------------------------------------------------------------

    def _reset_idle_timer(self) -> None:
        """Reset the idle timer on user or agent activity."""
        self._last_activity_time = time.time()
        self._idle_warning_count = 0
        self._logger.debug("[IDLE] Timer reset - activity detected")


    async def _start_idle_monitor(self) -> None:
        """Start the idle timeout monitoring task."""
        if self._idle_monitor_running:
            return

        self._idle_monitor_running = True
        self._last_activity_time = time.time()
        self._idle_warning_count = 0

        self._logger.info(
            f"[IDLE] Starting idle monitor (timeout={self._idle_timeout_seconds}s)"
        )

        self._idle_monitor_task = asyncio.create_task(self._idle_monitor_loop())

    async def _stop_idle_monitor(self) -> None:
        """Stop the idle timeout monitoring task."""
        self._idle_monitor_running = False
        if self._idle_monitor_task:
            self._idle_monitor_task.cancel()
            try:
                await self._idle_monitor_task
            except asyncio.CancelledError:
                pass
            self._idle_monitor_task = None
        self._logger.debug("[IDLE] Idle monitor stopped")

    async def _idle_monitor_loop(self) -> None:
        """Background task to monitor user idle time."""
        try:
            while self._idle_monitor_running and not self._is_shutting_down:
                await asyncio.sleep(0.5)  # Check every 500ms

                # Skip idle checks while agent is speaking or thinking
                if self._agent_state in ("speaking", "thinking"):
                    continue

                idle_duration = time.time() - self._last_activity_time

                # First warning at 50% of timeout (15s for 30s timeout)
                if (
                    idle_duration >= self._idle_warning_1_seconds
                    and self._idle_warning_count == 0
                ):
                    self._idle_warning_count = 1
                    await self._send_idle_warning(1)

                # Second warning at 83% of timeout (25s for 30s timeout)
                elif (
                    idle_duration >= self._idle_warning_2_seconds
                    and self._idle_warning_count == 1
                ):
                    self._idle_warning_count = 2
                    await self._send_idle_warning(2)

                # Disconnect at full timeout (30s)
                elif (
                    idle_duration >= self._idle_timeout_seconds
                    and self._idle_warning_count >= 2
                ):
                    self._logger.info(
                        f"[IDLE] User idle for {idle_duration:.1f}s, disconnecting"
                    )
                    await self._handle_idle_disconnect()
                    break

        except asyncio.CancelledError:
            self._logger.debug("[IDLE] Monitor task cancelled")
        except Exception as e:
            self._logger.error(f"[IDLE] Monitor error: {e}")

    async def _send_idle_warning(self, warning_number: int) -> None:
        """Send idle warning to user via agent speech."""
        if not self._session:
            return

        # Get user language from config
        user_language = self.config.get("preferred_language", "en") if self.config else "en"

        # Get localized warning message
        param = f"idle_warning_{warning_number}"
        warning_msg = self.prompt_manager.get_message(user_language, param)
        if not warning_msg:
            # Fallback to English
            warning_msg = self.prompt_manager.get_message("en", param)

        self._logger.info(f"[IDLE] Sending warning {warning_number}: {warning_msg}")

        try:
            self._sending_idle_warning = True
            # In full realtime mode, TTS is not available - use generate_reply instead
            if self._is_full_realtime:
                await self._session.generate_reply(
                    instructions=f"Say to the user: {warning_msg}"
                )
            else:
                await self._session.say(warning_msg)
        except Exception as e:
            self._logger.error(f"[IDLE] Failed to send warning: {e}")
        finally:
            self._sending_idle_warning = False

    async def _handle_idle_disconnect(self) -> None:
        """Handle disconnect due to user inactivity - delete room to end call."""
        if self._is_shutting_down:
            return

        self._is_shutting_down = True
        self._logger.info("[IDLE] Disconnecting due to user inactivity")

        if not isinstance(self.user_state.extra_data, dict):
            self.user_state.extra_data = {}

        if self.user_state.extra_data.get("call_type") != "sdk":
            self.user_state.call_status = CallStatusEnum.COMPLETED
            self.user_state.end_time = datetime.utcnow()

            res = await build_call_result(self.user_state)
            await trigger_post_call(user_state=self.user_state, res=res)

            self._logger.info(
                f"{'=' * 100}\n\n[END_CALL_TOOL]  Triggering post call \n\n{'=' * 100}"
            )

        # Send goodbye message
        if self._session:
            try:
                goodbye_msg = "No response detected. Goodbye! Have a great day."
                await self._session.generate_reply(instructions=goodbye_msg)
                # Brief delay for TTS to complete
                await asyncio.sleep(2.0)
            except Exception as e:
                self._logger.error(f"[IDLE] Failed to send goodbye: {e}")

        # Delete the room to properly end the call
        if self._job_context and hasattr(self._job_context, "room"):
            room_name = self._job_context.room.name
            try:
                from livekit import api

                self._logger.info(f"[IDLE] Deleting room: {room_name}")
                await self._job_context.api.room.delete_room(
                    api.DeleteRoomRequest(room=room_name)
                )
                self._logger.info(f"[IDLE] Room deleted successfully: {room_name}")
            except Exception as e:
                self._logger.error(f"[IDLE] Failed to delete room: {e}")
                await self.end_call("idle_timeout")
        else:
            await self.end_call("idle_timeout")

    # -------------------------------------------------------------------------
    # Goodbye Detection (Deprecated - now handled by end_call tool)
    # -------------------------------------------------------------------------

    # NOTE: Goodbye detection is now primarily handled by the end_call tool,
    # which allows the LLM to decide based on conversation context.
    # These patterns are kept as a minimal safety fallback but are no longer
    # actively called from event handlers.
    #
    # Removed ambiguous patterns that caused false positives:
    # - "okay", "ok" - common acknowledgments
    # - "that's it", "that's all", "done" - too context-dependent
    GOODBYE_PATTERNS = [
        "bye",
        "goodbye",
        "good bye",
        "bye-bye",
        "bye bye",
        "ok bye",
        "okay bye",
        "see you",
        "take care",
        "hang up",
        "end call",
        "disconnect",
        # Hindi/Urdu
        "alvida",
        "phir milenge",
        "theek hai bye",
        "chalo bye",
        # Combined farewells
        "thank you bye",
        "thanks bye",
        "thankyou bye",
    ]

    def _is_goodbye_intent(self, transcript: str) -> bool:
        """Check if transcript contains goodbye intent.

        NOTE: This method is deprecated. Goodbye detection is now handled
        by the end_call tool which has full conversation context.
        """
        transcript_lower = transcript.lower().strip()
        # Remove common punctuation for matching
        transcript_clean = transcript_lower.rstrip("!.,?")

        self._logger.debug(f"[GOODBYE_CHECK] Checking transcript: '{transcript_lower}'")

        for pattern in self.GOODBYE_PATTERNS:
            # Exact match
            if transcript_lower == pattern or transcript_clean == pattern:
                self._logger.info(f"[GOODBYE_CHECK] Matched pattern: '{pattern}'")
                return True
            # Starts with pattern
            if transcript_lower.startswith(
                f"{pattern} "
            ) or transcript_clean.startswith(f"{pattern} "):
                self._logger.info(f"[GOODBYE_CHECK] Starts with pattern: '{pattern}'")
                return True
            # Ends with "bye" (catch phrases like "okay bye", "alright bye", etc.)
            if transcript_lower.endswith(" bye") or transcript_clean.endswith(" bye"):
                self._logger.info(
                    f"[GOODBYE_CHECK] Ends with 'bye': '{transcript_lower}'"
                )
                return True

        return False

    async def _handle_goodbye_intent(self) -> None:
        """Handle goodbye intent - say goodbye and delete room to end session."""
        if self._is_shutting_down:
            return

        self._is_shutting_down = True
        self._logger.info("[GOODBYE] Handling goodbye intent, ending session")

        # Stop idle monitor
        await self._stop_idle_monitor()

        # Interrupt any ongoing agent generation first
        if self._session:
            try:
                # Interrupt current generation to stop agent from speaking
                self._session.interrupt()
                self._logger.info("[GOODBYE] Interrupted current agent generation")
                await asyncio.sleep(0.5)  # Brief pause for interrupt to take effect
            except Exception as e:
                self._logger.debug(
                    f"[GOODBYE] Interrupt failed (may not be speaking): {e}"
                )

        # Say goodbye via TTS
        if self._session:
            try:
                goodbye_msg = "Thank you for your time. Goodbye! Have a great day."
                await self._session.generate_reply(instructions=goodbye_msg)
                # Brief delay for TTS to complete
                await asyncio.sleep(2.0)
            except Exception as e:
                self._logger.error(f"[GOODBYE] Failed to send goodbye: {e}")

        # Delete the room to properly end the call (disconnects all participants)
        if self._job_context and hasattr(self._job_context, "room"):
            room_name = self._job_context.room.name
            try:
                from livekit import api

                self._logger.info(f"[GOODBYE] Deleting room: {room_name}")
                await self._job_context.api.room.delete_room(
                    api.DeleteRoomRequest(room=room_name)
                )
                self._logger.info(f"[GOODBYE] Room deleted successfully: {room_name}")
            except Exception as e:
                self._logger.error(f"[GOODBYE] Failed to delete room: {e}")
                # Fallback to regular end_call
                await self.end_call("user_goodbye")
        else:
            # Fallback if no job context
            await self.end_call("user_goodbye")

    async def _handle_tool_end_call(self, reason: str = "user_goodbye") -> None:
        """Handle end_call tool invocation - end session gracefully.

        The LLM will say goodbye naturally as part of its response.
        We wait for the participant to leave or remove them, then delete the room.
        """
        if self._is_shutting_down:
            return

        self._is_shutting_down = True
        self._logger.info(f"[END_CALL_TOOL] Ending session, reason: {reason}")

        # Stop idle monitor
        await self._stop_idle_monitor()

        # Schedule graceful room cleanup
        async def _graceful_room_cleanup():
            from livekit import api

            room = self._job_context.room if self._job_context else None
            if not room:
                await self.end_call(reason)
                return

            room_name = room.name

            # Step 1: Wait 2 seconds for TTS to start
            await asyncio.sleep(2.0)

            # Step 2: Remove all participants immediately
            if room.remote_participants:
                self._logger.info(
                    f"[END_CALL_TOOL] Removing {len(room.remote_participants)} participant(s)"
                )
                try:
                    for identity in list(room.remote_participants.keys()):
                        await self._job_context.api.room.remove_participant(
                            api.RoomParticipantIdentity(
                                room=room_name, identity=identity
                            )
                        )
                        self._logger.info(
                            f"[END_CALL_TOOL] Removed participant: {identity}"
                        )
                except Exception as e:
                    self._logger.warning(
                        f"[END_CALL_TOOL] Failed to remove participant: {e}"
                    )

            # Step 3: Wait 5 seconds before deleting room
            await asyncio.sleep(5.0)

            # Step 4: Delete the room
            try:
                self._logger.info(f"[END_CALL_TOOL] Deleting room: {room_name}")
                await self._job_context.api.room.delete_room(
                    api.DeleteRoomRequest(room=room_name)
                )
                self._logger.info(
                    f"[END_CALL_TOOL] Room deleted successfully: {room_name}"
                )
            except Exception as e:
                self._logger.error(f"[END_CALL_TOOL] Failed to delete room: {e}")
                await self.end_call(reason)

        asyncio.create_task(_graceful_room_cleanup())

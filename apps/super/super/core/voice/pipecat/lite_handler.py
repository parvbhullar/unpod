"""
Lite Voice Handler - Minimal, plugin-based voice processing.

A lightweight alternative to PipecatVoiceHandler that reduces startup time
from 2-3 seconds to <500ms through lazy loading and plugin architecture.

Key differences from PipecatVoiceHandler:
- Services created on-demand, not at startup
- KB preloading happens in background after first response
- Optional features loaded as plugins
- Simpler linear pipeline (no complex ParallelPipeline by default)
"""

import asyncio
import json
import logging
import os
from abc import ABC
from datetime import datetime
from typing import Any, Dict, List, Optional

from pipecat.frames.frames import (
    EndFrame,
    LLMMessagesAppendFrame,
    TTSSpeakFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.parallel_pipeline import ParallelPipeline
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.transcript_processor import TranscriptProcessor
from pipecat.transports.base_transport import BaseTransport

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
from super.core.voice.plugins.base import PluginPriority
from super.core.voice.managers.prompt_manager import PromptManager
from super.core.voice.schema import AgentConfig, CallSession, TransportType, UserState
from super.core.voice.services.lazy_factory import LazyServiceFactory
from super.core.voice.services.service_common import is_realtime_model
from super.core.voice.managers.transport_manager import TransportManager
from super.core.voice.pipecat.utils import UpPipelineRunner, create_usage
from super.core.voice.livekit.state_observer import (
    LiveKitStateObserver,
    create_livekit_state_observer,
)


class LiteVoiceHandler(BaseVoiceHandler, ABC):
    """
    Lightweight voice handler with plugin-based architecture.

    Optimized for fast startup (<500ms) while maintaining full functionality
    through lazy loading and modular plugins.

    Features:
    - Lazy service initialization (STT/LLM/TTS created on-demand)
    - Plugin system for optional features (RAG, streaming, silence trimming)
    - Background KB preloading (doesn't block first response)
    - Simplified pipeline construction
    """

    default_configuration = HandlerConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.voice.lite_handler.LiteVoiceHandler",
        ),
        role=RoleConfiguration(
            name="lite_voice_handler",
            role="A lightweight handler for voice conversations.",
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
            logger=logger or app_logging.get_logger("lite.voice.handler"),
        )

        self._session_id = session_id or (
            str(user_state.thread_id) if user_state else None
        )
        self._callback = callback
        self._logger = logger or app_logging.get_logger("lite.voice.handler")
        self._configuration = configuration

        # User state and config
        self.user_state = user_state
        self.config = model_config or (user_state.model_config if user_state else {})

        # Realtime mode configuration
        # use_realtime: Enable OpenAI Realtime API or Gemini Live
        # mixed_realtime_mode: Use Realtime LLM but separate TTS (text output)
        self.use_realtime = False
        self.mixed_realtime_mode = False

        # Transport
        self._transport_type = os.getenv("HANDLER_TRANSPORT", TransportType.LIVEKIT)
        self._transport: Optional[BaseTransport] = None
        self._room_name: Optional[str] = None

        # Observer for metrics
        self.observer = observer

        # Agent config
        self.agent_config = AgentConfig(
            agent_name=session_id or "LiteVoiceAgent",
            model_config=model_config,
        )

        # Plugin registry - manages optional features
        self.plugins = PluginRegistry(logger=self._logger.getChild("plugins"))

        # Lazy service factory - creates services on-demand
        self.services: Optional[LazyServiceFactory] = None

        # Prompt manager - initialized lazily
        self._prompt_manager: Optional[PromptManager] = None

        # Transport manager
        self._transport_manager: Optional[TransportManager] = None

        # Pipeline components
        self.task: Optional[PipelineTask] = None
        self.runner: Optional[UpPipelineRunner] = None
        self._context_aggregator: Optional[Any] = None

        # Session tracking
        self.active_sessions: Dict[str, CallSession] = {}

        # State flags
        self._is_shutting_down = False
        self._services_initialized = False
        self._first_response_sent = asyncio.Event()
        self._kb_ready = asyncio.Event()

        # Agent/user references for callbacks
        self.agent: Optional[User] = None

        # Event bridge for LiveKit transcript publishing
        self._event_bridge: Optional[Any] = None

        # LiveKit state observer for agent state tracking
        self._livekit_state_observer: Optional[LiveKitStateObserver] = None

        self._logger.info(f"LiteVoiceHandler created (session={self._session_id})")

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
    def transport_manager(self) -> TransportManager:
        """Lazy-initialized transport manager."""
        if self._transport_manager is None:
            self._transport_manager = TransportManager(
                logger=self._logger.getChild("transport"),
                config=self.config,
                user_state=self.user_state,
                room_name=self._room_name,
                transport_type=self._transport_type,
                task=self.task,
                active_sessions=self.active_sessions,
                end_call_callback=self.end_call,
            )
        return self._transport_manager

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

    def set_realtime_fields(self) -> None:
        """
        Determine realtime mode using priority chain:
        1. Database flag (llm_realtime) - source of truth
        2. Model name detection (LLM_REALTIME_MODELS list)

        Env var MIXED_REALTIME_MODE only affects mixed mode, not realtime detection.
        """
        # Priority 1: Database flag (source of truth)
        if self.config.get("llm_realtime"):
            self.use_realtime = True
            self._logger.info(
                "Realtime mode enabled via database flag (llm_realtime=True)"
            )
        # Priority 2: Model name detection
        elif is_realtime_model(self.config.get("llm_model", "")):
            self.use_realtime = True
            self._logger.info(
                f"Realtime mode enabled via model detection: {self.config.get('llm_model')}"
            )
        else:
            self.use_realtime = False

        # Mixed mode from env only (for text output with separate TTS)
        if self.use_realtime:
            self.mixed_realtime_mode = self.config.get(
                "mixed_realtime_mode",
                os.getenv("MIXED_REALTIME_MODE", "false").lower() == "true",
            )
        else:
            self.mixed_realtime_mode = False

        self._logger.info(
            f"Realtime mode: use_realtime={self.use_realtime}, "
            f"mixed_realtime_mode={self.mixed_realtime_mode}"
        )

    async def preload_agent(
        self,
        user_state: UserState,
        observer: Optional[Any] = None,
    ) -> bool:
        """
        Minimal preload - only essential initialization.

        Target: <200ms (vs 2-3s for PipecatVoiceHandler)

        Args:
            user_state: User state for the session
            observer: Optional observer for metrics

        Returns:
            True if preload successful
        """
        import time
        from super.core.voice.common.common import add_perf_log

        start_time = time.time()
        self._logger.info("Starting lite preload...")

        try:
            # Update state
            self.user_state = user_state
            self.config = user_state.model_config or self.config
            self._room_name = user_state.room_name
            self.observer = observer

            # Determine realtime mode from DB flag or model name
            self.set_realtime_fields()

            # Create users
            self._add_users()

            # Initialize lazy service factory with realtime mode settings
            _factory_start = time.time()
            service_config = self.config.copy() if self.config else {}
            service_config["use_realtime"] = self.use_realtime
            service_config["mixed_realtime_mode"] = self.mixed_realtime_mode

            # For realtime mode, create assistant prompt for LLM initialization
            assistant_prompt = None
            if self.use_realtime:
                llm_provider = self.config.get("llm_provider", "openai").lower()
                if llm_provider in ["openai", "google"]:
                    assistant_prompt = self.prompt_manager._create_assistant_prompt()
                    self._logger.info(
                        f"Created assistant prompt for {llm_provider.upper()} "
                        "Realtime API"
                    )

            self.services = LazyServiceFactory(
                config=service_config,
                logger=self._logger.getChild("services"),
                get_docs_callback=self.get_docs,
                assistant_prompt=assistant_prompt,
            )
            add_perf_log(
                user_state,
                "service_factory_init",
                (time.time() - _factory_start) * 1000,
            )

            # Get transport (required before pipeline)
            _transport_start = time.time()
            self._transport = await self.get_transport()
            add_perf_log(
                user_state, "transport_init", (time.time() - _transport_start) * 1000
            )

            # Start STT preload in background (only for standard mode)
            # In realtime mode, the realtime LLM handles audio input directly
            if not self.use_realtime:
                _stt_start = time.time()
                await self.services.preload_stt()
                add_perf_log(
                    user_state, "stt_preload", (time.time() - _stt_start) * 1000
                )
            else:
                self._logger.info(
                    "Skipping STT preload (realtime mode handles audio input)"
                )

            # Activate plugins from config
            _plugins_start = time.time()
            await self.plugins.activate_from_config(self, self.config)
            add_perf_log(
                user_state, "plugins_activation", (time.time() - _plugins_start) * 1000
            )

            # Start background KB warmup (non-blocking)
            if self._kb_enabled():
                asyncio.create_task(
                    self._background_kb_warmup(),
                    name=f"{self._session_id}-kb-warmup",
                )

            self._services_initialized = True
            elapsed = (time.time() - start_time) * 1000
            add_perf_log(user_state, "lite_preload_total", elapsed)
            self._logger.info(f"Lite preload complete in {elapsed:.0f}ms")
            return True

        except Exception as e:
            self._logger.error(f"Preload failed: {e}")
            return False

    def _kb_enabled(self) -> bool:
        """Check if knowledge base is configured."""
        if not self.config:
            return False
        return bool(self.config.get("knowledge_base"))

    async def _background_kb_warmup(self) -> None:
        """Warm up KB in background after first response."""
        try:
            # Wait for first response to be sent
            await asyncio.wait_for(
                self._first_response_sent.wait(),
                timeout=30.0,
            )

            # Small delay to not compete with response
            await asyncio.sleep(0.5)

            # Initialize KB manager if available
            if self._kb_enabled():
                from super.core.voice.managers.knowledge_base import (
                    KnowledgeBaseManager,
                )

                kb_manager = KnowledgeBaseManager(
                    logger=self._logger.getChild("kb"),
                    session_id=self._session_id,
                    user_state=self.user_state,
                    config=self.config,
                )
                await kb_manager._preload_knowledge_base_documents(self.user_state)
                self._kb_manager = kb_manager
                self._kb_ready.set()
                self._logger.info("Background KB warmup complete")

        except asyncio.TimeoutError:
            self._logger.warning("KB warmup timeout - first response not sent")
        except Exception as e:
            self._logger.warning(f"KB warmup failed: {e}")
            self._kb_ready.set()  # Set anyway to unblock waiters

    async def execute(self, *args, **kwargs) -> Any:
        """Execute the voice handler pipeline."""
        try:
            self._logger.info(f"Starting lite pipeline for {self.user_state.user_name}")

            if not self._transport:
                self._transport = await self.get_transport()

            # Create pipeline
            pipeline, context_aggregator = await self._create_pipeline(self._transport)
            self._context_aggregator = context_aggregator

            # Create observers
            observers = []
            if self.observer:
                observers.append(self.observer(user_state=self.user_state))

            # Add LiveKit state observer for agent state tracking
            # emit_transcripts=False because transcripts are handled via event bridge
            self._livekit_state_observer = create_livekit_state_observer(
                user_state=self.user_state,
                transport=self._transport,
                logger=self._logger.getChild("livekit.state"),
                emit_transcripts=False,
            )
            observers.append(self._livekit_state_observer)

            # Create pipeline task
            self.task = PipelineTask(
                pipeline,
                params=PipelineParams(
                    enable_metrics=True,
                    enable_usage_metrics=True,
                    audio_in_sample_rate=self.config.get("audio_in_sample_rate", 16000),
                    audio_out_sample_rate=self.config.get(
                        "audio_out_sample_rate", 24000
                    ),
                ),
                observers=observers,
            )

            # Update transport manager with task
            self.transport_manager.set_task(self.task)

            # Set up transport event handlers
            await self._setup_transport_events()

            # Run pipeline
            self.runner = UpPipelineRunner()
            await self.runner.run(self.task)

        except Exception as e:
            self._logger.error(f"Pipeline error: {e}")
            raise

    async def _create_pipeline(self, transport: BaseTransport) -> tuple:
        """
        Create pipeline with plugin processors and parallel transcript tracking.

        Supports three modes:
        - Standard mode: STT → LLM → TTS pipeline
        - Full Realtime mode: Realtime LLM with integrated audio (no STT/TTS)
        - Mixed Realtime mode: Realtime LLM (text output) → separate TTS

        Returns:
            Tuple of (pipeline, context_aggregator)
        """
        # Determine pipeline mode
        is_realtime_mode = self.use_realtime
        is_mixed_mode = self.mixed_realtime_mode

        # Log pipeline mode
        if is_realtime_mode and is_mixed_mode:
            self._logger.info(
                "🔀 Mixed Realtime Pipeline: Realtime LLM (text) → Separate TTS"
            )
        elif is_realtime_mode:
            self._logger.info(
                "⚡ Full Realtime Pipeline: Realtime LLM (integrated audio)"
            )
        else:
            self._logger.info("🔧 Standard Pipeline: STT → LLM → TTS")

        # Get services based on mode
        stt = None
        tts = None
        llm = await self.services.get_llm()

        if is_realtime_mode and not is_mixed_mode:
            # Full realtime: Only LLM (integrated STT/TTS)
            self._logger.info("Full realtime: Using only LLM (integrated audio)")
        elif is_realtime_mode and is_mixed_mode:
            # Mixed realtime: LLM + TTS (Realtime handles STT)
            tts = await self.services.get_tts()
            self._logger.info("Mixed realtime: Using LLM + TTS (no STT)")
        else:
            # Standard mode: All three services
            stt = await self.services.get_stt()
            tts = await self.services.get_tts()
            self._logger.info("Standard mode: Using STT + LLM + TTS")

        # Validate required services based on mode
        if not llm:
            raise Exception(
                "LLM service could not be created - missing API keys or unavailable"
            )

        if is_realtime_mode and not is_mixed_mode:
            self._logger.info(
                "✓ Full realtime mode: LLM service validated (STT/TTS integrated)"
            )
        elif is_realtime_mode and is_mixed_mode:
            if not tts:
                raise Exception(
                    "Mixed realtime mode: TTS service required but could not be created"
                )
            self._logger.info("✓ Mixed realtime mode: LLM + TTS services validated")
        else:
            if not stt:
                raise Exception(
                    "Standard mode: STT service required but could not be created"
                )
            if not tts:
                raise Exception(
                    "Standard mode: TTS service required but could not be created"
                )
            self._logger.info("✓ Standard mode: All services (STT/LLM/TTS) validated")

        # Create context
        context = self._create_context()
        context_aggregator = await self.services.get_context_aggregator(
            context,
            aggregation_timeout=self.config.get("context_aggregation_timeout", 0.05),
        )

        # Create transcript processor
        transcript = TranscriptProcessor()
        self._setup_transcript_handler(transcript)

        # Build pipeline stages based on mode
        stages: List[Any] = []

        # Input from transport (always needed)
        stages.append(transport.input())

        if is_realtime_mode and not is_mixed_mode:
            # Full Realtime Pipeline: transport.input → realtime_llm → transport.output
            # The realtime LLM handles audio input/output directly
            stages.append(
                ParallelPipeline(
                    [context_aggregator.user(), llm],
                    [transcript.user()],
                )
            )
            # Output with parallel transcript
            stages.append(
                ParallelPipeline(
                    [transport.output(), context_aggregator.assistant()],
                    [transcript.assistant()],
                )
            )
        elif is_realtime_mode and is_mixed_mode:
            # Mixed Realtime Pipeline: transport.input → realtime_llm → tts → transport.output
            # Realtime LLM outputs text, separate TTS generates audio

            # PRE_LLM plugins
            stages.extend(
                self.plugins.get_processors_at_priority(PluginPriority.PRE_LLM)
            )

            # User processing with parallel transcript
            stages.append(
                ParallelPipeline(
                    [context_aggregator.user(), llm],
                    [transcript.user()],
                )
            )

            # POST_LLM plugins
            stages.extend(
                self.plugins.get_processors_at_priority(PluginPriority.POST_LLM)
            )

            # PRE_TTS plugins
            stages.extend(
                self.plugins.get_processors_at_priority(PluginPriority.PRE_TTS)
            )

            # TTS
            stages.append(tts)

            # POST_TTS plugins
            stages.extend(
                self.plugins.get_processors_at_priority(PluginPriority.POST_TTS)
            )

            # Output with parallel transcript
            stages.append(
                ParallelPipeline(
                    [transport.output(), context_aggregator.assistant()],
                    [transcript.assistant()],
                )
            )
        else:
            # Standard Pipeline: STT → LLM → TTS
            # STT (Speech-to-Text)
            stages.append(stt)

            # PRE_LLM plugins (e.g., RAG context enrichment)
            stages.extend(
                self.plugins.get_processors_at_priority(PluginPriority.PRE_LLM)
            )

            # User processing with parallel transcript tracking
            stages.append(
                ParallelPipeline(
                    [context_aggregator.user(), llm],
                    [transcript.user()],
                )
            )

            # POST_LLM plugins (e.g., streaming parser for early TTS)
            stages.extend(
                self.plugins.get_processors_at_priority(PluginPriority.POST_LLM)
            )

            # PRE_TTS plugins
            stages.extend(
                self.plugins.get_processors_at_priority(PluginPriority.PRE_TTS)
            )

            # TTS (Text-to-Speech)
            stages.append(tts)

            # POST_TTS plugins (e.g., silence trimmer)
            stages.extend(
                self.plugins.get_processors_at_priority(PluginPriority.POST_TTS)
            )

            # Output processing with parallel transcript tracking
            stages.append(
                ParallelPipeline(
                    [transport.output(), context_aggregator.assistant()],
                    [transcript.assistant()],
                )
            )

        pipeline = Pipeline(stages)

        # Log final pipeline configuration
        if is_realtime_mode and is_mixed_mode:
            mode_name = "Mixed Realtime"
        elif is_realtime_mode:
            mode_name = "Full Realtime"
        else:
            mode_name = "Standard"

        self._logger.info(
            f"✅ Pipeline created with {len(stages)} stages ({mode_name} mode)"
        )

        return pipeline, context_aggregator

    def _create_context(self) -> OpenAILLMContext:
        """Create LLM context with system prompt."""
        system_prompt = self.prompt_manager._create_assistant_prompt()

        messages = [{"role": "system", "content": system_prompt}]

        # Add tools if enabled
        tools = []
        if self.config.get("tool_calling", True) and self._kb_enabled():
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": "get_knowledge_base_info",
                        "description": "Get relevant information from the knowledge base",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                }
            )

        return OpenAILLMContext(messages=messages, tools=tools if tools else None)

    def _setup_transcript_handler(self, transcript: TranscriptProcessor) -> None:
        """Set up transcript event handler."""

        @transcript.event_handler("on_transcript_update")
        async def handle_update(processor, frame):
            for message in frame.messages:
                # Store transcript
                entry = {
                    "role": message.role,
                    "content": message.content,
                    "timestamp": str(datetime.now()),
                }
                self.user_state.transcript.append(entry)

                # Send callback
                if message.role == "user":
                    msg = Message.create(
                        message.content,
                        user=self.user_state.user,
                        event=Event.USER_MESSAGE,
                    )
                    self._send_callback(msg, thread_id=str(self.user_state.thread_id))

                    # Notify plugins
                    await self.plugins.broadcast_event(
                        "on_user_speech", message.content
                    )

                elif message.role == "assistant":
                    msg = Message.create(
                        message.content,
                        user=self.agent,
                        event=Event.AGENT_MESSAGE,
                    )
                    self._send_callback(msg, thread_id=str(self.user_state.thread_id))

                    # Signal first response sent
                    if not self._first_response_sent.is_set():
                        self._first_response_sent.set()

                    # Notify plugins
                    await self.plugins.broadcast_event(
                        "on_agent_speech", message.content
                    )

                # Publish to LiveKit via native API and/or event bridge
                await self._publish_livekit_transcript(
                    role=message.role,
                    content=message.content,
                    is_final=True,
                )
                # Also emit via event bridge if available
                if self._event_bridge:
                    await self._publish_transcript(message.role, message.content)

    async def _setup_transport_events(self) -> None:
        """Set up transport event handlers."""

        @self._transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant_id):
            self._logger.info(f"Participant {participant_id} joined")
            self.user_state.start_time = datetime.now()

            # Notify plugins
            await self.plugins.broadcast_event("on_call_start")

            # Send first message
            first_message = self.config.get(
                "first_message",
                "Hello! How can I help you today?",
            )
            first_message = self.prompt_manager._replace_template_params(first_message)
            await self.task.queue_frame(TTSSpeakFrame(first_message))

            # Load previous chat context if available
            await self._load_chat_context()

            # Send start callback
            msg = Message.create(
                "CALL STARTED",
                role="system",
                event=Event.TASK_START,
            )
            self._send_callback(msg, thread_id=str(self.user_state.thread_id))

        @self._transport.event_handler("on_participant_disconnected")
        async def on_participant_disconnected(transport, participant_id):
            self._logger.info(f"Participant {participant_id} disconnected")

            # CRITICAL: Shutdown state observer IMMEDIATELY to prevent Rust SDK panics
            # The LiveKit Rust SDK can panic if we try to update participant attributes
            # while the room connection is being torn down
            if self._livekit_state_observer:
                self._livekit_state_observer.shutdown()

            self.user_state.end_time = datetime.now()
            self.user_state.end_reason = "Customer Ended The Call"

            # Notify plugins
            await self.plugins.broadcast_event("on_call_end")

            # Send end callback
            msg = Message.create(
                "CALL ENDED",
                role="system",
                event=Event.TASK_END,
            )
            self._send_callback(msg, thread_id=str(self.user_state.thread_id))

            # Stop pipeline
            await self.task.queue_frame(EndFrame())

    async def _load_chat_context(self) -> None:
        """
        Load previous chat context into the LLM context if available.

        Extracts chat context from user_state.extra_data or config and appends
        it to the LLM context as a system message with previous conversation history.
        """
        try:
            chat_context_data = None

            # Try to get chat context from user_state.extra_data
            if self.user_state and self.user_state.extra_data:
                if isinstance(self.user_state.extra_data, dict):
                    chat_context_data = (
                        self.user_state.extra_data.get("data", {})
                        .get("pre_call_result", {})
                        .get("chat_context")
                    )
                elif isinstance(self.user_state.extra_data, str):
                    chat_context_data = self.user_state.extra_data

            # Fallback to config if not found in extra_data
            if not chat_context_data and self.config:
                chat_context_data = self.config.get("chat_context")

            if not chat_context_data:
                self._logger.debug("No previous chat context to load")
                return

            self._logger.info("Loading previous chat context into LLM context")

            # Append chat context as a system message
            system_message = {
                "role": "system",
                "content": f"\n[previous conversations with user]\n{chat_context_data}",
            }

            if self.task:
                await self.task.queue_frame(
                    LLMMessagesAppendFrame([system_message], run_llm=False)
                )
                self._logger.info("Previous chat context loaded successfully")

        except Exception as e:
            self._logger.warning(f"Failed to load previous chat context: {e}")

    async def get_transport(self) -> BaseTransport:
        """Get transport instance."""
        return await self.transport_manager.get_transport()

    async def get_docs(self, query: Any, params: Any = None) -> str:
        """
        Get documents from knowledge base.

        Args:
            query: Search query (string or dict)
            params: Optional function call params

        Returns:
            JSON string with results
        """
        # Handle dict or string query
        if isinstance(query, dict):
            query_str = query.get("query", "")
        else:
            query_str = str(query)

        if not query_str:
            return json.dumps({"error": "Empty query"})

        # Wait for KB to be ready (with timeout)
        try:
            await asyncio.wait_for(self._kb_ready.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            self._logger.warning("KB not ready, attempting query anyway")

        # Get KB manager
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

    async def end_call(self, reason: str = "completed") -> str:
        """End the current call gracefully."""
        self._logger.info(f"Ending call: {reason}")
        self._is_shutting_down = True

        try:
            # Shutdown state observer FIRST to prevent Rust SDK panics
            # during room disconnection
            if self._livekit_state_observer:
                self._livekit_state_observer.shutdown()

            # Clean up plugins
            await self.plugins.cleanup_all()

            # Clean up services
            if self.services:
                await self.services.cleanup()

            # Stop pipeline
            if self.task:
                await self.task.queue_frame(EndFrame())
                await asyncio.sleep(0.5)

            # Clean up transport
            if self._transport:
                if hasattr(self._transport, "disconnect"):
                    await self._transport.disconnect()
                self._transport = None

            self._logger.info("Call ended successfully")
            return f"Call ended: {reason}"

        except Exception as e:
            self._logger.error(f"Error ending call: {e}")
            return f"Error: {e}"

    async def end_ongoing_agent(self) -> None:
        """Stop the agent (compatibility method)."""
        await self.end_call("agent_stopped")

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
        if self._event_bridge:
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

    def set_streaming_parser_enabled(self, enabled: bool) -> bool:
        """Enable or disable the streaming text parser at runtime.

        The streaming parser enables TTS to start while LLM is still generating,
        reducing latency by 500-1500ms.

        Args:
            enabled: Whether to enable streaming parsing.

        Returns:
            True if the plugin was found and updated, False otherwise.
        """
        result = self.plugins.set_plugin_enabled("streaming", enabled)
        if result:
            self._logger.info(
                f"Streaming parser {'enabled' if enabled else 'disabled'}"
            )
        return result

    def get_streaming_parser_metrics(self) -> Optional[dict]:
        """Get metrics from the streaming text parser.

        Returns:
            Dict with metrics (chunk_count, ttfc, etc.) or None if not available.
        """
        plugin = self.plugins.get_plugin("streaming")
        if plugin:
            return plugin.get_metrics()
        return None

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
        if not self._event_bridge or not content:
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

    async def _publish_livekit_transcript(
        self,
        role: str,
        content: str,
        is_final: bool = True,
    ) -> bool:
        """
        Publish transcript via native LiveKit transcription API.

        Uses participant.publish_transcription() which the frontend
        useVoiceAssistant hook automatically handles.

        Args:
            role: Speaker role ("user" or "assistant")
            content: Transcript text
            is_final: Whether this is a final transcript

        Returns:
            True if published successfully
        """
        if not content:
            return False

        try:
            # Get participant from state observer or job context
            participant = None

            if self._livekit_state_observer:
                participant = self._livekit_state_observer._get_participant()

            if not participant:
                # Try job context directly
                try:
                    from livekit.agents import get_job_context

                    ctx = get_job_context()
                    if ctx and ctx.room:
                        participant = ctx.room.local_participant
                except Exception:
                    pass

            if not participant:
                self._logger.debug("No participant for LiveKit transcript publish")
                return False

            from livekit import rtc

            # Generate transcript ID
            transcript_id = getattr(self, "_lk_transcript_id", 0) + 1
            self._lk_transcript_id = transcript_id

            segment = rtc.TranscriptionSegment(
                id=f"{role}-{transcript_id}",
                text=content,
                start_time=0,
                end_time=0,
                language="en",
                final=is_final,
            )

            transcription = rtc.Transcription(
                participant_identity=participant.identity,
                track_sid="",
                segments=[segment],
            )

            await participant.publish_transcription(transcription)
            self._logger.debug(f"LiveKit transcript published: {role}")
            return True

        except Exception as e:
            self._logger.error(f"LiveKit transcript publish failed: {e}")
            return False

    def _send_callback(self, message: Message, thread_id: str) -> None:
        """Send message through callback."""
        if self._callback:
            self._callback.send(message, thread_id=thread_id)

    def message_callback(
        self,
        transcribed_text: str,
        role: str,
        user_state: UserState,
    ) -> None:
        """Handle message callbacks (compatibility method)."""
        thread_id = str(user_state.thread_id)
        if "Call Status" in transcribed_text and role == "system":
            msg = Message.add_notification(transcribed_text.replace("Call Status:", ""))
            self._send_callback(msg, thread_id=thread_id)
        elif "EOF" in transcribed_text and role == "system":
            user_state.end_time = datetime.now()
            usage = self.create_usage(user_state)
            msg = Message.add_task_end_message(
                "Voice Execution Completed",
                id=thread_id,
                data={
                    "start_time": (
                        user_state.start_time.isoformat()
                        if user_state.start_time
                        else None
                    ),
                    "end_time": user_state.end_time.isoformat()
                    if user_state.end_time
                    else None,
                    "usage": usage,
                    "recording_url": user_state.recording_url,
                    "transcript": user_state.transcript or [],
                },
            )
            self._send_callback(msg, thread_id=thread_id)

    def create_usage(self, user_state: UserState) -> Dict[str, Any]:
        """Create usage data from user state."""
        return create_usage(user_state)

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics including plugin metrics."""
        metrics = {
            "handler": {
                "session_id": self._session_id,
                "services_initialized": self._services_initialized,
                "is_shutting_down": self._is_shutting_down,
                "plugins_active": len(self.plugins),
            },
            "plugins": self.plugins.get_all_metrics(),
        }
        return metrics

    def dump(self) -> dict:
        """Dump handler state."""
        return {
            "session_id": self._session_id,
            "agent_name": self.agent_config.agent_name if self.agent_config else None,
            "transport_type": str(self._transport_type),
            "services_initialized": self._services_initialized,
            "is_shutting_down": self._is_shutting_down,
            "active_plugins": list(self.plugins._activated),
        }

    def __repr__(self) -> str:
        return f"LiteVoiceHandler(session_id={self._session_id})"

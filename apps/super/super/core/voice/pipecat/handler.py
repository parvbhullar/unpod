"""
Refactored Pipecat Voice Handler - Core Orchestration Module

This module contains the main PipecatVoiceHandler class that orchestrates
voice call processing by delegating to specialized manager classes:
- KnowledgeBaseManager: Knowledge base operations and FAISS integration
- PromptManager: Prompt creation and context management
- TransportManager: Transport configuration and idle user handling
- ServiceFactory: LLM, STT, and TTS service creation
- SIPManager: SIP/telephony operations
- Utility functions from pipecat_utils
All heavy lifting has been delegated to the manager classes, leaving this class
focused on high-level orchestration and pipeline management.
"""

import asyncio
import base64
import json
import logging
import os
import re
import time
import traceback
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import logging as app_logging
from typing import List, Any, Dict, Optional, Set
from abc import ABC
from datetime import datetime

# from langchain_core.runnables.graph import node_data_str

# Core imports
from super.core.logging import logging as app_logging
from super.core.callback.base import BaseCallback
from super.core.configuration import BaseModelConfig
from super.core.context.schema import Message, Event, Role, User
from super.core.handler.config import (
    HandlerConfiguration,
    RoleConfiguration,
    ExecutionNature,
)

# from super.core.logging.logging import print_log
from super.core.plugin.base import PluginLocation, PluginStorageFormat
from super.core.voice.base import BaseVoiceHandler
from super.core.voice.schema import UserState, CallSession, AgentConfig, TransportType
from super.core.voice.services.service_common import is_realtime_model

# Import modular managers
from super.core.voice.managers.knowledge_base import KnowledgeBaseManager
from super.core.voice.managers.prompt_manager import PromptManager
from super.core.voice.managers.transport_manager import TransportManager
from super.core.voice.pipecat.services import ServiceFactory
from super.core.voice.livekit.telephony import SIPManager
from super.core.voice.pipecat.utils import (
    UpPipelineRunner,
    shutdown,
    get_user_state,
    create_usage,
    get_os_info,
    _get_default_config,
)
from super.core.voice.workflows.flows.conversation_flow import create_flow_from_plan
from super.core.voice.workflows.flows.pydantic_ai_section_parser import (
    parse_conversation_plan_async,
)
from super.core.voice.workflows.flows.section_parser import SectionParser
from super.core.voice.workflows.shared_queue import (
    SharedQueueManager,
    create_shared_queue_manager,
)

# from pipecat.services.openai.llm import OpenAILLMService

# Flows imports

from pipecat_flows import (
    FlowManager,
)

# Pipecat core imports
# try:
from pipecat.extensions.voicemail.voicemail_detector import VoicemailDetector
from super.core.voice.schema import CallStatusEnum
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.parallel_pipeline import ParallelPipeline
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.frames.frames import (
    BotInterruptionFrame,
    EndFrame,
    LLMMessagesAppendFrame,
    LLMRunFrame,
    # MixerEnableFrame,
    MixerUpdateSettingsFrame,
    TTSSpeakFrame,
    # TextFrame,
    TranscriptionFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.services.llm_service import FunctionCallParams
from pipecat.processors.aggregators.llm_response import LLMUserAggregatorParams
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.transports.base_transport import BaseTransport
from pipecat.processors.transcript_processor import TranscriptProcessor
from pipecat.processors.user_idle_processor import UserIdleProcessor

from super.core.voice.workflows.flows.flow_generator_v3 import (
    create_smart_flow,
    # create_react_smart_flow,
)
from super.core.voice.workflows.flows.react_flow_manager import ReActFlowManager

# from super.core.voice.workflows.flows.general_flow.passive_agent import PassiveAgent
from super.core.voice.workflows.flows.general_flow.passive_node import PassiveAgent
from super.core.voice.workflows.flows.general_flow.task_metrics import TaskQueueMetrics
from super.core.voice.processors.streaming_text_parser import (
    # StreamingTextParser,
    StreamingTextParserProcessor,
    create_streaming_parser_processor,
)
from super.core.voice.processors.rag_processor import (
    RAGProcessor,
    create_rag_processor,
)
from super.core.voice.processors.silence_trimmer import (
    SilenceTrimmerProcessor,
    create_silence_trimmer,
)
from super.core.voice.schema import CallStatusEnum

PIPECAT_AVAILABLE = True
# except ImportError as e:  # pragma: no cover - optional dependency in tests
#     print_log(f"Error while importing pipecat packages {e}")
#     PIPECAT_AVAILABLE = False

# LiveKit imports
from livekit import api
from livekit.agents import get_job_context

from dotenv import load_dotenv

try:
    import boto3
except ImportError:  # pragma: no cover - optional dependency in tests
    boto3 = None

load_dotenv(override=True)


class PipecatVoiceHandler(BaseVoiceHandler, ABC):
    """
    Refactored Pipecat Voice Handler using composition pattern.

    This class orchestrates voice call processing by delegating specialized
    operations to dedicated manager classes, keeping the core handler focused
    on pipeline coordination and high-level call management.
    """

    default_configuration = HandlerConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.voice.pipecat.PipecatVoiceHandler",
        ),
        role=RoleConfiguration(
            name="pipecat_voice_handler",
            role=("A handler to handle voice conversations."),
            cycle_count=0,
            max_task_cycle_count=3,
        ),
        execution_nature=ExecutionNature.AUTO,
    )

    def __init__(
        self,
        session_id: str = None,
        user_state: UserState = None,
        callback: BaseCallback = None,
        model_config: BaseModelConfig = None,
        configuration: HandlerConfiguration = default_configuration,
        observer=None,
        logger: logging.Logger = app_logging.get_logger("pipecat.voice.handler"),
    ) -> None:
        super().__init__(
            session_id=session_id,
            callback=callback,
            configuration=configuration,
            logger=logger,
        )
        self._session_id = session_id or str(user_state.thread_id)
        self._callback = callback or None
        self._logger = logger
        self._configuration = configuration
        self._execution_nature = configuration.execution_nature
        # Initialize config as a dictionary, converting from model_config if needed
        if model_config is None:
            self.config = {}
        elif hasattr(model_config, 'model_dump'):
            self.config = model_config.model_dump()
        elif hasattr(model_config, 'dict'):
            self.config = model_config.dict()
        elif isinstance(model_config, dict):
            self.config = model_config.copy()
        else:
            self.config = {}

        self.user_state = user_state
        self.input_data = None
        self.optimizations_applied: List[str] = []

        # Feature flag for section-based flow generation

        self.use_flows = (
            self.config.get("use_flows", os.getenv("USE_FLOWS", "false")) == "true"
        )
        self.use_flows = bool(self.config.get("use_flows", os.getenv("USE_FLOWS", "false").lower() == "true"))
        self.config["use_flows"] = self.use_flows

        # Feature flag for ReAct flow optimization
        self.use_react_flows = (
            self.config.get("use_react_flows", os.getenv("USE_REACT_FLOWS", "false"))
            == "true"
        )
        self.config["use_react_flows"] = self.use_react_flows

        # Realtime mode configuration
        # use_realtime: Enable OpenAI Realtime API
        # mixed_realtime_mode: Use Realtime LLM but separate TTS (text output)
        self.use_realtime = self.config.get("use_realtime", os.getenv("USE_REALTIME", "false").lower() == "true")
        self.mixed_realtime_mode = self.config.get("mixed_realtime_mode", os.getenv("MIXED_REALTIME_MODE", "false").lower() == "true")

        self._transport_type = os.getenv("HANDLER_TRANSPORT") or TransportType.LIVEKIT
        self.user_state.transport_type = self._transport_type
        self._transport: Optional[BaseTransport] = None
        # Set default observer to RTVIObserver if available and not provided
        if observer is None and PIPECAT_AVAILABLE:
            self.observer = RTVIObserver
        else:
            self.observer = observer
        self.agent_config = AgentConfig(
            agent_name=session_id or "SuperVoiceAgent",
            model_config=model_config,
        )

        # Pipecat components
        self.active_sessions: Dict[str, CallSession] = {}
        self._tts_service = None
        self._stt_service = None
        self._llm_service = None
        self._context_aggregator = None
        self._room_name = None

        # Shutdown state
        self._is_shutting_down = False
        self._services_initialized = False
        self._tool_calling = True
        self._language_guardrail_applied = False
        self._domain_guardrail_applied = False
        self._kb_enabled = self._determine_kb_enabled()
        self._kb_enrichment_tasks: Set[asyncio.Task] = set()
        # ✅ FIXED: Track KB preload completion to prevent cold start delays
        self._kb_preload_complete = asyncio.Event()
        self._kb_warm_complete = asyncio.Event()

        # Streaming text parser configuration
        # Enables TTS to start while LLM is still generating (reduces latency by 500-1500ms)
        self.use_streaming_parser = self.config.get(
            "use_streaming_parser",
            os.getenv("USE_STREAMING_PARSER", "true").lower() == "true",
        )
        self._streaming_parser_processor: Optional[StreamingTextParserProcessor] = None

        # RAG processor configuration
        # Enables synchronous context enrichment before LLM (reduces latency by 500-2000ms)
        self.use_rag_processor = self.config.get(
            "use_rag_processor",
            os.getenv("USE_RAG_PROCESSOR", "false").lower() == "true",
        )
        self._rag_processor: Optional[RAGProcessor] = None

        # Silence trimmer configuration
        # Trims leading silence from TTS audio (reduces perceived latency by 100-300ms)
        self.use_silence_trimmer = self.config.get(
            "use_silence_trimmer",
            os.getenv("USE_SILENCE_TRIMMER", "false").lower() == "true",
        )
        self._silence_trimmer: Optional[SilenceTrimmerProcessor] = None

        # Fast path pipeline configuration
        # Creates minimal linear pipeline without FlowManager, VoicemailDetector, parallel branches
        # Reduces latency by 50-100ms from simpler frame routing
        self.use_fast_path_pipeline = self.config.get(
            "use_fast_path_pipeline",
            os.getenv("USE_FAST_PATH_PIPELINE", "false").lower() == "true",
        )

        # Initialize all manager classes
        self.knowledge_base_manager = KnowledgeBaseManager(
            logger=self._logger,
            session_id=self._session_id,
            user_state=self.user_state,
            config=self.config,  # ✅ FIXED: Pass config for refresh_index setting
        )

        self.prompt_manager = PromptManager(
            config=self.config or {},
            agent_config=self.agent_config,
            session_id=self._session_id,
            tool_calling=self._tool_calling,
            logger=self._logger,
        )
        self._register_optimization(
            "Persona prompt updated for English-first UPSC counselling flow"
        )

        self.transport_manager = TransportManager(
            logger=self._logger,
            config=self.config,
            user_state=self.user_state,
            room_name=self._room_name,
            transport_type=self._transport_type,
            task=None,
            active_sessions=self.active_sessions,
            end_call_callback=self.end_call,
        )

        # Ensure use_realtime is in config for ServiceFactory
        service_config = self.config.copy() if self.config else {}
        service_config["use_realtime"] = self.use_realtime
        service_config["mixed_realtime_mode"] = self.mixed_realtime_mode

        self.service_factory = ServiceFactory(
            config=service_config,
            logger=self._logger,
            room_name=self._room_name,
            tool_calling=self._tool_calling,
            use_realtime=self.use_realtime,
            get_docs_callback=self.get_docs
        )

        self.sip_manager = SIPManager(
            logger=self._logger,
            config=self.config or {},
            session_id=self._session_id,
            room_name=self._room_name,
            user_state=self.user_state,
        )

        # Call data for tracking
        self.call_data = {}
        self.task = None
        self.runner = None
        self.flow_manager = None
        self.nodes = None
        self.conversation_flow = None
        self.shared_queue: Optional[SharedQueueManager] = None
        self.audio_buffer = None

        # LiveKit event bridge for transcript publishing
        # Set by VoiceAgentHandler via set_event_bridge()
        self._event_bridge = None

        # Initialize Redis client for conversation plan caching
        self._redis_client = None
        self._initialize_redis_client()
        self._recording_bucket: Optional[str] = os.getenv("AWS_STORAGE_BUCKET_NAME")
        self._recording_region: Optional[str] = os.getenv("AWS_DEFAULT_REGION")
        self._recording_access_key: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
        self._recording_secret_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
        self._s3_client = None
        self._recordings_dir = Path(
            os.getenv("VOICE_AGENT_RECORDINGS_DIR", "/tmp/voice_recordings")
        )
        self._recordings_dir.mkdir(parents=True, exist_ok=True)
        self._user_transcript = ""
        self._register_optimization(
            "Documented known call quality issues for Pipecat voice flows"
        )

        self.task_queue = []
        self.agent_running = True
        self.sections = None
        self.passive_agent = PassiveAgent(self)

        # Initialize metrics system for task queue observability
        self.metrics = TaskQueueMetrics()
        self._logger.info("Task queue metrics system initialized")

    async def _parse_section(self):
        parser = SectionParser()
        content = parser.parse_prompt(self.config.get("system_prompt"))
        print("\n\n", content.guidelines, "parsed content \n\n ")
        return content

    def set_realtime_fields(self):
        """
        Determine realtime mode using priority chain:
        1. Database flag (llm_realtime) - source of truth
        2. Model name detection (LLM_REALTIME_MODELS list)

        Env var MIXED_REALTIME_MODE only affects mixed mode, not realtime detection.
        """
        # Priority 1: Database flag (source of truth)
        if self.config.get("llm_realtime"):
            self.use_realtime = True
            self._logger.info("Realtime mode enabled via database flag (llm_realtime=True)")
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

    async def execute(self, *args, **kwargs) -> Any:
        """Execute the handler step."""
        if not PIPECAT_AVAILABLE:
            raise Exception("Pipecat is not available. Please install pipecat package.")

        data = kwargs.get("data", {})
        await self._run_pipecat_agent(data)

    def message_callback(
        self, transcribed_text: str, role: str, user_state: UserState
    ) -> None:
        """
        Process and send messages through the callback system.

        Args:
            transcribed_text: The text content to send
            role: Message role (user/system/assistant)
            user_state: Current user state
        """
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
        print(
            f"{'=' * 100} \n\n  Sending callback message: {message.sender.role}  for thread id :{thread_id} \n\n{'='*100}"
        )

        if self._callback:
            self._callback.send(message, thread_id=thread_id)

    def set_event_bridge(self, event_bridge) -> None:
        """
        Set the LiveKit event bridge for transcript publishing.

        This method is called by VoiceAgentHandler to pass the initialized
        event bridge to the Pipecat handler for publishing transcripts
        to LiveKit rooms.

        Args:
            event_bridge: LiveKitEventBridge instance from voice_agent_handler
        """
        self._event_bridge = event_bridge
        self._logger.info("LiveKit event bridge set for transcript publishing")

    async def _publish_livekit_transcript(
        self, role: str, content: str, is_final: bool = True
    ) -> bool:
        """
        Publish transcript to LiveKit using the event bridge.

        Args:
            role: Speaker role ("user" or "assistant")
            content: Transcript text
            is_final: Whether this is a final transcription

        Returns:
            True if published successfully, False otherwise
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
            self._logger.error(f"Failed to publish LiveKit transcript: {e}")
            return False

    def _register_optimization(self, description: str) -> None:
        """Track optimizations applied to the handler for observability."""
        if description not in self.optimizations_applied:
            self.optimizations_applied.append(description)
            self._logger.debug("Optimization applied: %s", description)

    def get_streaming_parser_metrics(self) -> Optional[dict]:
        """
        Get metrics from the streaming text parser.

        Returns:
            Dict with timing and chunk statistics, or None if parser not enabled.

        Example return value:
            {
                "total_time_ms": 1234.5,
                "time_to_first_chunk_ms": 45.2,
                "chunk_count": 156,
                "spoke_response_length": 342,
                "code_blocks_count": 0,
                "links_count": 0,
                "is_complete": True
            }
        """
        if self._streaming_parser_processor:
            return self._streaming_parser_processor.get_metrics()
        return None

    def set_streaming_parser_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the streaming text parser at runtime.

        Args:
            enabled: Whether to enable streaming parsing.
        """
        self.use_streaming_parser = enabled
        if self._streaming_parser_processor:
            self._streaming_parser_processor.set_enabled(enabled)
            self._logger.info(
                f"Streaming parser {'enabled' if enabled else 'disabled'}"
            )

    def get_rag_processor_metrics(self) -> Optional[dict]:
        """
        Get metrics from the RAG processor.

        Returns:
            Dict with RAG statistics, or None if processor not enabled.

        Example return value:
            {
                "total_queries": 10,
                "total_enrichments": 8,
                "enrichment_rate_pct": 80.0,
                "avg_latency_ms": 35.5,
                "total_latency_ms": 355.0,
                "enabled": True
            }
        """
        if self._rag_processor:
            return self._rag_processor.get_metrics()
        return None

    def set_rag_processor_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the RAG processor at runtime.

        Args:
            enabled: Whether to enable RAG context enrichment.
        """
        self.use_rag_processor = enabled
        if self._rag_processor:
            self._rag_processor.set_enabled(enabled)
            self._logger.info(f"RAG processor {'enabled' if enabled else 'disabled'}")

    def get_silence_trimmer_metrics(self) -> Optional[dict]:
        """
        Get metrics from the silence trimmer.

        Returns:
            Dict with silence trimming statistics, or None if trimmer not enabled.

        Example return value:
            {
                "total_frames": 50,
                "trimmed_frames": 35,
                "trim_rate_pct": 70.0,
                "total_bytes_trimmed": 12000,
                "total_latency_saved_ms": 250.0,
                "avg_latency_saved_ms": 7.14,
                "enabled": True,
                "threshold_db": -50.0
            }
        """
        if self._silence_trimmer:
            return self._silence_trimmer.get_metrics()
        return None

    def set_silence_trimmer_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the silence trimmer at runtime.

        Args:
            enabled: Whether to enable silence trimming.
        """
        self.use_silence_trimmer = enabled
        if self._silence_trimmer:
            self._silence_trimmer.set_enabled(enabled)
            self._logger.info(f"Silence trimmer {'enabled' if enabled else 'disabled'}")

    def _determine_kb_enabled(self) -> bool:
        """Check whether knowledge base retrieval should be active for this session."""
        # print("Knowledge base enabled" ,self.config)
        if not self.config:
            return False
        config_kb = self.config.get("knowledge_base") or None
        # print(self.config)
        # enabled = bool(config_kb)
        return False
        # if not enabled:
        #     self._logger.debug("Knowledge base disabled: no sources configured")
        # return enabled

    def _is_meaningful_query(self, text: str) -> bool:
        if not text or not isinstance(text, str):
            return False

        # Clean and normalize the text
        cleaned = text.strip().lower()

        # Check minimum length (at least 3 characters)
        if len(cleaned) < 3:
            return False

        # List of filler words to skip KB enrichment
        filler_words = {
            "yes",
            "no",
            "ok",
            "okay",
            "hi",
            "hello",
            "hey",
            "there",
            "thanks",
            "thank",
            "you",
            "bye",
            "goodbye",
            "alright",
            "sure",
            "fine",
            "good",
            "great",
            "nice",
            "cool",
            "yeah",
            "yep",
            "nope",
            "nah",
            "hmm",
            "uh",
            "um",
            "what",
            "huh",
            "oh",
            "ah",
            "right",
            "correct",
            "exactly",
            "yup",
            "well",
            "so",
            "now",
            "then",
            "please",
            "sorry",
            "welcome",
            "congratulations",
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "is",
            "are",
            "was",
            "were",
        }

        # Check if the cleaned text is exactly one of the filler phrases
        if cleaned in filler_words:
            self._logger.debug(f"Skipping KB enrichment for filler phrase: '{text}'")
            return False

        # Split into words and check if ALL words are filler words
        words = cleaned.split()
        if len(words) < 2:
            # Single word queries are only meaningful if longer than 4 characters
            if len(cleaned) <= 4:
                self._logger.debug(f"Skipping KB enrichment for short query: '{text}'")
                return False
        else:
            # ✅ FIXED: Check if ALL words are filler words (not just the phrase)
            # Example: "hello there" → both words are filler → skip KB
            # Example: "ok thanks" → both words are filler → skip KB
            non_filler_words = [w for w in words if w not in filler_words]
            if len(non_filler_words) == 0:
                self._logger.debug(
                    f"Skipping KB enrichment for all-filler phrase: '{text}'"
                )
                return False

        return True

    async def preload_agent(self, user_state, observer):
        self._room_name = user_state.room_name
        self.user_state = user_state
        self.config = user_state.model_config

        self.observer = observer
        self.call_data = {}

        # Pre-initialize services before creating SIP participant to reduce latency
        services_ready = await self._pre_initialize_services()

        if services_ready:
            return True

    def _requires_kb_lookup_via_ner(self, text: str) -> bool:
        if not text or not isinstance(text, str):
            return False

        # First check if it's a meaningful query
        if not self._is_meaningful_query(text):
            return False

        try:
            # Lazy import spaCy (only when needed)
            import spacy

            # Load NER model (cached after first load)
            if not hasattr(self, "_ner_model"):
                try:
                    # Try to load small English model
                    self._ner_model = spacy.load("en_core_web_sm")
                    self._logger.info("Loaded spaCy NER model (en_core_web_sm)")
                except OSError:
                    # Model not installed
                    self._logger.warning(
                        "spaCy model 'en_core_web_sm' not found. "
                        "Install with: python -m spacy download en_core_web_sm. "
                        "Falling back to non-NER mode (all queries trigger KB)."
                    )
                    self._ner_model = None
                    return True  # Fallback: trigger KB if NER not available

            if self._ner_model is None:
                return True  # Fallback mode

            # Process text with NER model
            doc = self._ner_model(text)

            # Extract named entities
            entities = [(ent.text, ent.label_) for ent in doc.ents]

            # Relevant entity types that suggest KB lookup needed
            relevant_entity_types = {
                "PERSON",
                "ORG",
                "GPE",
                "LOC",
                "PRODUCT",
                "EVENT",
                "WORK_OF_ART",
                "LAW",
                "LANGUAGE",
                "FAC",
                "NORP",
            }

            # Check if any relevant entities detected
            has_relevant_entities = any(
                entity_type in relevant_entity_types for _, entity_type in entities
            )

            if has_relevant_entities:
                entity_summary = ", ".join(
                    [f"{text}({label})" for text, label in entities]
                )
                self._logger.debug(
                    f"NER detected entities requiring KB: {entity_summary} "
                    f"in query: '{text[:50]}...'"
                )
                return True

            # Check for question words (fallback if no entities but looks like info-seeking)
            text_lower = text.lower()
            question_words = [
                "what",
                "where",
                "when",
                "who",
                "which",
                "how",
                "why",
                "tell me",
            ]
            has_question = any(qw in text_lower for qw in question_words)

            if has_question and len(text.split()) > 3:
                self._logger.debug(
                    f"NER: Question pattern detected, triggering KB for: '{text[:50]}...'"
                )
                return True

            self._logger.debug(f"NER: No KB lookup needed for: '{text[:50]}...'")
            return False

        except ImportError:
            self._logger.warning(
                "spaCy not installed. Install with: pip install spacy. "
                "Falling back to non-NER mode (all queries trigger KB)."
            )
            # Cache that spaCy is not available
            self._ner_model = None
            return True  # Fallback: trigger KB if spaCy not available

        except Exception as e:
            self._logger.error(
                f"NER detection failed: {e}. Falling back to triggering KB."
            )
            return True  # Fallback on error

    def _schedule_kb_enrichment(self, transcript_text: str) -> None:
        """
        Schedule KB enrichment without blocking the user turn.

        Respects kb_mode configuration:
        - "off": KB enrichment disabled
        - "on_demand": Only enrich meaningful queries (default)
        - "always": Enrich all queries regardless of content
        """
        if not self._kb_enabled or not transcript_text or not self.task:
            return

        # ✅ FIXED: Implement KB mode logic
        kb_mode = getattr(self, "_kb_mode", "on_demand")

        if kb_mode == "off":
            self._logger.debug("KB enrichment disabled (mode=off)")
            return
        elif kb_mode == "on_demand":
            # Only enrich meaningful queries
            if not self._is_meaningful_query(transcript_text):
                return
        elif kb_mode == "always":
            # Enrich all queries
            self._logger.debug(
                f"KB enrichment in 'always' mode for: '{transcript_text}'"
            )
        else:
            self._logger.warning(
                f"Unknown kb_mode '{kb_mode}', defaulting to 'on_demand'"
            )
            if not self._is_meaningful_query(transcript_text):
                return

        async def _run():
            try:
                # ✅ FIXED: Add timeout protection to prevent indefinite hangs
                kb_timeout = (
                    self.config.get("kb_timeout", 5.0)
                    if hasattr(self, "config") and self.config
                    else 5.0
                )

                try:
                    context_message = await asyncio.wait_for(
                        self.knowledge_base_manager.build_context_message(
                            transcript_text
                        ),
                        timeout=kb_timeout,
                    )
                except asyncio.TimeoutError:
                    self._logger.warning(
                        f"KB enrichment timed out after {kb_timeout}s for query: '{transcript_text[:50]}...'"
                    )
                    return

                if not context_message:
                    return

                # Only append KB context to system messages - no interruption needed
                # The context will be used naturally in the next LLM interaction
                await self.task.queue_frames(
                    [
                        LLMMessagesAppendFrame(
                            [{"role": "system", "content": context_message}],
                            run_llm=False,
                        ),
                        # ✅ REMOVED: BotInterruptionFrame() - was causing random interruptions after KB lookup
                        # LLMRunFrame() - not needed, context is available for next turn
                    ]
                )

            except Exception as exc:
                self._logger.error("KB enrichment task failed: %s", exc)

        task = asyncio.create_task(
            _run(), name=f"{self._session_id or 'pipecat'}-kb-enrichment"
        )
        self._kb_enrichment_tasks.add(task)
        task.add_done_callback(lambda t: self._kb_enrichment_tasks.discard(t))

    async def _cancel_kb_tasks(self) -> None:
        """
        Cancel all pending KB enrichment tasks with proper error handling.

        Logs any exceptions that occurred during task execution and ensures
        clean cancellation without hiding bugs.
        """
        if not self._kb_enrichment_tasks:
            return

        self._logger.debug(
            f"Cancelling {len(self._kb_enrichment_tasks)} KB enrichment tasks..."
        )

        # Cancel all pending tasks
        for task in list(self._kb_enrichment_tasks):
            if not task.done():
                task.cancel()

        # ✅ FIXED: Wait for all tasks and log any exceptions (don't swallow errors silently)
        results = await asyncio.gather(
            *self._kb_enrichment_tasks, return_exceptions=True
        )

        # Log any exceptions that occurred
        for i, result in enumerate(results):
            if isinstance(result, Exception) and not isinstance(
                result, asyncio.CancelledError
            ):
                self._logger.error(
                    f"KB enrichment task {i} failed with exception: {result}",
                    exc_info=result,
                )

        self._kb_enrichment_tasks.clear()
        self._logger.debug("✓ All KB enrichment tasks cancelled")

    async def _shutdown_background_workers(self) -> None:
        """Stop background tasks related to KB operations."""
        await self._cancel_kb_tasks()
        # Close Redis client connection
        if self._redis_client:
            try:
                await self._redis_client.aclose()
                self._logger.debug("✓ Redis client connection closed")
            except Exception as e:
                self._logger.warning(f"Failed to close Redis client: {e}")

    async def manage_call(
        self, participant, user_state: UserState, *args, **kwargs
    ) -> Any:
        """
        Manage the call lifecycle and status.

        Args:
            participant: SIP participant information
            user_state: Current user state
        """
        self._logger.info("dialing")
        self.message_callback(
            f"Call Status:Dialing\n",
            role="system",
            user_state=self.user_state,
        )
        from time import perf_counter

        start_time = perf_counter()
        dialling_count = 0

        print(participant)

    def _storage_is_configured(self) -> bool:
        required = [
            self._recording_bucket,
            self._recording_region,
            self._recording_access_key,
            self._recording_secret_key,
        ]
        return all(required)

    def _get_storage_client(self):
        if self._s3_client or not self._storage_is_configured() or boto3 is None:
            return self._s3_client
        try:
            self._s3_client = boto3.client(
                "s3",
                region_name=self._recording_region,
                aws_access_key_id=self._recording_access_key,
                aws_secret_access_key=self._recording_secret_key,
            )
        except Exception as exc:  # pragma: no cover - network dependency
            self._logger.error("Failed to initialize S3 client: %s", exc)
            self._s3_client = None
        else:
            self._register_optimization(
                "Configured async S3 uploads for voice recordings"
            )
        return self._s3_client

    async def _handle_audio_capture(
        self, audio: bytes, sample_rate: int, num_channels: int
    ) -> None:
        if not audio or not self.config.get("record_audio", True):
            return

        from wave import open as wave_open

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.user_state.thread_id}_{timestamp}.wav"
        file_path = self._recordings_dir / filename

        def _write_file():
            with wave_open(str(file_path), "wb") as wf:
                wf.setnchannels(num_channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio)

        await asyncio.to_thread(_write_file)
        self._logger.info("Saved recording to %s", file_path)

        if not self._storage_is_configured() or boto3 is None:
            self.user_state.recording_url = file_path.as_uri()
            return

        client = self._get_storage_client()
        if client is None:
            self.user_state.recording_url = file_path.as_uri()
            return

        s3_key = (
            f"media/call-recordings/{self.call_data.get('token', 'default')}/"
            f"{self.call_data.get('agent_id', 'default')}/{filename}"
        )

        def _upload():
            client.upload_file(
                Filename=str(file_path),
                Bucket=self._recording_bucket,
                Key=s3_key,
                ExtraArgs={"ContentType": "audio/wav"},
            )

        try:
            await asyncio.to_thread(_upload)
            audio_url = f"https://{self._recording_bucket}.s3.{self._recording_region}.amazonaws.com/{s3_key}"
            self.user_state.recording_url = audio_url

            def _cleanup():
                if file_path.exists():
                    file_path.unlink()

            await asyncio.to_thread(_cleanup)
            self._logger.info("Uploaded call recording to %s", audio_url)
            self._register_optimization(
                "Audio capture moved to async file and S3 operations"
            )
        except Exception as s3_error:  # pragma: no cover - network dependency
            self._logger.error("Failed to upload to S3: %s", s3_error)
            self.user_state.recording_url = file_path.as_uri()

    async def _prompt_language_correction(self) -> None:
        if not self.task:
            return
        language = self.config.get("language", "English")
        correction = f"Apologies, let me restate that in {language}."
        directive = f"System directive: Respond in {language} only and share precise topic information. "
        system_message = {"role": "system", "content": directive}
        self.service_factory._update_tts_language("en")
        await self.task.queue_frames(
            [
                BotInterruptionFrame(),
                TTSSpeakFrame(correction),
                LLMMessagesAppendFrame([system_message], run_llm=False),
                LLMRunFrame(),
            ]
        )
        if not self._language_guardrail_applied:
            self._register_optimization(
                "Runtime English guardrail for assistant responses"
            )
            self._language_guardrail_applied = True

    async def _init_variables(self):
        """Initialize instance variables from user state and config."""
        self._logger.info("Initializing variables...")
        if not self.config:
            self.config = self.user_state.model_config
        self.session_id = str(self.user_state.thread_id)
        self._room_name = (
            self.user_state.room_name or f"room-{self.user_state.thread_id}"
        )
        self._tool_calling = self.config.get("tool_calling", True)
        self.config.setdefault("language", "en")
        self.config.setdefault("restrict_to_topic", True)
        self.config.setdefault(
            "first_message",
            "Hello! How I can help you today?",
        )

        previous_state = self._kb_enabled
        self._kb_enabled = self._determine_kb_enabled()
        if previous_state != self._kb_enabled:
            state_msg = "enabled" if self._kb_enabled else "disabled"
            self._logger.info("Knowledge base support %s for this session", state_msg)
        # await self._ensure_transcript_cache_worker()

        # Update managers with new config and state
        self.knowledge_base_manager.user_state = self.user_state
        self.prompt_manager.user_state = (
            self.user_state
        )  # Update user_state for template replacement
        self.prompt_manager.input_data = (
            self.input_data
        )  # Pass input_data for template replacement
        self.prompt_manager.update_config(self.config)
        self.prompt_manager.update_session_id(self._session_id)
        self.transport_manager._room_name = self._room_name
        self.transport_manager.user_state = self.user_state
        self.transport_manager.config = self.config

        # Update service factory config with current settings
        self.service_factory.config = {
            **self.config,  # Include existing config
            'room_name': self._room_name,
            'session_id': self._session_id,
            'tool_calling': self._tool_calling
        }

        self.sip_manager._room_name = self._room_name
        self.sip_manager.user_state = self.user_state
        self.sip_manager.config = self.config

        # Set KB mode from config (default: "on_demand")
        self._kb_mode = self.config.get(
            "kb_mode", "on_demand"
        )  # Options: "always", "on_demand", "off"
        self._logger.info(f"KB enrichment mode set to: {self._kb_mode}")

        self._register_optimization(
            "Default configuration enforces English UPSC-first conversation flow"
        )

    def _add_users(self):
        import uuid

        self.agent = User.add_user(
            name=self.config.get("agent_id", ""),
            role=Role.ASSISTANT,
        )

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

    async def _pre_initialize_services(self) -> bool:
        """Pre-initialize all services to avoid delays during call setup"""
        # import time
        import traceback
        from time import perf_counter

        pre_init_start = perf_counter()
        try:
            self._logger.info("Starting service pre-initialization...")
            self._add_users()

            # Step 1: Initialize variables
            _step1_start = perf_counter()
            self._logger.info("Step 1/8: Initializing variables...")
            await self._init_variables()
            _step1_ms = (perf_counter() - _step1_start) * 1000
            self._logger.info(f"✓ Variables initialized [{_step1_ms:.1f}ms]")

            # Step 2: Get or create transport
            _step2_start = perf_counter()
            self._logger.info("Step 2/8: Getting transport...")
            transport = await self.get_transport()

            if not self._transport:
                self._transport = transport
            self.sip_manager.transport = self._transport
            _step2_ms = (perf_counter() - _step2_start) * 1000
            self._logger.info(f"✓ Transport ready [{_step2_ms:.1f}ms]")

            if self._services_initialized:
                self._logger.info("Services already initialized, skipping...")
                return True

            # Step 3: Set config
            _step3_start = perf_counter()
            self._logger.info("Step 3/8: Setting configuration...")
            if not self.config:
                self.config = self.user_state.model_config

            # Log configuration details
            llm_provider = self.config.get("llm_provider", "NOT_SET")
            stt_provider = self.config.get("stt_provider", "NOT_SET")
            tts_provider = self.config.get("tts_provider", "NOT_SET")
            _step3_ms = (perf_counter() - _step3_start) * 1000
            self._logger.info(
                f"✓ Configuration set: LLM={llm_provider}, STT={stt_provider}, TTS={tts_provider} [{_step3_ms:.1f}ms]"
            )

            # Steps 4-6: Initialize services based on mode
            # Determine which services to create
            is_realtime_mode = self.use_realtime
            is_mixed_mode = self.mixed_realtime_mode

            # Log mode-specific service initialization plan
            if is_realtime_mode and is_mixed_mode:
                self._logger.info(
                    f"Steps 4-6/8: 🔀 Mixed Realtime - Initializing LLM + TTS (LLM={llm_provider}, TTS={tts_provider})"
                )
            elif is_realtime_mode:
                self._logger.info(
                    f"Steps 4-6/8: ⚡ Full Realtime - Initializing LLM only (LLM={llm_provider})"
                )
            else:
                self._logger.info(
                    f"Steps 4-6/8: 🔧 Standard - Initializing STT + LLM + TTS (STT={stt_provider}, LLM={llm_provider}, TTS={tts_provider})"
                )

            # Per-service timeout to identify which service is slow
            SINGLE_SERVICE_TIMEOUT = 15.0  # seconds

            async def _init_stt():
                from time import perf_counter

                _stt_start = perf_counter()
                if is_realtime_mode:
                    self._logger.info(
                        "  → Skipping STT initialization (Realtime handles STT)"
                    )
                    return None
                self._logger.info(
                    f"  → Starting STT service initialization ({stt_provider})..."
                )
                try:
                    # Check cache first for faster startup
                    _cache_check_start = perf_counter()
                    from super.core.voice.voice_agent_handler import get_service_cache

                    cache = get_service_cache()
                    cached_stt = cache.get_stt(self.config)
                    _cache_check_ms = (perf_counter() - _cache_check_start) * 1000
                    if cached_stt:
                        _total_ms = (perf_counter() - _stt_start) * 1000
                        self._logger.info(
                            f"✓ STT service from cache: {type(cached_stt).__name__} "
                            f"[cache_lookup={_cache_check_ms:.1f}ms, total={_total_ms:.1f}ms]"
                        )
                        return cached_stt

                    _create_start = perf_counter()
                    stt = await asyncio.wait_for(
                        self.service_factory._create_stt_service_with_retry(),
                        timeout=SINGLE_SERVICE_TIMEOUT,
                    )
                    _create_ms = (perf_counter() - _create_start) * 1000
                    if stt:
                        _cache_set_start = perf_counter()
                        cache.set_stt(self.config, stt)
                        _cache_set_ms = (perf_counter() - _cache_set_start) * 1000
                        _total_ms = (perf_counter() - _stt_start) * 1000
                        self._logger.info(
                            f"✓ STT service created: {type(stt).__name__} "
                            f"[create={_create_ms:.1f}ms, cache_set={_cache_set_ms:.1f}ms, total={_total_ms:.1f}ms]"
                        )
                    else:
                        self._logger.error(
                            f"✗ STT service creation returned None - check {stt_provider} API keys"
                        )
                    return stt
                except asyncio.TimeoutError:
                    self._logger.error(
                        f"✗ STT service ({stt_provider}) timed out after {SINGLE_SERVICE_TIMEOUT}s"
                    )
                    return None
                except Exception as e:
                    self._logger.error(
                        f"✗ STT service creation failed: {str(e)}\n{traceback.format_exc()}"
                    )
                    return None

            async def _init_llm():
                from time import perf_counter

                _llm_start = perf_counter()
                self._logger.info(
                    f"  → Starting LLM service initialization ({llm_provider})..."
                )
                try:
                    # For realtime mode, pass the assistant prompt
                    if self.use_realtime and llm_provider == "openai":
                        assistant_prompt = self.prompt_manager._create_assistant_prompt()
                        self._logger.info("Creating LLM with assistant prompt for Realtime API")
                    # Check cache first for faster startup
                    _cache_check_start = perf_counter()
                    from super.core.voice.voice_agent_handler import get_service_cache

                    cache = get_service_cache()
                    cached_llm = cache.get_llm(self.config)
                    _cache_check_ms = (perf_counter() - _cache_check_start) * 1000
                    if cached_llm:
                        _total_ms = (perf_counter() - _llm_start) * 1000
                        self._logger.info(
                            f"✓ LLM service from cache: {type(cached_llm).__name__} "
                            f"[cache_lookup={_cache_check_ms:.1f}ms, total={_total_ms:.1f}ms]"
                        )
                        return cached_llm

                    # For realtime mode, pass the assistant prompt (OpenAI Realtime or Gemini Live)
                    _prompt_start = perf_counter()
                    if self.use_realtime and llm_provider.lower() in [
                        "openai",
                        "google",
                    ]:
                        assistant_prompt = (
                            self.prompt_manager._create_assistant_prompt()
                        )
                        self._logger.info(
                            f"Creating LLM with assistant prompt for {llm_provider.upper()} Realtime API"
                        )
                        # Pass assistant_prompt to service factory
                        self.service_factory._assistant_prompt = assistant_prompt
                    _prompt_ms = (perf_counter() - _prompt_start) * 1000

                    _create_start = perf_counter()
                    llm = await asyncio.wait_for(
                        self.service_factory._create_llm_service_with_retry(),
                        timeout=SINGLE_SERVICE_TIMEOUT,
                    )
                    _create_ms = (perf_counter() - _create_start) * 1000
                    if llm:
                        _cache_set_start = perf_counter()
                        cache.set_llm(self.config, llm)
                        _cache_set_ms = (perf_counter() - _cache_set_start) * 1000
                        _total_ms = (perf_counter() - _llm_start) * 1000
                        self._logger.info(
                            f"✓ LLM service created: {type(llm).__name__} "
                            f"[create={_create_ms:.1f}ms, prompt={_prompt_ms:.1f}ms, cache_set={_cache_set_ms:.1f}ms, total={_total_ms:.1f}ms]"
                        )
                    else:
                        self._logger.error(
                            f"✗ LLM service creation returned None - check {llm_provider} API keys"
                        )
                    return llm
                except asyncio.TimeoutError:
                    self._logger.error(
                        f"✗ LLM service ({llm_provider}) timed out after {SINGLE_SERVICE_TIMEOUT}s"
                    )
                    return None
                except Exception as e:
                    self._logger.error(
                        f"✗ LLM service creation failed: {str(e)}\n{traceback.format_exc()}"
                    )
                    return None

            async def _init_tts():
                from time import perf_counter

                _tts_start = perf_counter()
                if is_realtime_mode and not is_mixed_mode:
                    self._logger.info(
                        "  → Skipping TTS initialization (Full Realtime handles TTS)"
                    )
                    return None
                self._logger.info(
                    f"  → Starting TTS service initialization ({tts_provider})..."
                )
                try:
                    # Check cache first for faster startup
                    _cache_check_start = perf_counter()
                    from super.core.voice.voice_agent_handler import get_service_cache

                    cache = get_service_cache()
                    cached_tts = cache.get_tts(self.config)
                    _cache_check_ms = (perf_counter() - _cache_check_start) * 1000
                    if cached_tts:
                        _total_ms = (perf_counter() - _tts_start) * 1000
                        self._logger.info(
                            f"✓ TTS service from cache: {type(cached_tts).__name__} "
                            f"[cache_lookup={_cache_check_ms:.1f}ms, total={_total_ms:.1f}ms]"
                        )
                        return cached_tts

                    _create_start = perf_counter()
                    tts = await asyncio.wait_for(
                        self.service_factory._create_tts_service_with_retry(),
                        timeout=SINGLE_SERVICE_TIMEOUT,
                    )
                    _create_ms = (perf_counter() - _create_start) * 1000
                    if tts:
                        _cache_set_start = perf_counter()
                        cache.set_tts(self.config, tts)
                        _cache_set_ms = (perf_counter() - _cache_set_start) * 1000
                        _total_ms = (perf_counter() - _tts_start) * 1000
                        self._logger.info(
                            f"✓ TTS service created: {type(tts).__name__} "
                            f"[create={_create_ms:.1f}ms, cache_set={_cache_set_ms:.1f}ms, total={_total_ms:.1f}ms]"
                        )
                    else:
                        self._logger.error(
                            f"✗ TTS service creation returned None - check {tts_provider} API keys"
                        )
                    return tts
                except asyncio.TimeoutError:
                    self._logger.error(
                        f"✗ TTS service ({tts_provider}) timed out after {SINGLE_SERVICE_TIMEOUT}s"
                    )
                    return None
                except Exception as e:
                    self._logger.error(
                        f"✗ TTS service creation failed: {str(e)}\n{traceback.format_exc()}"
                    )
                    return None

            # Run service initializations concurrently with timeout (only creates needed services)
            _step456_start = perf_counter()
            self._logger.info(
                "DEBUG: About to call asyncio.gather for service initialization..."
            )

            # Timeout for service initialization to prevent LiveKit worker timeout
            SERVICE_INIT_TIMEOUT = 25.0  # seconds - must be less than LiveKit's ~30s timeout
            try:
                (
                    self._stt_service,
                    self._llm_service,
                    self._tts_service,
                ) = await asyncio.wait_for(
                    asyncio.gather(_init_stt(), _init_llm(), _init_tts()),
                    timeout=SERVICE_INIT_TIMEOUT,
                )
            except asyncio.TimeoutError:
                self._logger.error(
                    f"Service initialization timed out after {SERVICE_INIT_TIMEOUT}s - "
                    "check API connectivity (OpenAI, Deepgram, etc.)"
                )
                # Try to salvage what we can - check if any services completed
                self._logger.info("Attempting graceful degradation after timeout...")
                return False

            self._logger.info("DEBUG: asyncio.gather completed!")
            _step456_ms = (perf_counter() - _step456_start) * 1000

            # Log which services were actually created
            created_services = []
            if self._stt_service:
                created_services.append("STT")
            if self._llm_service:
                created_services.append("LLM")
            if self._tts_service:
                created_services.append("TTS")
            self._logger.info(
                f"✓ Steps 4-6: Services initialized in parallel [{_step456_ms:.1f}ms]: {', '.join(created_services)}"
            )

            faiss_time = 0.0
            if self._kb_enabled:
                self._logger.info(
                    "Step 7/8: Initializing FAISS index (async warm-up)..."
                )

                async def _warm_faiss():
                    faiss_start = perf_counter()
                    try:
                        if not self.knowledge_base_manager.is_initialized:
                            await self.knowledge_base_manager._init_context_retrieval()
                        context_retrieval = (
                            self.knowledge_base_manager.context_retrieval
                        )
                        if context_retrieval and hasattr(
                            context_retrieval, "faiss_index"
                        ):
                            self._logger.info(
                                "✓ FAISS index available with %s vectors",
                                context_retrieval.faiss_index.ntotal,
                            )
                        elapsed = (perf_counter() - faiss_start) * 1000
                        self._logger.info(
                            "✓ FAISS initialization completed in %.1fms", elapsed
                        )
                    except Exception as err:
                        self._logger.warning(
                            "FAISS initialization deferred due to error: %s", err
                        )
                    finally:
                        # ✅ FIXED: Signal completion to prevent cold start queries
                        self._kb_warm_complete.set()

                asyncio.create_task(_warm_faiss())
                asyncio.create_task(self._background_kb_preload())
                self._logger.info("✓ Started background KB document preload task")
                self._logger.info(
                    "DEBUG: Continuing main execution flow after background task creation..."
                )

                # Force log flush to ensure we see this message
                import sys

                sys.stdout.flush()
                sys.stderr.flush()
            else:
                self._logger.info(
                    "Step 7/8: Skipping FAISS initialization (knowledge base disabled)"
                )

            # ✅ FIXED: Check if critical services were created successfully with graceful degradation
            self._logger.info("DEBUG: Checking service initialization status...")
            self._logger.info(
                f"DEBUG: STT service: {self._stt_service is not None}, LLM service: {self._llm_service is not None}, TTS service: {self._tts_service is not None}"
            )

            failed_services = []
            if not self._stt_service:
                failed_services.append(f"STT ({stt_provider})")
            if not self._llm_service:
                failed_services.append(f"LLM ({llm_provider})")
            if not self._tts_service:
                failed_services.append(f"TTS ({tts_provider})")

            if failed_services:
                # LLM is critical - cannot proceed without it
                if not self._llm_service:
                    error_msg = (
                        f"CRITICAL: LLM service failed to initialize ({llm_provider})"
                    )
                    self._logger.error(error_msg)
                    self._logger.error(
                        "Common causes: Missing/invalid API keys, network issues, or unsupported provider"
                    )
                    self._logger.error(
                        "Please check environment variables for the required API keys"
                    )
                    return False

                # TTS/STT can degrade gracefully
                if not self._tts_service or not self._stt_service:
                    warning_msg = (
                        f"WARNING: Some services failed: {', '.join(failed_services)}"
                    )
                    self._logger.warning(warning_msg)
                    self._logger.warning(
                        "Call will proceed with reduced functionality (text-only mode may be activated)"
                    )
                    # Continue with degraded service - don't fail completely

            # Step 8: Pre-create context and register functions
            _step8_start = perf_counter()
            self._logger.info("DEBUG: Reached Step 8 - about to create LLM context...")
            self._logger.info(
                "Step 8/8: Creating LLM context and registering functions..."
            )
            try:
                if self._llm_service:
                    # ✅ FIXED: Register KB tool if tool_calling enabled (removed kb_enabled check)
                    # Tool should be available even if automatic enrichment is disabled
                    # This allows LLM to call KB via tool when needed
                    if self._tool_calling:
                        self._llm_service.register_function(
                            "get_knowledge_base_info", self.get_docs
                        )
                        self._logger.info(
                            "✓ Function 'get_knowledge_base_info' registered for tool calling"
                        )
                    # if self._tool_calling and self.config.get("language", "en") != "en":
                    #     self._llm_service.register_function("switch_language", self.service_factory._dual_language_tts.switch_language)
                    #     self._logger.info("✓ Function 'switch_language' registered")
                    context = self._create_context_with_tools()
                    # Use 50ms aggregation timeout for faster turn boundaries (reduces latency by 50-200ms)
                    aggregation_timeout = self.config.get(
                        "context_aggregation_timeout", 0.05
                    )
                    self._context_aggregator = (
                        self._llm_service.create_context_aggregator(
                            context,
                            user_params=LLMUserAggregatorParams(
                                aggregation_timeout=aggregation_timeout
                            ),
                        )
                    )
                    _step8_ms = (perf_counter() - _step8_start) * 1000
                    self._logger.info(
                        f"✓ Step 8: LLM context aggregator created (aggregation_timeout={aggregation_timeout}s) [{_step8_ms:.1f}ms]"
                    )
            except Exception as e:
                self._logger.error(
                    f"✗ Context creation failed: {str(e)}\n{traceback.format_exc()}"
                )
                return False

            self._services_initialized = True
            _total_ms = (perf_counter() - pre_init_start) * 1000
            self._logger.info("DEBUG: About to log success message and return True...")
            self._logger.info(
                f"✓ All services pre-initialized successfully [{_total_ms:.1f}ms] "
                f"(Step1={_step1_ms:.1f}ms, Step2={_step2_ms:.1f}ms, Step3={_step3_ms:.1f}ms, "
                f"Steps4-6={_step456_ms:.1f}ms, Step8={_step8_ms:.1f}ms)"
            )
            self._logger.info("DEBUG: Returning True from _pre_initialize_services")
            return True

        except Exception as e:
            self._logger.error(
                f"✗ Critical error during service pre-initialization: {str(e)}"
            )
            self._logger.error(f"Traceback:\n{traceback.format_exc()}")
            return False

    def _initialize_redis_client(self):
        """Initialize Redis client for conversation plan caching."""
        try:
            from redis.asyncio import Redis

            redis_url = os.getenv("SEARCH_REDIS_URL", "redis://localhost")
            self._redis_client = Redis.from_url(redis_url, decode_responses=True)
            self._logger.info(f"Redis client initialized for plan caching: {redis_url}")
        except ImportError:
            self._logger.warning(
                "redis-py not installed. Conversation plan caching disabled."
            )
            self._redis_client = None
        except Exception as e:
            self._logger.error(f"Failed to initialize Redis for plan caching: {e}")
            self._redis_client = None

    async def _get_or_create_conversation_plan(self):
        """
        Get conversation plan from cache or create new one.

        Uses Redis caching with hash(system_prompt + agent_id) as key to avoid
        re-parsing the conversation plan on every call.

        Returns:
            ConversationPlan: Parsed conversation plan
        """
        import hashlib
        from super.core.voice.workflows.flows.pydantic_ai_section_parser import (
            ConversationPlan,
        )
        import time

        start_time = time.time()

        # Generate cache key from system_prompt + agent_id
        agent_id = self.config.get("agent_id", "default")
        cache_key_input = f"{self.user_state.system_prompt}{agent_id}"
        cache_key = hashlib.sha256(cache_key_input.encode()).hexdigest()

        # If Redis is not available, parse directly
        if not self._redis_client:
            self._logger.debug(
                "Redis not available, parsing conversation plan directly"
            )
            return await parse_conversation_plan_async(self.user_state.system_prompt)

        try:
            # Try to get from cache
            cached_plan_json = await self._redis_client.get(
                f"conversation_plan:{cache_key}"
            )

            if cached_plan_json:
                # Deserialize from cache
                plan_dict = json.loads(cached_plan_json)
                plan = ConversationPlan(**plan_dict)
                cache_duration = time.time() - start_time
                self._logger.info(
                    f"✅ Cache HIT: Loaded plan in {cache_duration:.3f}s (key: {cache_key[:8]}...)"
                )
                return plan
            else:
                # Cache miss - parse with OpenAI (slow)
                self._logger.warning(
                    f"⚠️ Cache MISS for key {cache_key[:8]}... - calling OpenAI API"
                )
                parse_start = time.time()
                plan = await parse_conversation_plan_async(
                    self.user_state.system_prompt
                )
                parse_duration = time.time() - parse_start
                # Cache the result
                plan_json = json.dumps(plan.model_dump())
                await self._redis_client.set(
                    f"conversation_plan:{cache_key}", plan_json, ex=3600  # 1 hour TTL
                )
                total_duration = time.time() - start_time
                self._logger.warning(
                    f"⏱️ OpenAI API call took {parse_duration:.2f}s, total with caching: {total_duration:.2f}s"
                )
                return plan
        except Exception as e:
            # If caching fails, fall back to direct parsing
            self._logger.warning(f"Redis caching failed, parsing directly: {e}")
            return await parse_conversation_plan_async(self.user_state.system_prompt)

    async def _background_kb_preload(self):
        """Background task to preload knowledge base documents without blocking call setup."""
        import time

        if not self._kb_enabled:
            self._logger.debug("Skipping KB preload task (knowledge base disabled)")
            self._kb_preload_complete.set()  # Signal completion even if disabled
            return
        try:
            docs_start = time.time()
            self._logger.info("Starting background KB document preload...")
            await self.knowledge_base_manager._preload_knowledge_base_documents(
                self.user_state
            )
            docs_time = (time.time() - docs_start) * 1000
            self._logger.info(
                f"✓ Background KB document preload completed in {docs_time:.2f}ms"
            )
        except Exception as e:
            self._logger.warning(
                f"Background KB preload failed (non-critical): {str(e)}"
            )
        finally:
            # ✅ FIXED: Signal completion to prevent cold start delays on first query
            self._kb_preload_complete.set()

    async def initialize_inbound_call(
        self, room_name, model_config, observer, user_number, user_state
    ):
        """
        Initialize and handle an inbound call.

        Args:
            room_name: LiveKit room name
            model_config: Model configuration dictionary
            observer: RTVI observer instance
            user_number: User's phone number
            user_state: User state object
        """
        self._logger.info("Initializing pipecat inbound call...", room_name)
        if not PIPECAT_AVAILABLE:
            raise Exception("Pipecat is not available. Please install pipecat package.")

        self._room_name = room_name
        self.user_state = user_state
        self.user_state.room_name = room_name
        self.config = model_config

        self.observer = observer
        self.call_data = {}

        # Pre-initialize services before creating SIP participant to reduce latency
        services_ready = await self._pre_initialize_services()

        if services_ready:
            await self.execute(self.user_state)

    async def get_user_state(self, room_name, model_config):
        """
        Create a default user state for inbound calls.
        Args:
            room_name: LiveKit room name
            model_config: Model configuration dictionary

        Returns:
            UserState object
        """
        return await get_user_state(room_name, model_config)

    async def initialize_outbound_call(
        self, data: Dict, user_state: UserState, *args, **kwargs
    ) -> Any:
        """
        Initialize and execute an outbound call.

        Args:
            data: Call configuration data
            user_state: User state object

        Returns:
            bool: True if successful, False otherwise
        """
        self.user_state = user_state
        self.input_data = data

        if not PIPECAT_AVAILABLE:
            raise Exception("Pipecat is not available. Please install pipecat package.")

        # Pre-initialize services before creating SIP participant to reduce latency
        services_ready = await self._pre_initialize_services()
        if not services_ready:
            self._logger.error("Failed to pre-initialize services")
            self.user_state.end_time = datetime.now()
            thread_id = str(self.user_state.thread_id)
            msg = Message.add_task_end_message(
                "Voice Call Failed",
                id=thread_id,
                data={
                    "start_time": self.user_state.start_time.isoformat()
                    if self.user_state.start_time
                    else None,
                    "end_time": self.user_state.end_time.isoformat()
                    if self.user_state.end_time
                    else None,
                    "error": "Failed to initialize voice services",
                    "call_status": "failed",
                    "transcript": self.user_state.transcript or [],
                    "usage": self.create_usage(self.user_state),
                    "recording_url": self.user_state.recording_url,
                },
            )
            self._send_callback(msg, thread_id=thread_id)
            return False
        else:
            self._logger.info("Services pre-initialized successfully")

            # # Wait for background KB preload to complete for testing.
            # self._logger.info("Waiting for KB preload to complete...")
            # await asyncio.sleep(10)  # Or wait for the actual task
            #
            # while True:
            #     query = input("Enter query (or 'q' to quit): ")
            #     if query == 'q':
            #         break
            #     result = await self.knowledge_base_manager.build_context_message(query)
            #     print("Context message:", result)
            # return False
        participant, room_name = await self.sip_manager.create_sip_participant(data)

        # For Daily transport, participant will be None because dialout happens AFTER pipeline starts
        # For LiveKit transport, participant should exist at this point
        is_daily_deferred = (
            self.user_state.transport_type == "daily"
            and participant is None
            and room_name
        )

        if participant or is_daily_deferred:
            if participant:
                self.user_state.participant = participant
                self.user_state.call_status = CallStatusEnum.CONNECTED
                await self.manage_call(participant, self.user_state)

            self.user_state.room_name = room_name
            data["room_name"] = room_name

            if is_daily_deferred:
                self._logger.info(
                    "Daily dialout deferred - pipeline will start and dialout will be triggered via event handler"
                )

            await self.execute(data=data)
            return True
        else:
            self._logger.info("Failed to create SIP participant")
            # Send failure callback with error information
            self.user_state.end_time = datetime.now()
            thread_id = str(self.user_state.thread_id)
            self.user_state.call_status = CallStatusEnum.FAILED
            msg = Message.add_task_end_message(
                "Voice Call Failed",
                id=thread_id,
                data={
                    "start_time": self.user_state.start_time.isoformat()
                    if self.user_state.start_time
                    else None,
                    "end_time": self.user_state.end_time.isoformat()
                    if self.user_state.end_time
                    else None,
                    "error": self.user_state.call_error
                    or "Failed to create SIP participant",
                    "call_status": self.user_state.call_status or "failed",
                    "transcript": self.user_state.transcript or [],
                    "usage": self.create_usage(self.user_state),
                    "recording_url": self.user_state.recording_url,
                },
            )
            self.user_state.call_status = CallStatusEnum.FAILED
            self._send_callback(msg, thread_id=thread_id)
            return False

    async def get_transport(self) -> BaseTransport:
        """
        Get transport instance using TransportManager.

        Returns:
            BaseTransport instance
        """
        return await self.transport_manager.get_transport()

    def _send_end_message(self):
        msg = Message.create(
            f"CALL ENDED : user ended the call ", role="system", event=Event.TASK_END
        )
        self._send_callback(msg, thread_id=self.user_state.thread_id)

    def _send_start_message(self):
        msg = Message.create(
            f"CALL STARTED : User picked up the call",
            role="system",
            event=Event.TASK_START,
        )
        self._send_callback(msg, thread_id=self.user_state.thread_id)

    async def _run_pipecat_agent(self, data: Dict):
        """
        Run enhanced pipecat pipeline.

        Args:
            data: Configuration data for the pipeline
        """
        try:
            self._logger.info(
                f"Starting pipecat agent for user {self.user_state.user_name}"
            )

            if not self._transport:
                self._transport = await self.get_transport()

            rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

            # Create pipecat pipeline
            pipeline, context_aggregator = await self._create_pipeline(
                self._transport, rtvi
            )

            # Create observers list
            observers = []
            if self.observer:
                # Store observer instance to access turn metrics later
                self.observer_instance = self.observer(user_state=self.user_state)
                observers.append(self.observer_instance)

            # Add LiveKit state observer for agent state tracking
            # This bridges Pipecat events to LiveKit room (listening/thinking/speaking)
            # Pass the transport so the observer can use its room participant
            try:
                from super.core.voice.livekit.state_observer import (
                    create_livekit_state_observer,
                )

                livekit_observer = create_livekit_state_observer(
                    user_state=self.user_state,
                    transport=self._transport,  # Use transport's room participant
                    logger=self._logger,
                    emit_transcripts=False,  # Transcripts handled by on_transcript_update via event bridge
                )
                observers.append(livekit_observer)
                self._livekit_state_observer = livekit_observer
                self._logger.info(
                    f"LiveKit state observer added with transport: {type(self._transport).__name__}"
                )
            except Exception as e:
                self._logger.warning(f"Could not add LiveKit state observer: {e}")
                self._livekit_state_observer = None

            try:
                from super.core.voice.observers.metrics import (
                    UnpodTurnDetection,
                )

                self.unpod_turn_detection = UnpodTurnDetection()
                # observers.append(self.unpod_turn_detection)
            except Exception as e:
                pass

            # For debugging, add WhiskerObserver
            if self.config.get("debug_mode", False):
                from pipecat_whisker import WhiskerObserver

                observers.append(WhiskerObserver(pipeline))

            # Configure sample rates for audio pipeline
            # - Input: 16kHz is industry standard for speech recognition (Whisper, Deepgram, etc.)
            # - Output: 24kHz provides high-quality TTS without excessive bandwidth
            # - Explicit configuration prevents transport default mismatches and resampling artifacts
            audio_in_rate = self.config.get("audio_in_sample_rate", 16000)
            audio_out_rate = self.config.get("audio_out_sample_rate", 24000)

            self._logger.info(
                f"Audio sample rates configured - input: {audio_in_rate}Hz, output: {audio_out_rate}Hz"
            )

            # Create pipeline task with explicit sample rate configuration
            self.task = PipelineTask(
                pipeline,
                params=PipelineParams(
                    enable_metrics=True,
                    enable_usage_metrics=True,
                    audio_in_sample_rate=audio_in_rate,  # ✅ ENABLED: Standard rate for STT services
                    audio_out_sample_rate=audio_out_rate,  # ✅ ENABLED: High quality TTS output
                ),
                observers=observers,
            )

            # Access the observer
            turn_observer = self.task.turn_tracking_observer

            # Register event handlers
            @turn_observer.event_handler("on_turn_started")
            async def on_turn_started(observer, turn_number):
                self._logger.info(f"Turn {turn_number} started")
                # Sync turn number with CustomMetricObserver to track per-turn metrics
                if hasattr(self, 'observer_instance'):
                    # Set the turn number directly to match the turn_tracking_observer
                    self.observer_instance.current_turn_number = turn_number
                    # Initialize metrics for this turn
                    if hasattr(self.observer_instance, '_initialize_turn_metrics'):
                        self.observer_instance._initialize_turn_metrics()
                        self._logger.info(f"Initialized metrics for turn {turn_number}")

            @turn_observer.event_handler("on_turn_ended")
            async def on_turn_ended(observer, turn_number, duration, was_interrupted):
                status = "interrupted" if was_interrupted else "completed"
                self._logger.info(
                    f"Turn {turn_number} {status} in {duration:.2f}s  \n\n {observer}"
                )
                self._logger.info(f"Turn {turn_number} {status} in {duration:.2f}s")
                # Log turn metrics for debugging
                if hasattr(self, 'observer_instance') and hasattr(self.observer_instance, 'get_turn_metrics'):
                    turn_metrics = self.observer_instance.get_turn_metrics(turn_number)
                    if turn_metrics:
                        self._logger.info(f"Turn {turn_number} metrics: {turn_metrics}")

            # Update transport manager with task
            self.transport_manager.set_task(self.task)

            try:
                # Skip FlowManager initialization in fast path mode
                # FlowManager adds orchestration overhead (20-50ms latency)
                if self.use_fast_path_pipeline:
                    self._logger.info(
                        "🚀 Fast path mode: Skipping FlowManager initialization "
                        "(saves 20-50ms orchestration overhead)"
                    )
                    self.flow_manager = None
                    self.nodes = None
                    self.conversation_flow = None
                else:
                    # Store react_config for ReActFlowManager initialization
                    react_config = None
                self.flow_manager = FlowManager(
                    task=self.task,
                    llm=self._llm_service,
                    context_aggregator=context_aggregator,
                    transport=self._transport,
                )

                if self.config.get("agent_id") == os.getenv('VAJIRAM_HANDLE',"testing-good-qua.-xkc0gsvr7ns7") :
                    self._logger.info("creating default flow for Vajiram")
                    # from super.core.voice.workflows.flows.general_flow.VajiramFlowNodes import get_initial_node
                    # from super.core.voice.workflows.flows.general_flow.vajirao_agent_nodes import create_start_node
                    from super.core.voice.workflows.flows.general_flow.singular_flow import create_start_node
                    self.nodes = [create_start_node(self)]
                    if not self.use_flows and self.config.get("agent_id") == os.getenv(
                        "VAJIRAM_HANDLE", "testing-good-qua-xkc0gsvr7ns7"
                    ):
                        self._logger.info("creating default flow for Vajiram")
                        # from super.core.voice.workflows.flows.general_flow.VajiramFlowNodes import get_initial_node
                        # from super.core.voice.workflows.flows.general_flow.vajirao_agent_nodes import create_start_node
                        # from super.core.voice.workflows.flows.general_flow.singular_flow import create_start_node

                        from super.core.voice.workflows.flows.general_flow.active_node import (
                            conversation_node,
                        )

                        self.nodes = [conversation_node(self)]
                else:
                    self._logger.info(f"generating flow nodes")

                    if self.user_state.system_prompt:
                        if self.use_flows:
                            # NEW: Section-based approach with conditional branching
                            self._logger.info("🚀 Using SECTION-BASED flow generation (conditional branching enabled)")
                            from super.core.voice.workflows.flows.flow_generator import create_section_based_flow

                            # CRITICAL FIX: Pass assistant_prompt to preserve full context in flow nodes
                            # This ensures agent identity, rules, guidelines are available in every node
                            assistant_prompt = self.prompt_manager._create_assistant_prompt()
                        if self.user_state.system_prompt:
                            if self.use_flows:
                                # Get assistant prompt for flow generation
                                assistant_prompt = (
                                    self.prompt_manager._create_assistant_prompt()
                                )

                            # GAP #5 FIX: Pass global utility function handlers to inject into all nodes
                            # This makes get_docs, handover_call, end_call available from any node
                            self.nodes = await create_section_based_flow(
                                system_prompt=self.user_state.system_prompt,
                                assistant_prompt=assistant_prompt,
                                get_docs_handler=self.get_docs if self._tool_calling else None,
                                handover_handler=self._handover_call if hasattr(self, 'sip_manager') else None,
                                end_call_handler=None  # Keep internal for now
                            )

                            if self.nodes:
                                self._logger.info(f"✅ Section-based flow: Generated {len(self.nodes)} nodes with conditional branching + full context + global utilities")
                            else:
                                self._logger.warning("⚠️  Section-based flow generation failed, falling back to hybrid approach")

                    # Fallback or default: Hybrid DSPy approach
                    # if not self.nodes:
                    #     self._logger.info("Using HYBRID DSPy flow generation (content preservation)")
                    #     from super.core.voice.pipeline.config import create_nodes_from_system_prompt
                    #
                    #     self.nodes = await create_nodes_from_system_prompt(self.user_state.system_prompt)
                    #
                    #     if self.nodes:
                    #         self._logger.info(f"✅ Hybrid flow: Generated {len(self.nodes)} nodes")
                    #     else:
                    #         self._logger.info("No flow section found in system_prompt")
                    # Initialize FlowManager (standard or ReAct)
                    if self.use_react_flows:
                        # Use ReActFlowManager for Think → Act → Observe loop
                        self._logger.info(
                            "🧠 Initializing ReActFlowManager with observation tracking"
                        )

                        # Create SharedQueueManager for state management
                        self.shared_queue = create_shared_queue_manager(
                            conversation_id=self.session_id,
                            redis_url=None,  # Will use in-memory for now
                            use_redis=False,
                        )
                        await self.shared_queue.initialize()
                        self._logger.info("✅ SharedQueueManager initialized")

                        # Start PassiveAgent background task
                        self._passive_agent_task = asyncio.create_task(
                            self.passive_agent.run()
                        )
                        self._logger.info("✅ PassiveAgent background task started")

                        if not self.conversation_flow:
                            plan = await self._get_or_create_conversation_plan()
                            # Create flow
                            self.conversation_flow = await create_flow_from_plan(plan)
                        # Extract ReAct components from config
                        # parsed = react_config.get("parsed_config", {})
                        # instructions = react_config.get("instructions", "")
                        # identity = react_config.get("identity", "")
                        # objections = react_config.get("objections", {})

                # Final fallback: document-based generation (legacy)
                # if not self.nodes:
                #     self._logger.info("Using document-based node generation (legacy)")
                #     from super.core.voice.pipeline.config import create_document_with_nodes
                #     self.nodes = await create_document_with_nodes()
                        self.flow_manager = ReActFlowManager(
                            conversation_flow=self.conversation_flow,
                            shared_queue=self.shared_queue,
                            task=self.task,
                            llm=self._llm_service,
                            context_aggregator=context_aggregator,
                            transport=self._transport,
                        )

                        # # Initialize ReAct configuration
                        # self.flow_manager.initialize_react_config(
                        #     instructions=instructions,
                        #     identity=identity,
                        #     objections=objections,
                        #     available_actions=[n.get('name', f'node_{i}') for i, n in enumerate(self.nodes or [])]
                        # )

                        self._logger.info(
                            "✅ ReActFlowManager initialized with %d steps",
                            len(self.conversation_flow.plan.steps)
                            if self.conversation_flow
                            else 0,
                        )
                    else:
                        # Use standard FlowManager
                        self.flow_manager = FlowManager(
                            task=self.task,
                            llm=self._llm_service,
                            context_aggregator=context_aggregator,
                            transport=self._transport,
                        )

                # Summary logging
                    if self.nodes:
                        flow_type = "section-based" if self.use_flows else "hybrid DSPy"
                        self._logger.info(f"📊 Flow generation complete: {len(self.nodes)} nodes ({flow_type})")
                        self._logger.debug(f"Flow nodes detail: {self.nodes}")
                    else:
                        self._logger.warning("⚠️  No flow nodes generated - will use default conversation mode")
                        # Summary logging
                        if self.nodes:
                            flow_type = (
                                "ReAct (Think→Act→Observe)"
                                if self.use_react_flows
                                else "section-based"
                                if self.use_flows
                                else "hybrid DSPy"
                            )
                            self._logger.info(
                                f"📊 Flow generation complete: {len(self.nodes)} nodes ({flow_type})"
                            )
                            self._logger.debug(f"Flow nodes detail: {self.nodes}")
                        else:
                            self._logger.warning(
                                "⚠️  No flow nodes generated - will use default conversation mode"
                            )
            except Exception as e:
                self._logger.error(e)

            # Daily-specific: Trigger dialout after pipeline starts
            @self._transport.event_handler("on_call_state_updated")
            async def on_call_state_updated(transport, state):
                self._logger.info(f"Call state updated: {state}")
                # For Daily transport with deferred dialout
                if (state == "joined" and
                    self.user_state.transport_type == "daily" and
                    hasattr(self.user_state, 'dialout_sip_uri') and
                    self.user_state.dialout_sip_uri):

                    # Retry logic for Daily dialout with fallback to alternate SIP domain
                    # Attempts 1-2: Use primary domain (UNPOD_SIP_DOMAIN: sip-up-tt.unpod.tv)
                    # Attempt 3: Use alternate domain (UNPOD_SIP_DOMAIN_ALT: sip.unpod.tel)
                    max_retries = 3
                    for attempt in range(max_retries):
                        attempt_num = attempt + 1

                        # On last attempt, try alternate SIP domain
                        if attempt_num == max_retries and hasattr(self.user_state, 'dialout_phone_number'):
                            self._logger.info(f"⚠️ Final attempt - switching to alternate SIP domain")
                            # Format SIP URI with alternate domain
                            alternate_sip_uri = self.sip_manager._format_sip_uri(
                                self.user_state.dialout_phone_number,
                                use_alternate=True
                            )
                            if alternate_sip_uri:
                                sip_uri = alternate_sip_uri
                                self._logger.info(f"Using alternate SIP URI: {sip_uri}")
                            else:
                                sip_uri = self.user_state.dialout_sip_uri  # Fallback to primary
                                self._logger.warning("Alternate SIP domain not available, using primary")
                        else:
                            sip_uri = self.user_state.dialout_sip_uri

                        self._logger.info(f"🔄 Attempt {attempt_num}/{max_retries} - Triggering Daily dialout to {sip_uri}")

                        try:
                            # Now the pipeline is running, so start_dialout will work
                            # Use SIP URI instead of phone number (Daily requirement)
                            # Reference: https://docs.daily.co/reference/rest-api/rooms/dialout/start
                            participant = await transport.start_dialout({
                                "sipUri": sip_uri,
                                "video": False  # Audio-only call
                            })
                            self._logger.info(f"✅ Daily dialout initiated successfully on attempt {attempt_num}: {participant}")
                            self.user_state.participant = participant
                            break  # Success - exit retry loop
                        except Exception as e:
                            self._logger.error(f"❌ Attempt {attempt_num}/{max_retries} - Failed to start Daily dialout: {e}")

                            if attempt_num == max_retries:
                                # Final attempt failed
                                self._logger.error(f"❌ All {max_retries} dialout attempts failed (tried both primary and alternate SIP domains)")
                                self.user_state.call_error = f"Daily dialout failed after {max_retries} attempts: {str(e)}"
                                self.user_state.call_status = "failed"
                                # Queue end frame to stop the pipeline
                                await self.task.queue_frame(EndFrame())
                            else:
                                # Wait before retry (exponential backoff: 1, 2 seconds)
                                wait_time = 2 ** attempt
                                self._logger.info(f"Waiting {wait_time} seconds before retry...")
                                await asyncio.sleep(wait_time)
                if (
                    state == "joined"
                    and self.user_state.transport_type == "daily"
                    and hasattr(self.user_state, "dialout_sip_uri")
                    and self.user_state.dialout_sip_uri
                ):
                    self._logger.info("Call joined - triggering Daily dialout...")
                    await self.daily_dialout_trigger(self._transport)

                elif state == "left":
                    self._logger.info("Call ended - cleaning up")
                    await self.task.cancel()

            @self._transport.event_handler("on_dialout_answered")
            async def on_dialout_answered(transport, data):
                self._logger.info(f"📞 Dialout answered: {data}")

                self.user_state.call_status = CallStatusEnum.CONNECTED

                session_id = data.get("sessionId")
                self.user_state.call_status = CallStatusEnum.CONNECTED

                if session_id:
                    await transport.capture_participant_transcription(session_id)
                    self._logger.info(
                        "Transcription capture enabled for dialout participant"
                    )

            @self._transport.event_handler("on_dialout_error")
            async def on_dialout_error(transport, data):
                self._logger.error(f"❌ Dialout error: {data}")
                self.user_state.call_error = f"Dialout error: {data}"

                self.user_state.call_status = CallStatusEnum.FAILED

                # Queue end frame to stop the pipeline
                self.user_state.call_status = CallStatusEnum.FAILED

                await self.task.queue_frame(EndFrame())

            @self._transport.event_handler("on_first_participant_joined")
            async def on_first_participant_joined(transport, participant_id):
                self._logger.info(
                    f"First participant {participant_id} joined. Starting interaction..."
                )
                self.user_state.start_time = datetime.now()
                await self.audio_buffer.start_recording()
                self.user_state.call_status = CallStatusEnum.CONNECTED

                self._send_start_message()
                if self.nodes and self.flow_manager:
                    # await self.task.queue_frame(TTSSpeakFrame("hello"))
                    await self.flow_manager.initialize(self.nodes[0])
                    # from super.core.voice.workflows.flows.general_flow.passive_agent import passive_agent
                    await asyncio.gather(
                        self.passive_agent.run(),
                        self.flow_manager.initialize(self.nodes[0]),
                    )

                # Handle background sound mixer if configured
                background_sound_enabled = self.config.get(
                    "background_sound_enabled", True
                )

                if (
                    background_sound_enabled
                    and hasattr(transport, "params")
                    and hasattr(transport.params, "audio_out_mixer")
                    and transport.params.audio_out_mixer
                ):
                    # ✅ OPTIMIZED: Run mixer adjustment in background to not block first message
                    # Previous implementation: 3s blocking delay (2s + 1s)
                    # New implementation: Non-blocking with configurable timing
                    async def _adjust_background_sound():
                        try:
                            # Configurable delay before lowering volume (default: 1.5s, was 2.0s)
                            delay_before = self.config.get(
                                "background_sound_delay_before", 1.5
                            )
                            # Configurable delay after lowering (default: 0.5s, was 1.0s)
                            delay_after = self.config.get(
                                "background_sound_delay_after", 0.5
                            )
                            # Configurable volume (default: 0.2)
                            conversation_volume = self.config.get(
                                "background_sound_conversation_volume", 0.2
                            )

                            self._logger.debug(
                                f"Adjusting background sound: delay={delay_before}s, volume={conversation_volume}"
                            )

                            await asyncio.sleep(delay_before)
                            await self.task.queue_frame(
                                MixerUpdateSettingsFrame(
                                    {"volume": conversation_volume}
                                )
                            )
                            await asyncio.sleep(delay_after)

                            self._logger.debug("Background sound adjusted successfully")
                        except Exception as e:
                            self._logger.warning(
                                f"Error controlling background sound mixer: {e}"
                            )

                    # Run in background - don't block first message
                    asyncio.create_task(_adjust_background_sound())
                    self._logger.info(
                        "Background sound adjustment scheduled (non-blocking)"
                    )

                # Use configurable first message from config
                first_message = self.config.get(
                    "first_message", "Hello! How can I help you today?"
                )
                first_message = self.prompt_manager._replace_template_params(
                    first_message
                )
                await self.task.queue_frame(TTSSpeakFrame(first_message))

                # Load previous chat context if available
                await self._load_chat_context()

            @self._transport.event_handler("on_participant_disconnected")
            async def on_participant_disconnected(transport, participant_id):
                self._logger.info(
                    f"Participant {participant_id} disconnected. Stopping pipeline..."
                )
                # CRITICAL: Shutdown state observer IMMEDIATELY to prevent Rust SDK panics
                # The LiveKit Rust SDK can panic if we try to update participant attributes
                # while the room connection is being torn down
                if self._livekit_state_observer:
                    self._livekit_state_observer.shutdown()

                session_id = self.user_state.thread_id
                self.user_state.end_reason = "Customer Ended The Call"
                self.agent_running = False
                session = self.active_sessions.get(session_id)
                self.user_state.end_time = datetime.now()
                self.user_state.call_status = CallStatusEnum.COMPLETED

                self._send_end_message()

                if session and session.pipeline_task:
                    try:
                        await session.pipeline_task.stop()
                        self._logger.info(f"Pipeline stopped for session {session_id}")
                    except Exception as e:
                        self._logger.error(f"Error stopping pipeline: {e}")
                self.user_state.call_status = CallStatusEnum.COMPLETED

                # Cleanup session
                self.active_sessions.pop(session_id, None)
                try:
                    self._transport = None
                    await self.task.queue_frame(EndFrame())
                except Exception as e:
                    self._logger.error(f"Error closing pipeline: {e}")

            @self._transport.event_handler("on_data_received")
            async def on_data_received(transport, data, participant_id):
                self._logger.info(
                    f"Received data from participant {participant_id}: {data}"
                )
                json_data = json.loads(data)

                await self.task.queue_frames(
                    [
                        BotInterruptionFrame(),
                        UserStartedSpeakingFrame(),
                        TranscriptionFrame(
                            user_id=participant_id,
                            timestamp=json_data["timestamp"],
                            text=json_data["message"],
                        ),
                        UserStoppedSpeakingFrame(),
                    ],
                )

            # Store in session for cleanup
            session_id = self.user_state.thread_id
            if session_id in self.active_sessions:
                self.active_sessions[session_id].pipeline_task = self.task
                self.active_sessions[session_id].context_aggregator = context_aggregator

            # Start pipeline
            self.runner = UpPipelineRunner()
            await self.runner.run(self.task)
        except Exception as e:
            import traceback

            traceback.print_exc()
            self._logger.error(f"Error in pipecat agent: {e}")
            raise e

    async def daily_dialout_trigger(self, transport):
        # Retry logic for Daily dialout with fallback to alternate SIP domain
        # Attempts 1-2: Use primary domain (UNPOD_SIP_DOMAIN: sip-up-tt.unpod.tv)
        # Attempt 3: Use alternate domain (UNPOD_SIP_DOMAIN_ALT: sip.unpod.tel)
        max_retries = 3
        for attempt in range(max_retries):
            attempt_num = attempt + 1

            # On last attempt, try alternate SIP domain
            if attempt_num == max_retries and hasattr(
                self.user_state, "dialout_phone_number"
            ):
                self._logger.info(
                    f"⚠️ Final attempt - switching to alternate SIP domain"
                )
                # Format SIP URI with alternate domain
                alternate_sip_uri = self.sip_manager._format_sip_uri(
                    self.user_state.dialout_from_number, use_alternate=True
                )
                if alternate_sip_uri:
                    sip_uri = alternate_sip_uri
                    self._logger.info(f"Using alternate SIP URI: {sip_uri}")
                else:
                    sip_uri = self.user_state.dialout_sip_uri  # Fallback to primary
                    self._logger.warning(
                        "Alternate SIP domain not available, using primary"
                    )
            else:
                sip_uri = self.user_state.dialout_sip_uri

            self._logger.info(
                f"🔄 Attempt {attempt_num}/{max_retries} - Triggering Daily dialout to {sip_uri}"
            )

            try:
                # Now the pipeline is running, so start_dialout will work
                # Use SIP URI instead of phone number (Daily requirement)
                # Reference: https://docs.daily.co/reference/rest-api/rooms/dialout/start
                participant = await transport.start_dialout(
                    {
                        "sipUri": sip_uri,
                        "phoneNumber": self.user_state.dialout_phone_number,
                        "video": False,  # Audio-only call
                    }
                )
                self._logger.info(
                    f"✅ Daily dialout initiated successfully on attempt {attempt_num}: {participant}"
                )
                self.user_state.participant = participant
                break  # Success - exit retry loop
            except Exception as e:
                self._logger.error(
                    f"❌ Attempt {attempt_num}/{max_retries} - Failed to start Daily dialout: {e}"
                )

                if attempt_num == max_retries:
                    # Final attempt failed
                    self._logger.error(
                        f"❌ All {max_retries} dialout attempts failed (tried both primary and alternate SIP domains)"
                    )
                    self.user_state.call_error = (
                        f"Daily dialout failed after {max_retries} attempts: {str(e)}"
                    )
                    self.user_state.call_status = "failed"
                    # Queue end frame to stop the pipeline
                    await self.task.queue_frame(EndFrame())
                else:
                    # Wait before retry (exponential backoff: 1, 2 seconds)
                    wait_time = 2**attempt
                    self._logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)

    async def _create_pipeline(self, transport, rtvi):
        """
        Create pipecat pipeline with STT, LLM, and TTS.

        Supports two modes:
        - Standard mode: Separate STT -> LLM -> TTS pipeline
        - Realtime mode: OpenAI Realtime API (integrated audio input/output)

        Args:
            transport: Transport instance
            rtvi: RTVI processor instance

        Returns:
            Tuple of (pipeline, context_aggregator)
        """
        self._logger.info("Creating pipecat pipeline with config - %s", self.config)
        self.sections = await self._parse_section()
        if self.config is None:
            self.config = self.user_state.model_config

        # Determine pipeline mode
        is_realtime_mode = self.use_realtime
        is_mixed_mode = self.mixed_realtime_mode

        # Log pipeline mode
        if is_realtime_mode and is_mixed_mode:
            self._logger.info(
                "🔀 Mixed Realtime Pipeline: Realtime LLM (text) -> Separate TTS"
            )
        elif is_realtime_mode:
            self._logger.info(
                "⚡ Full Realtime Pipeline: Realtime LLM (integrated audio)"
            )
        else:
            self._logger.info("🔧 Standard Pipeline: Separate STT -> LLM -> TTS")

        # Use pre-initialized services if available, otherwise create new ones
        if self._services_initialized and self._llm_service:
            self._logger.info("Using pre-initialized services")
            # Determine which services to use based on mode
            if is_realtime_mode and not is_mixed_mode:
                # Full realtime: Only LLM (integrated STT/TTS)
                stt_service = None
                tts_service = None
            elif is_realtime_mode and is_mixed_mode:
                # Mixed realtime: LLM + TTS (Realtime handles STT)
                stt_service = None
                tts_service = self._tts_service
            else:
                # Standard mode: All three services
                stt_service = self._stt_service
                tts_service = self._tts_service

            llm_service = self._llm_service
            context_aggregator = self._context_aggregator
        else:
            self._logger.info("Creating services on-demand")
            # Get services from ServiceFactory with retry logic
            # Determine which services to create based on mode
            if is_realtime_mode and not is_mixed_mode:
                # Full realtime: Only LLM (integrated STT/TTS)
                self._logger.info(
                    "Full realtime: Creating only LLM service (integrated audio)"
                )
                stt_service = None
                tts_service = None
            elif is_realtime_mode and is_mixed_mode:
                # Mixed realtime: LLM + TTS (Realtime handles STT, outputs text)
                self._logger.info("Mixed realtime: Creating LLM + TTS services")
                stt_service = None
                tts_service = (
                    await self.service_factory._create_tts_service_with_retry()
                )
            else:
                # Standard mode: All three services
                self._logger.info("Standard mode: Creating STT + LLM + TTS services")
                stt_service = (
                    await self.service_factory._create_stt_service_with_retry()
                )
                tts_service = (
                    await self.service_factory._create_tts_service_with_retry()
                )

            llm_service = await self.service_factory._create_llm_service_with_retry()

            self._llm_service = llm_service

            # Check if required services are available based on mode
            if not llm_service:
                raise Exception(
                    "LLM service could not be created - missing API keys or service unavailable"
                )

            if is_realtime_mode and not is_mixed_mode:
                # Full realtime: Only LLM needed
                self._logger.info(
                    "✓ Full realtime mode: LLM service validated (STT/TTS integrated)"
                )
            elif is_realtime_mode and is_mixed_mode:
                # Mixed realtime: Need LLM + TTS
                if not tts_service:
                    raise Exception(
                        "Mixed realtime mode: TTS service could not be created - missing API keys or service unavailable"
                    )
                self._logger.info("✓ Mixed realtime mode: LLM + TTS services validated")
            else:
                # Standard mode: Need all three services
                if not stt_service:
                    raise Exception(
                        "Standard mode: STT service could not be created - missing API keys or service unavailable"
                    )
                if not tts_service:
                    raise Exception(
                        "Standard mode: TTS service could not be created - missing API keys or service unavailable"
                    )
                self._logger.info(
                    "✓ Standard mode: All services (STT/LLM/TTS) validated"
                )

            # Register functions for tool calling (both standard and realtime modes)
            if self._tool_calling:
                llm_service.register_function("get_knowledge_base_info", self.get_docs)
                llm_service.register_function("handover_call", self._handover_call)

            # Create context with tools
            context = self._create_context_with_tools()
            # LLM service handles creating the appropriate context aggregator (standard or realtime)
            # Use 50ms aggregation timeout for faster turn boundaries (reduces latency by 50-200ms)
            aggregation_timeout = self.config.get("context_aggregation_timeout", 0.05)
            context_aggregator = llm_service.create_context_aggregator(
                context,
                user_params=LLMUserAggregatorParams(
                    aggregation_timeout=aggregation_timeout
                ),
            )
            self._llm_service = llm_service
            self._tts_service = tts_service
            self._stt_service = stt_service

        # Only register TTS event handler for standard mode (realtime handles this internally)
        if tts_service:

            @llm_service.event_handler("on_function_calls_started")
            async def on_function_calls_started(service, function_calls):
                await tts_service.queue_frame(TTSSpeakFrame(""))

        transcript = TranscriptProcessor()

        @transcript.event_handler("on_transcript_update")
        async def handle_update(processor, frame):
            # Debug: Print shared queue state only if react flows enabled
            if self.use_react_flows and self.shared_queue is not None:
                try:
                    print(self.shared_queue._state.to_dict())
                except Exception as e:
                    self._logger.debug(f"Could not print shared queue state: {e}")

            for message in frame.messages:
                if message.role == "user":
                    # Convert TranscriptionMessage to serializable dict
                    transcript_entry = {
                        "role": message.role,
                        "content": message.content,
                        "user_id": getattr(message, "user_id", None),
                        "timestamp": str(getattr(message, "timestamp", None)),
                    }
                    self.user_state.transcript.append(transcript_entry)

                    msg = Message.create(
                        message.content,
                        user=self.user_state.user,
                        event=Event.USER_MESSAGE,
                    )

                    self._send_callback(msg, thread_id=self.user_state.thread_id)

                    # Publish user transcript to LiveKit
                    await self._publish_livekit_transcript(
                        role="user",
                        content=message.content,
                        is_final=True,
                    )

                if message.role == "assistant":
                    # Convert TranscriptionMessage to serializable dict
                    transcript_entry = {
                        "role": message.role,
                        "content": message.content,
                        "user_id": getattr(message, "user_id", None),
                        "timestamp": str(getattr(message, "timestamp", None)),
                    }
                    self.user_state.transcript.append(transcript_entry)

                    outputText = message.content

                    msg = Message.create(
                        message.content, user=self.agent, event=Event.AGENT_MESSAGE
                    )
                    self._send_callback(msg, thread_id=self.user_state.thread_id)

                    # Publish assistant transcript to LiveKit
                    await self._publish_livekit_transcript(
                        role="assistant",
                        content=message.content,
                        is_final=True,
                    )

                    if self.prompt_manager._needs_language_correction(outputText):
                        self._logger.info("Language correction - %s", outputText)
                        # await self._prompt_language_correction()

        # Create an LLM for classification
        classifier_llm = llm_service

        # Initialize the detector
        voicemail_detector = VoicemailDetector(
            llm=classifier_llm,
            voicemail_response_delay=2.0
        )
        # Skip VoicemailDetector and UserIdleProcessor in fast path mode
        # These add 500-1500ms latency and complexity
        if not self.use_fast_path_pipeline:
            # Create an LLM for classification
            classifier_llm = llm_service
            # Initialize the detector
            voicemail_detector = VoicemailDetector(
                llm=classifier_llm, voicemail_response_delay=2.0
            )

            # ⚠️ COST WARNING: VoicemailDetector uses LLM for classification
            # This adds latency (500-1500ms) and token cost to each call start
            # Consider implementing acoustic-based detector (beep detection, silence patterns)
            # for better performance and lower cost
            self._logger.info(
                "VoicemailDetector initialized using LLM classification. "
                "This adds ~500-1500ms latency and LLM token cost per call. "
                "Consider acoustic-based detection for production optimization."
            )

            @voicemail_detector.event_handler("on_voicemail_detected")
            async def handle_voicemail(processor):
                self._logger.info("Voicemail detected! Leaving a message...")

                await processor.push_frame(
                    TTSSpeakFrame(
                        "Hello we are unable to connect with you right now, I Will Call You Later."
                    )
                )
                await self.task.queue_frame(EndFrame())

            # Delegate idle user handling to TransportManager
            async def idle_callback(processor, retry_count):
                return await self.transport_manager.handle_idle_user(
                    processor, retry_count
                )

            # Configure user idle timeout (time without speech before warnings/disconnect)
            # Default: 30 seconds (more reasonable than previous 10s hardcoded value)
            # Allows time for users to think, read, or look up information
            idle_timeout = self.config.get("idle_timeout", 30.0)

            self._logger.info(f"User idle timeout configured: {idle_timeout}s")

            # Warn if timeout is aggressively short
            if idle_timeout < 15.0:
                self._logger.warning(
                    f"Idle timeout {idle_timeout}s is aggressive (<15s). "
                    "Users may be disconnected while thinking, reading, or looking up information. "
                    "Consider increasing to 20-30s for better user experience."
                )

            idle_user_detection = UserIdleProcessor(
                callback=idle_callback,
                timeout=idle_timeout,  # ✅ CONFIG-DRIVEN: Respects database/config settings (was hardcoded 10.0)
            )
        else:
            self._logger.info(
                "🚀 Fast path mode: Skipping VoicemailDetector and UserIdleProcessor "
                "(saves 500-1500ms latency)"
            )

        from pipecat.processors.audio.audio_buffer_processor import AudioBufferProcessor

        self.audio_buffer = AudioBufferProcessor(
            num_channels=2,
            enable_turn_audio=False,
        )

        @self.audio_buffer.event_handler("on_audio_data")
        async def on_audio_data(buffer, audio, sample_rate, num_channels):
            await self._handle_audio_capture(audio, sample_rate, num_channels)

        # Build pipeline based on mode
        # Standard: transport -> STT -> LLM -> TTS -> transport
        # Full Realtime: transport -> Realtime LLM (integrated audio) -> transport
        # Mixed Realtime: transport -> Realtime LLM (text output) -> TTS -> transport
        # Fast Path: Minimal linear pipeline without parallel branches
        pipeline_stages = [transport.input()]

        # Add STT for standard mode only
        # (Full realtime and mixed realtime have integrated STT in Realtime LLM)
        if stt_service:
            pipeline_stages.append(stt_service)
            self._logger.debug("✓ Added STT service to pipeline (standard mode)")

        # Add RAG processor if enabled (synchronous context enrichment before LLM)
        # This reduces latency by 500-2000ms vs tool-call based RAG
        if self.use_rag_processor and self._kb_enabled and self.knowledge_base_manager:
            similarity_top_k = self.config.get("rag_similarity_top_k", 3)
            self._rag_processor = create_rag_processor(
                knowledge_base_manager=self.knowledge_base_manager,
                similarity_top_k=similarity_top_k,
                enabled=True,
                logger=self._logger,
            )
            pipeline_stages.append(self._rag_processor)
            self._logger.info(
                f"✓ Added RAG processor to pipeline "
                f"(similarity_top_k={similarity_top_k})"
            )
            self._register_optimization(
                "Synchronous RAG processor enabled for inline context enrichment"
            )

        # # Fast path: Linear pipeline without parallel branches (50-100ms latency reduction)
        # if self.use_fast_path_pipeline:
        #     # Simple linear flow: context_aggregator.user() -> llm_service
        #     pipeline_stages.append(context_aggregator.user())
        #     pipeline_stages.append(llm_service)
        #     self._logger.debug("✓ Added LLM service to pipeline (fast path - linear)")
        # else:
        # Standard: User processing with parallel transcript tracking
        pipeline_stages.append(
            ParallelPipeline(
                [context_aggregator.user(), llm_service], [transcript.user()]
            )
        )
        self._logger.debug("✓ Added LLM service to pipeline (with parallel transcript)")

        # Add streaming text parser if enabled (reduces TTS latency by 500-1500ms)
        # The parser enables TTS to start while LLM is still generating
        if self.use_streaming_parser and tts_service:
            # Configure parser based on config
            streamable_fields = self.config.get(
                "streaming_parser_fields",
                ["spoke_response", "response", "text", "answer", "content"],
            )
            min_chunk_size = self.config.get("streaming_parser_min_chunk", 1)

            self._streaming_parser_processor = create_streaming_parser_processor(
                streamable_fields=streamable_fields,
                min_chunk_size=min_chunk_size,
                enabled=True,
                logger=self._logger,
            )
            pipeline_stages.append(self._streaming_parser_processor)
            self._logger.info(
                f"✓ Added streaming text parser to pipeline "
                f"(fields: {streamable_fields}, min_chunk: {min_chunk_size})"
            )
            self._register_optimization(
                "Streaming text parser enabled for early TTS synthesis"
            )
        # User processing (parallel: transcript tracking + context/LLM)
        pipeline_stages.append(ParallelPipeline(
            [
                context_aggregator.user(),
                llm_service
            ],
            [
                transcript.user()
            ]
        ))
        self._logger.debug("✓ Added LLM service to pipeline")

        # Add TTS service if available
        # - Standard mode: Separate TTS
        # - Mixed realtime: Separate TTS (Realtime outputs text)
        # - Full realtime: No TTS (Realtime outputs audio directly)
        if tts_service:
            pipeline_stages.append(tts_service)
            self._logger.debug("✓ Added TTS service to pipeline")

        # Add silence trimmer if enabled (reduces perceived latency by 100-300ms)
        # Trims leading silence from TTS audio for snappier responses
        if self.use_silence_trimmer:
            silence_threshold = self.config.get("silence_threshold_db", -50.0)
            sample_rate = self.config.get("tts_sample_rate", 24000)
            self._silence_trimmer = create_silence_trimmer(
                silence_threshold_db=silence_threshold,
                sample_rate=sample_rate,
                enabled=True,
                logger=self._logger,
            )
            pipeline_stages.append(self._silence_trimmer)
            self._logger.info(
                f"✓ Added silence trimmer to pipeline "
                f"(threshold={silence_threshold}dB, sample_rate={sample_rate}Hz)"
            )
            self._register_optimization(
                "Silence trimmer enabled for snappier TTS responses"
            )

        # Standard: Assistant processing with parallel transcript tracking
        pipeline_stages.append(
            ParallelPipeline(
                [transport.output(), self.audio_buffer, context_aggregator.assistant()],
                [transcript.assistant()],
            )
        )
        self._logger.debug(
            "✓ Added transport output to pipeline (with parallel transcript)"
        )

        pipeline = Pipeline(pipeline_stages)

        # Log final pipeline configuration
        if self.use_fast_path_pipeline:
            mode_name = "Fast Path"
            self._register_optimization(
                "Fast path pipeline enabled (linear flow, no parallel branches)"
            )
        elif is_realtime_mode and is_mixed_mode:
            mode_name = "Mixed Realtime"
        elif is_realtime_mode:
            mode_name = "Full Realtime"
        else:
            mode_name = "Standard"
        self._logger.info(
            f"✅ Pipeline created with {len(pipeline_stages)} stages ({mode_name} mode)"
        )

        return pipeline, context_aggregator

    async def end_ongoing_agent(self):
        await self.task.queue_frame(EndFrame())

    async def end_call(self, reason: str = "completed") -> str:
        """
        End the current call gracefully.

        Args:
            reason: Reason for ending the call (completed, busy, error, etc.)

        Returns:
            Confirmation message
        """
        self._logger.info(f"Ending call with reason: {reason}")

        # Set a flag to indicate we're shutting down
        self._is_shutting_down = True
        await self._shutdown_background_workers()
        self.user_state.call_status = CallStatusEnum.COMPLETED
        try:
            # Stop any ongoing processing
            if hasattr(self, "task") and self.task:
                try:
                    self._logger.info("Stopping pipeline task...")
                    # First try to stop the task gracefully
                    if hasattr(self.task, "stop"):
                        await self.task.stop()

                    # Then queue end frame as a fallback
                    try:
                        await self.task.queue_frame(EndFrame())
                        # ✅ FIXED: Use wait_for with timeout instead of hardcoded sleep
                        # Wait for task to finish processing, but don't block indefinitely
                        try:
                            await asyncio.wait_for(
                                asyncio.shield(asyncio.sleep(0.5)),  # Max wait time
                                timeout=0.5,
                            )
                        except asyncio.TimeoutError:
                            pass  # Expected timeout, continue cleanup
                    except Exception as frame_error:
                        self._logger.warning(f"Error queuing end frame: {frame_error}")

                except Exception as e:
                    self._logger.error(f"Error stopping task: {e}")
                finally:
                    self.task = None

            # Clean up transport
            transport = getattr(self, "_transport", None)
            if transport:
                cleanup_success = False
                try:
                    self._logger.info("Disconnecting transport...")
                    if hasattr(transport, "disconnect"):
                        await transport.disconnect()
                    if hasattr(transport, "cleanup"):
                        await transport.cleanup()
                    self._logger.info("Transport disconnected and cleaned up")
                    cleanup_success = True
                except Exception as e:
                    self._logger.error(f"Error during transport cleanup: {e}")
                    self._logger.warning(
                        "Transport cleanup failed - connection may remain open"
                    )
                finally:
                    # ✅ FIXED: Only set to None if cleanup was successful
                    if cleanup_success:
                        self._transport = None
                    else:
                        self._logger.warning(
                            "Transport reference kept due to cleanup failure"
                        )

            # Clean up active sessions
            if hasattr(self, "active_sessions"):
                self._logger.info(
                    f"Cleaning up {len(self.active_sessions)} active sessions..."
                )
                for session_id in list(self.active_sessions.keys()):
                    session = self.active_sessions.pop(session_id, None)
                    if session:
                        try:
                            if (
                                hasattr(session, "pipeline_task")
                                and session.pipeline_task
                            ):
                                self._logger.info(
                                    f"Stopping pipeline task for session {session_id}"
                                )
                                try:
                                    await session.pipeline_task.stop()
                                except Exception as e:
                                    self._logger.error(
                                        f"Error stopping pipeline task: {e}"
                                    )
                                # ✅ FIXED: No delay needed between stopping tasks - they stop concurrently
                        except Exception as e:
                            self._logger.error(
                                f"Error cleaning up session {session_id}: {e}"
                            )
                self.active_sessions.clear()

            # Update end time
            if hasattr(self, "user_state"):
                self.user_state.end_time = datetime.now()

                # Prepare call evaluation data if we have a transcript
                if hasattr(self.user_state, 'transcript') and self.user_state.transcript:
                    try:
                        # Get the audio file path if available
                        audio_file_path = None
                        if hasattr(self, '_recordings_dir') and hasattr(self, '_session_id'):
                            # Look for the most recent recording file for this session
                            recording_files = list(self._recordings_dir.glob(f"{self._session_id}*.wav"))
                            if recording_files:
                                # Sort by modification time and get the most recent
                                recording_files.sort(key=os.path.getmtime, reverse=True)
                                audio_file_path = recording_files[0]

                        # Prepare transcript data with timing information if available
                        transcript_data = {
                            'transcript': self.user_state.transcript,
                            'start_time': getattr(self.user_state, 'start_time', None),
                            'end_time': self.user_state.end_time.isoformat(),
                            'call_id': getattr(self, '_session_id', None),
                            'agent_id': getattr(self, 'call_data', {}).get('agent_id', 'default_agent')
                        }

                        # Only evaluate if we have both audio and transcript
                        if audio_file_path and os.path.exists(audio_file_path):
                            self._logger.info(f"Initiating call evaluation for session {self._session_id}")
                            # Run evaluation in the background without waiting for it to complete
                            try:
                                # Create the evaluation task but don't await it
                                evaluation_task = asyncio.create_task(
                                    self._evaluate_call(audio_file_path, transcript_data)
                                )

                                # Add a callback to log completion or errors
                                def log_evaluation_result(task):
                                    try:
                                        task.result()  # This will raise any exceptions
                                        self._logger.info("Call evaluation completed successfully")
                                    except Exception as e:
                                        if isinstance(e, asyncio.CancelledError):
                                            self._logger.warning("Call evaluation was cancelled")
                                        else:
                                            self._logger.error(f"Error during call evaluation: {str(e)}", exc_info=True)

                                evaluation_task.add_done_callback(log_evaluation_result)

                            except Exception as e:
                                self._logger.error(f"Failed to start call evaluation: {str(e)}", exc_info=True)
                        else:
                            self._logger.warning(
                                f"Skipping call evaluation: Audio file not found at {audio_file_path}"
                            )

                    except Exception as e:
                        self._logger.error(f"Error during call evaluation setup: {str(e)}", exc_info=True)

            # Try to delete the LiveKit room
            try:
                job_ctx = get_job_context()
                if job_ctx:
                    self._logger.info("Cleaning up LiveKit resources...")
                    if hasattr(job_ctx, "room") and job_ctx.room:
                        if hasattr(job_ctx.room, "disconnect"):
                            await job_ctx.room.disconnect()
                    if (
                        hasattr(job_ctx, "api")
                        and hasattr(job_ctx, "room")
                        and job_ctx.room
                    ):
                        try:
                            await job_ctx.api.room.delete_room(
                                api.DeleteRoomRequest(room=job_ctx.room.name)
                            )
                            self._logger.info("LiveKit room deleted successfully")
                        except Exception as delete_error:
                            self._logger.warning(
                                f"Could not delete LiveKit room: {delete_error}"
                            )
            except Exception as e:
                self._logger.warning(f"Error during LiveKit cleanup: {e}")

            self._logger.info("Call ended successfully")
            return f"Call ended successfully. Reason: {reason}"

        except Exception as e:
            error_msg = f"Error ending call: {str(e)}"
            self._logger.error(error_msg)
            return error_msg

    def _create_context_with_tools(self):
        """
        Create LLM context with knowledge base tools.
        Delegates to PromptManager.
        """
        if not self._kb_enabled:
            original_kb = self.prompt_manager.config.get("knowledge_bases")
            self.prompt_manager.config["knowledge_bases"] = []
            try:
                context = self.prompt_manager._create_context_with_tools()
            finally:
                if original_kb is not None:
                    self.prompt_manager.config["knowledge_bases"] = original_kb
                else:
                    self.prompt_manager.config.pop("knowledge_bases", None)
        else:
            context = self.prompt_manager._create_context_with_tools()

        return context

    async def get_docs(self, query, params: FunctionCallParams = None):
        # Handle both dict and string query parameters
        # Flows framework passes dict like {'query': 'search term'}
        # Direct calls pass string 'search term'
        if isinstance(query, dict):
            query_str = query.get("query", "")
        else:
            query_str = query

        return await self.knowledge_base_manager.get_docs(
            params=params, query=query_str, user_state=self.user_state
        )

    async def _handover_call(self, params: FunctionCallParams = None):
        return await self.sip_manager.handover_call()

    def get_user_state(self, room_name: str, model_config: Dict[str, Any]) -> UserState:
        return get_user_state(room_name, model_config)

    def create_usage(self, user_state: UserState) -> Dict[str, Any]:
        return create_usage(user_state)

    def _get_default_config(
        self, agent_name: str = None, knowledge_bases: List = None
    ) -> Dict[str, Any]:
        agent_name = agent_name or self.agent_config.agent_name
        return _get_default_config(agent_name, knowledge_bases)
    async def _evaluate_call(self, audio_file_path: Path, transcript_data: Union[list, dict]):
        """
        Evaluate the call using VoiceCallEvaluator and save results to the database.

        Args:
            audio_file_path: Path to the saved audio file
            transcript_data: Either a list of messages or a dict with a 'transcript' key
                            containing the conversation messages

        Returns:
            dict: Dictionary containing evaluation results and metrics or None if evaluation fails
        """
        try:
            await self._shutdown_background_workers()
            if hasattr(self, "task") and self.task:
                await self.task.stop()
            if hasattr(self, "runner") and self.runner:
                await self.runner.cancel()
            await shutdown()
            self._logger.info("Starting call evaluation process...")

            # Extract transcript from data if needed
            if isinstance(transcript_data, dict) and 'transcript' in transcript_data:
                transcript = transcript_data['transcript']
                call_data = transcript_data
            else:
                transcript = transcript_data
                call_data = {}

            if not transcript:
                self._logger.warning("Skipping call evaluation: No transcript provided")
                return None

            # Get or create session ID and agent ID
            session_id = getattr(self, '_session_id', f"session_{int(time.time())}")
            agent_id = getattr(self, 'call_data', {}).get('agent_id', 'default_agent')

            # Set up base directory paths
            base_dir = Path(__file__).parent / "voice_agent_evals"
            recordings_dir = base_dir / "db-and-recordings"

            # Ensure the recordings directory exists and is writable
            try:
                recordings_dir.mkdir(parents=True, exist_ok=True)
                # Test if directory is writable
                test_file = recordings_dir / ".write_test"
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                self._logger.error(f"Cannot write to recordings directory {recordings_dir}: {e}")
                # Fallback to /tmp if the default directory is not writable
                recordings_dir = Path("/tmp/voice_agent_evals")
                recordings_dir.mkdir(parents=True, exist_ok=True)
                self._logger.info(f"Falling back to temporary directory: {recordings_dir}")

            # Set up database path
            db_path = str(recordings_dir / "voice_evaluations.db")

            # Create the database file if it doesn't exist and set permissions
            try:
                if not os.path.exists(db_path):
                    with open(db_path, 'w'):
                        pass
                    os.chmod(db_path, 0o666)  # Ensure it's writable by all
                    self._logger.info(f"Created new database file at: {db_path}")

                # Verify database is writable
                import sqlite3
                test_conn = sqlite3.connect(db_path)
                test_cursor = test_conn.cursor()
                test_cursor.execute("PRAGMA journal_mode=WAL;")  # Enable WAL mode for better concurrency
                test_conn.close()

            except Exception as e:
                self._logger.error(f"Failed to initialize database at {db_path}: {e}")
                # Fallback to in-memory database if file-based fails
                db_path = ":memory:"
                self._logger.warning(f"Falling back to in-memory database")

            self._logger.info(f"Using database: {db_path}")
            self._logger.info(f"Recordings directory: {recordings_dir}")

            # Import here to avoid circular imports
            try:
                from super.core.voice.voice_agent_evals.voice_evaluation import VoiceCallEvaluator
            except ImportError as e:
                self._logger.error(f"Failed to import VoiceCallEvaluator: {e}")
                return None

            try:
                # Initialize evaluator with proper error handling
                try:
                    evaluator = VoiceCallEvaluator(
                        db_path=db_path,
                        recordings_dir=str(recordings_dir)
                    )
                    self._logger.info("Initialized VoiceCallEvaluator successfully")
                except Exception as e:
                    self._logger.error(f"Failed to initialize VoiceCallEvaluator: {str(e)}", exc_info=True)
                    return None

                # Get call timing information
                call_start_time = time.time() - 300  # Default fallback (5 minutes ago)
                call_end_time = time.time()

                # Try to get timestamps from call data or user state
                if hasattr(self, 'user_state'):
                    if hasattr(self.user_state, 'start_time'):
                        call_start_time = self.user_state.start_time.timestamp()
                        self._logger.info(f"Using start time from user state: {self.user_state.start_time}")

                    if hasattr(self.user_state, 'end_time'):
                        call_end_time = self.user_state.end_time.timestamp()
                        self._logger.info(f"Using end time from user state: {self.user_state.end_time}")

                # Fallback to call_data if user_state doesn't have timing info
                if call_start_time == time.time() - 300:  # If still using default
                    if 'start_time' in call_data and call_data['start_time']:
                        try:
                            call_start_time = datetime.fromisoformat(call_data['start_time'].replace('Z', '+00:00')).timestamp()
                        except (ValueError, AttributeError) as e:
                            self._logger.warning(f"Invalid start_time format: {call_data['start_time']}, error: {e}")

                if call_end_time == time.time():
                    if 'end_time' in call_data and call_data['end_time']:
                        try:
                            call_end_time = datetime.fromisoformat(call_data['end_time'].replace('Z', '+00:00')).timestamp()
                        except (ValueError, AttributeError) as e:
                            self._logger.warning(f"Invalid end_time format: {call_data['end_time']}, error: {e}")

                # Convert Path to string and ensure it's a relative path
                audio_file_str = str(audio_file_path)
                if str(recordings_dir) in audio_file_str:
                    # Make path relative to recordings directory
                    audio_file_str = str(Path(audio_file_str).relative_to(recordings_dir))

                # Verify audio file exists and is accessible
                full_audio_path = recordings_dir / audio_file_str
                if not full_audio_path.exists() or not os.access(full_audio_path, os.R_OK):
                    self._logger.warning(f"Audio file not found or not readable at: {full_audio_path}")

                    # Try to find the file with a different extension or by session ID
                    wav_files = list(recordings_dir.glob(f"{session_id}*.wav"))
                    if not wav_files:
                        # Try more flexible pattern matching
                        wav_files = list(recordings_dir.glob(f"*{session_id}*.wav"))

                    if wav_files:
                        # Sort by modification time to get the most recent
                        wav_files.sort(key=os.path.getmtime, reverse=True)
                        full_audio_path = wav_files[0]
                        audio_file_str = str(full_audio_path.relative_to(recordings_dir))
                        self._logger.info(f"Found matching audio file: {full_audio_path}")
                    else:
                        self._logger.error("No matching audio file found for this session")
                        return None

                # Ensure the audio file has the correct permissions
                try:
                    os.chmod(full_audio_path, 0o666)
                except Exception as e:
                    self._logger.warning(f"Could not set permissions on audio file: {e}")

                # Prepare transcript data if it's not already in the right format
                if not isinstance(transcript, list):
                    transcript = [{"role": "user", "content": str(transcript)}]

                # Save call session with the audio file path
                try:
                    self._logger.info(f"Saving call session to database: {session_id}")
                    self._logger.info(f"Audio file path to be saved: {audio_file_str}")

                    # Ensure the audio file path is not None or empty
                    if not audio_file_str:
                        self._logger.warning("Audio file path is empty, using 'unknown_audio.wav' as fallback")
                        audio_file_str = f"{session_id}_unknown_audio.wav"

                    # Ensure the file has a .wav extension
                    if not audio_file_str.lower().endswith('.wav'):
                        audio_file_str = f"{os.path.splitext(audio_file_str)[0]}.wav"
                        self._logger.info(f"Added .wav extension to audio file path: {audio_file_str}")

                    # Save to database
                    evaluator.save_call_session(
                        session_id=session_id,
                        agent_id=agent_id,
                        call_start_time=call_start_time,
                        call_end_time=call_end_time,
                        transcript=transcript,
                        audio_file_path=audio_file_str  # Save relative path
                    )
                    self._logger.info(f"Successfully saved call session with audio file: {audio_file_str}")

                    # Verify the record was saved
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT audio_file_path FROM call_session WHERE session_id = ?",
                            (session_id,)
                        )
                        result = cursor.fetchone()
                        if result:
                            self._logger.info(f"Verified database record - Audio file path: {result[0]}")
                        else:
                            self._logger.error("Failed to verify database record - session not found")
                except Exception as e:
                    self._logger.error(f"Error saving call session to database: {str(e)}", exc_info=True)
                    # Try to continue with evaluation even if saving session fails
                    return None
                turn_number = 0
                user_turn = None

                for i, message in enumerate(transcript):
                    role = message.get('role', '').lower()
                    content = message.get('content', '')
                    timestamp_str = message.get('timestamp')

                    # Parse timestamp if available, otherwise use relative timing
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).timestamp()
                        except (ValueError, AttributeError):
                            timestamp = call_start_time + (i * 30)  # Fallback to relative timing
                            self._logger.warning(f"Invalid timestamp format: {timestamp_str}")
                    else:
                        timestamp = call_start_time + (i * 30)  # Default relative timing

                    if role == 'user':
                        user_turn = {
                            'text': content,
                            'timestamp': timestamp
                        }
                    elif role == 'assistant' and user_turn:
                        turn_number += 1
                        # Calculate response time based on timestamps if available
                        response_time = timestamp - user_turn['timestamp'] if 'timestamp' in user_turn else 5.0

                        evaluator.save_conversation_turn(
                            session_id=session_id,
                            turn_number=turn_number,
                            turn_start_time=user_turn['timestamp'],
                            turn_end_time=timestamp,
                            user_speech_text=user_turn['text'],
                            llm_response_text=content,
                            voice_to_voice_response_time=response_time,
                            interrupted=False
                        )
                        user_turn = None

                import asyncio

                # Create a new event loop for the async call
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # Get turn metrics from observer if available
                    turn_metrics = None
                    if hasattr(self, 'observer_instance') and hasattr(self.observer_instance, 'get_all_turn_metrics'):
                        turn_metrics = self.observer_instance.get_all_turn_metrics()
                        self._logger.info(f"Retrieved turn metrics for {len(turn_metrics)} turns from observer")
                        self._logger.info(f"Turn metrics keys: {list(turn_metrics.keys())}")
                        # Log summary of each turn's metrics
                        for turn_key, turn_data in turn_metrics.items():
                            costs = turn_data.get("costs", {})
                            latencies = turn_data.get("latencies", {})
                            self._logger.info(f"{turn_key}: costs={{llm: {costs.get('llm_cost', 0):.4f}, stt: {costs.get('stt_cost', 0):.4f}, tts: {costs.get('tts_cost', 0):.4f}}}, latencies={{llm: {latencies.get('llm_latency', 0):.2f}ms}}")

                    # Run the async evaluation with turn metrics
                    evaluation_results = loop.run_until_complete(
                        evaluator.evaluate_call_quality(session_id, transcript, turn_metrics=turn_metrics)
                    )

                    # Calculate quality metrics
                    quality_metrics = evaluator.calculate_quality_metrics(session_id)

                    self._logger.info(
                        f"Call evaluation completed for session {session_id}. "
                        f"Quality score: {quality_metrics.get('overall_quality_score', 0):.2f}"
                    )

                    # Ensure call_data has post_call_data
                    if 'post_call_data' not in call_data:
                        call_data['post_call_data'] = {}

                    # Ensure call_evaluation exists in post_call_data
                    if 'call_evaluation' not in call_data['post_call_data']:
                        call_data['post_call_data']['call_evaluation'] = []

                    # Store evaluation results in call_evaluation array
                    if evaluation_results:
                        if isinstance(evaluation_results, list):
                            # Extend with new evaluations, ensuring no duplicates
                            existing_ids = {e.get('evaluation_id') for e in call_data['post_call_data']['call_evaluation']}
                            for eval_result in evaluation_results:
                                if eval_result.get('evaluation_id') not in existing_ids:
                                    call_data['post_call_data']['call_evaluation'].append(eval_result)
                        else:
                            # Single evaluation result
                            if not any(e.get('evaluation_id') == evaluation_results.get('evaluation_id')
                                     for e in call_data['post_call_data']['call_evaluation']):
                                call_data['post_call_data']['call_evaluation'].append(evaluation_results)

                    # Add/update quality metrics in post_call_data
                    call_data['post_call_data']['quality_metrics'] = quality_metrics
                    call_data['post_call_data']['evaluation_summary'] = {
                        'overall_quality': quality_metrics.get('overall_quality_score', 0),
                        'evaluation_count': len(call_data['post_call_data']['call_evaluation']),
                        'last_updated': datetime.datetime.utcnow().isoformat(),
                        'session_id': session_id
                    }

                    # Also return the evaluation data in the response
                    return {
                        'session_id': session_id,
                        'evaluation_results': evaluation_results,
                        'quality_metrics': quality_metrics,
                        'audio_file_path': str(audio_file_path),
                        'post_call_data': call_data.get('post_call_data', {})
                    }

                except Exception as e:
                    self._logger.error(f"Error in async call evaluation: {str(e)}", exc_info=True)
                    # Return empty evaluation results on error
                    return {
                        'session_id': session_id,
                        'evaluation_results': [],
                        'quality_metrics': {},
                        'audio_file_path': str(audio_file_path),
                        'post_call_data': call_data.get('post_call_data', {})
                    }

                finally:
                    # Clean up the event loop
                    loop.close()

            except Exception as e:
                self._logger.error(f"Error in call evaluation: {str(e)}", exc_info=True)
                return None

        except Exception as e:
            self._logger.error(f"Unexpected error in _evaluate_call: {str(e)}", exc_info=True)
            return None

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

    def __repr__(self):
        """String representation of the handler."""
        return f"PipecatVoiceHandler(session_id={self._session_id})"

    def __str__(self):
        """Human-readable string representation."""
        return f"Pipecat Voice Handler for session {self._session_id}"

    @property
    def name(self) -> str:
        """Get handler name."""
        return "PipecatVoiceHandler"

    def dump(self) -> dict:
        return {
            "session_id": self._session_id,
            "agent_name": self.agent_config.agent_name if self.agent_config else None,
            "transport_type": str(self._transport_type),
            "tool_calling": self._tool_calling,
            "services_initialized": self._services_initialized,
            "is_shutting_down": self._is_shutting_down,
            "active_sessions": len(self.active_sessions),
            "optimizations_applied": list(self.optimizations_applied),
        }


# Standalone functions for backward compatibility
def get_os_info_compat() -> str:
    """
    Get OS info (backward compatibility).
    Delegates to pipecat_utils.
    """
    return get_os_info()

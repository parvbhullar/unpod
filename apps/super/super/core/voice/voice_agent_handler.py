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
from super_services.voice.models.config import MessageCallBack
from super.core.voice.observers.metrics import CustomMetricObserver
from super.core.voice.livekit.lite_handler import LiveKitLiteHandler
from super.core.voice.pipecat.handler import PipecatVoiceHandler
from super.core.voice.pipecat.lite_handler import LiteVoiceHandler
from super.core.voice.common.common import build_call_result
from super.core.voice.common.prefect import trigger_post_call
from super.core.voice.schema import CallStatusEnum
from super.core.voice.workflows.pre_call import PreCallWorkFlow
from super.core.voice.common.common import send_web_notification

from super.core.voice.common.services import update_task_with_status
from super.core.voice.common.services import save_execution_log
from super_services.db.services.schemas.task import TaskStatusEnum

STARTUP_STAGE_BUDGETS_MS = {
    "room_connect": 1200,
    "config_resolution": 700,
    "assistant_create": 200,
    "pipecat_setup": 300,
    "total_entrypoint": 2500,
}
REQUIRED_STARTUP_PERF_STAGES = (
    "room_connect",
    "config_resolution",
    "pipecat_setup",
    "total_entrypoint",
)


@dataclass
class ServiceCache:
    """
    Global cache for pre-warmed resources and dynamically created services.

    - VAD model: Loaded once at prewarm (config-independent)
    - Embedding model: Loaded once at prewarm for KB search (config-independent)
    - STT/TTS/LLM services: Cached by config signature for reuse across calls
    - KB managers: Cached by knowledge base signature for reuse across calls

    Thread-safe via lock for concurrent access.
    """

    silero_vad: Optional[Any] = None
    vad_load_time_ms: float = 0.0
    is_vad_loaded: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock)

    # Embedding model for KB search (config-independent, loaded at prewarm)
    _embedding_fn: Optional[Any] = None
    embedding_load_time_ms: float = 0.0
    is_embedding_loaded: bool = False

    # ChromaDB client (shared across KB managers for in-memory collections)
    _chroma_client: Optional[Any] = None

    # Dynamic service cache keyed by config signature
    # Key format: "{provider}:{model}" e.g., "deepgram:nova-2", "openai:gpt-4o"
    _stt_cache: Dict[str, Any] = field(default_factory=dict)
    _tts_cache: Dict[str, Any] = field(default_factory=dict)
    _llm_cache: Dict[str, Any] = field(default_factory=dict)

    # KB manager cache keyed by knowledge base tokens
    _kb_cache: Dict[str, Any] = field(default_factory=dict)

    def get_vad(self) -> Optional[Any]:
        """Get pre-loaded VAD model."""
        return self.silero_vad

    def get_embedding_fn(self) -> Optional[Any]:
        """Get pre-loaded embedding function for KB search."""
        return self._embedding_fn

    def set_embedding_fn(self, embedding_fn: Any, load_time_ms: float = 0.0) -> None:
        """Set the pre-loaded embedding function."""
        with self._lock:
            self._embedding_fn = embedding_fn
            self.embedding_load_time_ms = load_time_ms
            self.is_embedding_loaded = True

    def get_chroma_client(self) -> Optional[Any]:
        """Get shared ChromaDB client."""
        return self._chroma_client

    def set_chroma_client(self, client: Any) -> None:
        """Set the shared ChromaDB client."""
        with self._lock:
            self._chroma_client = client

    def get_kb_manager(self, kb_key: str) -> Optional[Any]:
        """Get cached KB manager by key."""
        with self._lock:
            return self._kb_cache.get(kb_key)

    def set_kb_manager(self, kb_key: str, manager: Any) -> None:
        """Cache KB manager by key."""
        with self._lock:
            self._kb_cache[kb_key] = manager

    def get_stt(self, config: Dict[str, Any]) -> Optional[Any]:
        """Get cached STT service for config, or None if not cached."""
        key = self._make_stt_key(config)
        with self._lock:
            return self._stt_cache.get(key)

    def set_stt(self, config: Dict[str, Any], service: Any) -> None:
        """Cache STT service for config."""
        key = self._make_stt_key(config)
        with self._lock:
            self._stt_cache[key] = service

    def get_tts(self, config: Dict[str, Any]) -> Optional[Any]:
        """Get cached TTS service for config, or None if not cached."""
        key = self._make_tts_key(config)
        with self._lock:
            return self._tts_cache.get(key)

    def set_tts(self, config: Dict[str, Any], service: Any) -> None:
        """Cache TTS service for config."""
        key = self._make_tts_key(config)
        with self._lock:
            self._tts_cache[key] = service

    def get_llm(self, config: Dict[str, Any]) -> Optional[Any]:
        """Get cached LLM service for config, or None if not cached."""
        key = self._make_llm_key(config)
        with self._lock:
            return self._llm_cache.get(key)

    def set_llm(self, config: Dict[str, Any], service: Any) -> None:
        """Cache LLM service for config."""
        key = self._make_llm_key(config)
        with self._lock:
            self._llm_cache[key] = service

    def _make_stt_key(self, config: Dict[str, Any]) -> str:
        """Create cache key for STT service based on config."""
        provider = config.get("stt_provider", "deepgram")
        model = config.get("stt_model", "nova-2")
        language = config.get("language", "en")
        return f"stt:{provider}:{model}:{language}"

    def _make_tts_key(self, config: Dict[str, Any]) -> str:
        """Create cache key for TTS service based on config."""
        provider = config.get("tts_provider", DEFAULT_TTS_PROVIDER)
        voice = config.get("tts_voice", config.get("voice_id", DEFAULT_TTS_VOICE))
        return f"tts:{provider}:{voice}"

    def _make_llm_key(self, config: Dict[str, Any]) -> str:
        """Create cache key for LLM service based on config."""
        provider = config.get("llm_provider", "openai")
        model = config.get("llm_model", config.get("model", "gpt-4o-mini"))
        return f"llm:{provider}:{model}"

    def clear(self):
        """Clear all cached services (keeps VAD and embeddings loaded)."""
        with self._lock:
            self._stt_cache.clear()
            self._tts_cache.clear()
            self._llm_cache.clear()
            self._kb_cache.clear()

    def clear_all(self):
        """Clear everything including VAD and embeddings."""
        with self._lock:
            self.silero_vad = None
            self.vad_load_time_ms = 0.0
            self.is_vad_loaded = False
            self._embedding_fn = None
            self.embedding_load_time_ms = 0.0
            self.is_embedding_loaded = False
            self._chroma_client = None
            self._stt_cache.clear()
            self._tts_cache.clear()
            self._llm_cache.clear()
            self._kb_cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about cached services for monitoring."""
        with self._lock:
            return {
                "stt_cached": len(self._stt_cache),
                "tts_cached": len(self._tts_cache),
                "llm_cached": len(self._llm_cache),
                "kb_cached": len(self._kb_cache),
                "vad_loaded": self.is_vad_loaded,
                "embedding_loaded": self.is_embedding_loaded,
            }

    def clear_stale_services(self, max_services: int = 10) -> int:
        """
        Clear oldest cached services if cache grows too large.

        Args:
            max_services: Maximum number of services to keep per type

        Returns:
            Number of services cleared
        """
        cleared = 0
        with self._lock:
            for cache in [self._stt_cache, self._tts_cache, self._llm_cache]:
                if len(cache) > max_services:
                    keys_to_remove = list(cache.keys())[:-max_services]
                    for key in keys_to_remove:
                        del cache[key]
                        cleared += 1
            if len(self._kb_cache) > max_services:
                keys_to_remove = list(self._kb_cache.keys())[:-max_services]
                for key in keys_to_remove:
                    del self._kb_cache[key]
                    cleared += 1
        return cleared


# Global service cache - shared across all handler instances in the process
_service_cache = ServiceCache()


def get_service_cache() -> ServiceCache:
    """Get the global service cache instance."""
    return _service_cache


def _prewarm_embedding_model(cache: ServiceCache, logger: logging.Logger) -> None:
    """
    Prewarm the SentenceTransformer embedding model for KB search.

    This loads the embedding model once at process start to avoid the ~2s
    initialization delay during the first KB lookup in a call.

    Args:
        cache: ServiceCache instance to store the loaded model
        logger: Logger for timing and status messages
    """
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        _start = perf_counter()

        # Check embedding backend from env (default: onnx for faster init)
        embedding_backend = os.getenv("EMBEDDING_BACKEND", "onnx").lower()
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

        if embedding_backend == "onnx" and "minilm" in model_name.lower():
            # Use ChromaDB's built-in ONNX MiniLM (faster, but only for MiniLM)
            embedding_fn = embedding_functions.ONNXMiniLM_L6_V2()
            logger.info(f"[PREWARM] ONNX embedding function created: {model_name}")
        else:
            # SentenceTransformer: supports any model including multilingual
            embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model_name
            )
            logger.info(f"[PREWARM] SentenceTransformer embedding loaded: {model_name}")

        # Materialize model artifacts at prewarm time to avoid first-call downloads
        # during a live conversation (e.g., ONNX tarball fetch).
        force_materialize = (
            os.getenv("PREWARM_EMBEDDING_INFERENCE", "true").lower() == "true"
        )
        if force_materialize:
            _embed_start = perf_counter()
            _ = embedding_fn(["prewarm embedding model"])
            logger.info(
                f"[PREWARM] Embedding inference warmup complete: "
                f"{(perf_counter() - _embed_start) * 1000:.0f}ms"
            )

        # Also create shared ChromaDB ephemeral client
        chroma_client = chromadb.EphemeralClient()

        load_time_ms = (perf_counter() - _start) * 1000
        cache.set_embedding_fn(embedding_fn, load_time_ms)
        cache.set_chroma_client(chroma_client)

        logger.info(
            f"[PREWARM] Embedding model + ChromaDB client loaded: {load_time_ms:.0f}ms"
        )

    except Exception as e:
        logger.warning(f"[PREWARM] Embedding preload failed (will load lazily): {e}")


def prewarm_process(proc) -> None:
    """
    LiveKit prewarm function called before jobs are assigned to this process.

    This function runs synchronously in each worker process to initialize
    config-independent resources before any calls arrive:
    - VAD model: For voice activity detection (~200-500ms)
    - Embedding model: For KB search (~1-2s first time)
    - ChromaDB client: For in-memory vector storage

    STT/TTS/LLM services are created dynamically based on model_config
    and cached by config signature for reuse across calls with same config.

    Args:
        proc: JobProcess instance from LiveKit, has userdata dict for storage
    """
    logger = app_logging.get_logger("livekit.voice.prewarm")
    logger.info("[PREWARM] Process prewarm starting...")

    cache = get_service_cache()

    try:
        # Load Silero VAD synchronously (config-independent, ~200-500ms)
        if not livekit_services._ensure_livekit_plugins_loaded(logger):
            logger.warning(
                "[PREWARM] Skipping VAD preload; plugins not initialized on main thread"
            )
        else:
            _start = perf_counter()
            vad = livekit_services.silero.VAD.load()
            proc.userdata["vad"] = vad

            cache.silero_vad = vad
            cache.is_vad_loaded = True
            cache.vad_load_time_ms = (perf_counter() - _start) * 1000

            logger.info(f"[PREWARM] Silero VAD loaded: {cache.vad_load_time_ms:.0f}ms")

    except Exception as e:
        logger.error(f"[PREWARM] VAD prewarm error: {e}")
        import traceback

        logger.error(traceback.format_exc())

    # Prewarm embedding model for KB search (config-independent)
    # This prevents the ~2s delay on first KB lookup
    enable_kb_prewarm = os.getenv("PREWARM_KB_EMBEDDINGS", "true").lower() == "true"
    if enable_kb_prewarm:
        _prewarm_embedding_model(cache, logger)

    # Pre-warm PostgreSQL connection pool to avoid ~350ms cold-start on first config fetch
    try:
        _pg_start = perf_counter()
        from super_services.libs.core.postgres import _get_pool

        _get_pool()
        logger.info(
            f"[PREWARM] PostgreSQL pool created: {(perf_counter() - _pg_start) * 1000:.0f}ms"
        )
    except Exception as e:
        logger.warning(
            f"[PREWARM] PostgreSQL pool prewarm failed (will init lazily): {e}"
        )

    logger.info(
        f"[PREWARM] Process prewarm completed - "
        f"VAD: {cache.is_vad_loaded}, Embeddings: {cache.is_embedding_loaded}"
    )


# Load environment variables early - critical for LiveKit credentials
load_dotenv(override=True)

# S3 configuration for call recordings (LiveKit Egress)
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", os.getenv("AWS_DEFAULT_REGION"))


@dataclass
class AgentConfigResult:
    """Result from agent config resolution."""

    model_config: Dict[str, Any]
    user_data: Dict[str, Any]
    pilot_data: Optional[Dict[str, Any]] = None
    participant: Optional[Any] = None
    call_type: str = "inbound"


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
    # Agent,
    AgentSession,
    # RunContext,
    ConversationItemAddedEvent,
    # room_io,
    UserInputTranscribedEvent,
    AgentStateChangedEvent,
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
        self._execution_nature = configuration.execution_nature
        self.config = model_config or None
        self.user_state = None
        self._temp_perf_logs = None
        # LiveKit job context
        self._job_context: Optional[JobContext] = None
        self.is_sdk_call = False
        self._transport_type = TransportType.LIVEKIT
        self.agent_config = AgentConfig(
            agent_name=session_id or "SuperVoiceAgent",
            model_config=model_config,
            callback=callback,
        )
        self.agent_name = agent_name
        self._agent = None
        # LiveKit components
        self.active_sessions: Dict[str, CallSession] = {}
        # Track if room events have been registered to prevent duplicate handlers
        self._room_events_registered: bool = False
        # Handler type: "livekit", "pipecat", "superkik" (fallback to AGENT_PROVIDER env var)
        self.handler_type = handler_type or os.getenv("AGENT_PROVIDER", "pipecat")
        # Task tracking for proper cleanup
        self._pending_tasks: Set[asyncio.Task] = set()
        self._shutdown_event: Optional[asyncio.Event] = None
        self._is_shutting_down: bool = False

    def _append_temp_perf_log(self, name: str, duration_ms: float) -> None:
        """Append timing log entry to temporary perf list when available."""
        if isinstance(self._temp_perf_logs, list):
            self._temp_perf_logs.append(
                {
                    "name": name,
                    "duration_ms": round(duration_ms, 2),
                }
            )

    def _log_stage_timing(
        self,
        stage: str,
        started_at: float,
        user_state: Optional[UserState] = None,
        label: Optional[str] = None,
    ) -> float:
        """Log startup stage timing with budget checks and perf log sinks."""
        elapsed_ms = (perf_counter() - started_at) * 1000
        budget_ms = STARTUP_STAGE_BUDGETS_MS.get(stage)
        stage_label = label or stage
        self._append_temp_perf_log(stage, elapsed_ms)
        if user_state is not None:
            add_perf_log(user_state, stage, elapsed_ms)
        self._logger.info(f"[TIMING] {stage_label}: {elapsed_ms:.0f}ms")
        if budget_ms is not None and elapsed_ms > budget_ms:
            self._logger.warning(
                f"[TIMING][BUDGET] {stage_label} exceeded budget: "
                f"{elapsed_ms:.0f}ms > {budget_ms}ms"
            )
        return elapsed_ms

    def _track_task(self, task: asyncio.Task) -> asyncio.Task:
        """
        Track an async task for cleanup on shutdown.

        Args:
            task: The asyncio.Task to track

        Returns:
            The same task (for chaining)
        """
        self._pending_tasks.add(task)
        task.add_done_callback(self._pending_tasks.discard)
        return task

    def _start_assistant_task(
        self,
        existing_task: Optional[asyncio.Task],
        user_state: UserState,
        ctx: JobContext,
        handler_class,
        handler_name: str,
        task_name: str,
    ) -> asyncio.Task:
        """Start assistant creation exactly once and reuse existing task if present."""
        if existing_task and not existing_task.done():
            self._logger.info(
                f"[TIMING] Reusing existing assistant task: {existing_task.get_name()}"
            )
            return existing_task

        task = asyncio.create_task(
            self._create_assistant(user_state, ctx, handler_class, handler_name),
            name=task_name,
        )
        return self._track_task(task)

    async def _cancel_pending_tasks(self, timeout: float = 5.0) -> int:
        """
        Cancel all pending tracked tasks gracefully.

        Args:
            timeout: Maximum time to wait for tasks to complete

        Returns:
            Number of tasks cancelled
        """
        if not self._pending_tasks:
            return 0

        tasks_to_cancel = list(self._pending_tasks)
        cancelled = 0

        for task in tasks_to_cancel:
            if not task.done():
                task.cancel()
                cancelled += 1

        if tasks_to_cancel:
            await asyncio.wait(tasks_to_cancel, timeout=timeout)

        self._pending_tasks.clear()
        return cancelled

    def _register_session(self, session_id: str, session: CallSession) -> None:
        """Register an active session for tracking."""
        self.active_sessions[session_id] = session
        self._logger.debug(
            f"Session registered: {session_id}, total active: {len(self.active_sessions)}"
        )

    def _unregister_session(self, session_id: str) -> Optional[CallSession]:
        """Unregister and return a session, freeing its resources."""
        session = self.active_sessions.pop(session_id, None)
        if session:
            self._logger.debug(
                f"Session unregistered: {session_id}, remaining: {len(self.active_sessions)}"
            )
        return session

    async def _cleanup_session(self, user_state: UserState) -> None:
        """
        Clean up all resources associated with a call session.

        This should be called when a call ends to prevent memory leaks.
        """
        session_id = str(user_state.thread_id) if user_state.thread_id else None

        # Remove from active sessions
        if session_id:
            self._unregister_session(session_id)

        # Clean up the agent if it exists
        if self._agent:
            try:
                if hasattr(self._agent, "cleanup"):
                    await self._agent.cleanup()
                elif hasattr(self._agent, "close"):
                    await self._agent.close()
                elif hasattr(self._agent, "end_ongoing_agent"):
                    await self._agent.end_ongoing_agent()
            except Exception as e:
                self._logger.warning(f"Error cleaning up agent: {e}")
            finally:
                self._agent = None

        # Clear user_state reference
        if hasattr(self, "user_state") and self.user_state is user_state:
            self.user_state = None

        # Periodic cache cleanup - clear stale services if cache is growing
        cache = get_service_cache()
        cleared = cache.clear_stale_services(max_services=10)
        if cleared > 0:
            self._logger.info(f"Cleared {cleared} stale cached services")

        # Suggest garbage collection after cleanup
        gc.collect()

        self._logger.info(
            f"Session cleanup completed for {session_id}, "
            f"active sessions: {len(self.active_sessions)}"
        )

    async def _init_variables(self, user_state: UserState):
        """Initialize variables - same interface as livekit handler"""
        self._logger.info("Initializing variables...")
        if not self.config:
            self.config = user_state.model_config
        self.session_id = str(user_state.thread_id)
        self._room_name = user_state.room_name or f"room-{user_state.thread_id}"

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
                    "start_time": (
                        user_state.start_time.isoformat()
                        if user_state.start_time
                        and hasattr(user_state.start_time, "isoformat")
                        else user_state.start_time
                    ),
                    "end_time": (
                        user_state.end_time.isoformat()
                        if user_state.end_time
                        and hasattr(user_state.end_time, "isoformat")
                        else user_state.end_time
                    ),
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

    async def execute(self, user_state: UserState, *args, **kwargs) -> Any:
        """Execute the voice agent handler - same interface as livekit handler"""
        data = kwargs.get("data", {})
        self._logger.info(
            "Executing VoiceAgentHandler for user: {}".format(user_state.user_name)
        )

    async def session_recordings(self, room_name: str) -> str:
        """
        Start LiveKit Egress recording for the room and upload to S3.

        Args:
            room_name: The LiveKit room name to record

        Returns:
            The S3 URL of the recording, or empty string if failed
        """
        try:
            self._logger.info(
                f"[RECORDING] Starting session recording for room: {room_name}"
            )

            # Check if S3 credentials are configured
            if not all(
                [
                    AWS_STORAGE_BUCKET_NAME,
                    AWS_S3_REGION_NAME,
                    S3_ACCESS_KEY,
                    S3_SECRET_KEY,
                ]
            ):
                self._logger.warning(
                    "[RECORDING] S3 credentials not fully configured. "
                    "Set S3_ACCESS_KEY, S3_SECRET_KEY, AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME"
                )
                return ""

            req = api.RoomCompositeEgressRequest(
                room_name=room_name,
                audio_only=True,
                file_outputs=[
                    api.EncodedFileOutput(
                        file_type=api.EncodedFileType.OGG,
                        filepath=f"livekit/{room_name}.ogg",
                        s3=api.S3Upload(
                            bucket=AWS_STORAGE_BUCKET_NAME,
                            region=AWS_S3_REGION_NAME,
                            access_key=S3_ACCESS_KEY,
                            secret=S3_SECRET_KEY,
                        ),
                    )
                ],
            )

            lkapi = api.LiveKitAPI()
            await lkapi.egress.start_room_composite_egress(req)
            await lkapi.aclose()

            recording_url = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/livekit/{room_name}.ogg"
            self._logger.info(
                f"[RECORDING] Session recording started. URL: {recording_url}"
            )
            return recording_url

        except Exception as e:
            self._logger.error(
                f"[RECORDING] Failed to start session recording: {str(e)}"
            )
            self._logger.error(traceback.format_exc())
            return ""

    async def run_agent(
        self,
        ctx: agents.JobContext,
        user_state: UserState,
        _agent,
        retry: int = 3,
    ):
        try:
            if _agent:
                await self._start_session_recording(ctx, user_state)
                await self._init_event_bridge(ctx)
                await self._signal_agent_joined(ctx, user_state)
                if self._event_bridge:
                    _agent.set_event_bridge(self._event_bridge)

                # Check if this is a LiveKit native handler
                from super.core.voice.livekit.lite_handler import LiveKitLiteHandler

                from super.core.voice.testing_agents.vanilla_handler import (
                    VanillaAgenHandler,
                )

                if isinstance(_agent, LiveKitLiteHandler) or isinstance(
                    _agent, VanillaAgenHandler
                ):
                    await _agent.execute_with_context(ctx)
                else:
                    # Pipecat handlers - use standard execute
                    await _agent.execute()
                    await self.execute_post_call(user_state)
                    # res = await build_call_result(user_state)
                    # await trigger_post_call(user_state, res)

            else:
                # Use LiveKit AgentSession when pipecat is not available
                session = self._create_agent_session(ctx, user_state)
                if session:
                    self._setup_session_events(session, user_state)
                    await self._start_session_with_retry(ctx, session, retry)

        except Exception as e:
            user_state.call_status = CallStatusEnum.FAILED
            await self.execute_post_call(user_state)
            # res = await build_call_result(user_state)
            # await trigger_post_call(user_state, res)
            self._logger.error(f"Error starting agent session: {e}")
            self.message_callback("EOF\n", role="system", user_state=user_state)
            ctx.shutdown()

    async def _init_event_bridge(self, ctx: JobContext) -> None:
        """Initialize the LiveKit event bridge for state and transcript events."""
        try:
            from super.core.voice.livekit.event_bridge import create_event_bridge

            self._event_bridge = create_event_bridge(
                logger=self._logger,
                emit_transcripts=True,
            )
            # Initialize with job context
            await self._event_bridge.initialize(job_context=ctx)
            self._logger.info("LiveKit event bridge initialized")

        except Exception as e:
            self._logger.warning(f"Could not initialize event bridge: {e}")
            self._event_bridge = None

    async def _signal_agent_joined(
        self, ctx: JobContext, user_state: UserState
    ) -> None:
        """Signal to LiveKit room that agent has joined/connected."""
        try:
            local_participant = ctx.room.local_participant

            # Set lk.agent.state attribute - this is what useVoiceAssistant hook looks for
            # Valid states: "initializing", "listening", "thinking", "speaking"
            await local_participant.set_attributes(
                {
                    "lk.agent.state": "listening",  # Agent is ready and listening
                    "agent.name": self.agent_name,
                    "agent.session_id": str(user_state.thread_id),
                }
            )

            # Set metadata with full details
            await local_participant.set_metadata(
                json.dumps(
                    {
                        "agent_name": self.agent_name,
                        "agent_type": "pipecat",
                        "session_id": str(user_state.thread_id),
                        "joined_at": datetime.utcnow().isoformat(),
                        "status": "connected",
                    }
                )
            )

            self._logger.info(
                f"Agent joined signal sent: {self.agent_name} with state=listening"
            )

        except Exception as e:
            self._logger.error(f"Failed to signal agent joined: {e}")

    async def _update_agent_state(self, ctx: JobContext, state: str) -> None:
        """
        Update the agent state attribute for frontend state tracking.

        Args:
            ctx: LiveKit job context
            state: One of "initializing", "listening", "thinking", "speaking"
        """
        valid_states = {"initializing", "listening", "thinking", "speaking"}
        if state not in valid_states:
            self._logger.warning(
                f"Invalid agent state: {state}. Must be one of {valid_states}"
            )
            return

        try:
            await ctx.room.local_participant.set_attributes(
                {
                    "lk.agent.state": state,
                }
            )
            self._logger.debug(f"Agent state updated to: {state}")
        except Exception as e:
            self._logger.error(f"Failed to update agent state: {e}")

    async def publish_data(
        self,
        data: Dict[str, Any],
        topic: str = "message",
        reliable: bool = True,
        destination_identities: Optional[list] = None,
    ) -> bool:
        """
        Publish JSON data via LiveKit data channel.

        Wrapper for event bridge's publish_data method. Use for large payloads
        that don't fit in participant attributes.

        Args:
            data: Dictionary to publish as JSON
            topic: Data channel topic for filtering on frontend
            reliable: Use reliable delivery (default True)
            destination_identities: Target specific participants (None = broadcast)

        Returns:
            True if published successfully, False otherwise
        """
        if not hasattr(self, "_event_bridge") or not self._event_bridge:
            self._logger.warning("Event bridge not initialized, cannot publish data")
            return False

        result = await self._event_bridge.publish_data(
            data=data,
            topic=topic,
            reliable=reliable,
            destination_identities=destination_identities,
        )
        return bool(result)

    async def publish_message_callback(
        self,
        message: Dict[str, Any],
        destination_identities: Optional[list] = None,
    ) -> bool:
        """
        Publish a MessageCallback block via data channel.

        Wrapper for event bridge's publish_message_callback method.
        Uses topic "message_callback" for frontend message handling.

        Args:
            message: Message data with role, content, event, timestamp, etc.
            destination_identities: Target specific participants (None = broadcast)

        Returns:
            True if published successfully, False otherwise

        Example:
            await handler.publish_message_callback({
                "role": "assistant",
                "content": "Hello!",
                "event": "agent_message",
                "timestamp": datetime.utcnow().isoformat(),
            })
        """
        if not hasattr(self, "_event_bridge") or not self._event_bridge:
            self._logger.warning("Event bridge not initialized, cannot publish message")
            return False

        result = await self._event_bridge.publish_message_callback(
            message=message,
            destination_identities=destination_identities,
        )
        return bool(result)

    async def publish_transcript(
        self,
        role: str,
        content: str,
        is_final: bool = True,
    ) -> bool:
        """
        Publish a transcript event via LiveKit event bridge.

        Wrapper for event bridge's emit_transcript method. Emits transcripts
        that can be tracked by frontend listeners.

        Args:
            role: Speaker role ("user" or "assistant")
            content: Transcript text
            is_final: Whether this is a final transcription (default True)

        Returns:
            True if published successfully, False otherwise
        """
        if not hasattr(self, "_event_bridge") or not self._event_bridge:
            self._logger.warning(
                "Event bridge not initialized, cannot publish transcript"
            )
            return False

        result = await self._event_bridge.emit_transcript(
            role=role,
            content=content,
            is_final=is_final,
        )
        return result is not None

    def _create_agent_session(
        self, ctx: JobContext, user_state: UserState
    ) -> Optional[AgentSession]:
        """Create LiveKit AgentSession with configured STT/LLM/TTS."""
        try:
            from livekit.plugins import silero

            model_config = user_state.model_config or {}
            speaking_plan = model_config.get("speaking_plan", {})

            vad = silero.VAD.load(
                min_silence_duration=speaking_plan.get("min_silence_duration", 0.2),
                activation_threshold=0.3,
            )

            userdata = {
                "token": user_state.token,
                "knowledge_base": user_state.knowledge_base,
                "ctx_room": ctx.room,
            }

            session = AgentSession(
                userdata=userdata,
                vad=vad,
            )
            return session

        except Exception as e:
            self._logger.error(f"Failed to create agent session: {e}")
            return None

    async def _start_session_with_retry(
        self, ctx: JobContext, session: AgentSession, retry: int = 3
    ) -> bool:
        """Start AgentSession with retry logic using new RoomOptions API."""
        from livekit.agents.voice import room_io

        for attempt in range(retry):
            self._logger.info(f"Starting agent session, attempt {attempt + 1}")
            try:
                # Build room options - noise cancellation is optional (requires LiveKit Cloud)
                room_opts_kwargs = {}

                # BVC noise cancellation requires LiveKit Cloud with paid subscription
                # Set ENABLE_BVC_NOISE_CANCELLATION=true only if using LiveKit Cloud
                enable_bvc = (
                    os.getenv("ENABLE_BVC_NOISE_CANCELLATION", "true").lower() == "true"
                )

                if enable_bvc:
                    try:
                        from livekit.plugins import noise_cancellation

                        nc = noise_cancellation.BVC()
                        room_opts_kwargs["audio_input"] = room_io.AudioInputOptions(
                            noise_cancellation=nc,
                        )
                        self._logger.info("BVC noise cancellation enabled")
                    except ImportError:
                        self._logger.warning(
                            "Noise cancellation plugin not available - continuing without it"
                        )
                    except Exception as nc_error:
                        self._logger.warning(
                            f"Noise cancellation setup failed: {nc_error}. "
                            "Continuing without noise cancellation."
                        )
                else:
                    self._logger.info(
                        "BVC noise cancellation disabled (requires LiveKit Cloud). "
                        "Set ENABLE_BVC_NOISE_CANCELLATION=true to enable."
                    )

                # Create room options with new API (replaces deprecated room_input_options)
                room_options = room_io.RoomOptions(**room_opts_kwargs)

                await session.start(
                    room=ctx.room,
                    agent=self,
                    room_options=room_options,
                )
                self._logger.info("AgentSession started successfully with RoomOptions")
                return True
            except Exception as e:
                self._logger.warning(f"Session start attempt {attempt + 1} failed: {e}")
                if attempt == retry - 1:
                    raise
        return False

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
                user_state.call_status = CallStatusEnum.CONNECTED
                await self.run_agent(ctx, user_state, _agent)
                return

            elif call_status == "automation":
                pass
            elif participant.disconnect_reason == rtc.DisconnectReason.USER_REJECTED:
                if _agent:
                    await _agent.end_ongoing_agent()

                self._logger.info("user rejected the call, exiting job")
                self.message_callback(
                    f"Call Status:User rejected the call\n",
                    role="system",
                    user_state=user_state,
                )
                user_state.call_status = CallStatusEnum.CANCELLED
                await self.execute_post_call(user_state)

                # res = await build_call_result(user_state)
                # await trigger_post_call(user_state=user_state, res=res)
                self.message_callback("EOF\n", role="system", user_state=user_state)
                ctx.shutdown()
                break

            elif participant.disconnect_reason == rtc.DisconnectReason.USER_UNAVAILABLE:
                if _agent:
                    await _agent.end_ongoing_agent()

                self._logger.info("user did not pick up, exiting job")
                self.message_callback(
                    f"Call Status:User did not pick up\n",
                    role="system",
                    user_state=user_state,
                )
                user_state.end_time = user_state.start_time
                user_state.call_status = CallStatusEnum.NOT_CONNECTED
                await self.execute_post_call(user_state)

                # res = await build_call_result(user_state)
                # await trigger_post_call(user_state=user_state, res=res)

                self.message_callback("EOF\n", role="system", user_state=user_state)
                ctx.shutdown()
                break

            elif participant.disconnect_reason == rtc.DisconnectReason.ROOM_CLOSED:
                if _agent:
                    await _agent.end_ongoing_agent()

                self._logger.info(
                    f"User has disconnected: {participant.disconnect_reason}"
                )
                self.message_callback(
                    f"Call Status:User has hanged up\n",
                    role="system",
                    user_state=user_state,
                )
                user_state.call_status = CallStatusEnum.COMPLETED
                await self.execute_post_call(user_state)

                # res = await build_call_result(user_state)
                # await trigger_post_call(user_state=user_state, res=res)
                self.message_callback("EOF\n", role="system", user_state=user_state)
                ctx.shutdown()
                break

            elif participant.disconnect_reason == rtc.DisconnectReason.UNKNOWN_REASON:
                if _agent:
                    await _agent.end_ongoing_agent()

                self._logger.info(
                    f"User has disconnected: {participant.disconnect_reason}"
                )
                self.message_callback(
                    f"Call Status:User has hanged up\n",
                    role="system",
                    user_state=user_state,
                )

                user_state.call_status = CallStatusEnum.FAILED
                await self.execute_post_call(user_state)

                # res = await build_call_result(user_state)
                # await trigger_post_call(user_state=user_state, res=res)

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
            user_state.end_time = user_state.start_time
            user_state.call_status = CallStatusEnum.FAILED
            await self.execute_post_call(user_state)
            self.message_callback("EOF\n", role="system", user_state=user_state)
        ctx.shutdown()

    async def _create_assistant(
        self, user_state, ctx: JobContext, handler_class, handler_name
    ):
        """
        Create voice assistant based on AGENT_PROVIDER environment variable.

        AGENT_PROVIDER options:
        - "pipecat" (default): Use Pipecat-based handlers (LiteVoiceHandler or PipecatVoiceHandler)
        - "livekit": Use LiveKit native handler (LiveKitLiteHandler)

        For pipecat provider, USE_LITE_HANDLER=true selects LiteVoiceHandler for faster startup.
        """
        _start = perf_counter()
        print(f"[TIMING] _create_assistant START")

        try:
            _ctor_start = perf_counter()
            # Ensure agent_name is in config for transport identity
            handler_config = (
                dict(user_state.model_config) if user_state.model_config else {}
            )
            if "agent_name" not in handler_config:
                handler_config["agent_name"] = self.agent_name

            print(f"\n\n {handler_name} \n\n {handler_class}")
            self._agent = handler_class(
                session_id=user_state.thread_id,
                user_state=user_state,
                callback=MessageCallBack(),
                model_config=handler_config,
                observer=CustomMetricObserver,
            )
            print(
                f"[TIMING] {handler_name} constructor: {(perf_counter() - _ctor_start) * 1000:.0f}ms"
            )

            _preload_start = perf_counter()
            started = await self._agent.preload_agent(user_state, CustomMetricObserver)
            print(
                f"[TIMING] preload_agent: {(perf_counter() - _preload_start) * 1000:.0f}ms"
            )
            self._log_stage_timing(
                "assistant_create",
                _start,
                user_state=user_state,
                label=f"{handler_name} total setup",
            )

            if started:
                return True
            else:
                return False

        except Exception as e:
            traceback.print_exc()
            print(f"unable to initiate agent {str(e)}")

    async def _get_handler_classes(self, ctx: JobContext):
        import time

        _start = time.time()
        print(f"[TIMING] _create_assistant START")

        # Use instance handler_type (set in __init__ with env var fallback)
        agent_provider = self.handler_type.lower()

        agent_mode = os.getenv("RUN_TYPE")

        if agent_mode == "vanilla":
            print("\n\n\n\n creating vanilla handler \n\n\n")

            from super.core.voice.testing_agents.vanilla_handler import (
                VanillaAgenHandler,
            )

            handler_class = VanillaAgenHandler
            handler_name = "VanillaAgenHandler"

        elif agent_provider == "superkik":
            # Use SuperKik handler for service discovery and booking
            from super.core.voice.superkik import SuperKikHandler

            handler_class = SuperKikHandler
            handler_name = "SuperKikHandler"
        elif agent_provider == "livekit":
            # Use LiveKit native handler
            handler_class = LiveKitLiteHandler
            handler_name = "LiveKitLiteHandler"
        else:
            # Pipecat-based handlers
            use_lite_handler = os.getenv("USE_LITE_HANDLER", "false").lower() == "true"
            if use_lite_handler:
                handler_class = LiteVoiceHandler
                handler_name = "LiteVoiceHandler"
            else:
                handler_class = PipecatVoiceHandler
                handler_name = "PipecatVoiceHandler"

        print(
            f"[TIMING] {handler_name} import (provider={agent_provider}): {(time.time() - _start) * 1000:.0f}ms"
        )

        return handler_class, handler_name

    async def get_agent_number(self, ctx: JobContext) -> Optional[str]:
        """
        Get the agent's phone number from SIP participant attributes.

        For inbound calls, looks for sip.trunkPhoneNumber in participant attributes.

        Args:
            ctx: LiveKit job context

        Returns:
            Phone number string or None if not found
        """
        result = await self.get_agent_info(ctx)
        return result.get("phone_number") if result else None

    async def get_agent_info(self, ctx: JobContext) -> Optional[Dict[str, Any]]:
        """
        Get agent identification info from participant attributes.

        For SIP calls: looks for sip.trunkPhoneNumber or sip.calledNumber
        For web calls: looks for agent.name or lk.agent_name attributes

        Args:
            ctx: LiveKit job context

        Returns:
            Dict with 'phone_number' and/or 'agent_handle', or None if nothing found
        """
        try:
            # Add timeout to fail fast if API is slow (using wait_for for Python <3.11 compatibility)
            async def _get_participants():
                async with api.LiveKitAPI() as lkapi:
                    from livekit.api import ListParticipantsRequest

                    return await lkapi.room.list_participants(
                        ListParticipantsRequest(room=ctx.room.name)
                    )

            participants = await asyncio.wait_for(_get_participants(), timeout=5.0)
        except asyncio.TimeoutError:
            self._logger.error("Timeout getting agent info from LiveKit API (5s)")
            return None
        except Exception as e:
            self._logger.error(f"Error getting agent info: {e}")
            return None

        self._logger.debug(
            f"Found {len(participants.participants)} participants in room {ctx.room.name}"
        )

        result: Dict[str, Any] = {}

        for participant in participants.participants:
            # Use .get() to safely access attributes
            attrs = participant.attributes or {}

            # Check for SIP phone number
            trunk_number = attrs.get("sip.trunkPhoneNumber")
            if trunk_number:
                self._logger.info(f"Found agent trunk number: {trunk_number}")
                result["phone_number"] = trunk_number

            # Also check for calledNumber as fallback
            called_number = attrs.get("sip.calledNumber")
            if called_number and "phone_number" not in result:
                self._logger.info(f"Found agent called number: {called_number}")
                result["phone_number"] = called_number

            # Check for web participant agent metadata
            agent_name = attrs.get("agent.name") or attrs.get("lk.agent_name")
            if agent_name:
                self._logger.info(f"Found agent name from attributes: {agent_name}")
                result["agent_handle"] = agent_name

        if result:
            return result

        self._logger.warning(
            f"No agent info found in room {ctx.room.name}. "
            f"Participant attributes: {[p.attributes for p in participants.participants]}"
        )
        return None

    def _get_default_agent_pilot_data(self) -> Optional[Dict[str, Any]]:
        """
        Get pilot_data for the default fallback agent from environment variables.

        Returns:
            Dict with pilot, space_id, user_id, is_default flag, or None if not configured
        """
        default_agent = os.getenv("DEFAULT_VOICE_AGENT")
        if not default_agent:
            return None

        return {
            "pilot": default_agent,
            "space_id": os.getenv("DEFAULT_VOICE_SPACE_ID", "default_space"),
            "user_id": os.getenv("DEFAULT_VOICE_USER_ID", "default_user"),
            "is_default": True,
        }

    async def _resolve_sdk_call_config(
        self, ctx: "JobContext", metadata: Dict[str, Any]
    ) -> Optional[tuple[Dict, Dict, Optional[Dict], Optional[Any]]]:
        """
        Resolve config for SDK/web calls with agent_handle or space_token.
        Runs participant wait in parallel with config lookup for faster startup.

        Args:
            ctx: LiveKit job context for participant wait
            metadata: Job metadata containing agent_handle/space_token

        Returns:
            Tuple of (model_config, user_data, pilot_data, participant) or None
        """
        agent_handle = metadata.get("agent_handle")
        space_token = metadata.get("space_token") or metadata.get("token")

        self._logger.info(
            f"[SDK] SDK/web call detected - agent_handle: {agent_handle}, "
            f"space_token: {space_token}, starting parallel config+participant wait"
        )

        _start = perf_counter()

        async def resolve_config() -> Optional[tuple[Dict, Dict, Optional[Dict]]]:
            """Inner coroutine to resolve SDK config."""
            try:
                model_config = await self._get_config_with_cache(
                    agent_handle=agent_handle, space_token=space_token
                )
                pilot_data = None

                if not model_config:
                    self._logger.warning(
                        f"No config found for agent_handle: {agent_handle} "
                        f"or space_token: {space_token}, trying default agent"
                    )
                    default_pilot_data = self._get_default_agent_pilot_data()
                    if not default_pilot_data:
                        self._logger.error(
                            "No config found and DEFAULT_VOICE_AGENT not set"
                        )
                        return None

                    default_agent = default_pilot_data["pilot"]
                    model_config = await self._get_config_with_cache(
                        agent_handle=default_agent
                    )
                    if not model_config:
                        self._logger.error(
                            f"No config found for default agent: {default_agent}"
                        )
                        return None

                    pilot_data = default_pilot_data
                    self._logger.info(f"Using default agent: {default_agent}")

                user_data = {
                    "token": metadata.get("token") or metadata.get("space_token"),
                    "space_name": metadata.get("space_name"),
                    "space_slug": metadata.get("space_slug"),
                    "contact_name": metadata.get("contact_name"),
                    "user": metadata.get("user", {}),
                    "thread_id": metadata.get("thread_id", ""),
                    "space_id": metadata.get("space_id"),
                    "space_token": metadata.get("space_token"),
                }

                return model_config, user_data, pilot_data

            except Exception as e:
                self._logger.error(f"Error in SDK config resolution: {e}")
                import traceback

                self._logger.error(traceback.format_exc())
                return None

        # Run participant wait and config resolution IN PARALLEL
        try:
            participant, config_result = await asyncio.gather(
                asyncio.wait_for(ctx.wait_for_participant(), timeout=30.0),
                resolve_config(),
                return_exceptions=False,
            )
        except asyncio.TimeoutError:
            self._logger.error(
                "[SDK] Timeout waiting for participant during config resolution"
            )
            return None
        except Exception as e:
            self._logger.error(f"[SDK] Error in parallel SDK setup: {e}")
            return None

        self._logger.info(
            f"[TIMING] SDK parallel config+participant: {(perf_counter() - _start) * 1000:.0f}ms"
        )

        if not participant:
            self._logger.error("[SDK] Participant not connected")
            return None

        if not config_result:
            self._logger.error("[SDK] Config resolution failed")
            return None

        model_config, user_data, pilot_data = config_result

        self._logger.info(
            f"[SDK] Config resolved - thread_id: {user_data.get('thread_id')}, "
            f"participant: {participant.identity if participant else 'None'}"
        )

        return model_config, user_data, pilot_data, participant

    async def execute_post_call(self, user_state):
        from super.core.voice.common.prefect import store_perf_logs

        try:
            # Always save perf logs for both SDK and regular calls
            await store_perf_logs(user_state)

            if not self.is_sdk_call:
                res = await build_call_result(user_state)
                await trigger_post_call(user_state=user_state, res=res)

        except Exception as e:
            self._logger.error(f"Error in execute_post_call: {e}")
        finally:
            await self._cleanup_session(user_state)

    async def _start_session_recording(self, ctx, user_state):
        recording_session_id = (
            self._session_id or str(user_state.thread_id) or ctx.room.name
        )
        self._track_task(
            asyncio.create_task(
                self._start_recording_background(
                    ctx=ctx,
                    user_state=user_state,
                    session_id=recording_session_id,
                ),
                name="recording_background",
            )
        )

    async def _resolve_inbound_sip_config(
        self, ctx: JobContext
    ) -> tuple[Optional[Dict], Optional[Dict], Optional[Any]]:
        """
        Resolve config for inbound SIP calls by phone number lookup.
        Runs participant wait and config resolution in parallel.

        Returns:
            Tuple of (model_config, pilot_data, participant)
        """
        _inbound_start = perf_counter()
        self._logger.info("[INBOUND] Starting inbound SIP config resolution...")

        async def resolve_config_by_number():
            """Inner coroutine to resolve config from phone number.
            Retries participant lookup since SIP caller may not have joined yet.
            """
            _config_start = perf_counter()
            agent_number = None
            max_attempts = 5
            for attempt in range(max_attempts):
                agent_number = await self.get_agent_number(ctx)
                if agent_number:
                    break
                if attempt < max_attempts - 1:
                    self._logger.debug(
                        f"[INBOUND] SIP participant not yet joined, "
                        f"retrying ({attempt + 1}/{max_attempts})..."
                    )
                    await asyncio.sleep(0.5)

            self._logger.info(
                f"[TIMING] get_agent_number: {(perf_counter() - _config_start) * 1000:.0f}ms"
            )
            self._logger.info(f"[INBOUND] Extracted agent number: {agent_number}")

            if not agent_number:
                self._logger.warning(
                    "[INBOUND] Could not get agent number for inbound SIP call "
                    f"after {max_attempts} attempts. "
                    "Check participant attributes for sip.trunkPhoneNumber or sip.calledNumber"
                )
                return None, None, agent_number

            from super.core.voice.common.pilot import get_pilot_and_space_for_number

            _pilot_start = perf_counter()
            pilot_data = await get_pilot_and_space_for_number(agent_number)
            self._logger.info(
                f"[TIMING] get_pilot_and_space: "
                f"{(perf_counter() - _pilot_start) * 1000:.0f}ms"
            )

            if not pilot_data:
                self._logger.warning(
                    f"[INBOUND] No pilot found for number: {agent_number}. "
                    "Check that the number is configured in core_components_pilot_numbers table"
                )
                return None, None, agent_number

            slug = pilot_data.get("pilot")
            self._logger.info(
                f"[INBOUND] Found pilot: {slug} for number: {agent_number}"
            )

            _model_start = perf_counter()
            config = await self._get_config_with_cache(agent_handle=slug)
            self._logger.info(
                f"[TIMING] get_config: {(perf_counter() - _model_start) * 1000:.0f}ms"
            )

            if not config:
                self._logger.warning(
                    f"[INBOUND] No config found for pilot: {slug}. "
                    "Check ModelConfig.get_config() for this agent handle"
                )
                return None, pilot_data, agent_number

            self._logger.info(
                f"[INBOUND] Successfully resolved config for pilot: {slug}"
            )
            return config, pilot_data, agent_number

        # Run participant wait and config resolution IN PARALLEL
        _wait_start = perf_counter()
        try:
            (
                participant,
                (
                    model_config,
                    pilot_data,
                    agent_number,
                ),
            ) = await asyncio.gather(
                asyncio.wait_for(ctx.wait_for_participant(), timeout=30.0),
                resolve_config_by_number(),
                return_exceptions=False,
            )
        except asyncio.TimeoutError:
            self._logger.error("Timeout waiting for participant in inbound call")
            return None, None, None
        except Exception as e:
            self._logger.error(f"Error in parallel inbound setup: {e}")
            return None, None, None

        self._logger.info(
            f"[TIMING] parallel wait+config: {(perf_counter() - _wait_start) * 1000:.0f}ms"
        )

        if not participant:
            self._logger.error("Participant not connected")
            return None, None, None

        # If config resolution succeeded, return results
        if model_config and pilot_data:
            self._logger.info(
                f"[TIMING] Total inbound setup: "
                f"{(perf_counter() - _inbound_start) * 1000:.0f}ms"
            )
            return model_config, pilot_data, participant

        # Fallback to default agent if pilot lookup failed
        self._logger.warning(
            f"Pilot/config lookup failed for number: {agent_number}, "
            "attempting default agent fallback"
        )

        default_pilot_data = self._get_default_agent_pilot_data()
        if not default_pilot_data:
            self._logger.error(
                f"No pilot found for number: {agent_number} and "
                "DEFAULT_VOICE_AGENT env var not set"
            )
            return None, None, participant

        default_agent = default_pilot_data["pilot"]
        self._logger.info(f"Using default agent: {default_agent}")

        _model_start = perf_counter()
        model_config = await self._get_config_with_cache(agent_handle=default_agent)
        self._logger.info(
            f"[TIMING] get_default_config: {(perf_counter() - _model_start) * 1000:.0f}ms"
        )

        if not model_config:
            self._logger.error(f"No config found for default agent: {default_agent}")
            return None, None, participant

        self._logger.info(
            f"[TIMING] Total inbound setup (with fallback): "
            f"{(perf_counter() - _inbound_start) * 1000:.0f}ms"
        )
        return model_config, default_pilot_data, participant

    async def _resolve_agent_config(
        self,
        ctx: JobContext,
        metadata: Dict[str, Any],
    ) -> Optional[AgentConfigResult]:
        """
        Resolve agent configuration from metadata or SIP participant attributes.

        Handles three cases:
        1. SDK/web calls: agent_handle or space_token in metadata root
        2. Inbound SIP calls: phone number from participant attributes
        3. Outbound calls: model_config already in metadata

        Args:
            ctx: LiveKit job context
            metadata: Parsed job metadata

        Returns:
            AgentConfigResult with model_config, user_data, pilot_data, participant
            None if config could not be resolved
        """
        user_data = metadata.get("data", {})
        model_config = metadata.get("model_config", {})
        pilot_data = None
        participant = None
        call_type = "outbound" if metadata.get("call_type") == "outbound" else "inbound"

        # Case 1: SDK/web calls with agent_handle or space_token at root level
        # This must be checked FIRST since SDK calls also come as "inbound"
        # SDK config resolution runs participant wait in parallel for faster startup
        if not model_config and (
            metadata.get("agent_handle") or metadata.get("space_token")
        ):
            result = await self._resolve_sdk_call_config(ctx, metadata)
            if not result:
                return None
            model_config, user_data, pilot_data, participant = result

        # Case 2: Inbound SIP calls - lookup by phone number
        elif call_type == "inbound" and not model_config:
            (
                model_config,
                pilot_data,
                participant,
            ) = await self._resolve_inbound_sip_config(ctx)
            if not model_config:
                return None

        # Case 3: Outbound calls - fetch config by agent_id if model_config is empty
        elif call_type == "outbound" and not model_config:
            agent_id = user_data.get("agent_id")
            if agent_id:
                self._logger.info(
                    f"[OUTBOUND] Fetching config for agent_id: {agent_id}"
                )
                model_config = await self._get_config_with_cache(agent_handle=agent_id)

            # Fallback to env var if still no config
            if not model_config:
                fallback_agent = os.getenv("AGENT_NAME") or self.agent_name
                if fallback_agent:
                    self._logger.warning(
                        f"[OUTBOUND] No config for agent_id={agent_id}, "
                        f"falling back to AGENT_NAME: {fallback_agent}"
                    )
                    model_config = await self._get_config_with_cache(
                        agent_handle=fallback_agent
                    )

            if not model_config:
                self._logger.error(
                    f"[OUTBOUND] No config found for agent_id={agent_id} or fallback"
                )
                return None

        # Note: Skip phone number lookup for SDK calls (they have agent_handle/space_token)
        is_sdk_call = metadata.get("agent_handle") or metadata.get("space_token")

        if not pilot_data and call_type == "inbound" and not is_sdk_call:
            agent_number = await self.get_agent_number(ctx)
            if not agent_number:
                self._logger.warning("Could not get agent number for inbound SIP call")

            from super.core.voice.common.pilot import get_pilot_and_space_for_number

            pilot_data = await get_pilot_and_space_for_number(agent_number)

        # For SDK calls, don't wait for participant here - it's handled in entrypoint
        if not participant and call_type == "inbound" and not is_sdk_call:
            participant = await ctx.wait_for_participant()

        if model_config:
            agent_id = model_config.get("agent_id", "unknown")
            self._logger.info(f"Resolved agent config: {agent_id}")

        if is_sdk_call:
            self.is_sdk_call = True

            # MERGE space info into user_data instead of replacing it
            # This preserves thread_id and other fields from _resolve_sdk_call_config
            if not user_data:
                user_data = {}
            space_token = metadata.get("space_token")
            space_id = user_data.get("space_id") or model_config.get("space_id")
            user_data.update(
                {
                    "space_token": space_token,
                    "space_id": space_id,
                }
            )
            if not user_data.get("space_id") and space_token:
                self._track_task(
                    asyncio.create_task(
                        self._resolve_space_id_background(user_data, space_token),
                        name="resolve_space_id_background",
                    )
                )
            self._logger.info(
                f"[SDK] user_data after merge: thread_id={user_data.get('thread_id')}, "
                f"space_id={user_data.get('space_id')}"
            )

        if not user_data and pilot_data:
            user_data = {
                "token": pilot_data.get("token", ""),
                "space_name": pilot_data.get("space_name"),
            }

        print(
            f"{'=' * 100}\n\n found agent for number with handle {model_config.get('agent_id')} \n\n{'=' * 100}"
        )
        return AgentConfigResult(
            model_config=model_config,
            user_data=user_data,
            pilot_data=pilot_data,
            participant=participant,
            call_type=call_type,
        )

    async def create_task_run(self, pilot_data, user_state, sdk_call=False):
        if pilot_data.get("space_token") and not pilot_data.get("space_id"):
            from super.core.voice.common.pilot import get_space_id

            pilot_data["space_id"] = get_space_id(pilot_data.get("space_token"))

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

        if sdk_call:
            task_data.execution_type = "sdk_call"

        print(f" \n creating task  {task_data}\n")

        data = await create_task_and_thread(task_data)
        return data

    async def _update_user_state_with_task(
        self,
        task_creation: asyncio.Task,
        user_state: UserState,
        start_time: float,
    ) -> None:
        """
        Background callback to update user_state when task creation completes.

        This runs in the background while the call proceeds, ensuring
        task creation doesn't block call startup.
        """
        try:
            task_data = await task_creation
            task_timer = (perf_counter() - start_time) * 1000

            self._logger.info(
                f"[TIMING] SDK task and run created (background): {task_timer:.0f}ms"
            )
            add_perf_log(user_state, "task_creation_background", task_timer)

            user_state.thread_id = task_data.get("thread_id", "")
            user_state.task_id = task_data.get("task_id", "")

            try:
                if user_state.extra_data is None:
                    user_state.extra_data = {}
                user_state.extra_data["extra"] = task_data
            except Exception:
                pass

            self._logger.info(
                f"[BACKGROUND] Task IDs updated - thread_id: {user_state.thread_id}, "
                f"task_id: {user_state.task_id}"
            )
        except Exception as e:
            self._logger.error(f"[BACKGROUND] Failed to update task IDs: {e}")

    async def _start_recording_background(
        self, ctx: JobContext, user_state: UserState, session_id: str
    ) -> None:
        """Start recording with a bounded timeout so startup never blocks."""
        try:
            url = await asyncio.wait_for(
                self.start_session_recording(
                    room_name=ctx.room.name,
                    session_id=session_id,
                ),
                timeout=2.0,
            )
            if url:
                user_state.recording_url = url
                self._logger.info(f"Recording URL set: {url}")
        except asyncio.TimeoutError:
            self._logger.warning(
                "Background recording start timed out after 2s; continuing call startup"
            )
        except Exception as rec_err:
            self._logger.error(f"Background recording failed: {rec_err}")

    async def _await_call_context_with_timeout(
        self, call_context_task: Optional[asyncio.Task], timeout_sec: float = 0.4
    ) -> Optional[Dict[str, Any]]:
        """Await pre-call context within a strict timeout budget."""
        if not call_context_task:
            return None
        try:
            return await asyncio.wait_for(call_context_task, timeout=timeout_sec)
        except asyncio.TimeoutError:
            self._logger.warning(
                f"Pre-call context timed out after {timeout_sec:.1f}s; skipping context"
            )
            call_context_task.cancel()
        except Exception as e:
            self._logger.warning(f"Pre-call context fetch failed: {e}")
        return None

    def get_trunk_id(self, user_state):
        from super.core.voice.livekit.telephony import SIPManager
        return SIPManager.get_trunk_id(user_state.model_config or {})

    async def _instant_handover(self, user_state: UserState, trunk_id, ctx: JobContext):
        config = user_state.model_config

        if config.get("instant_handover", False):
            room_name = ctx.room.name

            handover_number = config.get("handover_number")

            if isinstance(handover_number, list):
                import random

                handover_number = random.choice(handover_number)
            handover_number = normalize_phone_number(handover_number)

            print(
                f"\n instant handover call  {handover_number} handover {room_name} \n"
            )

            try:
                handover_identity = "human_agent"
                await ctx.api.sip.create_sip_participant(
                    api.CreateSIPParticipantRequest(
                        sip_trunk_id=trunk_id,
                        sip_call_to=handover_number,
                        room_name=room_name,
                        participant_identity=handover_identity,
                        participant_name=handover_identity,
                        krisp_enabled=True,
                    )
                )

                participant = await asyncio.wait_for(
                    ctx.wait_for_participant(identity=handover_identity),
                    timeout=30.0,
                )
                try:
                    room = ctx.room
                    self._logger.info(
                        f"Setting up multi-participant transcription. Remote participants: {list(room.remote_participants.keys())}"
                    )

                    for p in room.remote_participants.values():
                        self._logger.info(
                            f"Starting transcription for existing participant: {p.identity}"
                        )
                        await self._agent._start_participant_transcription(p, room)

                    self._logger.info(
                        f"Started multi-participant transcription after handover"
                    )

                except Exception as e:
                    print(f"error while getting audio transcription: {e}")
                    pass

            except asyncio.TimeoutError:
                self._logger.warning(
                    "Handover timeout: human_agent not joined within 30s"
                )
                user_state.transcript.append(
                    {
                        "role": "system",
                        "type": "instant_handover",
                        "message": "human agent did not join in time",
                    }
                )
                return

            except Exception as e:
                print(
                    f"\n\n {'=' * 100} \n\n {e} \n\n failed transfer call \n\n {'=' * 100}"
                )

                user_state.transcript.append(
                    {
                        "role": "system",
                        "type": "instant_handover",
                        "message": "human agent busy",
                    }
                )

                return

            user_state.transcript.append(
                {
                    "role": "system",
                    "type": "instant_handover",
                    "message": "call successfully handed over to human agent",
                }
            )

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
                # Check if participant already connected (race with prior attempt)
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

                    # Wait for participant to connect
                    participant = await ctx.wait_for_participant(identity=identity)
                    self._logger.info(
                        f"SIP participant connected: {participant.identity}"
                    )

                    if participant:
                        try:
                            await self._instant_handover(user_state, trunk_id, ctx)
                        except Exception as handover_error:
                            self._logger.error(
                                "Instant handover failed after SIP participant "
                                f"connected: {handover_error}"
                            )

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

            self._logger.error(
                f"SIP participant creation exhausted retries for {phone_number}"
            )
            return None

        except Exception as e:
            self._logger.error(f"Error creating SIP participant: {e}")
            import traceback

            self._logger.error(traceback.format_exc())
            return None

    async def _resolve_space_id_background(
        self, user_data: Dict[str, Any], space_token: Optional[str]
    ) -> None:
        """Resolve SDK space_id in background to avoid startup-path DB blocking."""
        if not space_token:
            return

        try:
            from super.core.voice.common.pilot import get_space_id

            space_id = await asyncio.wait_for(
                asyncio.to_thread(get_space_id, space_token),
                timeout=1.0,
            )
            if (
                space_id
                and isinstance(user_data, dict)
                and not user_data.get("space_id")
            ):
                user_data["space_id"] = space_id
                self._logger.info(
                    f"[SDK] Background space_id resolved from token: {space_id}"
                )
        except asyncio.TimeoutError:
            self._logger.warning("[SDK] Background space_id lookup timed out after 1s")
        except Exception as e:
            self._logger.warning(f"[SDK] Background space_id lookup failed: {e}")

    async def _get_config_with_cache(
        self, agent_handle: Optional[str] = None, space_token: Optional[str] = None
    ) -> Optional[Dict]:
        """Get model config with caching to reduce DB lookups."""
        from super_services.voice.models.config import ModelConfig

        config_loader = ModelConfig()
        config = None

        if agent_handle:
            self._logger.info(f"Fetching config for agent_handle: {agent_handle}")
            config = await asyncio.to_thread(config_loader.get_config, agent_handle)
            if config:
                self._logger.info(
                    f"Config found for agent_handle: {agent_handle}, "
                    f"keys: {list(config.keys()) if isinstance(config, dict) else 'N/A'}"
                )
            else:
                self._logger.warning(
                    f"No config found for agent_handle: {agent_handle}"
                )

        if not config and space_token:
            # from super.core.voice.common.pilot import get_pilot_handle_by_space_token

            self._logger.info(f"Trying space_token lookup: {space_token}")
            resolved_handle = None  # get_pilot_handle_by_space_token(space_token)
            if resolved_handle:
                self._logger.info(
                    f"Resolved handle from space_token: {resolved_handle}"
                )
                config = await asyncio.to_thread(
                    config_loader.get_config, resolved_handle
                )
                if config:
                    self._logger.info(
                        f"Config found for resolved handle: {resolved_handle}"
                    )
                else:
                    self._logger.warning(
                        f"No config found for resolved handle: {resolved_handle}"
                    )
            else:
                self._logger.warning(
                    f"Could not resolve handle from space_token: {space_token}"
                )

        # Merge executor-level config overrides (from self.config)
        # This allows superkik_executor to override STT/TTS/LLM settings
        merger_start = perf_counter()
        config = self._merge_executor_config(config or {})
        merger_time = (perf_counter() - merger_start) * 1000
        if not isinstance(self._temp_perf_logs, list):
            self._temp_perf_logs = []
        self._temp_perf_logs.append(
            {"name": "merger_config", "duration_ms": round(merger_time, 2)}
        )
        self._logger.info(f"[TIMING] time for merger config: {merger_time:.0f}ms")
        return config if config else None

    def _merge_executor_config(self, db_config: Dict) -> Dict:
        """
        Merge executor-level config overrides with database config.

        Priority: executor config > database config
        This allows executors (like superkik_executor) to override
        STT/TTS/LLM provider settings.
        """
        # Log original DB config STT/TTS values for debugging
        self._logger.info(
            f"[CONFIG_MERGE] DB config - "
            f"stt_provider={db_config.get('stt_provider')}, "
            f"stt_model={db_config.get('stt_model')}, "
            f"tts_provider={db_config.get('tts_provider')}, "
            f"tts_model={db_config.get('tts_model')}"
        )

        if not self.config:
            self._logger.info("[CONFIG_MERGE] No executor config, using DB config only")
            return db_config

        # Extract executor config dict from BaseModelConfig or dict
        executor_config = {}
        if hasattr(self.config, "config") and isinstance(self.config.config, dict):
            executor_config = self.config.config
            self._logger.info(
                f"[CONFIG_MERGE] Extracted executor config from BaseModelConfig.config"
            )
        elif isinstance(self.config, dict):
            executor_config = self.config
            self._logger.info(f"[CONFIG_MERGE] Using executor config as dict directly")

        if not executor_config:
            self._logger.info(
                "[CONFIG_MERGE] Executor config is empty, using DB config"
            )
            return db_config

        # Log executor config STT/TTS values
        self._logger.info(
            f"[CONFIG_MERGE] Executor config - "
            f"stt_provider={executor_config.get('stt_provider')}, "
            f"stt_model={executor_config.get('stt_model')}, "
            f"tts_provider={executor_config.get('tts_provider')}, "
            f"tts_model={executor_config.get('tts_model')}"
        )

        # Merge: executor config takes priority for STT/TTS/LLM settings
        merged = db_config.copy()
        override_keys = [
            "stt_provider",
            "stt_model",
            "stt_language",
            "stt_inference",
            "tts_provider",
            "tts_model",
            "tts_voice",
            "tts_inference",
            "llm_provider",
            "llm_model",
            "llm_inference",
            "speaking_plan",
            "superkik",  # SuperKik-specific config
        ]

        overrides_applied = []
        for key in override_keys:
            if key in executor_config and executor_config[key]:
                old_val = merged.get(key)
                if (
                    key == "speaking_plan"
                    and isinstance(old_val, dict)
                    and isinstance(executor_config[key], dict)
                ):
                    merged_plan = old_val.copy()
                    merged_plan.update(executor_config[key])
                    merged[key] = merged_plan
                else:
                    merged[key] = executor_config[key]
                overrides_applied.append(f"{key}: {old_val} -> {merged.get(key)}")

        if overrides_applied:
            self._logger.info(
                f"[CONFIG_MERGE] Applied {len(overrides_applied)} overrides: "
                f"{', '.join(overrides_applied)}"
            )

        # Also merge nested configs like google_places, telephony
        for nested_key in ["google_places", "telephony"]:
            if nested_key in executor_config and executor_config[nested_key]:
                if nested_key not in merged:
                    merged[nested_key] = {}
                if isinstance(merged[nested_key], dict):
                    merged[nested_key].update(executor_config[nested_key])
                    self._logger.debug(f"[CONFIG_MERGE] Merged nested: {nested_key}")

        # Log final merged STT/TTS values
        self._logger.info(
            f"[CONFIG_MERGE] Final merged config - "
            f"stt_provider={merged.get('stt_provider')}, "
            f"stt_model={merged.get('stt_model')}, "
            f"tts_provider={merged.get('tts_provider')}, "
            f"tts_model={merged.get('tts_model')}"
        )

        return merged

    async def _signal_early_agent_state(
        self, ctx: JobContext, state: str = "initializing"
    ) -> None:
        """Signal agent state immediately to prevent frontend timeouts."""
        try:
            await ctx.room.local_participant.set_attributes(
                {
                    "lk.agent.state": state,
                    "agent.name": self.agent_name,
                }
            )
            self._logger.info(f"[TIMING] Early agent state signaled: {state}")
        except Exception as e:
            self._logger.warning(f"Failed to signal early agent state: {e}")

    async def get_call_context(self, number, assistant):
        executor = PreCallWorkFlow(agent_id=assistant)
        res = executor.execute_inbound(number)
        result = {
            "pre_call_result": res,
        }
        return result

    # Entrypoint for agent worker execution (from sip_lifecycle.py)
    async def entrypoint(self, ctx: JobContext):
        """
        Optimized entrypoint for LiveKit agent worker.

        Key optimizations:
        1. Early agent state signaling (prevents frontend timeouts)
        2. Config caching (reduces DB lookups)
        3. Parallel initialization (overlaps config lookup with participant wait)
        4. EARLY service preload (starts pipecat init during config resolution)
        5. Comprehensive timing instrumentation
        6. Performance logging to MongoDB for analysis
        """
        _entrypoint_start = perf_counter()

        # Temporary perf_logs list until user_state is created
        self._temp_perf_logs = []

        # Reset per-call state for dev mode where same handler instance handles multiple calls
        self._room_events_registered = False

        try:
            # Debug: Log LiveKit credentials availability (not the values themselves)
            lk_url = os.getenv("LIVEKIT_URL", "")
            lk_key = os.getenv("LIVEKIT_API_KEY", "")
            lk_secret = os.getenv("LIVEKIT_API_SECRET", "")
            self._logger.info(
                f"[DEBUG] LiveKit credentials check - "
                f"URL set: {bool(lk_url)} ({lk_url[:30]}...) | "
                f"API_KEY set: {bool(lk_key)} (len={len(lk_key)}) | "
                f"API_SECRET set: {bool(lk_secret)} (len={len(lk_secret)})"
            )
            task_creation = None
            # Step 1: Connect to room FIRST (required for all subsequent operations)
            _connect_start = perf_counter()
            self._logger.info(
                f"[DEBUG] Attempting to connect to room: {ctx.room.name if hasattr(ctx, 'room') and ctx.room else 'unknown'}"
            )
            _get_handlers = asyncio.create_task(
                self._get_handler_classes(ctx=ctx), name="handler_class"
            )

            await ctx.connect()

            _connect_time = (perf_counter() - _connect_start) * 1000
            self._append_temp_perf_log("room_connect", _connect_time)
            self._logger.info(f"[TIMING] Room connect: {_connect_time:.0f}ms")
            budget_ms = STARTUP_STAGE_BUDGETS_MS.get("room_connect")
            if budget_ms is not None and _connect_time > budget_ms:
                self._logger.warning(
                    f"[TIMING][BUDGET] room_connect exceeded budget: "
                    f"{_connect_time:.0f}ms > {budget_ms}ms"
                )
            self._job_context = ctx

            # Recording is started later (non-blocking) after participant joins
            # Removed redundant session_recordings() call that blocked startup

            # Step 2: Signal "initializing" state IMMEDIATELY after connect
            # This is critical for inbound calls - prevents disconnect before agent ready
            # await self._signal_early_agent_state(ctx, "initializing")

            # Step 3: Parse metadata and resolve agent config
            metadata = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
            self._logger.info(
                f"[TIMING] Metadata parsed: {(perf_counter() - _entrypoint_start) * 1000:.0f}ms"
            )
            print(f"[TIMING] metadata: {metadata}")

            user_data = metadata.get("data", {})
            update_task_with_status(user_data.get("task_id"),CallStatusEnum.InCall)
            await save_execution_log(
                user_data.get("task_id"),
                "call-request-received",
                TaskStatusEnum.completed,
                {"status": "call-request-received by livekit"},
            )
            # Determine call type early for optimization decisions
            call_type = (
                "outbound" if metadata.get("call_type") == "outbound" else "inbound"
            )

            print(
                f"{'='*100} \n\n\n sending call to {user_data.get('contact_number')} \n\n\n {'='*100}"
            )
            # Extract modality from metadata (multimodality -> modality)
            # Default to text_audio for full voice mode
            raw_modality = metadata.get("multimodality", "text_audio")
            modality = Modality.TEXT if raw_modality == "text" else Modality.TEXT_AUDIO
            self._logger.info(f"[MODALITY] Session modality: {modality}")

            # Step 4: For INBOUND calls, start config resolution AND early service init in parallel
            # This is the key optimization - services don't need full config to start initializing
            _config_start = perf_counter()

            if call_type == "inbound":
                # Get handler classes early (already started above)
                handler_class, handler_name = await _get_handlers

                # Create a minimal user_state for early service initialization
                # Services only need room_name and model_config (which we get from config resolution)

                # Start config resolution and early pipecat init IN PARALLEL
                config_task = asyncio.create_task(
                    self._resolve_agent_config(ctx, metadata), name="resolve_config"
                )

                # Don't wait for config - start preparing handler immediately
                # The handler will get full config when we call preload_agent
                self._logger.info(
                    "[TIMING] Starting parallel config + early handler init"
                )

                # Wait for config first (needed for user_state)
                config_result = await config_task
                if not config_result:
                    self._logger.error("Failed to resolve agent configuration")
                    return

                model_config = config_result.model_config
                user_data = config_result.user_data
                pilot_data = config_result.pilot_data
                participant = config_result.participant

                # Add config resolution timing
                self._log_stage_timing(
                    "config_resolution",
                    _config_start,
                    label=f"Config resolved ({call_type})",
                )

                # Build full user_state now that we have config
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
                    modality=modality,
                    extra_data={"perf_logs": self._temp_perf_logs},
                )
                self.user_state = user_state

                # Setup room events (fast, non-blocking)
                _room_events = asyncio.create_task(
                    self._setup_room_events(ctx, user_state), name="room_events"
                )

                _pipecat_start = perf_counter()

                # Start assistant exactly once per entrypoint, regardless of branch flow.
                pipecat_task: Optional[asyncio.Task] = None

                call_context = None

                if participant and model_config and not self.is_sdk_call:
                    number = participant.identity.replace("sip_0", "")
                    assistant = model_config.get("agent_id")
                    if number and assistant:
                        call_context = asyncio.create_task(
                            self.get_call_context(number, assistant)
                        )
                        self._track_task(call_context)

                # Case 1: SIP inbound call - participant already resolved
                if pilot_data and participant:
                    from super.core.voice.common.pilot import get_space_token

                    user_state.contact_number = participant.identity.replace(
                        "sip_0", ""
                    )
                    user_state.token = get_space_token(pilot_data.get("space_id"))
                    user_state.user_name = participant.identity

                    _task_start = perf_counter()
                    task_creation = asyncio.create_task(
                        self.create_task_run(pilot_data, user_state),
                        name="create_task",
                    )
                    self._track_task(task_creation)

                    # Wait for both pipecat and task creation in parallel
                    try:
                        pipecat_task = self._start_assistant_task(
                            existing_task=pipecat_task,
                            user_state=user_state,
                            ctx=ctx,
                            handler_class=handler_class,
                            handler_name=handler_name,
                            task_name="create_pipecat",
                        )
                        await pipecat_task
                        # task_data = await task_creation
                        self._logger.info(
                            f"[TIMING] parallel pipecat+task: {(perf_counter() - _task_start) * 1000:.0f}ms"
                        )
                    except Exception as e:
                        self._logger.error(f"Error in parallel task creation: {e}")
                        pipecat_task.cancel()
                        task_creation.cancel()
                        return

                    # user_state.thread_id = task_data.get("thread_id", "")
                    # user_state.task_id = task_data.get("task_id", "")
                    extra_data = {"call_type": "inbound"}

                    if call_context:
                        context = await self._await_call_context_with_timeout(
                            call_context
                        )
                        if context:
                            extra_data["data"] = context

                    if not user_state.extra_data:
                        user_state.extra_data = {}
                    user_state.extra_data.update(extra_data)

                    print(f"\n\n\n extra data for inbound {extra_data} \n\n\n")

                # Case 2: SDK/web call - participant already resolved in parallel during config
                elif self.is_sdk_call and participant:
                    self._logger.info(
                        f"[SDK] SDK/web call with participant resolved - "
                        f"participant: {participant.identity if participant else 'None'}"
                    )

                    # SDK calls: Differentiate between Conversation (SuperKik) and Talk to Agent
                    # - SuperKik (Conversation): Only create thread, no task
                    # - Other handlers (Talk to Agent): Nothing (no task, no thread)
                    space_id = (
                        model_config.get("space_id")
                        or user_data.get("space_id")
                        or user_data.get("space_token")
                    )
                    user_id = user_data.get("user", {}).get("id")
                    print(f"\n space id from config for sdk {space_id} \n")
                    print(f"\n handler_name for sdk: {handler_name} \n")

                    is_conversation = handler_name == "SuperKikHandler"

                    # IMPORTANT: Create thread BEFORE awaiting pipecat_task
                    # This ensures thread_id is set before agent starts listening
                    if is_conversation and space_id and user_id:
                        # Check if thread_id already exists in metadata
                        if user_state.thread_id:
                            # Use existing thread_id from metadata, no need to create new
                            self._logger.info(
                                f"[SDK-Conversation] Using existing thread_id from metadata: {user_state.thread_id}"
                            )
                        else:
                            # Conversation (SuperKik): Only create thread, no task
                            self._logger.info(
                                f"[SDK-Conversation] Creating thread only (no task) for SuperKik"
                            )
                            try:
                                from super_services.voice.common.threads import (
                                    create_thread_without_task,
                                )

                                thread_id = await create_thread_without_task(
                                    space_id=str(space_id),
                                    user_id=str(user_id),
                                    title="SDK Conversation",
                                )
                                # Update user_state with the new thread_id
                                user_state.thread_id = thread_id
                                self._logger.info(
                                    f"[SDK-Conversation] Created thread_id: {thread_id}"
                                )
                            except Exception as e:
                                self._logger.warning(
                                    f"[SDK-Conversation] Failed to create thread: {e}"
                                )
                    elif not is_conversation:
                        # Talk to Agent: No task, no thread required
                        self._logger.info(
                            f"[SDK-TalkToAgent] Skipping task/thread creation for Talk to Agent"
                        )
                    else:
                        self._logger.warning(
                            "[SDK] No space_id or user_id found, skipping thread creation"
                        )

                    # Now create pipecat AFTER thread_id is set
                    # This ensures agent has valid thread_id when it starts
                    pipecat_task = self._start_assistant_task(
                        existing_task=pipecat_task,
                        user_state=user_state,
                        ctx=ctx,
                        handler_class=handler_class,
                        handler_name=handler_name,
                        task_name="create_pipecat_sdk",
                    )
                    await pipecat_task

                    if not user_state.extra_data:
                        user_state.extra_data = {}

                    user_state.extra_data["call_type"] = "sdk"

                # Case 3: Unexpected - no participant available
                elif not participant:
                    self._logger.error(
                        f"[ERROR] No participant available - "
                        f"pilot_data: {pilot_data is not None}, is_sdk_call: {self.is_sdk_call}"
                    )
                    if pipecat_task:
                        pipecat_task.cancel()
                    return

                self._log_stage_timing(
                    "pipecat_setup",
                    _pipecat_start,
                    user_state=user_state,
                    label="total inbound pipecat setup",
                )

            else:
                extra_data = {}

                # OUTBOUND call flow - original sequential logic
                config_result = await self._resolve_agent_config(ctx, metadata)
                if not config_result:
                    self._logger.error("Failed to resolve agent configuration")
                    return

                model_config = config_result.model_config
                user_data = config_result.user_data
                pilot_data = config_result.pilot_data
                participant = config_result.participant

                self._logger.info(
                    f"[TIMING] Config resolved ({call_type}): "
                    f"{(perf_counter() - _config_start) * 1000:.0f}ms"
                )

                # Build user_state
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
                    modality=modality,
                    extra_data={"perf_logs": self._temp_perf_logs},
                )
                self.user_state = user_state

                # Create thread if not provided (similar to SDK flow)
                if not user_state.thread_id:
                    space_id = user_data.get("space_id") or user_data.get("space_token")
                    user_id = user_data.get("user", {}).get("id")
                    if space_id and user_id:
                        self._logger.info(
                            f"[OUTBOUND] Creating thread for call (no thread_id in user_data)"
                        )
                        try:
                            from super_services.voice.common.threads import (
                                create_thread_without_task,
                            )

                            thread_id = await create_thread_without_task(
                                space_id=str(space_id),
                                user_id=str(user_id),
                                title="Voice Call",
                            )
                            user_state.thread_id = thread_id
                            self._logger.info(
                                f"[OUTBOUND] Created thread_id: {thread_id}"
                            )
                        except Exception as e:
                            self._logger.warning(
                                f"[OUTBOUND] Failed to create thread: {e}"
                            )
                    else:
                        self._logger.warning(
                            f"[OUTBOUND] No space_id or user_id found, skipping thread creation"
                        )

                _room_events = asyncio.create_task(
                    self._setup_room_events(ctx, user_state), name="room_events"
                )
                handler_class, handler_name = await _get_handlers

                _pipecat_start = perf_counter()
                await self._create_assistant(
                    user_state, ctx, handler_class, handler_name
                )
                self._logger.info(
                    f"[TIMING] pipecat creation: {(perf_counter() - _pipecat_start) * 1000:.0f}ms"
                )

                _sip_start = perf_counter()
                participant = await self._create_sip_participant_in_room(
                    ctx=ctx, data=user_data, user_state=user_state
                )
                self._logger.info(
                    f"[TIMING] SIP participant creation: {(perf_counter() - _sip_start) * 1000:.0f}ms"
                )
                extra_data["call_type"] = "outbound"
                extra_data["data"] = metadata.get("data")

                if not user_state.extra_data:
                    user_state.extra_data = {}

                user_state.extra_data.update(extra_data)

            if participant:
                if user_data:
                    if not isinstance(user_state.extra_data, dict):
                        user_state.extra_data = {}
                    user_state.extra_data["user_data"] = user_data

                self._logger.info(
                    f"Participant ready: {participant.identity}, kind: {participant.kind}"
                )

                if task_creation:
                    # Schedule background callback to update user_state when task is ready
                    asyncio.create_task(
                        self._update_user_state_with_task(
                            task_creation, user_state, perf_counter()
                        )
                    )

                self._log_stage_timing(
                    "total_entrypoint",
                    _entrypoint_start,
                    user_state=user_state,
                    label="Total entrypoint setup",
                )
                self._logger.info(
                    f"[DEBUG] participant check - participant: {participant}, "
                    f"call_type: {call_type}, pilot_data: {pilot_data}"
                )

                if participant.kind in [
                    rtc.ParticipantKind.PARTICIPANT_KIND_SIP,
                    rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD,
                ]:
                    await self.manage_call(
                        ctx, participant, user_state, self._agent, call_type
                    )
            else:
                self._logger.error(
                    f"[ERROR] Failed to create/get participant - "
                    f"call_type: {call_type}, model_config exists: {bool(model_config)}"
                )
                self.message_callback("EOF\n", role="system", user_state=user_state)

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
                self.message_callback(
                    "EOF\n", role="system", user_state=self.user_state
                )
            raise e

    def execute_agent_worker(self):
        """Execute agent worker - based on sip_lifecycle.py"""
        try:
            # Verify environment variables are set before starting
            lk_url = os.getenv("LIVEKIT_URL", "")
            lk_key = os.getenv("LIVEKIT_API_KEY", "")
            lk_secret = os.getenv("LIVEKIT_API_SECRET", "")

            self._logger.info(
                f"Starting LiveKit agent worker: {self.agent_config.agent_name}"
            )
            self._logger.info(
                f"[WORKER] LiveKit config - URL: {lk_url[:30] if lk_url else 'NOT SET'}... | "
                f"API_KEY: {'set' if lk_key else 'NOT SET'} (len={len(lk_key)}) | "
                f"API_SECRET: {'set' if lk_secret else 'NOT SET'} (len={len(lk_secret)})"
            )

            if not all([lk_url, lk_key, lk_secret]):
                self._logger.error(
                    "[WORKER] Missing required LiveKit credentials! "
                    "Ensure LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET are set."
                )
                raise ValueError("Missing LiveKit credentials in environment")

            # Preload LiveKit plugins on the main thread to avoid registration errors
            livekit_services._ensure_livekit_plugins_loaded(self._logger)

            # Check if prewarm is enabled (default: true for faster startup)
            enable_prewarm = os.getenv("ENABLE_PREWARM", "true").lower() == "true"

            # Run the worker using cli.run_app with prewarm function
            cli.run_app(
                WorkerOptions(
                    entrypoint_fnc=self.entrypoint,
                    agent_name=self.agent_config.agent_name,
                    prewarm_fnc=prewarm_process if enable_prewarm else None,
                    num_idle_processes=int(os.getenv("NUM_IDLE_PROCESSES", "1")),
                )
            )

        except Exception as e:
            self._logger.error(f"Error in agent worker: {e}")
            raise e

    async def _setup_room_events(self, ctx: JobContext, user_state: UserState) -> None:
        """Register LiveKit room event handlers following the EventEmitter pattern."""
        # Guard against duplicate registration
        if self._room_events_registered:
            self._logger.debug("Room events already registered, skipping")
            return
        self._room_events_registered = True

        room = ctx.room

        @room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            self._logger.info(f"Participant connected: {participant.identity}")

        events = []
        ringing = False
        calling_time = 0

        @room.on("participant_attributes_changed")
        def on_participant_attributes_changed(
            changed_attributes: dict, participant: rtc.Participant
        ):
            self._logger.info(
                f"Participant {participant.identity} attributes changed: {changed_attributes}"
            )
            nonlocal events, calling_time, ringing

            async def handle_disconnect(status):
                # user_state.end_time = datetime.utcnow()
                user_state.call_status = status
                await self.execute_post_call(user_state)

                # res = await build_call_result(user_state)
                # await trigger_post_call(user_state=user_state, res=res)

                print(
                    f"{'=' * 50} \n\n livekit call ended triggering post call \n\n {'=' * 50}"
                )
                # ctx.shutdown()

            async def handle_ringing():
                nonlocal calling_time, ringing
                while ringing:
                    await asyncio.sleep(1)
                    calling_time += 1
                    if calling_time >= 30:
                        ringing = False
                        await send_web_notification(
                            "completed",
                            "call_missed",
                            self.user_state,
                            "user did not pick up call",
                        )
                        user_state.end_time = user_state.start_time
                        await handle_disconnect(CallStatusEnum.NOT_CONNECTED)

            if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                call_status = changed_attributes.get("sip.callStatus")
                if call_status not in events:
                    events.append(call_status)
                    print(events)

                if call_status:
                    self._logger.info(f"SIP Call Status updated: {call_status}")

                    if call_status == "active":
                        ringing = False

                        asyncio.create_task(
                            send_web_notification(
                                "completed",
                                "call_started",
                                self.user_state,
                                "call picked up by user",
                            )
                        )
                        user_state.call_status = CallStatusEnum.CONNECTED
                        self._logger.info("Call is now active and connected")

                    elif call_status == "ringing":
                        ringing = True
                        asyncio.create_task(handle_ringing())

                    elif call_status == "hangup":
                        ringing = False
                        user_state.end_time = datetime.utcnow()

                        asyncio.create_task(
                            send_web_notification(
                                "completed",
                                "call_hang_up",
                                self.user_state,
                                "user hang up the call",
                            )
                        )
                        self._logger.info("Call has been ended by participant")
                        # asyncio.create_task(handle_disconnect(CallStatusEnum.COMPLETED))

                        self.message_callback(
                            "Call Status:User hung up\n",
                            role="system",
                            user_state=user_state,
                        )

                        self.message_callback(
                            "EOF\n", role="system", user_state=user_state
                        )
                    elif call_status == "dialing":
                        user_state.call_status = CallStatusEnum.CONNECTED

        @room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            self._logger.info(f"Participant disconnected: {participant.identity}")

            # Check if this is a handover scenario
            is_handover_active = False
            handover_identity = None
            if isinstance(user_state.extra_data, dict):
                is_handover_active = user_state.extra_data.get(
                    "is_handed_over_call", False
                )
                handover_identity = user_state.extra_data.get(
                    "handover_participant_identity"
                )

            phone_number = normalize_phone_number(user_state.contact_number)
            is_original_caller = participant.identity == f"idt_{phone_number}"

            # Handle handover scenario - end session only when BOTH user and handover participant leave
            if is_handover_active and handover_identity:
                # Initialize tracking dict if not exists
                if not isinstance(
                    user_state.extra_data.get("_handover_disconnected"), dict
                ):
                    user_state.extra_data["_handover_disconnected"] = {
                        "user": False,
                        "handover": False,
                    }

                disconnected = user_state.extra_data["_handover_disconnected"]

                # Track who disconnected
                if participant.identity == handover_identity:
                    disconnected["handover"] = True
                    self._logger.info(
                        f"Handover participant {participant.identity} disconnected"
                    )
                elif is_original_caller:
                    disconnected["user"] = True
                    self._logger.info(
                        f"Original user {participant.identity} disconnected during handover"
                    )

                # Check if BOTH have disconnected
                if disconnected["user"] and disconnected["handover"]:
                    self._logger.info(
                        "Both user and handover participant have disconnected, ending session"
                    )
                    # Continue to end session below
                else:
                    still_connected = (
                        "handover participant"
                        if not disconnected["handover"]
                        else "user"
                    )
                    self._logger.info(
                        f"Handover mode: {still_connected} still connected, session continues"
                    )
                    return

            # Use user_state from closure (captured at registration time), not self.user_state
            # which may have been overwritten by a subsequent call
            self.message_callback(
                f"Call Status:User Left the call\n",
                role="system",
                user_state=user_state,
            )
            self.message_callback("EOF\n", role="system", user_state=user_state)

            # End session if original caller disconnects (no handover) OR both have disconnected
            if is_original_caller:
                async def handle_disconnect():
                    user_state.call_status = CallStatusEnum.COMPLETED
                    user_state.end_time = datetime.utcnow()
                    await self.execute_post_call(user_state)

                    print(
                        f"{'=' * 50} \n\n livekit call ended triggering post call \n\n {'=' * 50}"
                    )

                asyncio.create_task(handle_disconnect())

        @room.on("track_subscribed")
        def on_track_subscribed(track, _publication, participant):
            self._logger.info(
                f"Track subscribed: {track.kind} from {participant.identity}"
            )

        @room.on("connection_state_changed")
        def on_connection_state_changed(state):
            self._logger.info(f"Room connection state changed: {state}")
            # state: 0=DISCONNECTED, 1=CONNECTED, 2=RECONNECTING
            if state == 0:  # DISCONNECTED
                # Only log - let reconnecting handler attempt reconnection
                self._logger.warning(
                    "Room disconnected - waiting for reconnection attempt"
                )

        @room.on("reconnecting")
        def on_reconnecting():
            self._logger.warning(
                "Room reconnecting... agent will resume when connected"
            )
            # Don't shut down - LiveKit SDK will attempt auto-reconnection

        @room.on("reconnected")
        def on_reconnected():
            self._logger.info("Room reconnected - agent resumed")

        @room.on("disconnected")
        def on_disconnected():
            self._logger.warning("Room permanently disconnected - unable to reconnect")

    def _setup_session_events(
        self, session: AgentSession, user_state: UserState
    ) -> None:
        """Register AgentSession event handlers for metrics and transcripts."""

        @session.on("metrics_collected")
        def on_metrics_collected(ev: MetricsCollectedEvent):
            if not hasattr(user_state, "usage"):
                user_state.usage = metrics.UsageCollector()
            user_state.usage.collect(ev.metrics)
            metrics.log_metrics(ev.metrics)

        @session.on("agent_state_changed")
        def on_agent_state_changed(state: AgentStateChangedEvent):
            self._logger.info(f"Agent state changed: {state.new_state}")

        @session.on("conversation_item_added")
        def on_conversation_item_added(msg: ConversationItemAddedEvent):
            if msg.item.role == "assistant":
                agent_text = msg.item.content[0] if msg.item.content else ""
                if agent_text:
                    transcript_entry = {
                        "role": "assistant",
                        "content": str(agent_text),
                        "timestamp": str(datetime.now()),
                    }
                    user_state.transcript.append(transcript_entry)
                    self.message_callback(
                        str(agent_text), role="assistant", user_state=user_state
                    )

        @session.on("user_input_transcribed")
        def on_user_input_transcribed(ev: UserInputTranscribedEvent):
            print(f"identity in {ev.identity} on_user_input_transcribed  ")
            if ev.is_final and ev.transcript:
                transcript_entry = {
                    "role": "user",
                    "content": ev.transcript,
                    "timestamp": str(datetime.now()),
                }
                user_state.transcript.append(transcript_entry)
                self.message_callback(ev.transcript, role="user", user_state=user_state)

    async def start_session_recording(
        self, room_name: str, session_id: Optional[str] = None
    ) -> str:
        """Start room composite egress recording to S3.

        Args:
            room_name: The name of the LiveKit room to record.
            session_id: Optional session ID to use as filename (falls back to room_name).

        Returns:
            The S3 URL where the recording will be stored, or empty string on failure.
        """
        try:
            s3_bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
            s3_region = os.getenv("AWS_S3_REGION_NAME", "ap-south-1")
            s3_access_key = os.getenv("AWS_ACCESS_KEY_ID")
            s3_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

            if not all([s3_bucket, s3_region, s3_access_key, s3_secret_key]):
                self._logger.warning(
                    "S3 credentials not configured, skipping recording"
                )
                return ""

            # Use session_id for filename if available, fallback to room_name
            filename = session_id or room_name
            filepath = f"media/private/high-call-recordings/{filename}.ogg"

            req = api.RoomCompositeEgressRequest(
                room_name=room_name,
                audio_only=True,
                file_outputs=[
                    api.EncodedFileOutput(
                        file_type=api.EncodedFileType.OGG,
                        filepath=filepath,
                        s3=api.S3Upload(
                            bucket=s3_bucket,
                            region=s3_region,
                            access_key=s3_access_key,
                            secret=s3_secret_key,
                        ),
                    )
                ],
            )

            lkapi = api.LiveKitAPI()
            await lkapi.egress.start_room_composite_egress(req)
            await lkapi.aclose()

            recording_url = (
                f"https://{s3_bucket}.s3.{s3_region}.amazonaws.com/{filepath}"
            )
            self._logger.info(f"Recording started: {recording_url}")
            return recording_url

        except Exception as e:
            self._logger.error(f"Recording failed: {e}")
            return ""

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
            try:
                duration_seconds = (
                    user_state.end_time - user_state.start_time
                ).total_seconds()
                usage_data["call_duration_seconds"] = duration_seconds

            except Exception as e:
                pass
        try:
            extra_data = (
                user_state.extra_data
                if isinstance(getattr(user_state, "extra_data", None), dict)
                else {}
            )
            latency_metrics = extra_data.get("latency_metrics", [])
            if isinstance(latency_metrics, list) and latency_metrics:
                llm_values = []
                for item in latency_metrics:
                    if not isinstance(item, dict):
                        continue
                    for key in ("llm_latency", "realtime_latency"):
                        value = item.get(key)
                        if isinstance(value, (int, float)) and value > 0:
                            llm_values.append(float(value))

                if llm_values:
                    usage_data["llm_latency_samples"] = len(llm_values)
                    usage_data["llm_latency_avg_seconds"] = round(
                        sum(llm_values) / len(llm_values), 4
                    )
                    usage_data["llm_latency_last_seconds"] = round(llm_values[-1], 4)
        except Exception:
            pass

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

    def _setup_signal_handlers(self) -> None:
        """
        Setup signal handlers for graceful shutdown.

        Handles SIGTERM and SIGINT to ensure proper cleanup of:
        - Active sessions
        - Pending async tasks
        - Cached services
        """

        def signal_handler(signum, frame):
            sig_name = signal.Signals(signum).name
            self._logger.info(f"Received {sig_name}, initiating graceful shutdown...")
            self._is_shutting_down = True

            # Log active sessions that need cleanup
            if self.active_sessions:
                self._logger.info(
                    f"Cleaning up {len(self.active_sessions)} active sessions..."
                )

            # Schedule async cleanup in the event loop if running
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._graceful_shutdown())
            except RuntimeError:
                # No event loop running, perform sync cleanup
                self._logger.info("No event loop, performing sync cleanup...")
                self._sync_cleanup()

        # Register handlers for graceful shutdown signals
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        self._logger.info("Signal handlers registered for graceful shutdown")

    async def _graceful_shutdown(self, timeout: float = 30.0) -> None:
        """
        Perform graceful async shutdown of all resources.

        Args:
            timeout: Maximum time to wait for cleanup
        """
        self._logger.info("Starting graceful shutdown...")

        try:
            # Cancel all pending tasks
            cancelled = await self._cancel_pending_tasks(timeout=5.0)
            self._logger.info(f"Cancelled {cancelled} pending tasks")

            # Clean up all active sessions
            session_ids = list(self.active_sessions.keys())
            for session_id in session_ids:
                session = self._unregister_session(session_id)
                if session:
                    self._logger.debug(f"Cleaned up session: {session_id}")

            # Clear service cache
            cache = get_service_cache()
            cache.clear()
            self._logger.info("Service cache cleared")

            # Force garbage collection
            gc.collect()

            self._logger.info("Graceful shutdown completed")

        except Exception as e:
            self._logger.error(f"Error during graceful shutdown: {e}")

    def _sync_cleanup(self) -> None:
        """Synchronous cleanup when no event loop is available."""
        try:
            # Clear active sessions
            self.active_sessions.clear()

            # Clear service cache
            cache = get_service_cache()
            cache.clear()

            # Force garbage collection
            gc.collect()

            self._logger.info("Sync cleanup completed")
        except Exception as e:
            self._logger.error(f"Error during sync cleanup: {e}")

    def execute_agent(self):
        """Execute agent worker - synchronous wrapper for cli.run_app"""
        try:
            outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
            if not outbound_trunk_id or not outbound_trunk_id.startswith("ST_"):
                raise ValueError(
                    "SIP_OUTBOUND_TRUNK_ID is not set. Please follow the guide at https://docs.livekit.io/agents/quickstarts/outbound-calls/ to set it up."
                )

            self._logger.info(f"Starting LiveKit agent worker: {self.agent_name}")

            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()

            # Register atexit handler for cleanup on process exit
            atexit.register(self._sync_cleanup)

            # Preload LiveKit plugins on the main thread to avoid registration errors
            livekit_services._ensure_livekit_plugins_loaded(self._logger)

            # Check if prewarm is enabled (default: true for faster startup)
            enable_prewarm = os.getenv("ENABLE_PREWARM", "true").lower() == "true"

            try:
                cli.run_app(
                    WorkerOptions(
                        entrypoint_fnc=self.entrypoint,
                        agent_name=self.agent_name,
                        initialize_process_timeout=float(
                            os.getenv("LK_PROCESS_TIMEOUT", "60.0")
                        ),
                        prewarm_fnc=prewarm_process if enable_prewarm else None,
                        num_idle_processes=int(os.getenv("NUM_IDLE_PROCESSES", "1")),
                    )
                )
            finally:
                # Ensure cleanup on normal exit
                self._sync_cleanup()

        except Exception as e:
            self._logger.error(f"Error in execute_agent: {e}")
            raise e

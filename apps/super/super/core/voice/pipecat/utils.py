"""
Pipecat Voice Handler Utility Module

This module contains utility functions and helper classes extracted from the main
PipecatVoiceHandler to improve code organization and reusability.

Classes:
    UpPipelineRunner: Custom PipelineRunner with graceful shutdown handling

Functions:
    shutdown: Async function to gracefully shutdown AsyncClient tasks
    get_user_state: Creates a UserState object for voice sessions
    create_usage: Extracts and serializes usage data from UserState
    get_os_info: Returns formatted operating system information
    _get_default_config: Returns default agent configuration
"""

import asyncio
import platform
import signal
from datetime import datetime
from typing import Any, Dict, Optional

import distro

from super.core.voice.schema import UserState

# Import pipecat components
try:
    from pipecat.pipeline.runner import PipelineRunner
    PIPECAT_AVAILABLE = True
except ImportError:
    PIPECAT_AVAILABLE = False
    PipelineRunner = object  # Fallback for type hints


# Async Shutdown Function
async def shutdown() -> None:
    """
    Gracefully shutdown all AsyncClient related tasks.

    This function identifies and cancels all pending asyncio tasks related to
    AsyncClient operations (lease loops, warmup tasks, etc.) to ensure a clean
    shutdown without leaving dangling tasks.

    The function suppresses CancelledError and other exceptions that may occur
    during task cancellation to ensure shutdown completes.

    Returns:
        None

    Example:
        # >>> await shutdown()
    """
    try:
        # Get all pending tasks
        tasks = [task for task in asyncio.all_tasks() if not task.done()]

        # Cancel tasks related to AsyncClient
        for task in tasks:
            try:
                task_str = str(task.get_coro())
                if any(name in task_str for name in ['AsyncClient', '_lease_loop', 'warmup']):
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        pass
            except Exception as e:
                pass
    except Exception as e:
        pass


# Custom Pipeline Runner
class UpPipelineRunner(PipelineRunner):
    """
    Custom PipelineRunner with enhanced signal handling for graceful shutdown.

    This class extends the base PipelineRunner to provide platform-specific
    signal handling, particularly for SIGINT (Ctrl+C) on Unix-like systems
    and proper handling on Windows where signal handling is limited.

    The class overrides the _setup_sigint method to:
    - Set up proper signal handlers on Unix-like systems (Linux, macOS)
    - Provide dummy signal handlers on Windows to prevent errors

    Attributes:
        Inherits all attributes from PipelineRunner

    Example:
        # >>> runner = UpPipelineRunner()
        # >>> await runner.run(pipeline_task)
    # """

    def _setup_sigint(self) -> None:
        """
        Set up signal handlers for graceful shutdown.

        On Unix-like systems (Linux, macOS), this method sets up a proper
        SIGINT handler that triggers the pipeline's shutdown mechanism.

        On Windows, where signal handling is limited, it installs a dummy
        signal handler to prevent errors from the base class.

        Signal handlers can only be set in the main thread. If running in a
        worker thread/process (e.g., Dask, Celery), this method safely skips setup.

        Returns:
            None
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, can't set up signal handlers
            return

        if platform.system() != "Windows":
            try:
                # Attempt to add signal handler - will fail if not in main thread
                loop.add_signal_handler(signal.SIGINT, lambda *args: self._sig_handler())
            except (RuntimeError, ValueError, OSError) as e:
                # Failed to add signal handler (not in main thread, or other error)
                # This is expected in worker processes - silently continue
                pass
        else:
            def _dummy_signal_handler(*args, **kwargs):
                pass

            try:
                asyncio.get_event_loop().add_signal_handler = _dummy_signal_handler
            except Exception:
                pass


# User State Helper
async def get_user_state(
    room_name: str,
    model_config: Dict[str, Any]
) -> UserState:
    """
    Create a UserState object for voice call sessions.

    This function initializes a UserState object with default values and
    configuration from the provided model_config. It's typically used at
    the start of inbound calls to set up the session state.

    Args:
        room_name: The LiveKit room name for the voice session
        model_config: Dictionary containing agent configuration including:
            - persona: Agent's personality/role
            - system_prompt: Instructions for the LLM
            - first_message: Initial greeting message
            - knowledge_base: List of knowledge base documents (optional)

    Returns:
        UserState: Initialized state object containing:
            - Default user information
            - Room and session details
            - Agent configuration
            - Empty transcript and usage tracking
            - Session start timestamp

    Example:
        >>> config = {
        ...     "persona": "customer_support",
        ...     "system_prompt": "You are a helpful assistant",
        ...     "first_message": "Hello! How can I help?",
        ...     "knowledge_base": ["doc1.txt", "doc2.txt"]
        ... }
        # >>> state = await get_user_state("room_123", config)
    """
    return UserState(
        user_name="default_inbound_user",
        space_name="",
        room_name=room_name,
        contact_number="",
        token="",
        language="English",
        thread_id="123",
        user={},
        persona=model_config.get("persona"),
        system_prompt=model_config.get("system_prompt"),
        first_message=model_config.get("first_message"),
        config=model_config,
        knowledge_base=model_config.get("knowledge_base", []),
        start_time=datetime.now(),
        usage={},
        transcript=[],
        recording_url=""
    )


# Default Configuration Helper
def _get_default_config(
    agent_name: str,
    knowledge_bases: Optional[list] = None
) -> Dict[str, Any]:
    """
    Get default configuration for voice agent.

    This function returns a dictionary with default configuration values
    for a voice agent, including system prompt, initial message, and
    knowledge base settings.

    Args:
        agent_name: Name of the voice agent
        knowledge_bases: Optional list of knowledge base paths or identifiers.
                        Defaults to empty list if not provided.

    Returns:
        Dict[str, Any]: Configuration dictionary containing:
            - system_prompt: Default instructions for the agent
            - first_message: Default greeting message
            - knowledge_base: List of knowledge bases to use

    Example:
        >>> config = _get_default_config(
        ...     agent_name="SupportBot",
        ...     knowledge_bases=["faq.txt", "products.json"]
        ... )
        >>> print(config["system_prompt"])
        You are SupportBot, a helpful voice assistant.
    """
    if knowledge_bases is None:
        knowledge_bases = []

    return {
        "system_prompt": f"You are {agent_name}, a helpful voice assistant.",
        "first_message": "Hello! I'm your voice assistant. How can I help you today?",
        "knowledge_base": knowledge_bases
    }


# Usage Data Serialization Helper
def create_usage(user_state: UserState) -> Dict[str, Any]:
    """
    Create serializable usage data from user_state.

    This function extracts usage metrics from the UserState object and
    converts them into a JSON-serializable dictionary format. It handles
    LLM token usage, TTS character usage, STT audio duration, and associated
    costs, along with call duration calculation.

    Args:
        user_state: UserState object containing usage tracking information
                   and call timing data

    Returns:
        Dict[str, Any]: Dictionary containing serialized usage metrics:
            - llm_tokens_used: Total LLM tokens consumed
            - llm_tokens_cost: Cost of LLM token usage
            - tts_characters_used: Total TTS characters generated
            - tts_cost: Cost of TTS generation
            - stt_audio_duration: Duration of audio transcribed (seconds)
            - stt_cost: Cost of speech-to-text processing
            - call_duration_seconds: Total call duration (if available)

    Example:
        >>> usage_data = create_usage(user_state)
        >>> print(f"Call duration: {usage_data['call_duration_seconds']}s")
        >>> print(f"Total cost: ${usage_data['llm_tokens_cost']:.4f}")
    """
    usage_data = {}

    if user_state.usage and hasattr(user_state.usage, '_summary'):
        summary = user_state.usage._summary
        usage_data = {
            "llm_tokens_used": getattr(summary, 'llm_tokens_used', 0),
            "llm_tokens_cost": getattr(summary, 'llm_tokens_cost', 0),
            "tts_characters_used": getattr(summary, 'tts_characters_used', 0),
            "tts_cost": getattr(summary, 'tts_cost', 0),
            "stt_audio_duration": getattr(summary, 'stt_audio_duration', 0),
            "stt_cost": getattr(summary, 'stt_cost', 0),
        }

    # Calculate call duration in seconds (serializable)
    if user_state.start_time and user_state.end_time:
        duration_seconds = (user_state.end_time - user_state.start_time).total_seconds()
        usage_data["call_duration_seconds"] = duration_seconds

    return usage_data


# OS Information Helper
def get_os_info() -> str:
    """
    Get formatted operating system information.

    This function returns a human-readable string describing the current
    operating system. On Linux systems, it uses the distro package to get
    pretty distribution names. On other systems (Windows, macOS), it uses
    platform.platform() with terse formatting.

    Returns:
        str: Formatted OS information string
            - Linux: Distribution name (e.g., "Ubuntu 22.04 LTS")
            - macOS: Platform string (e.g., "macOS-13.0")
            - Windows: Platform string (e.g., "Windows-10")

    Example:
        >>> os_info = get_os_info()
        >>> print(f"Running on: {os_info}")
        Running on: Ubuntu 22.04 LTS
    """
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info
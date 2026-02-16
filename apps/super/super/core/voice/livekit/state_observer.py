"""
LiveKit State Observer for Pipecat Integration.

This module bridges Pipecat pipeline events to LiveKit room state, enabling
frontend applications using useVoiceAssistant hook to track agent states
(listening, thinking, speaking) and receive transcript events.

The observer monitors Pipecat frames and updates LiveKit participant attributes:
- lk.agent.state: Current agent state (listening/thinking/speaking)
- Transcript events via data channel or participant attributes
"""

import logging
from collections import deque
from typing import Any, Deque, Optional, Set

from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    TextFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    TTSSpeakFrame,
    LLMTextFrame,
)
from pipecat.observers.base_observer import BaseObserver, FramePushed
from pipecat.processors.frame_processor import FrameDirection

from super.core.logging import logging as app_logging

# Valid LiveKit agent states for useVoiceAssistant hook
AGENT_STATE_INITIALIZING = "initializing"
AGENT_STATE_LISTENING = "listening"
AGENT_STATE_THINKING = "thinking"
AGENT_STATE_SPEAKING = "speaking"

VALID_AGENT_STATES = {
    AGENT_STATE_INITIALIZING,
    AGENT_STATE_LISTENING,
    AGENT_STATE_THINKING,
    AGENT_STATE_SPEAKING,
}


class LiveKitStateObserver(BaseObserver):
    """
    Observer that bridges Pipecat pipeline events to LiveKit room state.

    This observer monitors frame events and updates the LiveKit participant's
    `lk.agent.state` attribute, which the frontend useVoiceAssistant hook uses
    to display agent state (listening, thinking, speaking).

    It also emits transcript events via participant attributes for real-time
    transcription display on the frontend.

    Usage:
        from super.core.voice.livekit.state_observer import LiveKitStateObserver

        # Option 1: With transport reference (recommended for Pipecat)
        observer = LiveKitStateObserver(transport=transport)

        # Option 2: With job context (for LiveKit native agents)
        observer = LiveKitStateObserver()  # Will use get_job_context()

        task = PipelineTask(pipeline, observers=[observer])
    """

    def __init__(
        self,
        user_state: Optional[Any] = None,
        transport: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
        emit_transcripts: bool = True,
        **kwargs,
    ):
        """
        Initialize the LiveKit state observer.

        Args:
            user_state: User state object containing session information
            transport: Optional Pipecat LiveKitTransport instance. If provided,
                      state updates will use the transport's room participant.
            logger: Optional logger instance
            emit_transcripts: Whether to emit transcript events (default True)
        """
        super().__init__(**kwargs)
        self.user_state = user_state
        self._transport = transport
        self._logger = logger or app_logging.get_logger("livekit.state.observer")
        self._emit_transcripts = emit_transcripts

        # Frame deduplication (same pattern as TurnTrackingObserver)
        # Each frame has a unique ID - we track processed frames to avoid duplicates
        self._processed_frames: Set[str] = set()
        self._frame_history: Deque[str] = deque(maxlen=1000)

        # Current state tracking
        self._current_state: str = AGENT_STATE_LISTENING
        self._is_user_speaking: bool = False
        self._is_bot_speaking: bool = False
        self._is_processing: bool = False

        # Transcript accumulation
        self._current_user_transcript: str = ""
        self._current_bot_response: str = ""
        self._transcript_id: int = 0

        # Cache participant to avoid repeated lookups
        self._local_participant = None
        self._job_ctx = None

        # Shutdown flag to prevent API calls during cleanup
        self._is_shutting_down: bool = False

        self._logger.info(
            f"LiveKitStateObserver initialized (transport={'provided' if transport else 'will use job_context'})"
        )

    def set_transport(self, transport: Any) -> None:
        """
        Set or update the transport reference.

        This allows setting the transport after initialization, which is useful
        when the transport is created after the observer.

        Args:
            transport: Pipecat LiveKitTransport instance
        """
        self._transport = transport
        self._local_participant = None  # Clear cache to re-fetch
        self._logger.debug("Transport reference updated")

    def _get_participant(self):
        """
        Get the local participant for setting attributes.

        IMPORTANT: We prioritize the Job Context participant (LiveKit Worker) because:
        1. _signal_agent_joined sets initial state on the Worker participant
        2. Frontend useVoiceAssistant tracks the Worker as the agent
        3. State updates must be on the SAME participant as the initial state

        Tries in order:
        1. Job context's room.local_participant (LiveKit worker) - PREFERRED
        2. Transport's room.local_participant (Pipecat transport) - FALLBACK
        """
        # Validate cached participant is still valid
        if self._local_participant:
            if self._is_participant_valid(self._local_participant):
                return self._local_participant
            # Clear invalid cache
            self._local_participant = None
            self._logger.debug("Cached participant invalid, re-fetching")

        # Try job context FIRST (LiveKit worker's connection)
        # This is the participant that _signal_agent_joined uses
        try:
            from livekit.agents import get_job_context

            self._job_ctx = get_job_context()
            if self._job_ctx and hasattr(self._job_ctx, "room") and self._job_ctx.room:
                participant = self._job_ctx.room.local_participant
                if participant and self._is_participant_valid(participant):
                    self._local_participant = participant
                    self._logger.info(
                        f"Using job context participant: {participant.identity}"
                    )
                    return self._local_participant
        except Exception as e:
            self._logger.debug(f"Could not get job context participant: {e}")

        # Fallback to transport (Pipecat's connection)
        # Only used if job context is not available
        if self._transport:
            try:
                room = getattr(self._transport, "room", None)
                if room:
                    participant = room.local_participant
                    if participant and self._is_participant_valid(participant):
                        self._local_participant = participant
                        self._logger.info(
                            f"Using transport participant (fallback): {participant.identity}"
                        )
                        return self._local_participant
            except Exception as e:
                self._logger.debug(f"Could not get transport participant: {e}")

        self._logger.warning("No participant available for state updates")
        return None

    def _is_participant_valid(self, participant) -> bool:
        """Check if participant is valid and connected.

        The LiveKit Rust SDK can panic if we try to use a participant
        that is not properly connected or has an empty identity.
        """
        try:
            # Check identity exists and is not empty
            identity = getattr(participant, "identity", None)
            if not identity or identity == "":
                return False

            # Check sid exists (indicates proper connection)
            sid = getattr(participant, "sid", None)
            if not sid or sid == "":
                return False

            return True
        except Exception:
            return False

    async def on_push_frame(self, data: FramePushed):
        """
        Process frame events and trigger state updates.

        This method is called for every frame push in the pipeline.
        We deduplicate frames by their ID to avoid processing the same
        frame multiple times as it flows through different processors.
        """
        frame = data.frame
        frame_type = type(frame).__name__
        direction = data.direction

        # Skip already processed frames (deduplication)
        # This is critical because observers see frames at every processor boundary
        frame_id = getattr(frame, "id", None)
        if frame_id is not None:
            if frame_id in self._processed_frames:
                return
            self._processed_frames.add(frame_id)
            self._frame_history.append(frame_id)

            # Cleanup old frame IDs if history exceeds capacity
            if len(self._processed_frames) > len(self._frame_history):
                self._processed_frames = set(self._frame_history)

        # Only process DOWNSTREAM frames for state transitions
        # UPSTREAM frames are responses going back through the pipeline
        if direction != FrameDirection.DOWNSTREAM:
            return

        # Log state-changing frames at INFO level, TTS frames at DEBUG
        state_changing_frames = (
            UserStartedSpeakingFrame,
            UserStoppedSpeakingFrame,
            TranscriptionFrame,
            InterimTranscriptionFrame,
            LLMFullResponseStartFrame,
            LLMFullResponseEndFrame,
            BotStartedSpeakingFrame,
            BotStoppedSpeakingFrame,
        )
        tts_frames = (TTSStartedFrame, TTSStoppedFrame, TTSSpeakFrame)

        if isinstance(frame, state_changing_frames):
            src_name = type(data.source).__name__ if data.source else "None"
            dst_name = type(data.destination).__name__ if data.destination else "None"
            self._logger.info(
                f"[StateObserver] Frame: {frame_type} | {src_name} -> {dst_name} | "
                f"current_state={self._current_state}"
            )
        elif isinstance(frame, tts_frames):
            # TTS frames logged at debug level - they don't trigger state changes
            self._logger.debug(f"[StateObserver] TTS Frame: {frame_type}")

        # User started speaking -> "listening" state
        if isinstance(frame, UserStartedSpeakingFrame):
            self._is_user_speaking = True
            self._current_user_transcript = ""
            self._logger.info(f"[StateObserver] UserStartedSpeaking -> LISTENING")
            await self._update_state(AGENT_STATE_LISTENING)

        # User stopped speaking
        elif isinstance(frame, UserStoppedSpeakingFrame):
            self._is_user_speaking = False
            self._logger.info(f"[StateObserver] UserStoppedSpeaking")

        # User transcription (interim or final)
        elif isinstance(frame, (TranscriptionFrame, InterimTranscriptionFrame)):
            if hasattr(frame, "text") and frame.text:
                is_final = isinstance(frame, TranscriptionFrame)
                self._current_user_transcript = frame.text

                text_preview = frame.text[:50] if len(frame.text) > 50 else frame.text
                self._logger.info(
                    f"[StateObserver] Transcription (final={is_final}): '{text_preview}'"
                )

                if self._emit_transcripts:
                    await self._emit_transcript(
                        role="user",
                        content=frame.text,
                        is_final=is_final,
                    )

                # If final transcription, move to "thinking" state
                if is_final and not self._is_bot_speaking:
                    self._logger.info(
                        f"[StateObserver] Final transcription -> THINKING"
                    )
                    await self._update_state(AGENT_STATE_THINKING)

        # LLM processing started -> "thinking" state
        elif isinstance(frame, LLMFullResponseStartFrame):
            self._is_processing = True
            self._current_bot_response = ""
            if not self._is_bot_speaking:
                self._logger.info(f"[StateObserver] LLMFullResponseStart -> THINKING")
                await self._update_state(AGENT_STATE_THINKING)

        # LLM text frame (accumulate response)
        elif isinstance(frame, LLMTextFrame):
            if hasattr(frame, "text") and frame.text:
                self._current_bot_response += frame.text

        # LLM processing ended
        elif isinstance(frame, LLMFullResponseEndFrame):
            self._is_processing = False
            self._logger.info(f"[StateObserver] LLMFullResponseEnd")

        # TTS frames - only log, don't change state
        # TTS frames indicate audio GENERATION, not actual playback
        # State changes should only happen on BotStarted/StoppedSpeakingFrame
        elif isinstance(frame, TTSSpeakFrame):
            self._logger.debug(f"[StateObserver] TTSSpeakFrame -> TTS preparing")

        elif isinstance(frame, TTSStartedFrame):
            self._logger.debug(f"[StateObserver] TTSStartedFrame -> TTS generating")

        elif isinstance(frame, TTSStoppedFrame):
            self._logger.debug(f"[StateObserver] TTSStoppedFrame -> TTS generation complete")

        # Bot started speaking -> "speaking" state (actual audio playback)
        elif isinstance(frame, BotStartedSpeakingFrame):
            self._is_bot_speaking = True
            self._logger.info(f"[StateObserver] BotStartedSpeakingFrame -> SPEAKING")
            await self._update_state(AGENT_STATE_SPEAKING)

        # Bot stopped speaking -> "listening" state (audio playback ended)
        elif isinstance(frame, BotStoppedSpeakingFrame):
            self._is_bot_speaking = False
            self._is_processing = False

            self._logger.info(f"[StateObserver] BotStoppedSpeakingFrame -> LISTENING")

            # Emit final bot response transcript
            if self._emit_transcripts and self._current_bot_response:
                await self._emit_transcript(
                    role="assistant",
                    content=self._current_bot_response,
                    is_final=True,
                )
                self._current_bot_response = ""

            await self._update_state(AGENT_STATE_LISTENING)

        # Text frames during bot speaking (accumulate for transcript)
        elif isinstance(frame, TextFrame):
            if hasattr(frame, "text") and frame.text and self._is_bot_speaking:
                self._current_bot_response += frame.text

    async def _update_state(self, state: str):
        """Update the LiveKit participant's lk.agent.state attribute."""
        # Skip all API calls during shutdown to prevent Rust SDK panics
        if self._is_shutting_down:
            self._logger.debug(f"[StateObserver] Skipping state update during shutdown")
            return

        if state not in VALID_AGENT_STATES:
            self._logger.warning(f"Invalid agent state: {state}")
            return

        # Skip if state unchanged
        if state == self._current_state:
            self._logger.debug(
                f"[StateObserver] State unchanged, skipping: {state}"
            )
            return

        old_state = self._current_state
        self._current_state = state

        participant = self._get_participant()
        if not participant:
            self._logger.warning(
                f"[StateObserver] Cannot update state to {state}: no participant available"
            )
            return

        # Final validation before calling LiveKit API
        # The Rust SDK can panic on invalid participants
        if not self._is_participant_valid(participant):
            self._local_participant = None  # Clear invalid cache
            self._logger.warning(
                f"[StateObserver] Participant invalid, skipping state update to {state}"
            )
            return

        try:
            await participant.set_attributes({"lk.agent.state": state})
            self._logger.info(
                f"[StateObserver] ✓ LiveKit state: {old_state} -> {state} "
                f"(participant: {participant.identity})"
            )
        except Exception as e:
            # Clear cache on error - participant may have disconnected
            self._local_participant = None
            self._logger.error(
                f"[StateObserver] ✗ Failed to update state {old_state} -> {state}: {e}"
            )

    async def _emit_transcript(self, role: str, content: str, is_final: bool = True):
        """Emit transcript event via LiveKit publish_transcription API.

        Uses the native LiveKit transcription API which the useVoiceAssistant
        hook automatically handles for displaying transcripts.
        """
        # Skip all API calls during shutdown to prevent Rust SDK panics
        if self._is_shutting_down:
            return

        participant = self._get_participant()
        if not participant:
            return

        # Validate participant before calling LiveKit API
        if not self._is_participant_valid(participant):
            self._local_participant = None
            self._logger.debug("Skipping transcript: participant invalid")
            return

        try:
            from livekit import rtc

            self._transcript_id += 1

            # Create transcription segment
            segment = rtc.TranscriptionSegment(
                id=f"{role}-{self._transcript_id}",
                text=content,
                start_time=0,
                end_time=0,
                language="en",
                final=is_final,
            )

            # Create transcription with participant identity
            # track_sid is empty string when not associated with a specific track
            transcription = rtc.Transcription(
                participant_identity=participant.identity,
                track_sid="",  # Empty when not from a specific audio track
                segments=[segment],
            )

            # Publish transcription via native LiveKit API
            await participant.publish_transcription(transcription)

            text_preview = content[:50] if len(content) > 50 else content
            self._logger.debug(
                f"[StateObserver] Transcript published: {role} - '{text_preview}'"
            )

        except Exception as e:
            # Clear cache on error
            self._local_participant = None
            self._logger.error(f"Failed to emit transcript: {e}")

    def get_current_state(self) -> str:
        """Get the current agent state."""
        return self._current_state

    def shutdown(self) -> None:
        """Mark observer as shutting down to prevent further API calls.

        Call this before disconnecting from LiveKit to prevent Rust SDK panics
        during cleanup when the room/participant is being torn down.
        """
        self._is_shutting_down = True
        self._local_participant = None
        self._logger.debug("StateObserver marked as shutting down")


def create_livekit_state_observer(
    user_state: Optional[Any] = None,
    transport: Optional[Any] = None,
    logger: Optional[logging.Logger] = None,
    emit_transcripts: bool = True,
) -> LiveKitStateObserver:
    """
    Factory function to create a LiveKit state observer.

    Args:
        user_state: User state object
        transport: Optional Pipecat LiveKitTransport instance
        logger: Optional logger instance
        emit_transcripts: Whether to emit transcript events

    Returns:
        Configured LiveKitStateObserver instance
    """
    return LiveKitStateObserver(
        user_state=user_state,
        transport=transport,
        logger=logger,
        emit_transcripts=emit_transcripts,
    )

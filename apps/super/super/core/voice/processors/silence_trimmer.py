"""
Silence Trimmer Processor - Trims leading silence from TTS audio frames.

This processor reduces perceived latency by removing leading silence from TTS
audio output, providing snappier responses (100-300ms improvement).

Usage:
    from super.core.voice.processors.silence_trimmer import (
        SilenceTrimmerProcessor,
        create_silence_trimmer,
    )

    trimmer = create_silence_trimmer(
        silence_threshold=-50.0,
        chunk_size_ms=10,
        sample_rate=24000,
    )
    # Add to pipeline AFTER TTS service
"""

import logging
import struct
import time
from typing import Optional

from pipecat.frames.frames import Frame, TTSAudioRawFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class SilenceTrimmerProcessor(FrameProcessor):
    """
    Trims leading silence from TTS audio frames.

    Uses dB-based silence detection similar to pydub's approach,
    but operates directly on raw audio bytes for efficiency.
    """

    def __init__(
        self,
        silence_threshold_db: float = -50.0,
        chunk_size_ms: int = 10,
        sample_rate: int = 24000,
        sample_width: int = 2,
        num_channels: int = 1,
        enabled: bool = True,
        trim_trailing: bool = False,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ):
        """
        Initialize the silence trimmer.

        Args:
            silence_threshold_db: Threshold in dB below which audio is considered silence.
                                 Default: -50.0 dB (very quiet sounds)
            chunk_size_ms: Size of audio chunks to analyze in milliseconds.
                          Default: 10ms
            sample_rate: Audio sample rate in Hz. Default: 24000
            sample_width: Bytes per sample. Default: 2 (16-bit audio)
            num_channels: Number of audio channels. Default: 1 (mono)
            enabled: Whether silence trimming is enabled. Default: True
            trim_trailing: Whether to trim trailing silence. Default: False
                          (trailing silence is usually less impactful for latency)
            logger: Optional logger instance.
        """
        super().__init__(**kwargs)
        self._silence_threshold_db = silence_threshold_db
        self._chunk_size_ms = chunk_size_ms
        self._sample_rate = sample_rate
        self._sample_width = sample_width
        self._num_channels = num_channels
        self._enabled = enabled
        self._trim_trailing = trim_trailing
        self._logger = logger or logging.getLogger(__name__)

        # Calculate chunk size in bytes
        self._bytes_per_ms = (sample_rate * sample_width * num_channels) // 1000
        self._chunk_size_bytes = self._bytes_per_ms * chunk_size_ms

        # Metrics
        self._total_frames = 0
        self._trimmed_frames = 0
        self._total_bytes_trimmed = 0
        self._total_latency_saved_ms = 0.0

    async def process_frame(
        self, frame: Frame, direction: FrameDirection
    ) -> None:
        """Process frames, trimming silence from TTS audio frames."""
        await super().process_frame(frame, direction)

        if isinstance(frame, TTSAudioRawFrame) and self._enabled:
            trimmed_frame = self._trim_silence(frame)
            await self.push_frame(trimmed_frame, direction)
            return

        await self.push_frame(frame, direction)

    def _trim_silence(self, frame: TTSAudioRawFrame) -> TTSAudioRawFrame:
        """Trim leading silence from audio frame."""
        self._total_frames += 1
        audio_data = frame.audio

        if not audio_data or len(audio_data) < self._chunk_size_bytes:
            return frame

        try:
            # Detect leading silence
            trim_start = self._detect_leading_silence(audio_data)

            # Optionally detect trailing silence
            trim_end = 0
            if self._trim_trailing:
                trim_end = self._detect_trailing_silence(audio_data)

            # Calculate actual trim positions
            total_len = len(audio_data)
            start_pos = min(trim_start, total_len)
            end_pos = max(0, total_len - trim_end)

            if start_pos >= end_pos:
                # Would trim entire frame, return as-is
                return frame

            if start_pos > 0 or trim_end > 0:
                trimmed_audio = audio_data[start_pos:end_pos]
                bytes_trimmed = len(audio_data) - len(trimmed_audio)
                latency_saved_ms = (bytes_trimmed / self._bytes_per_ms)

                self._trimmed_frames += 1
                self._total_bytes_trimmed += bytes_trimmed
                self._total_latency_saved_ms += latency_saved_ms

                self._logger.debug(
                    f"Trimmed {bytes_trimmed} bytes ({latency_saved_ms:.1f}ms) "
                    f"from TTS frame"
                )

                return TTSAudioRawFrame(
                    audio=trimmed_audio,
                    sample_rate=frame.sample_rate,
                    num_channels=frame.num_channels,
                )

            return frame

        except Exception as e:
            self._logger.warning(f"Error trimming silence: {e}")
            return frame

    def _detect_leading_silence(self, audio_data: bytes) -> int:
        """
        Detect leading silence in audio data.

        Returns:
            Number of bytes of leading silence to trim.
        """
        trim_bytes = 0
        audio_len = len(audio_data)

        while trim_bytes + self._chunk_size_bytes <= audio_len:
            chunk = audio_data[trim_bytes:trim_bytes + self._chunk_size_bytes]
            db = self._calculate_db(chunk)

            if db >= self._silence_threshold_db:
                # Found non-silent audio
                break

            trim_bytes += self._chunk_size_bytes

        # Return trim position, keeping a small buffer to avoid clipping
        return max(0, trim_bytes - self._chunk_size_bytes)

    def _detect_trailing_silence(self, audio_data: bytes) -> int:
        """
        Detect trailing silence in audio data.

        Returns:
            Number of bytes of trailing silence to trim.
        """
        trim_bytes = 0
        audio_len = len(audio_data)

        while trim_bytes + self._chunk_size_bytes <= audio_len:
            start_pos = audio_len - trim_bytes - self._chunk_size_bytes
            chunk = audio_data[start_pos:start_pos + self._chunk_size_bytes]
            db = self._calculate_db(chunk)

            if db >= self._silence_threshold_db:
                # Found non-silent audio
                break

            trim_bytes += self._chunk_size_bytes

        return max(0, trim_bytes - self._chunk_size_bytes)

    def _calculate_db(self, chunk: bytes) -> float:
        """
        Calculate dB level of audio chunk.

        Uses RMS (Root Mean Square) to calculate average amplitude,
        then converts to dB scale.
        """
        if len(chunk) < self._sample_width:
            return -100.0  # Return very quiet for invalid chunks

        try:
            # Unpack audio samples (assuming 16-bit signed PCM)
            num_samples = len(chunk) // self._sample_width
            fmt = f"<{num_samples}h"  # Little-endian signed short
            samples = struct.unpack(fmt, chunk[:num_samples * self._sample_width])

            if not samples:
                return -100.0

            # Calculate RMS
            sum_squares = sum(s * s for s in samples)
            rms = (sum_squares / len(samples)) ** 0.5

            # Convert to dB (reference: max int16 value)
            if rms < 1:
                return -100.0  # Effectively silence

            import math
            db = 20 * math.log10(rms / 32768.0)
            return db

        except Exception:
            return -100.0

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable silence trimming."""
        self._enabled = enabled
        self._logger.info(f"Silence trimmer {'enabled' if enabled else 'disabled'}")

    def set_threshold(self, threshold_db: float) -> None:
        """Set silence threshold in dB."""
        self._silence_threshold_db = threshold_db
        self._logger.info(f"Silence threshold set to {threshold_db} dB")

    def get_metrics(self) -> dict:
        """Get silence trimmer metrics."""
        return {
            "total_frames": self._total_frames,
            "trimmed_frames": self._trimmed_frames,
            "trim_rate_pct": round(
                self._trimmed_frames / self._total_frames * 100
                if self._total_frames > 0 else 0.0, 1
            ),
            "total_bytes_trimmed": self._total_bytes_trimmed,
            "total_latency_saved_ms": round(self._total_latency_saved_ms, 1),
            "avg_latency_saved_ms": round(
                self._total_latency_saved_ms / self._trimmed_frames
                if self._trimmed_frames > 0 else 0.0, 2
            ),
            "enabled": self._enabled,
            "threshold_db": self._silence_threshold_db,
        }

    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self._total_frames = 0
        self._trimmed_frames = 0
        self._total_bytes_trimmed = 0
        self._total_latency_saved_ms = 0.0

    @property
    def is_enabled(self) -> bool:
        """Check if silence trimming is enabled."""
        return self._enabled


def create_silence_trimmer(
    silence_threshold_db: float = -50.0,
    chunk_size_ms: int = 10,
    sample_rate: int = 24000,
    enabled: bool = True,
    logger: Optional[logging.Logger] = None,
) -> SilenceTrimmerProcessor:
    """
    Factory function to create a SilenceTrimmerProcessor.

    Args:
        silence_threshold_db: Threshold in dB for silence detection.
                             Default: -50.0 dB
        chunk_size_ms: Analysis chunk size in milliseconds. Default: 10ms
        sample_rate: Audio sample rate. Default: 24000 Hz
        enabled: Whether to enable trimming. Default: True
        logger: Optional logger instance.

    Returns:
        Configured SilenceTrimmerProcessor instance.
    """
    return SilenceTrimmerProcessor(
        silence_threshold_db=silence_threshold_db,
        chunk_size_ms=chunk_size_ms,
        sample_rate=sample_rate,
        enabled=enabled,
        logger=logger,
    )

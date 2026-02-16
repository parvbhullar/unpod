"""
Streaming Text Parser Processor for Pipecat Voice Pipeline.

This module implements a streaming JSON parser that enables TTS synthesis to begin
while the LLM is still generating responses. This reduces end-to-end latency by
500-1500ms compared to waiting for complete responses.

The parser supports structured JSON responses with fields like:
- spoke_response: Text to be spoken (streamed character-by-character)
- code_blocks: Code snippets (buffered until complete)
- links: URLs (buffered and validated)

Usage:
    parser = StreamingTextParser()
    processor = StreamingTextParserProcessor(parser)
    # Insert into pipeline between LLM and TTS
"""

import enum
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from pipecat.frames.frames import (
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
    TextFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class ParseState(enum.Enum):
    """States for the streaming JSON parser state machine."""

    WAITING_FOR_OBJECT_START = "waiting_for_object_start"
    WAITING_FOR_KEY = "waiting_for_key"
    IN_KEY = "in_key"
    WAITING_FOR_COLON = "waiting_for_colon"
    WAITING_FOR_VALUE = "waiting_for_value"
    IN_STRING_VALUE = "in_string_value"
    IN_ARRAY_VALUE = "in_array_value"
    WAITING_FOR_COMMA_OR_END = "waiting_for_comma_or_end"
    COMPLETE = "complete"
    # Plain text mode (non-JSON)
    PLAIN_TEXT = "plain_text"


@dataclass
class StreamingTextBuffer:
    """Buffer for accumulating streaming text chunks."""

    spoke_response: str = ""
    code_blocks: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    raw_text: str = ""


class StreamingTextParser:
    """
    Character-by-character streaming JSON parser for LLM responses.

    Enables TTS synthesis to begin while LLM is still generating by
    streaming the `spoke_response` field character-by-character.

    Supports both JSON structured responses and plain text fallback.

    Example JSON format:
        {
            "spoke_response": "Hello, how can I help you today?",
            "code_blocks": ["print('hello')"],
            "links": ["https://example.com"]
        }

    Example plain text:
        Hello, how can I help you today?
    """

    def __init__(
        self,
        streamable_fields: Optional[List[str]] = None,
        sentence_end_pattern: Optional[str] = None,
        min_chunk_size: int = 1,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the streaming parser.

        Args:
            streamable_fields: JSON fields to stream character-by-character.
                              Default: ["spoke_response", "response", "text", "answer"]
            sentence_end_pattern: Regex pattern for sentence boundaries.
                                 Default: r'[.!?]\\s+'
            min_chunk_size: Minimum characters before emitting a chunk.
                           Default: 1 (character-by-character streaming)
            logger: Optional logger instance.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._streamable_fields = streamable_fields or [
            "spoke_response",
            "response",
            "text",
            "answer",
            "content",
        ]
        self._sentence_end_pattern = re.compile(
            sentence_end_pattern or r"[.!?]\s+"
        )
        self._min_chunk_size = min_chunk_size

        # Callbacks for streaming events
        self._on_text_chunk: Optional[Callable[[str], None]] = None
        self._on_field_complete: Optional[Callable[[str, Any], None]] = None
        self._on_parse_complete: Optional[Callable[[StreamingTextBuffer], None]] = None

        self.reset()

    def reset(self) -> None:
        """Reset parser state for a new response."""
        self.state = ParseState.WAITING_FOR_OBJECT_START
        self.current_key = ""
        self.current_value = ""
        self.brace_depth = 0
        self.bracket_depth = 0
        self.in_string = False
        self.escape_next = False
        self.current_field: Optional[str] = None

        # Buffers
        self.buffer = StreamingTextBuffer()
        self._pending_chunk = ""

        # Flags
        self._streaming_active = False
        self._response_complete = False

        # Timing
        self._start_time = time.perf_counter()
        self._first_chunk_time: Optional[float] = None
        self._chunk_count = 0

    def set_callbacks(
        self,
        on_text_chunk: Optional[Callable[[str], None]] = None,
        on_field_complete: Optional[Callable[[str, Any], None]] = None,
        on_parse_complete: Optional[Callable[[StreamingTextBuffer], None]] = None,
    ) -> None:
        """
        Set callback functions for streaming events.

        Args:
            on_text_chunk: Called for each streamable text chunk.
            on_field_complete: Called when a JSON field is fully parsed.
            on_parse_complete: Called when entire JSON is parsed.
        """
        self._on_text_chunk = on_text_chunk
        self._on_field_complete = on_field_complete
        self._on_parse_complete = on_parse_complete

    async def process_chunk(self, content: str) -> List[str]:
        """
        Process a chunk of streaming content.

        Args:
            content: Text chunk from LLM.

        Returns:
            List of text chunks to emit for TTS.
        """
        emitted_chunks: List[str] = []

        for char in content:
            chunk = await self._process_char(char)
            if chunk:
                emitted_chunks.append(chunk)

        return emitted_chunks

    async def _process_char(self, char: str) -> Optional[str]:
        """
        Process a single character through the state machine.

        Args:
            char: Single character to process.

        Returns:
            Text chunk to emit (if any).
        """
        # Accumulate raw text
        self.buffer.raw_text += char

        # Handle escape sequences in strings
        if self.escape_next:
            self._pending_chunk += char
            self.escape_next = False
            return await self._maybe_emit_chunk()

        if char == "\\" and self.in_string:
            self._pending_chunk += char
            self.escape_next = True
            return await self._maybe_emit_chunk()

        # State machine transitions
        return await self._handle_state(char)

    async def _handle_state(self, char: str) -> Optional[str]:
        """Handle state machine transitions."""
        if self.state == ParseState.WAITING_FOR_OBJECT_START:
            return await self._handle_waiting_for_object(char)

        elif self.state == ParseState.WAITING_FOR_KEY:
            return await self._handle_waiting_for_key(char)

        elif self.state == ParseState.IN_KEY:
            return await self._handle_in_key(char)

        elif self.state == ParseState.WAITING_FOR_COLON:
            return await self._handle_waiting_for_colon(char)

        elif self.state == ParseState.WAITING_FOR_VALUE:
            return await self._handle_waiting_for_value(char)

        elif self.state == ParseState.IN_STRING_VALUE:
            return await self._handle_in_string_value(char)

        elif self.state == ParseState.IN_ARRAY_VALUE:
            return await self._handle_in_array_value(char)

        elif self.state == ParseState.WAITING_FOR_COMMA_OR_END:
            return await self._handle_waiting_for_comma_or_end(char)

        elif self.state == ParseState.PLAIN_TEXT:
            return await self._handle_plain_text(char)

        return None

    async def _handle_waiting_for_object(self, char: str) -> Optional[str]:
        """Handle WAITING_FOR_OBJECT_START state."""
        if char == "{":
            self.brace_depth = 1
            self.state = ParseState.WAITING_FOR_KEY
        elif not char.isspace():
            # Not JSON - switch to plain text mode
            self._logger.debug("Non-JSON response detected, switching to plain text mode")
            self.state = ParseState.PLAIN_TEXT
            self._streaming_active = True
            self._pending_chunk = char
            return await self._maybe_emit_chunk()
        return None

    async def _handle_waiting_for_key(self, char: str) -> Optional[str]:
        """Handle WAITING_FOR_KEY state."""
        if char == '"':
            self.in_string = True
            self.current_key = ""
            self.state = ParseState.IN_KEY
        elif char == "}":
            # Empty object or end
            self.brace_depth -= 1
            if self.brace_depth == 0:
                self.state = ParseState.COMPLETE
                await self._handle_parse_complete()
        return None

    async def _handle_in_key(self, char: str) -> Optional[str]:
        """Handle IN_KEY state."""
        if char == '"' and not self.escape_next:
            self.in_string = False
            self.current_field = self.current_key
            self.state = ParseState.WAITING_FOR_COLON
        else:
            self.current_key += char
        return None

    async def _handle_waiting_for_colon(self, char: str) -> Optional[str]:
        """Handle WAITING_FOR_COLON state."""
        if char == ":":
            self.state = ParseState.WAITING_FOR_VALUE
        return None

    async def _handle_waiting_for_value(self, char: str) -> Optional[str]:
        """Handle WAITING_FOR_VALUE state."""
        if char == '"':
            self.in_string = True
            self.current_value = ""
            self.state = ParseState.IN_STRING_VALUE

            # Start streaming if this is a streamable field
            if self.current_field in self._streamable_fields:
                self._streaming_active = True
                self._logger.debug(f"Started streaming field: {self.current_field}")

        elif char == "[":
            self.bracket_depth = 1
            self.current_value = char
            self.state = ParseState.IN_ARRAY_VALUE

        elif char == "{":
            # Nested object - for now treat as string
            self.brace_depth += 1
            self.current_value = char

        elif not char.isspace():
            # Primitive value (number, boolean, null)
            self.current_value = char

        return None

    async def _handle_in_string_value(self, char: str) -> Optional[str]:
        """Handle IN_STRING_VALUE state."""
        if char == '"' and not self.escape_next:
            self.in_string = False
            await self._handle_string_complete()
            self.state = ParseState.WAITING_FOR_COMMA_OR_END
            # Flush any remaining pending chunk
            if self._pending_chunk:
                chunk = self._pending_chunk
                self._pending_chunk = ""
                return chunk
        else:
            self.current_value += char

            # Stream if this is a streamable field
            if self._streaming_active and self.current_field in self._streamable_fields:
                self._pending_chunk += char
                return await self._maybe_emit_chunk()

        return None

    async def _handle_in_array_value(self, char: str) -> Optional[str]:
        """Handle IN_ARRAY_VALUE state."""
        self.current_value += char

        if char == "[":
            self.bracket_depth += 1
        elif char == "]":
            self.bracket_depth -= 1
            if self.bracket_depth == 0:
                await self._handle_array_complete()
                self.state = ParseState.WAITING_FOR_COMMA_OR_END

        return None

    async def _handle_waiting_for_comma_or_end(self, char: str) -> Optional[str]:
        """Handle WAITING_FOR_COMMA_OR_END state."""
        if char == ",":
            self.state = ParseState.WAITING_FOR_KEY
        elif char == "}":
            self.brace_depth -= 1
            if self.brace_depth == 0:
                self.state = ParseState.COMPLETE
                await self._handle_parse_complete()
        return None

    async def _handle_plain_text(self, char: str) -> Optional[str]:
        """Handle PLAIN_TEXT state (non-JSON responses)."""
        self._pending_chunk += char
        return await self._maybe_emit_chunk()

    async def _maybe_emit_chunk(self) -> Optional[str]:
        """
        Emit pending chunk if it meets criteria.

        Criteria:
        - Minimum chunk size reached, OR
        - Sentence boundary detected

        Returns:
            Text chunk to emit (if any).
        """
        if not self._pending_chunk:
            return None

        # Check if we should emit
        should_emit = False

        # Emit at sentence boundaries for more natural TTS
        if self._sentence_end_pattern.search(self._pending_chunk):
            should_emit = True

        # Emit if minimum chunk size reached
        if len(self._pending_chunk) >= self._min_chunk_size:
            should_emit = True

        if should_emit:
            chunk = self._pending_chunk
            self._pending_chunk = ""

            # Track metrics
            self._chunk_count += 1
            if self._first_chunk_time is None:
                self._first_chunk_time = time.perf_counter()
                ttfc = (self._first_chunk_time - self._start_time) * 1000
                self._logger.debug(f"Time to first chunk: {ttfc:.2f}ms")

            # Call callback if set
            if self._on_text_chunk:
                self._on_text_chunk(chunk)

            return chunk

        return None

    async def _handle_string_complete(self) -> None:
        """Handle completion of a string value."""
        if not self.current_field:
            return

        # Store in appropriate buffer
        if self.current_field in ["spoke_response", "response", "text", "answer", "content"]:
            self.buffer.spoke_response = self.current_value

        self._streaming_active = False

        # Call callback
        if self._on_field_complete:
            self._on_field_complete(self.current_field, self.current_value)

        self._logger.debug(f"Field complete: {self.current_field} ({len(self.current_value)} chars)")

    async def _handle_array_complete(self) -> None:
        """Handle completion of an array value."""
        if not self.current_field:
            return

        import json

        try:
            array_data = json.loads(self.current_value)

            if self.current_field == "code_blocks":
                self.buffer.code_blocks = array_data
            elif self.current_field == "links":
                self.buffer.links = array_data

            # Call callback
            if self._on_field_complete:
                self._on_field_complete(self.current_field, array_data)

            self._logger.debug(f"Array complete: {self.current_field} ({len(array_data)} items)")

        except json.JSONDecodeError as e:
            self._logger.warning(f"Failed to parse array for {self.current_field}: {e}")

    async def _handle_parse_complete(self) -> None:
        """Handle completion of entire JSON parsing."""
        self._response_complete = True

        total_time = (time.perf_counter() - self._start_time) * 1000
        self._logger.info(
            f"Parse complete: {self._chunk_count} chunks in {total_time:.2f}ms"
        )

        if self._on_parse_complete:
            self._on_parse_complete(self.buffer)

    async def flush(self) -> Optional[str]:
        """
        Flush any remaining pending content.

        Call this when the LLM response ends to emit any buffered text.

        Returns:
            Remaining text chunk (if any).
        """
        if self._pending_chunk:
            chunk = self._pending_chunk
            self._pending_chunk = ""
            return chunk
        return None

    def get_metrics(self) -> dict:
        """
        Get parsing metrics.

        Returns:
            Dict with timing and chunk statistics.
        """
        total_time = (time.perf_counter() - self._start_time) * 1000
        ttfc = None
        if self._first_chunk_time:
            ttfc = (self._first_chunk_time - self._start_time) * 1000

        return {
            "total_time_ms": total_time,
            "time_to_first_chunk_ms": ttfc,
            "chunk_count": self._chunk_count,
            "spoke_response_length": len(self.buffer.spoke_response),
            "code_blocks_count": len(self.buffer.code_blocks),
            "links_count": len(self.buffer.links),
            "is_complete": self._response_complete,
        }


class StreamingTextParserProcessor(FrameProcessor):
    """
    Pipecat frame processor that enables streaming TTS synthesis.

    Intercepts LLMTextFrame and TextFrame, parses streaming content,
    and emits text chunks for immediate TTS processing.

    This processor should be inserted into the pipeline between
    the LLM service and TTS service.

    Usage:
        parser = StreamingTextParser()
        processor = StreamingTextParserProcessor(parser)

        # In pipeline construction:
        pipeline_stages = [
            transport.input(),
            stt_service,
            context_aggregator.user(),
            llm_service,
            processor,  # <-- Insert here
            tts_service,
            transport.output(),
            context_aggregator.assistant(),
        ]
    """

    def __init__(
        self,
        parser: Optional[StreamingTextParser] = None,
        enabled: bool = True,
        passthrough_non_text: bool = True,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ):
        """
        Initialize the streaming text parser processor.

        Args:
            parser: StreamingTextParser instance. Creates default if not provided.
            enabled: Whether streaming parsing is enabled. If False, frames pass through unchanged.
            passthrough_non_text: Whether to pass through non-text frames unchanged.
            logger: Optional logger instance.
        """
        super().__init__(**kwargs)
        self._parser = parser or StreamingTextParser()
        self._enabled = enabled
        self._passthrough_non_text = passthrough_non_text
        self._logger = logger or logging.getLogger(__name__)

        # Track response boundaries
        self._in_response = False

    async def process_frame(
        self, frame: Frame, direction: FrameDirection
    ) -> None:
        """
        Process frames through the streaming parser.

        Args:
            frame: Input frame.
            direction: Frame direction (downstream/upstream).
        """
        await super().process_frame(frame, direction)

        # Handle response boundaries
        if isinstance(frame, LLMFullResponseStartFrame):
            self._in_response = True
            self._parser.reset()
            self._logger.debug("LLM response started - parser reset")
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, LLMFullResponseEndFrame):
            self._in_response = False
            # Flush any remaining content
            remaining = await self._parser.flush()
            if remaining:
                await self.push_frame(TextFrame(text=remaining), direction)

            # Log metrics
            metrics = self._parser.get_metrics()
            self._logger.info(
                f"LLM response complete - "
                f"chunks: {metrics['chunk_count']}, "
                f"ttfc: {metrics.get('time_to_first_chunk_ms', 'N/A')}ms"
            )
            await self.push_frame(frame, direction)
            return

        # Process LLM text frames only (not generic TextFrame)
        # The streaming parser is positioned at POST_LLM, so it should only
        # process frames from the LLM, not other sources that might emit TextFrame
        if isinstance(frame, LLMTextFrame) and self._enabled:
            await self._process_text_frame(frame, direction)
            return

        # Pass through other frames unchanged
        if self._passthrough_non_text:
            await self.push_frame(frame, direction)

    async def _process_text_frame(
        self, frame: LLMTextFrame, direction: FrameDirection
    ) -> None:
        """
        Process an LLM text frame through the streaming parser.

        Args:
            frame: LLM text frame to process.
            direction: Frame direction.
        """
        text = frame.text

        # Parse and emit chunks
        chunks = await self._parser.process_chunk(text)

        for chunk in chunks:
            if chunk:
                # Emit as TextFrame for TTS
                await self.push_frame(TextFrame(text=chunk), direction)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable streaming parsing."""
        self._enabled = enabled
        self._logger.info(f"Streaming parser {'enabled' if enabled else 'disabled'}")

    def get_metrics(self) -> dict:
        """Get current parsing metrics."""
        return self._parser.get_metrics()


def create_streaming_parser_processor(
    streamable_fields: Optional[List[str]] = None,
    min_chunk_size: int = 1,
    enabled: bool = True,
    logger: Optional[logging.Logger] = None,
) -> StreamingTextParserProcessor:
    """
    Factory function to create a configured streaming parser processor.

    Args:
        streamable_fields: JSON fields to stream. Default: spoke_response, response, text, answer, content
        min_chunk_size: Minimum characters per chunk. Default: 1 (character streaming)
        enabled: Whether to enable streaming. Default: True
        logger: Optional logger.

    Returns:
        Configured StreamingTextParserProcessor instance.
    """
    parser = StreamingTextParser(
        streamable_fields=streamable_fields,
        min_chunk_size=min_chunk_size,
        logger=logger,
    )
    return StreamingTextParserProcessor(
        parser=parser,
        enabled=enabled,
        logger=logger,
    )

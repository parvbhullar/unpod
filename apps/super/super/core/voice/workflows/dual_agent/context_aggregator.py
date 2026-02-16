"""
Context Aggregator - Single source of truth for conversation state

This module provides shared conversation state between Communication and Processing agents:
- Communication Agent reads context to determine conversation flow
- Processing Agent updates context with tool results
- Both agents add conversation turns for history
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class ConversationPhase(Enum):
    """High-level conversation phases"""
    GREETING = "greeting"
    INFORMATION_COLLECTION = "information_collection"
    OPEN_ENDED_QA = "open_ended_qa"
    CLOSING = "closing"
    COMPLETED = "completed"


class NodeType(Enum):
    """Types of conversation nodes"""
    INSTRUCTION = "instruction"  # Agent speaks (no user input needed)
    QUESTION = "question"        # Agent asks, waits for user response
    TOOL = "tool"               # Execute tool (async via Processing Agent)
    EXPLANATION = "explanation"  # Agent explains tool results
    REACT = "react"             # Open-ended reasoning + action


@dataclass
class ConversationTurn:
    """Single conversation exchange"""
    timestamp: datetime
    speaker: str  # "user" or "agent"
    content: str
    node_id: Optional[str] = None
    function_called: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "speaker": self.speaker,
            "content": self.content,
            "node_id": self.node_id,
            "function_called": self.function_called
        }


@dataclass
class ConversationNode:
    """Definition of a conversation flow node"""
    id: str
    type: NodeType
    prompt: str
    next_node: Optional[str] = None
    required_fields: List[str] = field(default_factory=list)
    tool_config: Optional[Dict[str, Any]] = None


@dataclass
class ConversationContext:
    """
    Complete conversation state shared between agents.

    This is the single source of truth for:
    - Current conversation position
    - Collected user information
    - Recent conversation history
    - Tool execution results
    - TTS timing state
    """
    session_id: str

    # Flow state
    conversation_phase: ConversationPhase = ConversationPhase.GREETING
    completed_nodes: List[str] = field(default_factory=list)
    current_node: Optional[str] = None
    pending_nodes: List[str] = field(default_factory=list)

    # Collected data
    user_attributes: Dict[str, Any] = field(default_factory=dict)

    # Conversation history (sliding window)
    recent_exchanges: List[ConversationTurn] = field(default_factory=list)
    max_history_turns: int = 5

    # Tool results cache
    tool_results: Dict[str, Any] = field(default_factory=dict)

    # TTS state
    last_tts_timestamp: Optional[datetime] = None
    tts_frame_progress: float = 0.0  # 0.0 to 1.0

    # Task queue integration
    waiting_for_task: Optional[str] = None  # task_id if waiting
    last_filler_message: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context for logging/debugging"""
        return {
            "session_id": self.session_id,
            "conversation_phase": self.conversation_phase.value,
            "completed_nodes": self.completed_nodes,
            "current_node": self.current_node,
            "pending_nodes": self.pending_nodes,
            "user_attributes": self.user_attributes,
            "recent_exchanges": [turn.to_dict() for turn in self.recent_exchanges],
            "tool_results": list(self.tool_results.keys()),  # Just keys for brevity
            "waiting_for_task": self.waiting_for_task,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ContextAggregator:
    """
    Thread-safe context manager for conversation state.

    Both Communication and Processing agents interact with this class:
    - Communication Agent: Reads context, updates conversation flow
    - Processing Agent: Updates tool results, caches data

    Thread-safe via asyncio locks.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._context = ConversationContext(session_id=session_id)
        self._lock = asyncio.Lock()
        self._conversation_flow: List[ConversationNode] = []

    async def get_context(self) -> ConversationContext:
        """Get current conversation context (read-only copy)"""
        async with self._lock:
            return self._context

    async def set_conversation_flow(self, flow: List[ConversationNode]):
        """Initialize the conversation flow structure"""
        async with self._lock:
            self._conversation_flow = flow
            if flow:
                self._context.pending_nodes = [node.id for node in flow]

    async def get_current_node(self) -> Optional[ConversationNode]:
        """Get the current conversation node"""
        async with self._lock:
            if not self._context.current_node:
                return None

            for node in self._conversation_flow:
                if node.id == self._context.current_node:
                    return node
            return None

    async def update_user_attribute(self, key: str, value: Any):
        """
        Update collected user information.

        Args:
            key: Attribute name (e.g., "name", "phone", "course_interest")
            value: Attribute value
        """
        async with self._lock:
            self._context.user_attributes[key] = value
            self._context.updated_at = datetime.now()

    async def mark_node_complete(self, node_id: str):
        """
        Mark a conversation node as completed.

        Args:
            node_id: Node identifier
        """
        async with self._lock:
            if node_id not in self._context.completed_nodes:
                self._context.completed_nodes.append(node_id)

            if node_id in self._context.pending_nodes:
                self._context.pending_nodes.remove(node_id)

            self._context.updated_at = datetime.now()

    async def advance_to_node(self, node_id: str):
        """
        Move to the next conversation node.

        Args:
            node_id: Next node identifier
        """
        async with self._lock:
            # Mark previous node as complete
            if self._context.current_node:
                await self._mark_complete_unsafe(self._context.current_node)

            self._context.current_node = node_id
            self._context.updated_at = datetime.now()

    async def _mark_complete_unsafe(self, node_id: str):
        """Internal method to mark node complete (no lock)"""
        if node_id not in self._context.completed_nodes:
            self._context.completed_nodes.append(node_id)

        if node_id in self._context.pending_nodes:
            self._context.pending_nodes.remove(node_id)

    async def add_exchange(
        self,
        speaker: str,
        content: str,
        node_id: Optional[str] = None,
        function_called: Optional[str] = None
    ):
        """
        Add a conversation turn to history.

        Maintains sliding window of last N turns.

        Args:
            speaker: "user" or "agent"
            content: Spoken/typed content
            node_id: Associated conversation node
            function_called: Function name if tool was called
        """
        async with self._lock:
            turn = ConversationTurn(
                timestamp=datetime.now(),
                speaker=speaker,
                content=content,
                node_id=node_id,
                function_called=function_called
            )

            self._context.recent_exchanges.append(turn)

            # Maintain sliding window
            max_turns = self._context.max_history_turns
            if len(self._context.recent_exchanges) > max_turns:
                self._context.recent_exchanges = self._context.recent_exchanges[-max_turns:]

            self._context.updated_at = datetime.now()

    async def cache_tool_result(self, tool_name: str, result: Any, ttl_seconds: int = 300):
        """
        Cache tool execution result.

        Args:
            tool_name: Tool/function name
            result: Execution result
            ttl_seconds: Time-to-live for cache entry (default 5 minutes)
        """
        async with self._lock:
            self._context.tool_results[tool_name] = {
                "result": result,
                "cached_at": datetime.now(),
                "ttl": ttl_seconds
            }
            self._context.updated_at = datetime.now()

    async def get_cached_result(self, tool_name: str) -> Optional[Any]:
        """
        Retrieve cached tool result if still valid.

        Args:
            tool_name: Tool/function name

        Returns:
            Cached result or None if expired/not found
        """
        async with self._lock:
            cached = self._context.tool_results.get(tool_name)
            if not cached:
                return None

            # Check TTL
            age = (datetime.now() - cached["cached_at"]).total_seconds()
            if age > cached["ttl"]:
                # Expired - remove from cache
                del self._context.tool_results[tool_name]
                return None

            return cached["result"]

    async def set_waiting_for_task(self, task_id: str, filler_message: str):
        """
        Mark that Communication Agent is waiting for Processing Agent task.

        Args:
            task_id: Task queue task identifier
            filler_message: Message agent should speak while waiting
        """
        async with self._lock:
            self._context.waiting_for_task = task_id
            self._context.last_filler_message = filler_message
            self._context.updated_at = datetime.now()

    async def clear_waiting_task(self):
        """Clear task waiting state"""
        async with self._lock:
            self._context.waiting_for_task = None
            self._context.last_filler_message = None
            self._context.updated_at = datetime.now()

    async def update_tts_state(self, frame_progress: float):
        """
        Update TTS playback state (for 90% overlap rule).

        Args:
            frame_progress: Progress from 0.0 to 1.0
        """
        async with self._lock:
            self._context.tts_frame_progress = frame_progress
            self._context.last_tts_timestamp = datetime.now()

    async def can_speak_next(self) -> bool:
        """
        Check if agent can speak next message (90% overlap rule).

        Returns:
            True if TTS is 90%+ complete or no TTS playing
        """
        async with self._lock:
            return self._context.tts_frame_progress >= 0.9

    async def get_recent_context(self, max_turns: int = 3) -> List[ConversationTurn]:
        """
        Get recent conversation history for prompt context.

        Args:
            max_turns: Maximum number of recent turns to return

        Returns:
            List of recent conversation turns
        """
        async with self._lock:
            return self._context.recent_exchanges[-max_turns:]

    async def update_phase(self, phase: ConversationPhase):
        """
        Update high-level conversation phase.

        Args:
            phase: New conversation phase
        """
        async with self._lock:
            self._context.conversation_phase = phase
            self._context.updated_at = datetime.now()

    async def get_collected_attributes(self) -> Dict[str, Any]:
        """Get all collected user attributes"""
        async with self._lock:
            return self._context.user_attributes.copy()

    async def check_required_fields(self, required: List[str]) -> Dict[str, bool]:
        """
        Check which required fields have been collected.

        Args:
            required: List of required field names

        Returns:
            Dict mapping field names to collection status
        """
        async with self._lock:
            return {
                field: field in self._context.user_attributes
                for field in required
            }

    async def get_stats(self) -> Dict[str, Any]:
        """Get context statistics for monitoring"""
        async with self._lock:
            return {
                "session_id": self.session_id,
                "phase": self._context.conversation_phase.value,
                "completed_nodes": len(self._context.completed_nodes),
                "pending_nodes": len(self._context.pending_nodes),
                "collected_attributes": len(self._context.user_attributes),
                "conversation_turns": len(self._context.recent_exchanges),
                "cached_results": len(self._context.tool_results),
                "waiting_for_task": self._context.waiting_for_task is not None,
                "uptime_seconds": (datetime.now() - self._context.created_at).total_seconds()
            }

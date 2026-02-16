"""
Conversation State for LiveKit Voice Agent.

Simplified state model with structured LLM output:
- TurnResponse: What LLM returns each turn (speech + state metadata)
- ContentBlock: Topic or repair strategy block
- DynamicConversationState: Tracks topics, repair state, objective, quality
- ConversationObjective: Goal tracking with CTA

Repair handling based on breakdown type × retry count matrix.
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Set, Dict, Any, List, Literal

from pydantic import BaseModel


# --- Structured LLM Output Models ---

BreakdownType = Literal["non_understanding", "misunderstanding"]


class BreakdownReport(BaseModel):
    """Report of conversation breakdown detected by LLM."""

    type: BreakdownType
    reason: str


class TurnResponse(BaseModel):
    """Structured output from LLM each turn."""

    speech: str
    covered: List[str] = []
    user_info: Dict[str, str] = {}
    objection_detected: Optional[str] = None
    breakdown: Optional[BreakdownReport] = None


# Default directory for quality metrics logs
QUALITY_METRICS_DIR = Path("logs/quality_metrics")


@dataclass
class ContentBlock:
    """
    A discrete piece of content to deliver (topic or repair strategy).

    Types:
    - topic: Regular content to deliver
    - repair_ask: Ask strategy (repeat/rephrase)
    - repair_solve: Solve strategy (offer options)
    - repair_social: Social strategy (apologize/fallback)
    - repair_info: Information strategy (explain error)
    - repair_confirmation: Confirmation strategy
    - repair_disclosure: Disclosure strategy (state limitations)
    """

    id: str
    content: str
    content_hi: str = ""
    type: str = "topic"  # topic | repair_*
    delivery_order: int = 0
    delivered: bool = False

    # Repair-specific fields
    breakdown_trigger: Optional[str] = None  # non_understanding | misunderstanding
    retry_trigger: int = 0

    # Optional metadata
    trigger_condition: str = "sequential"
    is_cta_point: bool = False


def get_default_repair_blocks() -> List[ContentBlock]:
    """
    Get default repair strategy blocks based on breakdown × retry matrix.

    Matrix:
    | Breakdown Type     | Retry 0        | Retry 1        | Retry 2       | Retry 3+       |
    |--------------------|----------------|----------------|---------------|----------------|
    | non_understanding  | Ask (repeat)   | Ask (rephrase) | Solve (opts)  | Social (fall)  |
    | misunderstanding   | Confirmation   | Solve (clarify)| Solve (opts)  | Social (fall)  |
    """
    return [
        ContentBlock(
            id="repair_ask_repeat",
            content="I didn't catch that clearly. Could you please repeat?",
            content_hi="Mujhe samajh nahi aaya. Kya aap dobara bol sakte hain?",
            type="repair_ask",
            breakdown_trigger="non_understanding",
            retry_trigger=0,
        ),
        ContentBlock(
            id="repair_ask_rephrase",
            content="I'm having trouble understanding. Could you say that differently?",
            content_hi="Mujhe samajhne mein mushkil ho rahi hai. Kya aap alag tarike se bol sakte hain?",
            type="repair_ask",
            breakdown_trigger="non_understanding",
            retry_trigger=1,
        ),
        ContentBlock(
            id="repair_solve_options",
            content="Let me help. Are you asking about: fees, location, or schedule?",
            content_hi="Main madad karta hoon. Kya aap fees, location, ya schedule ke baare mein pooch rahe hain?",
            type="repair_solve",
            breakdown_trigger="non_understanding",
            retry_trigger=2,
        ),
        ContentBlock(
            id="repair_confirm",
            content="Just to confirm, you're asking about {topic}. Is that correct?",
            content_hi="Confirm karne ke liye, aap {topic} ke baare mein pooch rahe hain. Kya yeh sahi hai?",
            type="repair_confirmation",
            breakdown_trigger="misunderstanding",
            retry_trigger=0,
        ),
        ContentBlock(
            id="repair_solve_clarify",
            content="I may have misunderstood. Could you clarify what you'd like to know?",
            content_hi="Shayad maine galat samjha. Kya aap clarify kar sakte hain?",
            type="repair_solve",
            breakdown_trigger="misunderstanding",
            retry_trigger=1,
        ),
        ContentBlock(
            id="repair_misunderstanding_options",
            content="Let me understand better. Were you asking about A, B, or something else?",
            content_hi="Main behtar samajhna chahta hoon. Kya aap A, B, ya kuch aur pooch rahe the?",
            type="repair_solve",
            breakdown_trigger="misunderstanding",
            retry_trigger=2,
        ),
        ContentBlock(
            id="repair_social_fallback",
            content="I apologize for the confusion. Let me connect you with someone who can help better.",
            content_hi="Confusion ke liye maafi chahta hoon. Main aapko kisi aur se connect karta hoon.",
            type="repair_social",
            breakdown_trigger=None,  # Matches any breakdown at high retry
            retry_trigger=3,
        ),
    ]


@dataclass
class ConversationObjective:
    """
    The goal extracted from prompt/config.

    Tracks primary and fallback objectives with reattempt logic.
    """

    # Primary objective
    primary_goal: str            # e.g., "book_site_visit"
    primary_cta: str             # e.g., "Would you like to schedule a site visit?"
    primary_cta_hi: str = ""     # Hindi version

    # Fallback objective (when primary fails after max attempts)
    fallback_goal: str = ""      # e.g., "share_brochure"
    fallback_cta: str = ""       # e.g., "Can I share the brochure on WhatsApp?"
    fallback_cta_hi: str = ""    # Hindi version

    # Success detection
    success_keywords: List[str] = field(default_factory=lambda: [
        "yes", "sure", "ok", "haan", "theek hai", "book", "schedule"
    ])
    decline_keywords: List[str] = field(default_factory=lambda: [
        "no", "nahi", "not now", "later", "busy", "think about it"
    ])


@dataclass
class DynamicConversationState:
    """
    Simplified conversation state for structured LLM output.

    Tracks topics, repair state, objective, and quality metrics.
    LLM returns TurnResponse each turn which updates this state.
    """

    # Content management
    content_blocks: List[ContentBlock] = field(default_factory=list)
    delivered_content: Set[str] = field(default_factory=set)

    # User data (collected via TurnResponse.user_info)
    user_info: Dict[str, Any] = field(default_factory=dict)

    # Objective tracking
    objective: Optional[ConversationObjective] = None
    objective_achieved: bool = False
    objective_outcome: str = ""  # "primary_success" | "fallback_success" | "declined"

    # Repair state (based on breakdown × retry matrix)
    in_repair: bool = False
    breakdown_type: Optional[str] = None  # non_understanding | misunderstanding
    repair_retry_count: int = 0

    # Metrics
    turn_count: int = 0
    call_start_time: float = field(default_factory=time.time)

    # Quality tracking
    repetition_count: int = 0
    clarification_count: int = 0
    question_only_turns: int = 0
    breakdown_count: int = 0
    agent_responses: List[Dict[str, Any]] = field(default_factory=list)

    # Call metadata
    task_id: str = ""
    session_id: str = ""
    agent_handle: str = ""
    call_type: str = "outbound"

    # Backward compat (deprecated, use user_info instead)
    user_profile: Dict[str, Any] = field(default_factory=dict)
    user_language: str = "en"

    # --- Content Block Methods ---

    def get_next_content_block(self) -> Optional[ContentBlock]:
        """Get next undelivered content block."""
        for block in self.content_blocks:
            # Check both the block flag AND the delivered_content set
            if not block.delivered and block.id not in self.delivered_content:
                return block
        return None

    def mark_block_delivered(self, block_id: str) -> None:
        """Mark a content block as delivered."""
        for block in self.content_blocks:
            if block.id == block_id:
                block.delivered = True
                self.delivered_content.add(block_id)
                break

    def all_content_delivered(self) -> bool:
        """Check if all content blocks have been delivered."""
        return all(b.delivered for b in self.content_blocks)

    def get_content_for_language(self, block: ContentBlock) -> str:
        """Get content in user's preferred language."""
        if self.user_language == "hi" and block.content_hi:
            return block.content_hi
        return block.content

    def get_delivered_block_ids(self) -> List[str]:
        """Get IDs of all delivered blocks."""
        return [b.id for b in self.content_blocks if b.delivered]

    def get_delivery_progress(self) -> Dict[str, int]:
        """Get content delivery progress."""
        delivered = sum(1 for b in self.content_blocks if b.delivered)
        total = len(self.content_blocks)
        return {"delivered": delivered, "total": total, "remaining": total - delivered}

    # --- Repair State Methods ---

    def enter_repair(self, breakdown_type: str) -> None:
        """Enter repair mode for a breakdown."""
        self.in_repair = True
        self.breakdown_type = breakdown_type
        self.breakdown_count += 1

    def exit_repair(self) -> None:
        """Exit repair mode after successful recovery."""
        self.in_repair = False
        self.breakdown_type = None
        self.repair_retry_count = 0

    def increment_repair_retry(self) -> int:
        """Increment repair retry count."""
        self.repair_retry_count += 1
        return self.repair_retry_count

    def get_repair_block(self) -> Optional[ContentBlock]:
        """Get appropriate repair strategy block based on breakdown type and retry count."""
        if not self.in_repair or not self.breakdown_type:
            return None

        for block in self.content_blocks:
            if block.type.startswith("repair_"):
                # Match breakdown trigger and retry level
                if block.breakdown_trigger == self.breakdown_type:
                    if block.retry_trigger == self.repair_retry_count:
                        return block
                # Fallback blocks (breakdown_trigger=None) match any breakdown at high retry
                elif block.breakdown_trigger is None and self.repair_retry_count >= 3:
                    return block
        return None

    def get_topics(self) -> List[ContentBlock]:
        """Get topic content blocks (not repair strategies)."""
        return [b for b in self.content_blocks if b.type == "topic"]

    # --- User Info Methods ---

    def record_user_info_item(self, key: str, value: Any) -> None:
        """Record information about the user."""
        self.user_info[key] = value
        self.user_profile[key] = value  # backward compat

    def get_user_info_item(self, key: str, default: Any = None) -> Any:
        """Get recorded user information."""
        return self.user_info.get(key, default)

    # --- Turn Tracking ---

    def increment_turn(self) -> int:
        """Increment turn count and return new value."""
        self.turn_count += 1
        return self.turn_count

    # --- Do Not Repeat ---

    def mark_content_delivered(self, content_id: str) -> None:
        """Mark content as delivered (should not be repeated)."""
        self.delivered_content.add(content_id)

    def was_content_delivered(self, content_id: str) -> bool:
        """Check if content has already been delivered."""
        return content_id in self.delivered_content

    def get_do_not_repeat_summary(self) -> str:
        """
        Generate a summary of content that should not be repeated.

        Returns:
            Formatted string for injection into agent instructions.
        """
        if not self.delivered_content:
            return ""

        lines = ["## DO NOT REPEAT (already covered):"]
        for content in self.delivered_content:
            lines.append(f"- {content}")

        return "\n".join(lines)

    # --- LLM Context ---

    def build_llm_context(self) -> str:
        """
        Build context to inject into LLM prompt each turn.

        Includes checklist, objective, and repair strategy if in repair mode.
        """
        lines = []

        # Checklist of topics
        lines.append("[CHECKLIST]")
        for block in self.get_topics():
            marker = "[✓]" if block.delivered else "[ ]"
            lines.append(f"{marker} {block.id}")
        lines.append("")

        # Objective and CTA
        if self.objective:
            lines.append(f"[GOAL] {self.objective.primary_goal}")
            lines.append(f"[CTA] {self.objective.primary_cta}")
            lines.append("")

        # Repair mode context
        if self.in_repair:
            lines.append(f"[REPAIR] retry={self.repair_retry_count}")
            repair_block = self.get_repair_block()
            if repair_block:
                lines.append(f"Strategy: {repair_block.content}")
            lines.append("")

        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        """Get state summary for logging/debugging."""
        topics = self.get_topics()
        delivered = sum(1 for t in topics if t.delivered)
        return {
            "turn_count": self.turn_count,
            "topics_delivered": f"{delivered}/{len(topics)}",
            "in_repair": self.in_repair,
            "breakdown_type": self.breakdown_type,
            "objective_achieved": self.objective_achieved,
            "user_info": self.user_info,
        }

    # --- Quality Metrics ---

    def record_agent_response(
        self,
        response_text: str,
        phase: str,
        turn: int,
    ) -> Dict[str, Any]:
        """
        Record agent response and detect anti-patterns.

        Returns detected issues for logging.
        """
        issues: List[str] = []
        response_lower = response_text.lower()

        # Check for question-only response (ends with ? and < 20 words)
        words = response_text.split()
        if response_text.strip().endswith("?") and len(words) < 20:
            self.question_only_turns += 1
            issues.append("question_only_turn")

        # Check for clarification patterns
        clarification_patterns = [
            "could you clarify",
            "kya matlab",
            "can you explain",
            "what do you mean",
            "please clarify",
            "samjha nahi",
        ]
        if any(p in response_lower for p in clarification_patterns):
            self.clarification_count += 1
            issues.append("clarification_request")

        # Check for repetition
        response_hash = hash(response_text[:100]) if len(response_text) > 100 else hash(response_text)
        for prev in self.agent_responses[-5:]:
            if prev.get("hash") == response_hash:
                self.repetition_count += 1
                issues.append("content_repetition")
                break

        # Record the response
        record = {
            "turn": turn,
            "phase": phase,
            "length": len(response_text),
            "word_count": len(words),
            "timestamp": time.time(),
            "hash": response_hash,
            "issues": issues,
        }
        self.agent_responses.append(record)

        return {"issues": issues, "record": record}

    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get comprehensive quality metrics for the conversation."""
        now = time.time()
        call_duration = now - self.call_start_time

        # Calculate quality scores
        repetition_score = max(0, 1.0 - (self.repetition_count * 0.25))
        question_only_score = max(0, 1.0 - (self.question_only_turns * 0.15))
        clarification_score = max(0, 1.0 - (max(0, self.clarification_count - 1) * 0.2))
        breakdown_score = max(0, 1.0 - (self.breakdown_count * 0.20))

        # Objective score
        objective_score = 1.0 if self.objective_achieved else 0.5 if self.objective_outcome == "fallback_success" else 0.0

        # Overall quality score
        overall_score = (
            repetition_score * 0.20
            + question_only_score * 0.15
            + clarification_score * 0.15
            + breakdown_score * 0.15
            + objective_score * 0.35
        )

        return {
            "call_duration_seconds": round(call_duration, 2),
            "total_turns": self.turn_count,
            "in_repair": self.in_repair,
            # Objective metrics
            "objective_achieved": self.objective_achieved,
            "objective_outcome": self.objective_outcome,
            # Anti-pattern counts
            "repetition_count": self.repetition_count,
            "clarification_count": self.clarification_count,
            "question_only_turns": self.question_only_turns,
            "breakdown_count": self.breakdown_count,
            # Content delivery
            "content_progress": self.get_delivery_progress(),
            # Quality scores (0-1, higher is better)
            "scores": {
                "repetition_score": round(repetition_score, 2),
                "question_only_score": round(question_only_score, 2),
                "clarification_score": round(clarification_score, 2),
                "breakdown_score": round(breakdown_score, 2),
                "objective_score": round(objective_score, 2),
                "overall": round(overall_score, 2),
            },
            # User data collected
            "user_info_fields": list(self.user_info.keys()),
            "content_delivered": list(self.delivered_content),
        }

    def get_quality_log_line(self) -> str:
        """Get a single-line quality summary for structured logging."""
        metrics = self.get_quality_metrics()
        scores = metrics["scores"]
        progress = metrics["content_progress"]

        return (
            f"[CONV_QUALITY] "
            f"turns={metrics['total_turns']} "
            f"repair={self.in_repair} "
            f"content={progress['delivered']}/{progress['total']} "
            f"objective={'achieved' if self.objective_achieved else self.objective_outcome or 'pending'} "
            f"breakdowns={self.breakdown_count} "
            f"score={scores['overall']}"
        )

    def persist_quality_metrics(
        self,
        reason: str = "call_ended",
        output_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """Persist quality metrics to a JSONL file."""
        output_dir = output_dir or QUALITY_METRICS_DIR
        os.makedirs(output_dir, exist_ok=True)

        record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": self.task_id,
            "agent_handle": self.agent_handle,
            "session_id": self.session_id,
            "call_type": self.call_type,
            "end_reason": reason,
            "quality_metrics": self.get_quality_metrics(),
            "user_info": self.user_info,
        }

        date_str = datetime.now().strftime("%Y-%m-%d")
        filepath = output_dir / f"quality_metrics_{date_str}.jsonl"

        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return filepath
        except Exception:
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary for logging/persistence."""
        return {
            "task_id": self.task_id,
            "agent_handle": self.agent_handle,
            "session_id": self.session_id,
            "in_repair": self.in_repair,
            "breakdown_type": self.breakdown_type,
            "content_blocks": [
                {"id": b.id, "type": b.type, "delivered": b.delivered}
                for b in self.content_blocks
            ],
            "objective_achieved": self.objective_achieved,
            "objective_outcome": self.objective_outcome,
            "user_info": self.user_info,
            "delivered_content": list(self.delivered_content),
            "turn_count": self.turn_count,
            "call_type": self.call_type,
            "quality_metrics": self.get_quality_metrics(),
        }

    def build_call_summary(self, end_reason: str = "completed") -> str:
        """Build a human-readable call summary dashboard for end-of-call review."""
        now = time.time()
        call_duration = now - self.call_start_time
        metrics = self.get_quality_metrics()
        progress = metrics["content_progress"]
        scores = metrics["scores"]

        lines = []

        # Header
        lines.append("=" * 50)
        lines.append("[CALL SUMMARY]")
        lines.append("=" * 50)
        lines.append("")

        # Call metadata
        lines.append("[CALL INFO]")
        lines.append(f"Session ID: {self.session_id}")
        lines.append(f"Task ID: {self.task_id}")
        lines.append(f"Agent: {self.agent_handle}")
        lines.append(f"Call Type: {self.call_type}")
        lines.append(f"End Reason: {end_reason}")
        lines.append(f"Duration: {call_duration:.1f}s ({self.turn_count} turns)")
        lines.append("")

        # Content delivery checklist
        lines.append("[CONTENT DELIVERY]")
        lines.append(f"Progress: {progress['delivered']}/{progress['total']} topics covered")
        for block in self.get_topics():
            marker = "[✓]" if block.delivered else "[ ]"
            lines.append(f"  {marker} {block.id}")
        lines.append("")

        # Objective outcome
        lines.append("[OBJECTIVE]")
        if self.objective:
            lines.append(f"Primary Goal: {self.objective.primary_goal}")
            if self.objective_achieved:
                lines.append(f"Status: ACHIEVED ({self.objective_outcome})")
            else:
                status = self.objective_outcome or "not attempted"
                lines.append(f"Status: {status.upper()}")
            if self.objective.fallback_goal:
                lines.append(f"Fallback: {self.objective.fallback_goal}")
        else:
            lines.append("No objective configured")
        lines.append("")

        # User info collected
        lines.append("[USER INFO COLLECTED]")
        if self.user_info:
            for key, value in self.user_info.items():
                lines.append(f"  {key}: {value}")
        else:
            lines.append("  (none)")
        lines.append("")

        # Quality scores
        lines.append("[QUALITY SCORES]")
        lines.append(f"  Overall: {scores['overall']:.0%}")
        lines.append(f"  Objective: {scores['objective_score']:.0%}")
        lines.append(f"  No Repetition: {scores['repetition_score']:.0%}")
        lines.append(f"  No Breakdown: {scores['breakdown_score']:.0%}")
        lines.append("")

        # Issues detected
        if self.repetition_count or self.breakdown_count or self.question_only_turns:
            lines.append("[ISSUES DETECTED]")
            if self.repetition_count:
                lines.append(f"  Repetitions: {self.repetition_count}")
            if self.breakdown_count:
                lines.append(f"  Breakdowns: {self.breakdown_count}")
            if self.question_only_turns:
                lines.append(f"  Question-only turns: {self.question_only_turns}")
            lines.append("")

        lines.append("=" * 50)

        return "\n".join(lines)

    def get_call_summary_dict(self, end_reason: str = "completed") -> Dict[str, Any]:
        """Get call summary as a dictionary for database storage."""
        now = time.time()
        call_duration = now - self.call_start_time
        metrics = self.get_quality_metrics()

        return {
            # Identifiers
            "session_id": self.session_id,
            "task_id": self.task_id,
            "agent_handle": self.agent_handle,
            # Call info
            "call_type": self.call_type,
            "end_reason": end_reason,
            "duration_seconds": round(call_duration, 2),
            "turn_count": self.turn_count,
            # Content delivery
            "content_delivered": [b.id for b in self.get_topics() if b.delivered],
            "content_pending": [b.id for b in self.get_topics() if not b.delivered],
            "content_progress_pct": round(
                metrics["content_progress"]["delivered"] / max(1, metrics["content_progress"]["total"]) * 100
            ),
            # Objective
            "objective_goal": self.objective.primary_goal if self.objective else None,
            "objective_achieved": self.objective_achieved,
            "objective_outcome": self.objective_outcome,
            # User info
            "user_info": self.user_info,
            # Quality
            "quality_overall": metrics["scores"]["overall"],
            "quality_scores": metrics["scores"],
            "issues": {
                "repetitions": self.repetition_count,
                "breakdowns": self.breakdown_count,
                "question_only_turns": self.question_only_turns,
            },
            # Timestamps
            "call_start_time": datetime.fromtimestamp(self.call_start_time).isoformat(),
            "call_end_time": datetime.now().isoformat(),
            # Text summary for display
            "summary_text": self.build_call_summary(end_reason),
        }


# --- Prompt Parsing ---


class PromptParser:
    """
    Parser for extracting content blocks from structured prompts.

    Supports multiple header formats:
    - [Section Name] bracket headers
    - ## Markdown headers
    - **Bold headers**: with colons
    - 1. Numbered lists

    Features:
    - CTA detection via keywords
    - Hinglish content extraction
    - Duplicate ID handling
    - Empty section filtering

    Usage:
        parser = PromptParser()
        blocks = parser.parse(prompt_text)

        # Or with custom settings:
        parser = PromptParser(cta_keywords=["book", "visit"])
        blocks = parser.parse(prompt_text)
    """

    # Default CTA keywords
    DEFAULT_CTA_KEYWORDS = [
        "visit", "closing", "invitation", "offer",
        "book", "schedule", "cta", "action"
    ]

    # Section header patterns (order matters - more specific first)
    SECTION_PATTERNS = [
        r"^\[([^\]]+)\]",                    # [Section Name]
        r"^##\s+(.+)$",                       # ## Section Name
        r"^#\s+(.+)$",                        # # Section Name
        r"^\*\*([^*]+)\*\*\s*[:\-]",          # **Section Name**: or **Section Name** -
        r"^(\d+)\.\s*\*\*([^*]+)\*\*",        # 1. **Section Name**
        r"^(\d+)\.\s+([A-Z][^:]+):",          # 1. Section Name:
        r"^(\d+)\)\s+(.+)$",                  # 1) Section Name
    ]

    # Hinglish detection keywords
    HINGLISH_MARKERS = ["hai", "hain", "karo", "kijiye", "aap", "mein", "ke", "ka", "ki"]

    def __init__(
        self,
        cta_keywords: Optional[List[str]] = None,
        max_id_length: int = 50,
    ):
        """
        Initialize the prompt parser.

        Args:
            cta_keywords: Custom CTA detection keywords (default: visit, closing, etc.)
            max_id_length: Maximum length for generated IDs (default: 50)
        """
        import re
        self._re = re
        self.cta_keywords = cta_keywords or self.DEFAULT_CTA_KEYWORDS
        self.max_id_length = max_id_length

    def _slugify(self, text: str) -> str:
        """Convert text to slug ID."""
        slug = self._re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
        return slug[:self.max_id_length] if slug else "block"

    def _detect_hinglish(self, text: str) -> str:
        """Extract Hinglish content if present (after / or in parentheses)."""
        # Pattern: English / Hinglish
        match = self._re.search(r"/\s*(.+)$", text)
        if match:
            return match.group(1).strip()

        # Pattern: English (Hinglish with markers)
        markers_pattern = "|".join(self.HINGLISH_MARKERS)
        match = self._re.search(
            rf"\(([^)]*(?:{markers_pattern})[^)]*)\)",
            text,
            self._re.IGNORECASE
        )
        if match:
            return match.group(1).strip()

        return ""

    def _is_cta(self, block_id: str, title: str) -> bool:
        """Check if block is a CTA based on keywords."""
        text = f"{block_id} {title}".lower()
        return any(kw in text for kw in self.cta_keywords)

    def parse(self, prompt: str) -> List[ContentBlock]:
        """
        Parse prompt into content blocks.

        Args:
            prompt: The system prompt text to parse

        Returns:
            List of ContentBlock objects

        Edge cases handled:
        - Empty prompt returns []
        - Empty sections are skipped
        - Duplicate IDs get numeric suffix (_2, _3, etc.)
        - Content before first header creates "intro" section
        """
        if not prompt or not prompt.strip():
            return []

        blocks: List[ContentBlock] = []
        seen_ids: Dict[str, int] = {}
        lines = prompt.split("\n")

        current_section: Optional[Dict[str, Any]] = None
        content_lines: List[str] = []

        def make_unique_id(base_id: str) -> str:
            if base_id not in seen_ids:
                seen_ids[base_id] = 1
                return base_id
            seen_ids[base_id] += 1
            return f"{base_id}_{seen_ids[base_id]}"

        def save_section():
            nonlocal current_section, content_lines
            if not current_section:
                return

            content = "\n".join(content_lines).strip()
            if not content:
                current_section = None
                content_lines = []
                return

            base_id = current_section.get("id", f"block_{len(blocks)}")
            block_id = make_unique_id(base_id)
            title = current_section.get("title", "")

            blocks.append(ContentBlock(
                id=block_id,
                content=content,
                content_hi=self._detect_hinglish(content) or content,
                delivery_order=len(blocks),
                is_cta_point=self._is_cta(block_id, title),
            ))

            current_section = None
            content_lines = []

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped:
                if content_lines:
                    content_lines.append("")
                continue

            # Check for section headers
            matched = False
            for pattern in self.SECTION_PATTERNS:
                match = self._re.match(pattern, line_stripped)
                if match:
                    save_section()
                    groups = match.groups()
                    title = groups[-1] if len(groups) > 1 else groups[0]
                    current_section = {
                        "id": self._slugify(title),
                        "title": title.strip(),
                    }
                    matched = True
                    break

            if not matched:
                if current_section:
                    content_lines.append(line_stripped)
                else:
                    # Content before first section
                    current_section = {"id": "intro", "title": "Introduction"}
                    content_lines.append(line_stripped)

        save_section()
        return blocks


def build_conversation_state(
    config: Dict[str, Any],
    system_prompt: str = "",
) -> DynamicConversationState:
    """
    Build conversation state from config and system prompt.

    Args:
        config: Agent configuration dict
        system_prompt: System prompt to parse content blocks from

    Returns:
        Initialized DynamicConversationState
    """
    state = DynamicConversationState()
    state.call_type = config.get("call_type", "outbound")

    # Set language default
    lang = config.get("preferred_language", "en")
    state.user_language = {"english": "en", "hindi": "hi"}.get(lang, lang)

    # Parse content blocks from prompt
    if system_prompt:
        state.content_blocks = PromptParser().parse(system_prompt)

    # Fallback to config checklist
    if not state.content_blocks:
        for i, topic in enumerate(config.get("content_checklist", [])):
            state.content_blocks.append(
                ContentBlock(
                    id=topic.lower().replace(" ", "_"),
                    content=topic,
                    delivery_order=i,
                )
            )

    # Extract objective from CTA block in parsed content
    cta_block = next((b for b in state.content_blocks if b.is_cta_point), None)
    if cta_block:
        state.objective = ConversationObjective(
            primary_goal=cta_block.id,
            primary_cta=cta_block.content,
            primary_cta_hi=cta_block.content_hi,
        )

    # Add default repair blocks
    state.content_blocks.extend(get_default_repair_blocks())

    return state

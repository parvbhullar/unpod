"""
Prompt composer - assembles conversational prompts from modular components.

This module provides a tone-based prompt composition system that combines:
- Base voice rules (how to speak on a call)
- Conversation patterns (support, sales, booking, multilingual)
- Tone modifiers (professional, casual)
- Optional guidelines (memory, follow-up)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from super.core.voice.prompts.base import (
    VOICE_RULES,
    STT_ERROR_HANDLING,
    REFERENCE_CONTEXT_HANDLING,
)
from super.core.voice.prompts.patterns.support import SUPPORT_PATTERNS
from super.core.voice.prompts.patterns.sales import SALES_PATTERNS
from super.core.voice.prompts.patterns.booking import BOOKING_PATTERNS
from super.core.voice.prompts.patterns.multilingual import MULTILINGUAL_PATTERNS
from super.core.voice.prompts.tones.professional import PROFESSIONAL_MODIFIER
from super.core.voice.prompts.tones.casual import CASUAL_MODIFIER
from super.core.voice.prompts.guidelines import MEMORY_GUIDELINES, FOLLOWUP_GUIDELINES


class Tone(Enum):
    """Voice tone options."""

    PROFESSIONAL = "professional"
    CASUAL = "casual"


class Pattern(Enum):
    """Conversation pattern types."""

    SUPPORT = "support"
    SALES = "sales"
    BOOKING = "booking"
    MULTILINGUAL = "multilingual"


# Pattern to prompt mapping
PATTERN_MAP = {
    Pattern.SUPPORT: SUPPORT_PATTERNS,
    Pattern.SALES: SALES_PATTERNS,
    Pattern.BOOKING: BOOKING_PATTERNS,
    Pattern.MULTILINGUAL: MULTILINGUAL_PATTERNS,
}


@dataclass
class PromptConfig:
    """Configuration for prompt composition."""

    # Agent identity
    agent_name: str = "Assistant"
    company_name: str = ""
    current_datetime: Optional[str] = None

    # Tone selection
    tone: Tone = Tone.PROFESSIONAL

    # Patterns to include (empty = support only)
    patterns: List[Pattern] = field(default_factory=list)

    # Language (triggers multilingual patterns if not "en")
    language: str = "en"

    # Optional features
    include_memory: bool = False
    include_followup: bool = False

    # Custom persona (user's system_prompt, appended at end)
    custom_persona: Optional[str] = None

    # Strict script mode: prioritize campaign script over generic examples/patterns
    strict_script_mode: bool = False


def compose_prompt(config: PromptConfig) -> str:
    """
    Assemble conversational prompt from modular components.

    Structure:
    1. Identity (who you are) - concise
    2. Voice rules (how you speak)
    3. STT error handling
    4. Reference context handling
    5. Conversation patterns (based on config)
    6. Tone modifier
    7. Optional guidelines (memory, follow-up)
    8. Custom persona (user's system_prompt)

    Args:
        config: PromptConfig with composition settings

    Returns:
        Complete assembled prompt string
    """
    sections = []

    # 1. Identity - concise
    identity = f"You are {config.agent_name}"
    if config.company_name:
        identity += f", a voice assistant for {config.company_name}"
    identity += ". You're on a phone call—speak naturally, keep it brief."
    if config.current_datetime:
        identity += f"\nCurrent date/time: {config.current_datetime}"
    sections.append(identity)

    # 2. Custom persona (user's system_prompt) - HIGH PRIORITY
    # Business context must come BEFORE generic rules to take precedence
    if config.custom_persona and config.custom_persona.strip():
        sections.append(f"## YOUR BUSINESS CONTEXT - FOLLOW THIS EXACTLY\n{config.custom_persona}")
        print(f"[DEBUG] Business context loaded: {config.custom_persona[:200]}...")
    else:
        print("[DEBUG] WARNING: No business context found in config.custom_persona")

    # 2. Core voice rules (skip generic examples in strict scripted campaigns)
    if not config.strict_script_mode:
        sections.append(VOICE_RULES)

    # 3. STT error handling
    sections.append(STT_ERROR_HANDLING)

    # 4. Reference context handling
    sections.append(REFERENCE_CONTEXT_HANDLING)

    # 5. Conversation patterns
    # In strict scripted campaigns, avoid generic support/sales/booking examples.
    patterns_to_add = [] if config.strict_script_mode else (
        config.patterns.copy() if config.patterns else [Pattern.SUPPORT]
    )

    # Auto-add multilingual if language is not English
    # Covers Indian languages and any non-English language for code-switching support
    non_english_languages = {
        # Indian languages
        "hi", "hindi", "hinglish", "hn",
        "pa", "punjabi",
        "ta", "tamil",
        "te", "telugu",
        "mr", "marathi",
        "gu", "gujarati",
        "bn", "bengali",
        "kn", "kannada",
        "ml", "malayalam",
        "ur", "urdu",
        "or", "odia",
        # Other common languages
        "es", "spanish",
        "fr", "french",
        "de", "german",
        "pt", "portuguese",
        "ar", "arabic",
        "zh", "chinese",
        "ja", "japanese",
        "ko", "korean",
    }
    lang_lower = config.language.lower() if config.language else "en"
    # Check if language is non-English (not starting with 'en')
    is_non_english = not lang_lower.startswith("en") and lang_lower != "english"
    if is_non_english or lang_lower in non_english_languages:
        if Pattern.MULTILINGUAL not in patterns_to_add:
            patterns_to_add.append(Pattern.MULTILINGUAL)

    if config.strict_script_mode:
        sections.append(
            "## Script Execution Mode\n"
            "- Follow the provided business/campaign script exactly.\n"
            "- Do not use generic support fallback lines.\n"
            "- On yes/ok/go-ahead acknowledgments, continue to the next scripted line."
        )

    for pattern in patterns_to_add:
        if pattern in PATTERN_MAP:
            sections.append(PATTERN_MAP[pattern])

    # 6. Tone modifier
    if config.tone == Tone.CASUAL:
        sections.append(CASUAL_MODIFIER)
    else:
        sections.append(PROFESSIONAL_MODIFIER)

    # 7. Optional guidelines
    if config.include_memory:
        sections.append(MEMORY_GUIDELINES)
    if config.include_followup:
        sections.append(FOLLOWUP_GUIDELINES)

    return "\n\n".join(sections)


def get_tone_from_config(config: dict) -> Tone:
    """
    Map config values to Tone enum.

    Args:
        config: Agent configuration dictionary

    Returns:
        Tone enum value
    """
    tone_str = config.get("agent_tone", "professional").lower()
    if tone_str == "casual":
        return Tone.CASUAL
    return Tone.PROFESSIONAL


def get_patterns_from_config(config: dict) -> List[Pattern]:
    """
    Determine which patterns to include based on config.

    Args:
        config: Agent configuration dictionary

    Returns:
        List of Pattern enum values
    """
    patterns = []

    # Always include support as base
    patterns.append(Pattern.SUPPORT)

    # Check call_type for additional patterns
    call_type = config.get("call_type", "").lower()
    if call_type in ("outbound", "outbound_sales", "sales"):
        patterns.append(Pattern.SALES)
        patterns.append(Pattern.BOOKING)  # Sales often needs callback booking
    elif call_type in ("appointment", "booking"):
        patterns.append(Pattern.BOOKING)

    # Check for explicit pattern flags
    if config.get("include_sales_patterns"):
        if Pattern.SALES not in patterns:
            patterns.append(Pattern.SALES)
    if config.get("include_booking_patterns"):
        if Pattern.BOOKING not in patterns:
            patterns.append(Pattern.BOOKING)

    return patterns


def create_prompt_from_agent_config(
    config: dict,
    agent_name: str = "Assistant",
    current_datetime: Optional[str] = None,
    custom_persona: Optional[str] = None,
) -> str:
    """
    Convenience function to create prompt directly from agent config dict.

    Args:
        config: Agent configuration dictionary
        agent_name: Name of the agent
        current_datetime: Current date/time string
        custom_persona: Custom system prompt to append

    Returns:
        Assembled prompt string
    """
    prompt_config = PromptConfig(
        agent_name=agent_name,
        company_name=config.get("company_name", ""),
        current_datetime=current_datetime,
        tone=get_tone_from_config(config),
        patterns=get_patterns_from_config(config),
        language=config.get("stt_language")
        or config.get("preferred_language")
        or config.get("language", "en"),
        include_memory=config.get("enable_memory", False),
        include_followup=config.get("follow_up_enabled", False),
        custom_persona=custom_persona,
        strict_script_mode=config.get("strict_script_mode", False),
    )

    return compose_prompt(prompt_config)

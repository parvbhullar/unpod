"""
Voice prompt modules.

This package provides modular, tone-based prompts for conversational voice agents.

New system (recommended):
- Use `compose_prompt()` from composer module
- Set `use_conversational_prompts: true` in agent config

Legacy system (backward compatible):
- Import from `super.core.voice.prompts.legacy`
"""

# New conversational prompt system
from super.core.voice.prompts.base import (
    VOICE_RULES,
    STT_ERROR_HANDLING,
    REFERENCE_CONTEXT_HANDLING,
)
from super.core.voice.prompts.composer import (
    compose_prompt,
    create_prompt_from_agent_config,
    PromptConfig,
    Tone,
    Pattern,
)
from super.core.voice.prompts.guidelines import (
    MEMORY_GUIDELINES,
    FOLLOWUP_GUIDELINES,
)

# Re-export legacy prompts for backward compatibility
from super.core.voice.prompts.legacy import (
    BASIC_PROMPT,
    CASUAL_PROMPT,
    PROFESSIONAL_PROMPT,
    MEMORY_PROMPT,
    FOLLOW_UP_PROMPT,
)

__all__ = [
    # New system
    "VOICE_RULES",
    "STT_ERROR_HANDLING",
    "REFERENCE_CONTEXT_HANDLING",
    "compose_prompt",
    "create_prompt_from_agent_config",
    "PromptConfig",
    "Tone",
    "Pattern",
    "MEMORY_GUIDELINES",
    "FOLLOWUP_GUIDELINES",
    # Legacy (backward compatible)
    "BASIC_PROMPT",
    "CASUAL_PROMPT",
    "PROFESSIONAL_PROMPT",
    "MEMORY_PROMPT",
    "FOLLOW_UP_PROMPT",
]

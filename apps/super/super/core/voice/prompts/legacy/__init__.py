"""
Legacy prompt modules.

These prompts are retained for backward compatibility with existing
agents that have not migrated to the new conversational prompt system.

To use the new system, set `use_conversational_prompts: true` in agent config.
"""

from super.core.voice.prompts.legacy.basic import BASIC_PROMPT
from super.core.voice.prompts.legacy.casual import CASUAL_PROMPT
from super.core.voice.prompts.legacy.professional import PROFESSIONAL_PROMPT
from super.core.voice.prompts.legacy.guidelines_prompt import (
    MEMORY_PROMPT,
    FOLLOW_UP_PROMPT,
)

__all__ = [
    "BASIC_PROMPT",
    "CASUAL_PROMPT",
    "PROFESSIONAL_PROMPT",
    "MEMORY_PROMPT",
    "FOLLOW_UP_PROMPT",
]

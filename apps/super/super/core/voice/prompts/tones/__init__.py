"""
Tone modifier modules for voice prompts.

Each module provides tone-specific guidance that layers on top of
the base voice rules and conversation patterns.
"""

from super.core.voice.prompts.tones.professional import PROFESSIONAL_MODIFIER
from super.core.voice.prompts.tones.casual import CASUAL_MODIFIER

__all__ = [
    "PROFESSIONAL_MODIFIER",
    "CASUAL_MODIFIER",
]

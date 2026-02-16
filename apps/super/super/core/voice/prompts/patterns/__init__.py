"""
Conversation pattern modules for different call types.

Each module contains example-driven conversation flows that model
natural dialogue patterns rather than instructional rules.
"""

from super.core.voice.prompts.patterns.support import SUPPORT_PATTERNS
from super.core.voice.prompts.patterns.sales import SALES_PATTERNS
from super.core.voice.prompts.patterns.booking import BOOKING_PATTERNS
from super.core.voice.prompts.patterns.multilingual import MULTILINGUAL_PATTERNS

__all__ = [
    "SUPPORT_PATTERNS",
    "SALES_PATTERNS",
    "BOOKING_PATTERNS",
    "MULTILINGUAL_PATTERNS",
]

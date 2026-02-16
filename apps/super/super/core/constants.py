"""Constants for the Super framework."""
from enum import Enum


class DocumentSource(str, Enum):
    """Document source types."""

    GMAIL = "gmail"
    FILE = "file"
    WEB = "web"
    CHAT = "chat"


# Separators
SECTION_SEPARATOR = "\n\n"
TITLE_SEPARATOR = " | "

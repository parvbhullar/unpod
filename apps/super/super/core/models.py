"""Core models for the Super framework."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Document:
    """Document model for storing text content."""

    sections: List[str] = field(default_factory=list)
    source: str = ""
    semantic_identifier: str = ""

    def get_title_for_document_index(self) -> str:
        """Get document title for indexing."""
        return self.semantic_identifier


@dataclass
class DocAwareChunk:
    """Chunk model that maintains awareness of its source document."""

    source_document: Document
    chunk_id: int
    blurb: str
    content: str
    source_links: Dict[int, str] = field(default_factory=dict)
    section_continuation: bool = False

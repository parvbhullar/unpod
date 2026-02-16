"""SearchDoc model for document retrieval."""

import hashlib
import json
from datetime import datetime

from super.core.memory.index.base import BaseDocument


class SearchDoc(BaseDocument):
    """Class to represent detailed information."""

    document_id: str
    content: str
    semantic_identifier: str
    link: str | None
    blurb: str
    source_type: str
    boost: int = 1
    recency_bias: float = 1
    hidden: bool = False
    metadata: dict[str, str | list[str]]
    score: float | None
    match_highlights: list[str] | None
    updated_at: datetime | None
    primary_owners: list[str] | None
    secondary_owners: list[str] | None

    def __init__(
        self,
        blurb,
        content,
        source_type,
        document_id,
        semantic_identifier,
        metadata,
        url=None,
        match_highlights=None,
        score=0.01,
        recency_bias=1,
        **kwargs,
    ):
        super().__init__()
        self.blurb = blurb
        self.content = content
        self.source_type = source_type
        self.document_id = document_id
        self.semantic_identifier = semantic_identifier
        self.metadata = metadata
        self.url = url if url is not None else self.document_id
        self.citation_uuid = -1
        self.score = score
        self.recency_bias = recency_bias
        self.match_highlights = match_highlights
        self.updated_at = kwargs.get("updated_at", None)

    def __eq__(self, other):
        if not isinstance(other, SearchDoc):
            return False
        return (
            self.url == other.url
            and self.blurb == other.blurb
            and self.content == other.content
            and self.source_type == other.source_type
            and self.document_id == other.document_id
            and self.semantic_identifier == other.semantic_identifier
            and self.metadata == other.metadata
        )

    def __hash__(self):
        return int(
            self._md5_hash(
                (
                    self.url,
                    self.blurb,
                    self.content,
                    self.source_type,
                    self.document_id,
                    self.semantic_identifier,
                    self._metadata_str(),
                )
            ),
            16,
        )

    def _metadata_str(self):
        return json.dumps(self.metadata, sort_keys=True)

    def _md5_hash(self, value):
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, sort_keys=True)
        return hashlib.md5(str(value).encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, info_dict):
        import ast

        def get_url(info_dict):
            metadata = info_dict.get("metadata", {})
            url = info_dict.get("url", metadata.get("url", ""))
            source_type = info_dict.get("source_type", "")
            if source_type == "gmail":
                links = info_dict.get("source_links", "")
                if links:
                    url = links["0"]
                else:
                    url = info_dict.get("semantic_identifier", "")
            if source_type == "file":
                url = metadata.get("url", "")
                if ".md" in url:
                    meta = ast.literal_eval(metadata.get("meta", "{}"))
                    if meta:
                        url = meta.get("source_url", "")
                    else:
                        url = metadata.get("url", "")
                else:
                    url = info_dict.get("document_id", "")
            return url

        metadata = info_dict.get("metadata", {})
        return cls(
            blurb=info_dict.get("blurb", ""),
            content=info_dict.get("content", ""),
            source_type=info_dict.get("source_type", ""),
            document_id=info_dict.get("document_id", ""),
            semantic_identifier=info_dict.get("semantic_identifier", ""),
            metadata=metadata,
            url=get_url(info_dict),
            score=info_dict.get("score", 0.01),
            recency_bias=info_dict.get("recency_bias", 1),
            match_highlights=info_dict.get("match_highlights", []),
        )

    def to_dict(self):
        return {
            "blurb": self.blurb,
            "content": self.content,
            "source_type": self.source_type,
            "document_id": self.document_id,
            "semantic_identifier": self.semantic_identifier,
            "url": self.url,
            "citation_uuid": self.citation_uuid,
            "match_highlights": self.match_highlights,
            "score": self.score,
        }

    def to_short_descriptor(self):
        return {
            "blurb": self.blurb,
            "semantic_identifier": self.semantic_identifier,
            "score": self.score,
        }

    def __str__(self):
        return (
            f"SearchDoc: {self.semantic_identifier}"
            f" - {self.score} - {self.blurb}"
        )

import hashlib
import json
from datetime import datetime

from super.core.memory.index.base import BaseDocument


class SearchDoc(BaseDocument):
    """Class to represent detailed information.

    Attributes:
        blurb (str): Brief blurb or summary.
        content (str): Main content of the information.
        source_type (str): Type of the source (e.g., "file", "web").
        document_id (str): Unique identifier for the document.
        semantic_identifier (str): Semantic identifier, such as a filename.
        metadata (dict): Additional metadata associated with the information.
        url (str): Unique URL or identifier for the information.
        citation_uuid (int): Citation UUID, default is -1.
    """

    document_id: str
    content: str
    semantic_identifier: str
    link: str | None
    blurb: str
    source_type: str
    boost: int = 1
    recency_bias: float = 1
    # Whether the document is hidden when doing a standard search
    # since a standard search will never find a hidden doc, this can only ever
    # be `True` when doing an admin search
    hidden: bool = False
    metadata: dict[str, str | list[str]]
    score: float | None
    # Matched sections in the doc. Uses Vespa syntax e.g. <hi>TEXT</hi>
    # to specify that a set of words should be highlighted. For example:
    # ["<hi>the</hi> <hi>answer</hi> is 42", "the answer is <hi>42</hi>""]
    match_highlights: list[str] | None
    # when the doc was last updated
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
        """Initialize the Information object with detailed attributes.

        Args:
            blurb (str): Brief blurb or summary.
            content (str): Main content of the information.
            source_type (str): Type of the source.
            document_id (str): Unique identifier for the document.
            semantic_identifier (str): Semantic identifier.
            metadata (dict): Additional metadata.
            url (str, optional): Unique URL or identifier. Defaults to document_id.
        """
        # super().__init__(content=content, metadata=metadata)
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
        """Generate a string representation of metadata."""
        return json.dumps(self.metadata, sort_keys=True)

    def _md5_hash(self, value):
        """Generate an MD5 hash for a given value."""
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, sort_keys=True)
        return hashlib.md5(str(value).encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, info_dict):
        """Create an Information object from a dictionary.

        Args:
            info_dict (dict): Dictionary containing keys corresponding to the object's attributes.

        Returns:
            SearchDoc: An instance of Information.
        """
        def get_url(info_dict):
            import ast
            
            metadata = info_dict.get("metadata", {})
            url=info_dict.get("url", metadata.get("url", ""))
            source_type = info_dict.get("source_type", "")
            if source_type == "gmail":
                links=info_dict.get("source_links", "")
                if links:
                    url=links['0']
                else:
                    url=info_dict.get('semantic_identifier', "")
            if source_type == "file":
                url=metadata.get("url", "")
                if '.md' in url:
                    meta=ast.literal_eval(metadata.get("meta", "{}"))
                    if meta:
                        url=meta.get("source_url", "")
                    else:
                        url=metadata.get("url", "")
                else:
                    url=info_dict.get("document_id", "")

                
            
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
        """Convert the Information object to a dictionary."""
        return {
            "blurb": self.blurb,
            "content": self.content,
            "source_type": self.source_type,
            "document_id": self.document_id,
            "semantic_identifier": self.semantic_identifier,
            # "metadata": self.metadata,
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
        return f"SearchDoc: {self.semantic_identifier} - {self.score} - {self.blurb}"

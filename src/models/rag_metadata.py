"""
Utility dataclasses for multimodal chunk metadata used by Vertex AI RAG Engine.
Aligns with the recommended structure in the 2025 technical guide.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Literal
from uuid import uuid4


ContentType = Literal[
    "text",
    "pdf_text",
    "pdf_image",
    "image",
    "audio",
    "video",
]


@dataclass
class ChunkMetadata:
    """
    Metadata descriptor for a single chunk ingested into the RAG Engine.
    """

    content_type: ContentType
    document_id: str
    chunk_index: int
    page_number: Optional[int] = None
    source_uri: Optional[str] = None
    summary: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    chunk_id: str = field(default_factory=lambda: str(uuid4()))

    def to_vertex_payload(self) -> Dict[str, Any]:
        """
        Convert metadata to the payload format expected by Vertex AI RAG.
        """
        payload = {
            "id": self.chunk_id,
            "content_type": self.content_type,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
        }

        if self.page_number is not None:
            payload["page_number"] = self.page_number

        if self.source_uri:
            payload["source_uri"] = self.source_uri

        if self.summary:
            payload["summary"] = self.summary

        if self.extra:
            payload["metadata"] = self.extra

        return payload

    def to_dict(self) -> Dict[str, Any]:
        """
        Helper for persistence or logging.
        """
        data = asdict(self)
        data["metadata"] = data.pop("extra", {})
        return data

"""
Pydantic models for API request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Types of documents that can be uploaded."""
    MANUAL = "manual"
    DRAWING = "drawing"
    QUALITY_MANUAL = "quality_manual"
    SPECIFICATION = "specification"


class DocumentStatus(str, Enum):
    """Status of document processing."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class AnalysisStatus(str, Enum):
    """Status of analysis."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportType(str, Enum):
    """Types of reports."""
    EXECUTIVE = "executive"
    DETAILED = "detailed"


# Knowledge Base Schemas
class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    document_id: str
    filename: str
    document_type: DocumentType
    size_bytes: int
    status: DocumentStatus
    uploaded_at: datetime
    gcs_uri: Optional[str] = None


class DocumentInfo(BaseModel):
    """Information about a document in the knowledge base."""
    document_id: str
    filename: str
    document_type: DocumentType
    status: DocumentStatus
    uploaded_at: datetime
    indexed_at: Optional[datetime] = None
    page_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeBaseStats(BaseModel):
    """Statistics about the knowledge base."""
    total_documents: int
    documents_by_type: Dict[str, int]
    total_pages_indexed: int
    last_updated: Optional[datetime] = None


# Analysis Schemas
class AnalysisUploadRequest(BaseModel):
    """Request to upload a drawing for analysis."""
    project_name: Optional[str] = None
    include_quality_manual: bool = False
    quality_mode: str = Field(default="flash", pattern="^(flash|pro)$")


class AnalysisUploadResponse(BaseModel):
    """Response after uploading drawing for analysis."""
    analysis_id: str
    status: AnalysisStatus
    uploaded_at: datetime
    drawing_filename: str


class AnalysisInfo(BaseModel):
    """Information about an analysis."""
    analysis_id: str
    status: AnalysisStatus
    project_name: Optional[str] = None
    drawing_filename: str
    uploaded_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    quality_mode: str
    exception_count: Optional[int] = None
    executive_report_url: Optional[str] = None
    detailed_report_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    """Response containing report URLs."""
    analysis_id: str
    report_type: ReportType
    report_url: str
    generated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


# Chat Schemas
class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Request to chat about an analysis."""
    message: str
    history: List[ChatMessage] = Field(default_factory=list)
    file: Optional[Dict[str, Any]] = Field(default=None, description="Optional file metadata for unified chat")


class ChatResponse(BaseModel):
    """Response from chat."""
    message: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    grounded: bool = True


# Health Check
class HealthCheck(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "0.1.0"
    services: Dict[str, str] = Field(default_factory=dict)

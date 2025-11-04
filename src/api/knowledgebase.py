"""
Knowledge Base API endpoints.
Handles upload and management of manuals, specifications, and reference documents.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi import Form
from typing import List, Optional
from datetime import datetime
import uuid
import structlog

from src.models.schemas import (
    DocumentUploadResponse,
    DocumentInfo,
    KnowledgeBaseStats,
    DocumentType,
    DocumentStatus
)
from src.config.settings import settings

logger = structlog.get_logger()
router = APIRouter()


from src.services.knowledge_base import KnowledgeBaseService
from src.services.sqlite_db import get_db


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.MANUAL),
) -> DocumentUploadResponse:
    """
    Upload a document to the knowledge base.

    **Supported document types:**
    - `manual`: Injection molding manuals, textbooks
    - `specification`: Material specifications, standards
    - `quality_manual`: Quality manuals, procedures

    **Process:**
    1. Upload to Cloud Storage
    2. Extract text and chunk
    3. Create embeddings
    4. Index in RAG Engine / Vector Search

    **Returns:** Document metadata and upload confirmation
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Check size limit
        max_size = settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {settings.max_upload_size_mb}MB limit"
            )

        document_id = str(uuid.uuid4())

        logger.info(
            "document_upload_started",
            document_id=document_id,
            filename=file.filename,
            type=document_type,
            size_bytes=file_size
        )

        # Process document with Knowledge Base Service
        kb_service = KnowledgeBaseService()
        doc_info = await kb_service.process_document(
            document_id=document_id,
            content=content,
            filename=file.filename,
            document_type=document_type
        )

        # Save to database
        db = get_db()
        db.save_document(doc_info)

        # Return response
        return DocumentUploadResponse(
            document_id=doc_info.document_id,
            filename=doc_info.filename,
            document_type=doc_info.document_type,
            size_bytes=file_size,
            status=doc_info.status,
            uploaded_at=doc_info.uploaded_at,
            gcs_uri=doc_info.metadata.get("gcs_uri")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_upload_failed", error=str(e), filename=file.filename)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents(
    document_type: Optional[DocumentType] = None,
    status_filter: Optional[DocumentStatus] = None,
    limit: int = 100,
    offset: int = 0
) -> List[DocumentInfo]:
    """
    List documents in the knowledge base.

    **Filters:**
    - `document_type`: Filter by document type
    - `status_filter`: Filter by processing status
    - `limit`: Maximum number of results (default: 100)
    - `offset`: Pagination offset (default: 0)
    """
    try:
        logger.info(
            "list_documents",
            type=document_type,
            status=status_filter,
            limit=limit,
            offset=offset
        )

        # Get documents from database
        db = get_db()
        documents = db.list_documents(document_type, status_filter, limit, offset)

        return documents

    except Exception as e:
        logger.error("list_documents_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str) -> DocumentInfo:
    """
    Get details about a specific document.

    **Returns:** Document metadata, status, and indexing information
    """
    try:
        logger.info("get_document", document_id=document_id)

        # Get document from database
        db = get_db()
        document = db.get_document(document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_document_failed", error=str(e), document_id=document_id)
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str):
    """
    Delete a document from the knowledge base.

    **Warning:** This will remove the document from storage and all indexes.
    """
    try:
        logger.info("delete_document", document_id=document_id)

        # Delete from database
        db = get_db()
        success = db.delete_document(document_id)

        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        # TODO: Also delete from GCS and RAG Engine
        # For now, just delete from DB

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_document_failed", error=str(e), document_id=document_id)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_stats() -> KnowledgeBaseStats:
    """
    Get statistics about the knowledge base.

    **Returns:** Document counts, types, pages indexed, last update time
    """
    try:
        logger.info("get_knowledge_base_stats")

        # Get stats from database
        db = get_db()
        stats = db.get_documents_stats()

        return KnowledgeBaseStats(**stats)

    except Exception as e:
        logger.error("get_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

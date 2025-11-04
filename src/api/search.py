"""
Search API endpoints.
Visual similarity search for drawings.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, status, Query
from typing import List, Optional
import structlog
import numpy as np

from src.services.vector_search import get_vector_search
from src.services.drawing_processor import DrawingProcessor
from src.config.settings import settings

logger = structlog.get_logger()
router = APIRouter()


@router.post("/visual-similarity")
async def search_by_image(
    file: UploadFile = File(...),
    top_k: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0)
):
    """
    Find visually similar drawings by uploading an image.

    **Process:**
    1. Generate embedding from uploaded image
    2. Search vector database for similar pages
    3. Return ranked results with similarity scores

    **Parameters:**
    - `file`: Image file (PNG, JPG, or PDF with single page)
    - `top_k`: Number of results to return (1-50)
    - `min_similarity`: Minimum similarity threshold (0.0-1.0)

    **Returns:** List of similar pages with scores

    **Use cases:**
    - Find similar designs in knowledge base
    - Locate reused components across drawings
    - Identify potential design conflicts
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Read file
        content = await file.read()

        logger.info(
            "visual_search_request",
            filename=file.filename,
            top_k=top_k,
            min_similarity=min_similarity
        )

        # Generate embedding from uploaded image
        processor = DrawingProcessor()

        # If PDF, convert to image first
        if file.filename.lower().endswith('.pdf'):
            # Convert first page only
            import io
            from pdf2image import convert_from_bytes

            images = convert_from_bytes(content, dpi=300, first_page=1, last_page=1)
            if not images:
                raise HTTPException(status_code=400, detail="Could not process PDF")

            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            images[0].save(img_byte_arr, format='PNG')
            image_bytes = img_byte_arr.getvalue()
        else:
            image_bytes = content

        # Generate embedding
        query_embedding = await processor.generate_image_embedding(image_bytes)

        # Search for similar images
        vector_search = get_vector_search()
        results = vector_search.search_similar(
            query_embedding=query_embedding,
            top_k=top_k,
            min_similarity=min_similarity
        )

        payload = [
            {
                "document_id": r.document_id,
                "page_number": r.page_number,
                "gcs_uri": r.gcs_uri,
                "similarity": r.similarity,
                "metadata": r.metadata,
            }
            for r in results
        ]

        logger.info(
            "visual_search_completed",
            results_count=len(payload),
            top_similarity=payload[0]["similarity"] if payload else 0
        )

        return {
            "query_filename": file.filename,
            "results_count": len(payload),
            "results": payload
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("visual_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/document/{document_id}/similar")
async def find_similar_to_document(
    document_id: str,
    page_number: int = Query(0, ge=0),
    top_k: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0)
):
    """
    Find drawings similar to a specific page of an existing document.

    **Parameters:**
    - `document_id`: Document or analysis ID
    - `page_number`: Page number to use as query (0-indexed)
    - `top_k`: Number of results to return (1-50)
    - `min_similarity`: Minimum similarity threshold (0.0-1.0)

    **Returns:** List of similar pages with scores
    """
    try:
        logger.info(
            "document_similarity_search",
            document_id=document_id,
            page_number=page_number
        )

        # Get embeddings for the document
        vector_search = get_vector_search()
        try:
            doc_embeddings = vector_search.get_document_embeddings(document_id)
        except NotImplementedError as exc:
            raise HTTPException(
                status_code=501,
                detail=str(exc)
            )

        if not doc_embeddings:
            raise HTTPException(
                status_code=404,
                detail="Document not found or embeddings not available"
            )

        # Find the requested page
        page_embedding = None
        for page_num, embedding, _ in doc_embeddings:
            if page_num == page_number:
                page_embedding = embedding
                break

        if page_embedding is None:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page_number} not found in document"
            )

        # Search for similar pages (excluding the same document)
        results = vector_search.search_similar(
            query_embedding=page_embedding,
            top_k=top_k + 10,  # Get extra to filter out same document
            min_similarity=min_similarity
        )

        # Filter out pages from the same document
        filtered_results = [
            r for r in results if r.document_id != document_id
        ]
        filtered_results = filtered_results[:top_k]

        payload = [
            {
                "document_id": r.document_id,
                "page_number": r.page_number,
                "gcs_uri": r.gcs_uri,
                "similarity": r.similarity,
                "metadata": r.metadata,
            }
            for r in filtered_results
        ]

        logger.info(
            "document_similarity_search_completed",
            results_count=len(payload)
        )

        return {
            "query_document_id": document_id,
            "query_page_number": page_number,
            "results_count": len(payload),
            "results": payload
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_similarity_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats")
async def get_search_stats():
    """
    Get statistics about the vector search index.

    **Returns:** Index statistics including total embeddings and documents
    """
    try:
        logger.info("search_stats_request")

        vector_search = get_vector_search()
        stats = vector_search.get_stats()

        return stats

    except Exception as e:
        logger.error("search_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/document/{document_id}")
async def delete_document_from_index(document_id: str):
    """
    Delete all embeddings for a document from the search index.

    **Parameters:**
    - `document_id`: Document or analysis ID

    **Returns:** Success status
    """
    try:
        logger.info("delete_from_index", document_id=document_id)

        vector_search = get_vector_search()
        deleted = vector_search.delete_document_embeddings(document_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Document not found in search index"
            )

        return {"status": "deleted", "document_id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_from_index_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

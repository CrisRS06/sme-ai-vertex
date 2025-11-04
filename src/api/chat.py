"""
Chat API endpoints.
Provides conversational interface to discuss analysis results.
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
import structlog
from typing import Optional

from src.models.schemas import ChatRequest, ChatResponse
from src.config.settings import settings

logger = structlog.get_logger()
router = APIRouter()


from src.services.chat_service import ChatService


@router.post("/upload", response_model=ChatResponse)
async def unified_chat_with_file(
    message: str = Form(...),
    chat_history: Optional[str] = Form(None),
    file: UploadFile = File(...)
) -> ChatResponse:
    """
    Unified chat endpoint that handles PDF uploads + chat in single request.
    
    **Features:**
    - PDF analysis + chat with analysis context + RAG grounding
    - File upload for PDF analysis
    - Chat history for context
    - Context-aware responses
    
    **Parameters:**
    - `message`: User's message
    - `chat_history`: JSON string of conversation history
    - `file`: PDF file to analyze
    
    **Returns:** AI response with sources and analysis context
    """
    try:
        if not message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty")
            
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported")
            
        logger.info(
            "unified_chat_file_request",
            message_length=len(message),
            filename=file.filename,
            file_size=len(await file.read())
        )
        
        # Reset file pointer after reading size
        await file.seek(0)
        
        # Parse chat history
        history = []
        if chat_history:
            try:
                import json
                history = json.loads(chat_history)
            except json.JSONDecodeError:
                logger.warning("invalid_chat_history_format")
                
        # Use chat service
        chat_service = ChatService()
        response = await chat_service.unified_chat_with_file(
            message=message,
            history=history,
            file=file
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("unified_chat_file_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat with file failed: {str(e)}")


@router.post("/{analysis_id}/chat", response_model=ChatResponse)
async def chat_about_analysis(
    analysis_id: str,
    request: ChatRequest
) -> ChatResponse:
    """
    Chat with AI expert about an analysis.

    **Features:**
    - Grounded responses based on analysis results
    - RAG retrieval from knowledge base + drawing analysis
    - Cites sources (page numbers, sections)
    - Maintains conversation context

    **Parameters:**
    - `analysis_id`: ID of the analysis to discuss
    - `message`: User's question or message
    - `history`: Optional conversation history for context

    **Returns:** AI response with sources and grounding status

    **Example questions:**
    - "Why is dimension X flagged as an exception?"
    - "What material would you recommend for this part?"
    - "How can we reduce the risk of warping?"
    - "Explain the GD&T issue on page 2"
    """
    try:
        if not settings.enable_chat:
            raise HTTPException(
                status_code=503,
                detail="Chat feature is currently disabled"
            )

        if not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )

        logger.info(
            "chat_request",
            analysis_id=analysis_id,
            message_length=len(request.message),
            history_length=len(request.history)
        )

        # Use chat service
        chat_service = ChatService()
        response = await chat_service.chat(
            analysis_id=analysis_id,
            message=request.message,
            history=request.history
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("chat_failed", error=str(e), analysis_id=analysis_id)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/general", response_model=ChatResponse)
async def chat_general(request: ChatRequest) -> ChatResponse:
    """
    General chat about injection molding (no specific analysis).

    **Features:**
    - Grounded responses from knowledge base
    - Expert guidance on injection molding
    - No analysis context required

    **Parameters:**
    - `message`: User's question
    - `history`: Optional conversation history

    **Returns:** AI response with sources

    **Example questions:**
    - "What is the minimum draft angle for ABS?"
    - "How do I prevent sink marks?"
    - "What's the difference between GD&T perpendicularity and parallelism?"
    - "Best practices for ribs in injection molding?"
    """
    try:
        if not settings.enable_chat:
            raise HTTPException(
                status_code=503,
                detail="Chat feature is currently disabled"
            )

        if not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )

        logger.info(
            "general_chat_request",
            message_length=len(request.message),
            history_length=len(request.history)
        )

        # Use chat service
        chat_service = ChatService()
        response = await chat_service.chat_without_analysis(
            message=request.message,
            history=request.history
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("general_chat_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("", response_model=ChatResponse)
async def unified_chat(request: ChatRequest) -> ChatResponse:
    """
    Unified chat endpoint - Combines PDF analysis + RAG chat in single interface.
    
    **Features:**
    - Handles both text chat and PDF upload in one flow
    - PDF analysis + chat with analysis context + RAG grounding
    - General chat with RAG grounding (no PDF)
    - Context-aware responses
    
    **Parameters:**
    - `message`: User's message
    - `history`: Conversation history for context
    - Optional file upload for PDF analysis
    
    **Returns:** AI response with sources and analysis context
    """
    try:
        if not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )

        logger.info(
            "unified_chat_request",
            message_length=len(request.message),
            history_length=len(request.history),
            has_file=request.file is not None
        )

        # Use chat service
        chat_service = ChatService()
        response = await chat_service.unified_chat(
            message=request.message,
            history=request.history,
            file=request.file  # This will be handled by FastAPI file upload
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("unified_chat_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

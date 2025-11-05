"""
Configuration API endpoints.
Allows runtime configuration of prompts and system settings.
"""
from fastapi import APIRouter, HTTPException, status
import structlog

from src.models.schemas import (
    PromptsConfigResponse,
    PromptConfig,
    UpdatePromptRequest,
    UpdatePromptResponse
)
from src.config.prompts import prompts_config

logger = structlog.get_logger()
router = APIRouter()


@router.get("/prompts", response_model=PromptsConfigResponse)
async def get_prompts_config():
    """
    Get current prompts configuration.

    Returns all configurable prompts used for PDF analysis.
    """
    try:
        all_prompts = prompts_config.get_all_prompts()

        return PromptsConfigResponse(
            pdf_extraction=PromptConfig(**all_prompts["pdf_extraction"]),
            kb_analysis=PromptConfig(**all_prompts["kb_analysis"]),
            unified_response=PromptConfig(**all_prompts["unified_response"])
        )
    except Exception as e:
        logger.error("get_prompts_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get prompts configuration: {str(e)}"
        )


@router.put("/prompts", response_model=UpdatePromptResponse)
async def update_prompt(request: UpdatePromptRequest):
    """
    Update a specific prompt.

    **Prompt keys:**
    - `pdf_extraction`: Prompt for extracting specs from PDF
    - `kb_analysis`: Prompt for analyzing with Knowledge Base
    - `unified_response`: Template for combining results
    """
    try:
        valid_keys = ["pdf_extraction", "kb_analysis", "unified_response"]

        if request.prompt_key not in valid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid prompt_key. Must be one of: {', '.join(valid_keys)}"
            )

        success = prompts_config.update_prompt(request.prompt_key, request.new_prompt)

        if success:
            logger.info(
                "prompt_updated",
                prompt_key=request.prompt_key,
                new_length=len(request.new_prompt)
            )
            return UpdatePromptResponse(
                success=True,
                message=f"Prompt '{request.prompt_key}' updated successfully",
                prompt_key=request.prompt_key
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to save updated prompt"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_prompt_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update prompt: {str(e)}"
        )


@router.post("/prompts/reset", response_model=UpdatePromptResponse)
async def reset_prompts_to_defaults():
    """
    Reset all prompts to default values.

    ⚠️ This will discard all custom modifications.
    """
    try:
        success = prompts_config.reset_to_defaults()

        if success:
            logger.info("prompts_reset_to_defaults")
            return UpdatePromptResponse(
                success=True,
                message="All prompts have been reset to default values",
                prompt_key="all"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset prompts"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("reset_prompts_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset prompts: {str(e)}"
        )

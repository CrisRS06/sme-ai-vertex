"""
Metrics API endpoints.
Provides insights into system performance and quality.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
import structlog

from src.services.metrics_service import get_metrics

logger = structlog.get_logger()
router = APIRouter()


@router.get("/summary")
async def get_metrics_summary(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    last_n_days: Optional[int] = Query(None, ge=1, le=365, description="Last N days")
):
    """
    Get aggregate metrics summary.

    **Metrics included:**
    - Analysis: processing times, costs, extraction counts, accuracy
    - Chat: response times, grounding percentage, costs
    - OCR: fallback usage, fields recovered

    **Filters:**
    - `start_date`: Start date (ISO format, e.g., 2024-01-01)
    - `end_date`: End date (ISO format)
    - `last_n_days`: Last N days (alternative to date range)

    **Returns:** Comprehensive metrics summary
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None

        if last_n_days:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=last_n_days)
        else:
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)

        logger.info(
            "metrics_summary_request",
            start_date=start_dt.isoformat() if start_dt else None,
            end_date=end_dt.isoformat() if end_dt else None
        )

        metrics_service = get_metrics()
        summary = metrics_service.get_summary_metrics(start_dt, end_dt)

        return summary

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error("get_metrics_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/analysis/{analysis_id}")
async def get_analysis_metrics(analysis_id: str):
    """
    Get detailed metrics for a specific analysis.

    **Returns:** All tracked metrics for the analysis including:
    - Processing times (VLM, exception engine, reports)
    - Costs (total, VLM, embeddings)
    - Token usage
    - Extraction counts (dimensions, GD&T, notes)
    - Quality metrics (confidence, bbox coverage)
    - Exception breakdown by severity
    """
    try:
        logger.info("get_analysis_metrics", analysis_id=analysis_id)

        metrics_service = get_metrics()
        metrics = metrics_service.get_analysis_metrics(analysis_id)

        if not metrics:
            raise HTTPException(
                status_code=404,
                detail="Metrics not found for this analysis"
            )

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_analysis_metrics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/dashboard")
async def get_dashboard_metrics():
    """
    Get key metrics for dashboard display.

    **Returns:** High-level KPIs for last 7, 30, and all-time:
    - Total analyses
    - Average cost per analysis
    - Average processing time
    - Critical exceptions rate
    - Chat grounding percentage
    - OCR fallback rate
    """
    try:
        logger.info("dashboard_metrics_request")

        metrics_service = get_metrics()

        # Get metrics for different periods
        last_7_days = metrics_service.get_summary_metrics(
            start_date=datetime.now() - timedelta(days=7)
        )

        last_30_days = metrics_service.get_summary_metrics(
            start_date=datetime.now() - timedelta(days=30)
        )

        all_time = metrics_service.get_summary_metrics()

        return {
            "last_7_days": last_7_days,
            "last_30_days": last_30_days,
            "all_time": all_time,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error("get_dashboard_metrics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard metrics: {str(e)}")

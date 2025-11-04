"""
Analysis API endpoints.
Handles upload and analysis of technical drawings.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, status
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import structlog

from src.models.schemas import (
    AnalysisUploadResponse,
    AnalysisInfo,
    AnalysisStatus,
    ReportResponse,
    ReportType
)
from src.config.settings import settings

logger = structlog.get_logger()
router = APIRouter()


from src.services.drawing_processor import DrawingProcessor
from src.services.drawing_analyzer import DrawingAnalyzer
from src.services.exception_engine import ExceptionEngine
from src.services.report_generator import ReportGenerator
from src.services.sqlite_db import get_db
from src.services.metrics_service import get_metrics
import asyncio
import time


async def process_drawing_analysis(
    analysis_id: str,
    pdf_content: bytes,
    filename: str,
    project_name: Optional[str],
    quality_mode: str
):
    """
    Complete drawing analysis pipeline (runs async in background).

    Pipeline:
    1. Process PDF → PNG images + embeddings
    2. Analyze with Gemini 2.5 VLM
    3. Validate with Exception Engine
    4. Generate reports (Executive + Detailed)
    5. Update database with results
    """
    db = get_db()
    start_time = time.time()

    # Timing trackers
    vlm_time = 0
    exception_time = 0
    report_time = 0

    try:
        # Update status to processing
        analysis = db.get_analysis(analysis_id)
        if analysis:
            analysis.status = AnalysisStatus.PROCESSING
            analysis.started_at = datetime.now()
            db.save_analysis(analysis)

        logger.info("starting_analysis_pipeline", analysis_id=analysis_id)

        # Step 1: Process drawing (PDF → PNG + embeddings)
        processor = DrawingProcessor()
        gcs_uris, embeddings = await processor.process_drawing(
            analysis_id=analysis_id,
            pdf_content=pdf_content,
            filename=filename
        )

        logger.info(
            "drawing_processed",
            analysis_id=analysis_id,
            pages=len(gcs_uris)
        )

        # Step 2: Analyze with VLM (with OCR fallback if needed)
        vlm_start = time.time()
        analyzer = DrawingAnalyzer()
        drawing_analysis = await analyzer.analyze_drawing_from_pdf(
            pdf_content=pdf_content,
            analysis_id=analysis_id  # Pass for OCR metrics tracking
        )
        vlm_time = time.time() - vlm_start

        logger.info(
            "drawing_analyzed",
            analysis_id=analysis_id,
            dimensions=len(drawing_analysis.dimensions),
            gdandt=len(drawing_analysis.gdandt),
            vlm_time=vlm_time
        )

        # Step 3: Validate with Exception Engine
        exception_start = time.time()
        engine = ExceptionEngine()
        exception_report = engine.validate_analysis(
            analysis=drawing_analysis,
            analysis_id=analysis_id
        )
        exception_time = time.time() - exception_start

        logger.info(
            "exceptions_generated",
            analysis_id=analysis_id,
            total_exceptions=len(exception_report.exceptions),
            critical=exception_report.summary.critical_count,
            exception_time=exception_time
        )

        # Step 4: Generate reports
        report_start = time.time()
        report_gen = ReportGenerator()
        executive_uri, detailed_uri = await report_gen.generate_both_reports(
            analysis_id=analysis_id,
            drawing_analysis=drawing_analysis,
            exception_report=exception_report
        )
        report_time = time.time() - report_start

        # Generate signed URLs (valid for 1 hour)
        executive_url = report_gen.get_signed_url(executive_uri, expiration_hours=1)
        detailed_url = report_gen.get_signed_url(detailed_uri, expiration_hours=1)

        logger.info(
            "reports_generated",
            analysis_id=analysis_id,
            executive=executive_uri,
            detailed=detailed_uri,
            report_time=report_time
        )

        # Step 5: Update database with results
        analysis = db.get_analysis(analysis_id)
        if analysis:
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.now()
            analysis.exception_count = len(exception_report.exceptions)
            analysis.executive_report_url = executive_url
            analysis.detailed_report_url = detailed_url

            # Store GCS URIs in metadata for regenerating signed URLs
            analysis.metadata["executive_report_gcs_uri"] = executive_uri
            analysis.metadata["detailed_report_gcs_uri"] = detailed_uri
            analysis.metadata["processed_images_gcs_uris"] = gcs_uris

            db.save_analysis(analysis)

        # Step 6: Track metrics
        total_time = time.time() - start_time

        # Calculate extraction metrics
        dimensions_with_bbox = sum(1 for d in drawing_analysis.dimensions if d.bbox)
        gdandt_with_bbox = sum(1 for g in drawing_analysis.gdandt if g.frame_bbox)
        total_fields = len(drawing_analysis.dimensions) + len(drawing_analysis.gdandt)
        fields_with_bbox = dimensions_with_bbox + gdandt_with_bbox
        bbox_pct = (fields_with_bbox / total_fields * 100) if total_fields > 0 else 0

        # Calculate average confidence
        dim_confidences = [d.confidence for d in drawing_analysis.dimensions if d.confidence is not None]
        avg_dim_confidence = sum(dim_confidences) / len(dim_confidences) if dim_confidences else None

        gdandt_confidences = [g.confidence for g in drawing_analysis.gdandt if g.confidence is not None]
        avg_gdandt_confidence = sum(gdandt_confidences) / len(gdandt_confidences) if gdandt_confidences else None

        # Count tolerances
        tolerances_count = sum(1 for d in drawing_analysis.dimensions if d.tolerance)

        # Exception by severity
        exceptions_by_severity = {
            'critical': exception_report.summary.critical_count,
            'high': exception_report.summary.high_count,
            'medium': exception_report.summary.medium_count,
            'low': exception_report.summary.low_count
        }

        # Estimate tokens (rough approximation)
        # Each page typically uses ~2000-3000 input tokens, ~1000 output tokens
        input_tokens = len(gcs_uris) * 2500
        output_tokens = len(drawing_analysis.dimensions) * 50 + len(drawing_analysis.gdandt) * 60

        metrics_service = get_metrics()
        metrics_service.track_analysis(
            analysis_id=analysis_id,
            processing_time=total_time,
            vlm_time=vlm_time,
            exception_time=exception_time,
            report_time=report_time,
            dimensions_count=len(drawing_analysis.dimensions),
            gdandt_count=len(drawing_analysis.gdandt),
            notes_count=len(drawing_analysis.notes),
            tolerances_count=tolerances_count,
            exceptions_by_severity=exceptions_by_severity,
            avg_dimension_confidence=avg_dim_confidence,
            avg_gdandt_confidence=avg_gdandt_confidence,
            fields_with_bbox_pct=bbox_pct,
            vlm_model=settings.vertex_ai_model_pro if quality_mode == "pro" else settings.vertex_ai_model_flash,
            quality_mode=quality_mode,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            metadata={
                "filename": filename,
                "pages": len(gcs_uris),
                "project_name": project_name
            }
        )

        logger.info("analysis_pipeline_completed", analysis_id=analysis_id, total_time=total_time)

    except Exception as e:
        logger.error(
            "analysis_pipeline_failed",
            error=str(e),
            analysis_id=analysis_id
        )

        # Update status to failed
        analysis = db.get_analysis(analysis_id)
        if analysis:
            analysis.status = AnalysisStatus.FAILED
            analysis.completed_at = datetime.now()
            db.save_analysis(analysis)


@router.post("/upload", response_model=AnalysisUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_drawing(
    file: UploadFile = File(...),
    project_name: Optional[str] = Form(None),
    include_quality_manual: bool = Form(False),
    quality_mode: str = Form("flash"),
) -> AnalysisUploadResponse:
    """
    Upload a technical drawing for feasibility analysis.

    **Process:**
    1. Upload drawing to Cloud Storage
    2. Convert PDF → PNG (300 DPI) per page
    3. Generate multimodal embeddings
    4. Retrieve similar pages from knowledge base
    5. Extract dimensions, GD&T, tolerances with Gemini 2.5
    6. Run Exception Engine (best practices validation)
    7. Generate Executive & Detailed reports

    **Parameters:**
    - `file`: PDF drawing file
    - `project_name`: Optional project identifier
    - `include_quality_manual`: Include quality manual in analysis
    - `quality_mode`: `flash` (fast/cheap) or `pro` (accurate/expensive)

    **Returns:** Analysis ID and status
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Validate quality mode
        if quality_mode not in ["flash", "pro"]:
            raise HTTPException(status_code=400, detail="quality_mode must be 'flash' or 'pro'")

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

        analysis_id = str(uuid.uuid4())

        logger.info(
            "analysis_upload_started",
            analysis_id=analysis_id,
            filename=file.filename,
            project_name=project_name,
            quality_mode=quality_mode,
            size_bytes=file_size
        )

        # Create initial analysis record
        analysis_info = AnalysisInfo(
            analysis_id=analysis_id,
            status=AnalysisStatus.PENDING,
            project_name=project_name,
            drawing_filename=file.filename,
            uploaded_at=datetime.now(),
            quality_mode=quality_mode
        )

        # Save to database
        db = get_db()
        db.save_analysis(analysis_info)

        # Start async processing
        asyncio.create_task(
            process_drawing_analysis(
                analysis_id,
                content,
                file.filename,
                project_name,
                quality_mode
            )
        )

        return AnalysisUploadResponse(
            analysis_id=analysis_id,
            status=AnalysisStatus.PROCESSING,
            uploaded_at=datetime.now(),
            drawing_filename=file.filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("analysis_upload_failed", error=str(e), filename=file.filename)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/documents", response_model=List[AnalysisInfo])
async def list_analyses(
    status_filter: Optional[AnalysisStatus] = None,
    project_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[AnalysisInfo]:
    """
    List all analyses.

    **Filters:**
    - `status_filter`: Filter by analysis status
    - `project_name`: Filter by project name
    - `limit`: Maximum results (default: 100)
    - `offset`: Pagination offset
    """
    try:
        logger.info(
            "list_analyses",
            status=status_filter,
            project_name=project_name,
            limit=limit,
            offset=offset
        )

        # Get analyses from database
        db = get_db()
        analyses = db.list_analyses(status_filter, project_name, limit, offset)

        return analyses

    except Exception as e:
        logger.error("list_analyses_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list analyses: {str(e)}")


@router.get("/{analysis_id}", response_model=AnalysisInfo)
async def get_analysis(analysis_id: str) -> AnalysisInfo:
    """
    Get details about a specific analysis.

    **Returns:** Analysis status, metadata, exception count, report URLs
    """
    try:
        logger.info("get_analysis", analysis_id=analysis_id)

        # Get analysis from database
        db = get_db()
        analysis = db.get_analysis(analysis_id)

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_analysis_failed", error=str(e), analysis_id=analysis_id)
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


@router.get("/{analysis_id}/report", response_model=ReportResponse)
async def get_report(
    analysis_id: str,
    report_type: ReportType = ReportType.EXECUTIVE
) -> ReportResponse:
    """
    Get analysis report (Executive or Detailed).

    **Report Types:**
    - `executive`: Summary report for client sign-off (1-2 pages)
      - Exception count by severity
      - Critical issues requiring changes
      - Sign-off section
    - `detailed`: Complete technical report (multi-page)
      - All dimensions with bboxes
      - All GD&T specifications
      - All exceptions with evidence
      - Best practice references

    **Returns:** Signed URL to report (PDF/HTML), expires in 1 hour
    """
    try:
        logger.info("get_report", analysis_id=analysis_id, report_type=report_type)

        # Get analysis from database
        db = get_db()
        analysis = db.get_analysis(analysis_id)

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Check if analysis is completed
        if analysis.status != AnalysisStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Analysis is not ready. Current status: {analysis.status}"
            )

        # Get appropriate report URL
        if report_type == ReportType.EXECUTIVE:
            report_url = analysis.executive_report_url
        else:  # ReportType.DETAILED
            report_url = analysis.detailed_report_url

        if not report_url:
            raise HTTPException(
                status_code=404,
                detail=f"{report_type} report not found. It may have expired."
            )

        # Regenerate signed URL if needed (since they expire in 1 hour)
        report_gen = ReportGenerator()

        # Extract GCS URI from the stored URL or metadata
        if report_type == ReportType.EXECUTIVE:
            gcs_uri = analysis.metadata.get("executive_report_gcs_uri")
        else:
            gcs_uri = analysis.metadata.get("detailed_report_gcs_uri")

        # Generate fresh signed URL (valid for 1 hour)
        if gcs_uri:
            fresh_url = report_gen.get_signed_url(gcs_uri, expiration_hours=1)
            report_url = fresh_url

        return ReportResponse(
            analysis_id=analysis_id,
            report_type=report_type,
            report_url=report_url,
            generated_at=analysis.completed_at,
            expires_at=datetime.now() + timedelta(hours=1)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_report_failed", error=str(e), analysis_id=analysis_id)
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(analysis_id: str):
    """
    Delete an analysis and its associated reports.

    **Warning:** This will remove all data including reports from storage.
    """
    try:
        logger.info("delete_analysis", analysis_id=analysis_id)

        # Get analysis from database
        db = get_db()
        analysis = db.get_analysis(analysis_id)

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Delete from database
        success = db.delete_analysis(analysis_id)

        if not success:
            raise HTTPException(status_code=404, detail="Failed to delete analysis")

        # TODO: Optionally delete from GCS
        # This could include:
        # - Processed PNG images (drawings bucket)
        # - Generated reports (reports bucket)
        # For now, we keep files in GCS for audit/backup purposes

        logger.info("analysis_deleted", analysis_id=analysis_id)

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_analysis_failed", error=str(e), analysis_id=analysis_id)
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis: {str(e)}")

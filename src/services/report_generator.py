"""
Report Generator Service (Simplified for Chat Unificado)
Generates Executive and Detailed feasibility reports from analysis results.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
import structlog
from jinja2 import Environment, FileSystemLoader

from google.cloud import storage

from src.models.drawing_analysis import DrawingAnalysis
from src.models.exceptions import ExceptionReport, ExceptionSeverity
from src.models.schemas import ReportType
from src.config.settings import settings
from src.config.gcp_clients import get_storage_client

logger = structlog.get_logger()


class ReportGenerator:
    """Service for generating feasibility reports in HTML format (simplified)."""

    def __init__(self):
        self.storage_client = get_storage_client()

        # Setup Jinja2 environment
        template_dir = settings.report_template_dir
        if not os.path.exists(template_dir):
            logger.warning("template_directory_not_found", dir=template_dir)
            # Try alternative path
            template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')

        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )

        logger.info("report_generator_initialized", template_dir=template_dir)

    def generate_executive_report(
        self,
        analysis_id: str,
        drawing_analysis: DrawingAnalysis,
        exception_report: ExceptionReport
    ) -> str:
        """
        Generate Executive Report (1-2 pages) for client sign-off.

        Args:
            analysis_id: Analysis identifier
            drawing_analysis: Drawing analysis results
            exception_report: Exception report

        Returns:
            GCS URI of generated report
        """
        try:
            logger.info(
                "generating_executive_report",
                analysis_id=analysis_id,
                part_id=drawing_analysis.part_id
            )

            # Prepare template context
            context = self._prepare_executive_context(
                analysis_id,
                drawing_analysis,
                exception_report
            )

            # Render HTML
            template = self.jinja_env.get_template('executive_report.html')
            html_content = template.render(**context)

            # Always use HTML format for simplified version
            report_content = html_content.encode('utf-8')
            filename = f"{analysis_id}_executive.html"
            content_type = "text/html"

            # Upload to GCS
            gcs_uri = self._upload_report(
                report_content,
                filename,
                content_type
            )

            logger.info(
                "executive_report_generated",
                analysis_id=analysis_id,
                gcs_uri=gcs_uri
            )

            return gcs_uri

        except Exception as e:
            logger.error(
                "executive_report_generation_failed",
                error=str(e),
                analysis_id=analysis_id
            )
            raise

    def generate_detailed_report(
        self,
        analysis_id: str,
        drawing_analysis: DrawingAnalysis,
        exception_report: ExceptionReport
    ) -> str:
        """
        Generate Detailed Report (multi-page) with complete analysis.

        Args:
            analysis_id: Analysis identifier
            drawing_analysis: Drawing analysis results
            exception_report: Exception report

        Returns:
            GCS URI of generated report
        """
        try:
            logger.info(
                "generating_detailed_report",
                analysis_id=analysis_id,
                part_id=drawing_analysis.part_id
            )

            # Prepare template context
            context = self._prepare_detailed_context(
                analysis_id,
                drawing_analysis,
                exception_report
            )

            # Render HTML
            template = self.jinja_env.get_template('detailed_report.html')
            html_content = template.render(**context)

            # Always use HTML format for simplified version
            report_content = html_content.encode('utf-8')
            filename = f"{analysis_id}_detailed.html"
            content_type = "text/html"

            # Upload to GCS
            gcs_uri = self._upload_report(
                report_content,
                filename,
                content_type
            )

            logger.info(
                "detailed_report_generated",
                analysis_id=analysis_id,
                gcs_uri=gcs_uri
            )

            return gcs_uri

        except Exception as e:
            logger.error(
                "detailed_report_generation_failed",
                error=str(e),
                analysis_id=analysis_id
            )
            raise

    def generate_teaser(
        self,
        analysis_id: str,
        drawing_analysis: DrawingAnalysis,
        exception_report: ExceptionReport
    ) -> str:
        """
        Generate One-Pager Teaser (single page) for quick quotation/decision.

        This is the lightweight summary for clients who want to know
        "Can we do it? What are the main concerns?" before committing
        to a full assessment.

        Args:
            analysis_id: Analysis identifier
            drawing_analysis: Drawing analysis results
            exception_report: Exception report

        Returns:
            GCS URI of generated teaser
        """
        try:
            logger.info(
                "generating_teaser_report",
                analysis_id=analysis_id,
                part_id=drawing_analysis.part_id
            )

            # Prepare template context
            context = self._prepare_teaser_context(
                analysis_id,
                drawing_analysis,
                exception_report
            )

            # Render HTML
            template = self.jinja_env.get_template('one_pager_teaser.html')
            html_content = template.render(**context)

            # Use HTML format
            report_content = html_content.encode('utf-8')
            filename = f"{analysis_id}_teaser.html"
            content_type = "text/html"

            # Upload to GCS
            gcs_uri = self._upload_report(
                report_content,
                filename,
                content_type
            )

            logger.info(
                "teaser_report_generated",
                analysis_id=analysis_id,
                gcs_uri=gcs_uri
            )

            return gcs_uri

        except Exception as e:
            logger.error(
                "teaser_report_generation_failed",
                error=str(e),
                analysis_id=analysis_id
            )
            raise

    def _prepare_teaser_context(
        self,
        analysis_id: str,
        drawing: DrawingAnalysis,
        exceptions: ExceptionReport
    ) -> dict:
        """Prepare context dict for teaser template."""
        # Get top 5 most critical/important exceptions as highlights
        critical_exceptions = [
            e for e in exceptions.exceptions
            if e.severity == ExceptionSeverity.CRITICAL
        ]
        warning_exceptions = [
            e for e in exceptions.exceptions
            if e.severity == ExceptionSeverity.WARNING
        ]
        info_exceptions = [
            e for e in exceptions.exceptions
            if e.severity == ExceptionSeverity.INFO
        ]

        # Create highlights list (top 5 issues)
        highlights = []

        # Add all critical as highlights
        for exc in critical_exceptions[:3]:  # Top 3 critical
            highlights.append({
                "category": exc.category.value.replace('_', ' ').title(),
                "description": exc.title,
                "severity": "critical"
            })

        # Add top warnings
        for exc in warning_exceptions[:2]:  # Top 2 warnings
            highlights.append({
                "category": exc.category.value.replace('_', ' ').title(),
                "description": exc.title,
                "severity": "warning"
            })

        # If not enough highlights, add info items
        if len(highlights) < 5:
            for exc in info_exceptions[:5 - len(highlights)]:
                highlights.append({
                    "category": exc.category.value.replace('_', ' ').title(),
                    "description": exc.title,
                    "severity": "info"
                })

        return {
            # Analysis metadata
            "analysis_id": analysis_id,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "generated_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            # Part info
            "part_id": drawing.part_id or "N/A",
            "part_name": drawing.part_name or "N/A",
            "material": drawing.material or "Not Specified",
            "project_name": "Injection Molding Feasibility",

            # Summary counts
            "total_exceptions": exceptions.summary.total_exceptions,
            "total_critical": exceptions.summary.critical_count,
            "total_warnings": exceptions.summary.warning_count,
            "total_info": exceptions.summary.info_count,

            # Highlights for quick view
            "highlights": highlights,
            "show_stats": True,  # Always show stats in teaser
        }

    def _prepare_executive_context(
        self,
        analysis_id: str,
        drawing: DrawingAnalysis,
        exceptions: ExceptionReport
    ) -> dict:
        """Prepare context dict for executive report template."""
        critical_exceptions = [
            e for e in exceptions.exceptions
            if e.severity == ExceptionSeverity.CRITICAL
        ]

        warning_exceptions = [
            e for e in exceptions.exceptions
            if e.severity == ExceptionSeverity.WARNING
        ]

        return {
            # Analysis metadata
            "analysis_id": analysis_id,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            # Part info
            "part_id": drawing.part_id,
            "part_name": drawing.part_name,
            "material": drawing.material,

            # Summary
            "executive_summary": exceptions.executive_summary,
            "can_proceed": exceptions.summary.can_proceed,
            "risk_level": exceptions.summary.overall_risk_level,

            # Counts
            "total_exceptions": exceptions.summary.total_exceptions,
            "critical_count": exceptions.summary.critical_count,
            "warning_count": exceptions.summary.warning_count,
            "info_count": exceptions.summary.info_count,

            # Exception lists
            "critical_exceptions": critical_exceptions,
            "warning_exceptions": warning_exceptions,
        }

    def _prepare_detailed_context(
        self,
        analysis_id: str,
        drawing: DrawingAnalysis,
        exceptions: ExceptionReport
    ) -> dict:
        """Prepare context dict for detailed report template."""
        return {
            # Analysis metadata
            "analysis_id": analysis_id,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "quality_mode": settings.quality_mode,

            # Part info
            "part_id": drawing.part_id,
            "part_name": drawing.part_name,
            "material": drawing.material,
            "material_grade": drawing.material_grade,
            "page_count": drawing.page_count,

            # Summary
            "executive_summary": exceptions.executive_summary,
            "can_proceed": exceptions.summary.can_proceed,
            "risk_level": exceptions.summary.overall_risk_level,

            # Counts
            "total_exceptions": exceptions.summary.total_exceptions,
            "critical_count": exceptions.summary.critical_count,
            "warning_count": exceptions.summary.warning_count,
            "info_count": exceptions.summary.info_count,

            # Complete data
            "exceptions": exceptions.exceptions,
            "dimensions": drawing.dimensions,
            "gdandt": drawing.gdandt,
            "surface_finishes": drawing.surface_finishes,
            "notes": drawing.notes,
            "action_items": exceptions.action_items,
        }

    def _html_to_pdf(self, html_content: str) -> bytes:
        """Convert HTML to PDF - Simplified version returns HTML bytes."""
        logger.warning("pdf_generation_not_supported", using_html_fallback=True)
        return html_content.encode('utf-8')

    def _upload_report(
        self,
        content: bytes,
        filename: str,
        content_type: str
    ) -> str:
        """
        Upload report to Cloud Storage.

        Args:
            content: Report content bytes
            filename: Filename for the report
            content_type: MIME type

        Returns:
            GCS URI
        """
        try:
            bucket = self.storage_client.bucket(settings.gcs_bucket_reports)
            blob = bucket.blob(filename)

            # Upload with metadata
            blob.metadata = {
                "generated_at": datetime.now().isoformat(),
                "generator": "SME AI Vertex v0.1.0"
            }

            blob.upload_from_string(content, content_type=content_type)

            gcs_uri = f"gs://{settings.gcs_bucket_reports}/{filename}"

            logger.info(
                "report_uploaded",
                gcs_uri=gcs_uri,
                size_bytes=len(content)
            )

            return gcs_uri

        except Exception as e:
            logger.error("report_upload_failed", error=str(e), filename=filename)
            raise

    def get_signed_url(
        self,
        gcs_uri: str,
        expiration_hours: int = 1
    ) -> str:
        """
        Generate signed URL for report access.

        Args:
            gcs_uri: GCS URI (gs://bucket/path)
            expiration_hours: URL expiration time in hours

        Returns:
            Signed URL
        """
        try:
            # Parse GCS URI
            parts = gcs_uri.replace("gs://", "").split("/", 1)
            bucket_name = parts[0]
            blob_path = parts[1]

            # Get blob
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="GET"
            )

            logger.info(
                "signed_url_generated",
                gcs_uri=gcs_uri,
                expiration_hours=expiration_hours
            )

            return url

        except Exception as e:
            logger.error("signed_url_generation_failed", error=str(e), gcs_uri=gcs_uri)
            raise

    async def generate_both_reports(
        self,
        analysis_id: str,
        drawing_analysis: DrawingAnalysis,
        exception_report: ExceptionReport
    ) -> tuple[str, str]:
        """
        Generate both Executive and Detailed reports.

        Args:
            analysis_id: Analysis identifier
            drawing_analysis: Drawing analysis results
            exception_report: Exception report

        Returns:
            Tuple of (executive_gcs_uri, detailed_gcs_uri)
        """
        try:
            logger.info("generating_both_reports", analysis_id=analysis_id)

            # Generate both reports
            executive_uri = self.generate_executive_report(
                analysis_id,
                drawing_analysis,
                exception_report
            )

            detailed_uri = self.generate_detailed_report(
                analysis_id,
                drawing_analysis,
                exception_report
            )

            logger.info(
                "both_reports_generated",
                analysis_id=analysis_id,
                executive=executive_uri,
                detailed=detailed_uri
            )

            return executive_uri, detailed_uri

        except Exception as e:
            logger.error("report_generation_failed", error=str(e), analysis_id=analysis_id)
            raise

    async def generate_all_reports(
        self,
        analysis_id: str,
        drawing_analysis: DrawingAnalysis,
        exception_report: ExceptionReport
    ) -> tuple[str, str, str]:
        """
        Generate all three report types: Teaser, Executive, and Detailed.

        This is the complete offering:
        - Teaser: One-page summary for quick decision
        - Executive: Client sign-off report
        - Detailed: Complete technical analysis

        Args:
            analysis_id: Analysis identifier
            drawing_analysis: Drawing analysis results
            exception_report: Exception report

        Returns:
            Tuple of (teaser_gcs_uri, executive_gcs_uri, detailed_gcs_uri)
        """
        try:
            logger.info("generating_all_reports", analysis_id=analysis_id)

            # Generate all three reports
            teaser_uri = self.generate_teaser(
                analysis_id,
                drawing_analysis,
                exception_report
            )

            executive_uri = self.generate_executive_report(
                analysis_id,
                drawing_analysis,
                exception_report
            )

            detailed_uri = self.generate_detailed_report(
                analysis_id,
                drawing_analysis,
                exception_report
            )

            logger.info(
                "all_reports_generated",
                analysis_id=analysis_id,
                teaser=teaser_uri,
                executive=executive_uri,
                detailed=detailed_uri
            )

            return teaser_uri, executive_uri, detailed_uri

        except Exception as e:
            logger.error("all_reports_generation_failed", error=str(e), analysis_id=analysis_id)
            raise

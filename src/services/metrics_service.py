"""
Metrics Service for tracking system performance.
Tracks accuracy, costs, response times, and coverage.
"""
import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import structlog
from contextlib import contextmanager

logger = structlog.get_logger()


class MetricsService:
    """
    Service for tracking and analyzing system metrics.

    Tracks:
    - Analysis performance (time, cost, token usage)
    - Extraction accuracy (dimensions, GD&T, coverage)
    - Exception quality (precision, recall)
    - Grounding quality (% grounded responses)
    """

    def __init__(self, db_path: str = "data/metrics.db"):
        """
        Initialize metrics service.

        Args:
            db_path: Path to metrics database
        """
        self.db_path = db_path

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema
        self._init_schema()

        logger.info("metrics_service_initialized", db_path=db_path)

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("metrics_db_error", error=str(e))
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize metrics database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Analysis metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    -- Timing metrics
                    processing_time_seconds REAL,
                    vlm_time_seconds REAL,
                    exception_engine_time_seconds REAL,
                    report_generation_time_seconds REAL,

                    -- Cost metrics
                    total_cost_usd REAL,
                    vlm_cost_usd REAL,
                    embedding_cost_usd REAL,

                    -- Token usage
                    input_tokens INTEGER,
                    output_tokens INTEGER,

                    -- Extraction metrics
                    dimensions_extracted INTEGER,
                    gdandt_extracted INTEGER,
                    notes_extracted INTEGER,
                    tolerances_extracted INTEGER,

                    -- Quality metrics
                    avg_dimension_confidence REAL,
                    avg_gdandt_confidence REAL,
                    fields_with_bbox_pct REAL,

                    -- Exception metrics
                    total_exceptions INTEGER,
                    critical_exceptions INTEGER,
                    high_exceptions INTEGER,
                    medium_exceptions INTEGER,
                    low_exceptions INTEGER,

                    -- Model info
                    vlm_model TEXT,
                    quality_mode TEXT,

                    -- Additional data
                    metadata TEXT
                )
            """)

            # Chat metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    -- Timing
                    response_time_seconds REAL,

                    -- Cost
                    cost_usd REAL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,

                    -- Quality
                    grounded BOOLEAN,
                    sources_count INTEGER,
                    avg_source_relevance REAL,

                    -- Model
                    model TEXT,

                    -- Additional
                    metadata TEXT
                )
            """)

            # OCR fallback metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ocr_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    -- OCR usage
                    ocr_triggered BOOLEAN,
                    ocr_reason TEXT,

                    -- Results
                    fields_recovered INTEGER,
                    vlm_confidence_before REAL,
                    merged_confidence_after REAL,

                    -- Cost
                    ocr_cost_usd REAL,

                    -- Additional
                    metadata TEXT
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analysis_metrics_created
                ON analysis_metrics(created_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_metrics_created
                ON chat_metrics(created_at)
            """)

            logger.info("metrics_schema_initialized")

    # Analysis metrics

    def track_analysis(
        self,
        analysis_id: str,
        processing_time: float,
        vlm_time: float,
        exception_time: float,
        report_time: float,
        dimensions_count: int,
        gdandt_count: int,
        notes_count: int,
        tolerances_count: int,
        exceptions_by_severity: Dict[str, int],
        avg_dimension_confidence: float = None,
        avg_gdandt_confidence: float = None,
        fields_with_bbox_pct: float = None,
        vlm_model: str = None,
        quality_mode: str = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        metadata: Dict[str, Any] = None
    ):
        """
        Track analysis metrics.

        Args:
            analysis_id: Analysis ID
            processing_time: Total processing time (seconds)
            vlm_time: VLM analysis time
            exception_time: Exception engine time
            report_time: Report generation time
            dimensions_count: Number of dimensions extracted
            gdandt_count: Number of GD&T specs extracted
            notes_count: Number of notes extracted
            tolerances_count: Number of tolerances extracted
            exceptions_by_severity: Dict of severity -> count
            avg_dimension_confidence: Average confidence for dimensions
            avg_gdandt_confidence: Average confidence for GD&T
            fields_with_bbox_pct: Percentage of fields with bounding boxes
            vlm_model: Model used
            quality_mode: Quality mode (flash/pro)
            input_tokens: Input tokens used
            output_tokens: Output tokens used
            metadata: Additional metadata
        """
        try:
            # Calculate costs (approximate)
            # Gemini 2.0 Flash: $0.075 / 1M input, $0.30 / 1M output
            # Gemini 1.5 Pro: $1.25 / 1M input, $5.00 / 1M output
            if quality_mode == "pro":
                vlm_cost = (input_tokens / 1_000_000 * 1.25) + (output_tokens / 1_000_000 * 5.00)
            else:  # flash
                vlm_cost = (input_tokens / 1_000_000 * 0.075) + (output_tokens / 1_000_000 * 0.30)

            # Embedding cost (multimodal embeddings): $0.025 / 1000 images
            embedding_cost = 0.025 * (1 / 1000)  # Approximate per page

            total_cost = vlm_cost + embedding_cost

            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO analysis_metrics
                    (analysis_id, processing_time_seconds, vlm_time_seconds,
                     exception_engine_time_seconds, report_generation_time_seconds,
                     total_cost_usd, vlm_cost_usd, embedding_cost_usd,
                     input_tokens, output_tokens,
                     dimensions_extracted, gdandt_extracted, notes_extracted, tolerances_extracted,
                     avg_dimension_confidence, avg_gdandt_confidence, fields_with_bbox_pct,
                     total_exceptions, critical_exceptions, high_exceptions,
                     medium_exceptions, low_exceptions,
                     vlm_model, quality_mode, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id, processing_time, vlm_time, exception_time, report_time,
                    total_cost, vlm_cost, embedding_cost,
                    input_tokens, output_tokens,
                    dimensions_count, gdandt_count, notes_count, tolerances_count,
                    avg_dimension_confidence, avg_gdandt_confidence, fields_with_bbox_pct,
                    sum(exceptions_by_severity.values()),
                    exceptions_by_severity.get('critical', 0),
                    exceptions_by_severity.get('high', 0),
                    exceptions_by_severity.get('medium', 0),
                    exceptions_by_severity.get('low', 0),
                    vlm_model, quality_mode,
                    json.dumps(metadata) if metadata else None
                ))

                logger.info(
                    "analysis_metrics_tracked",
                    analysis_id=analysis_id,
                    total_cost=total_cost,
                    processing_time=processing_time
                )

        except Exception as e:
            logger.error("track_analysis_failed", error=str(e))
            raise

    def track_chat(
        self,
        analysis_id: Optional[str],
        response_time: float,
        grounded: bool,
        sources_count: int,
        avg_source_relevance: float = None,
        model: str = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        metadata: Dict[str, Any] = None
    ):
        """Track chat interaction metrics."""
        try:
            # Gemini Flash cost
            cost = (input_tokens / 1_000_000 * 0.075) + (output_tokens / 1_000_000 * 0.30)

            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO chat_metrics
                    (analysis_id, response_time_seconds, cost_usd, input_tokens, output_tokens,
                     grounded, sources_count, avg_source_relevance, model, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id, response_time, cost, input_tokens, output_tokens,
                    grounded, sources_count, avg_source_relevance, model,
                    json.dumps(metadata) if metadata else None
                ))

                logger.info("chat_metrics_tracked", grounded=grounded, sources=sources_count)

        except Exception as e:
            logger.error("track_chat_failed", error=str(e))

    def track_ocr_fallback(
        self,
        analysis_id: str,
        page_number: int,
        ocr_triggered: bool,
        ocr_reason: str,
        fields_recovered: int = 0,
        vlm_confidence_before: float = None,
        merged_confidence_after: float = None,
        ocr_cost: float = None,
        metadata: Dict[str, Any] = None
    ):
        """Track OCR fallback usage."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO ocr_metrics
                    (analysis_id, page_number, ocr_triggered, ocr_reason,
                     fields_recovered, vlm_confidence_before, merged_confidence_after,
                     ocr_cost_usd, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id, page_number, ocr_triggered, ocr_reason,
                    fields_recovered, vlm_confidence_before, merged_confidence_after,
                    ocr_cost, json.dumps(metadata) if metadata else None
                ))

                logger.info("ocr_metrics_tracked", triggered=ocr_triggered, reason=ocr_reason)

        except Exception as e:
            logger.error("track_ocr_failed", error=str(e))

    # Aggregate metrics

    def get_summary_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get aggregate metrics summary."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Build date filter
                date_filter = ""
                params = []
                if start_date:
                    date_filter = " WHERE created_at >= ?"
                    params.append(start_date.isoformat())
                if end_date:
                    date_filter += " AND created_at <= ?" if date_filter else " WHERE created_at <= ?"
                    params.append(end_date.isoformat())

                # Analysis metrics
                cursor.execute(f"""
                    SELECT
                        COUNT(*) as total_analyses,
                        AVG(processing_time_seconds) as avg_processing_time,
                        SUM(total_cost_usd) as total_cost,
                        AVG(total_cost_usd) as avg_cost_per_analysis,
                        AVG(dimensions_extracted) as avg_dimensions,
                        AVG(gdandt_extracted) as avg_gdandt,
                        AVG(avg_dimension_confidence) as avg_dim_confidence,
                        AVG(fields_with_bbox_pct) as avg_bbox_coverage,
                        SUM(total_exceptions) as total_exceptions,
                        SUM(critical_exceptions) as critical_exceptions
                    FROM analysis_metrics
                    {date_filter}
                """, params)

                analysis_row = cursor.fetchone()

                # Chat metrics
                cursor.execute(f"""
                    SELECT
                        COUNT(*) as total_chats,
                        AVG(response_time_seconds) as avg_response_time,
                        SUM(cost_usd) as total_chat_cost,
                        AVG(CASE WHEN grounded = 1 THEN 1.0 ELSE 0.0 END) as grounded_pct,
                        AVG(sources_count) as avg_sources
                    FROM chat_metrics
                    {date_filter}
                """, params)

                chat_row = cursor.fetchone()

                # OCR metrics
                cursor.execute(f"""
                    SELECT
                        COUNT(*) as total_pages_processed,
                        SUM(CASE WHEN ocr_triggered = 1 THEN 1 ELSE 0 END) as ocr_triggered_count,
                        AVG(CASE WHEN ocr_triggered = 1 THEN 1.0 ELSE 0.0 END) as ocr_trigger_rate,
                        AVG(fields_recovered) as avg_fields_recovered
                    FROM ocr_metrics
                    {date_filter}
                """, params)

                ocr_row = cursor.fetchone()

                return {
                    "analysis": {
                        "total_analyses": analysis_row['total_analyses'] or 0,
                        "avg_processing_time_seconds": analysis_row['avg_processing_time'] or 0,
                        "total_cost_usd": analysis_row['total_cost'] or 0,
                        "avg_cost_per_analysis_usd": analysis_row['avg_cost_per_analysis'] or 0,
                        "avg_dimensions_extracted": analysis_row['avg_dimensions'] or 0,
                        "avg_gdandt_extracted": analysis_row['avg_gdandt'] or 0,
                        "avg_dimension_confidence": analysis_row['avg_dim_confidence'] or 0,
                        "avg_bbox_coverage_pct": analysis_row['avg_bbox_coverage'] or 0,
                        "total_exceptions": analysis_row['total_exceptions'] or 0,
                        "critical_exceptions": analysis_row['critical_exceptions'] or 0,
                    },
                    "chat": {
                        "total_chats": chat_row['total_chats'] or 0,
                        "avg_response_time_seconds": chat_row['avg_response_time'] or 0,
                        "total_cost_usd": chat_row['total_chat_cost'] or 0,
                        "grounded_percentage": (chat_row['grounded_pct'] or 0) * 100,
                        "avg_sources_per_response": chat_row['avg_sources'] or 0,
                    },
                    "ocr": {
                        "total_pages_processed": ocr_row['total_pages_processed'] or 0,
                        "ocr_triggered_count": ocr_row['ocr_triggered_count'] or 0,
                        "ocr_trigger_rate_pct": (ocr_row['ocr_trigger_rate'] or 0) * 100,
                        "avg_fields_recovered": ocr_row['avg_fields_recovered'] or 0,
                    },
                    "period": {
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None,
                    }
                }

        except Exception as e:
            logger.error("get_summary_metrics_failed", error=str(e))
            raise

    def get_analysis_metrics(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for specific analysis."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM analysis_metrics WHERE analysis_id = ?
                """, (analysis_id,))

                row = cursor.fetchone()

                if not row:
                    return None

                return dict(row)

        except Exception as e:
            logger.error("get_analysis_metrics_failed", error=str(e))
            return None


# Global instance
_metrics = None


def get_metrics() -> MetricsService:
    """Get singleton metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsService()
    return _metrics

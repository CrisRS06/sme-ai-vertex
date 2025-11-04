"""
SQLite database service for production use.
Provides persistent storage with better performance and ACID compliance.
"""
import sqlite3
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import structlog
from contextlib import contextmanager

from src.models.schemas import (
    DocumentInfo,
    DocumentType,
    DocumentStatus,
    AnalysisInfo,
    AnalysisStatus
)

logger = structlog.get_logger()


class SQLiteDB:
    """
    SQLite database for documents and analyses.

    Features:
    - ACID compliance
    - Relational structure
    - Better query performance
    - Concurrent access support
    """

    def __init__(self, db_path: str = "data/sme_ai.db"):
        """
        Initialize SQLite database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_schema()

        logger.info("sqlite_db_initialized", db_path=db_path)

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("database_error", error=str(e))
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize database schema if not exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    indexed_at TEXT,
                    page_count INTEGER,
                    metadata TEXT
                )
            """)

            # Analyses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    analysis_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    project_name TEXT,
                    drawing_filename TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    quality_mode TEXT NOT NULL,
                    exception_count INTEGER,
                    executive_report_url TEXT,
                    detailed_report_url TEXT,
                    metadata TEXT
                )
            """)

            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_type
                ON documents(document_type)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_status
                ON documents(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analyses_status
                ON analyses(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analyses_project
                ON analyses(project_name)
            """)

            logger.info("database_schema_initialized")

    # Document methods

    def save_document(self, doc_info: DocumentInfo):
        """Save or update a document."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO documents
                (document_id, filename, document_type, status, uploaded_at,
                 indexed_at, page_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_info.document_id,
                doc_info.filename,
                doc_info.document_type.value,
                doc_info.status.value,
                doc_info.uploaded_at.isoformat(),
                doc_info.indexed_at.isoformat() if doc_info.indexed_at else None,
                doc_info.page_count,
                json.dumps(doc_info.metadata)
            ))

            logger.info("document_saved_sqlite", document_id=doc_info.document_id)

    def get_document(self, document_id: str) -> Optional[DocumentInfo]:
        """Get a document by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM documents WHERE document_id = ?
            """, (document_id,))

            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_document(row)

    def list_documents(
        self,
        document_type: Optional[DocumentType] = None,
        status_filter: Optional[DocumentStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentInfo]:
        """List documents with optional filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM documents WHERE 1=1"
            params = []

            if document_type:
                query += " AND document_type = ?"
                params.append(document_type.value)

            if status_filter:
                query += " AND status = ?"
                params.append(status_filter.value)

            query += " ORDER BY uploaded_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)

            rows = cursor.fetchall()

            return [self._row_to_document(row) for row in rows]

    def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM documents WHERE document_id = ?
            """, (document_id,))

            deleted = cursor.rowcount > 0

            if deleted:
                logger.info("document_deleted_sqlite", document_id=document_id)

            return deleted

    def get_documents_stats(self) -> Dict[str, Any]:
        """Get statistics about documents."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total documents
            cursor.execute("SELECT COUNT(*) FROM documents")
            total = cursor.fetchone()[0]

            # Documents by type
            cursor.execute("""
                SELECT document_type, COUNT(*)
                FROM documents
                GROUP BY document_type
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # Total pages
            cursor.execute("""
                SELECT SUM(page_count)
                FROM documents
                WHERE page_count IS NOT NULL
            """)
            total_pages = cursor.fetchone()[0] or 0

            # Last updated
            cursor.execute("""
                SELECT MAX(uploaded_at)
                FROM documents
            """)
            last_updated = cursor.fetchone()[0]

            return {
                "total_documents": total,
                "documents_by_type": by_type,
                "total_pages_indexed": total_pages,
                "last_updated": datetime.fromisoformat(last_updated) if last_updated else None
            }

    # Analysis methods

    def save_analysis(self, analysis_info: AnalysisInfo):
        """Save or update an analysis."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO analyses
                (analysis_id, status, project_name, drawing_filename, uploaded_at,
                 started_at, completed_at, quality_mode, exception_count,
                 executive_report_url, detailed_report_url, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_info.analysis_id,
                analysis_info.status.value,
                analysis_info.project_name,
                analysis_info.drawing_filename,
                analysis_info.uploaded_at.isoformat(),
                analysis_info.started_at.isoformat() if analysis_info.started_at else None,
                analysis_info.completed_at.isoformat() if analysis_info.completed_at else None,
                analysis_info.quality_mode,
                analysis_info.exception_count,
                analysis_info.executive_report_url,
                analysis_info.detailed_report_url,
                json.dumps(analysis_info.metadata)
            ))

            logger.info("analysis_saved_sqlite", analysis_id=analysis_info.analysis_id)

    def get_analysis(self, analysis_id: str) -> Optional[AnalysisInfo]:
        """Get an analysis by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM analyses WHERE analysis_id = ?
            """, (analysis_id,))

            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_analysis(row)

    def list_analyses(
        self,
        status_filter: Optional[AnalysisStatus] = None,
        project_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AnalysisInfo]:
        """List analyses with optional filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM analyses WHERE 1=1"
            params = []

            if status_filter:
                query += " AND status = ?"
                params.append(status_filter.value)

            if project_name:
                query += " AND project_name = ?"
                params.append(project_name)

            query += " ORDER BY uploaded_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)

            rows = cursor.fetchall()

            return [self._row_to_analysis(row) for row in rows]

    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete an analysis by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM analyses WHERE analysis_id = ?
            """, (analysis_id,))

            deleted = cursor.rowcount > 0

            if deleted:
                logger.info("analysis_deleted_sqlite", analysis_id=analysis_id)

            return deleted

    # Helper methods

    def _row_to_document(self, row: sqlite3.Row) -> DocumentInfo:
        """Convert SQLite row to DocumentInfo."""
        return DocumentInfo(
            document_id=row['document_id'],
            filename=row['filename'],
            document_type=DocumentType(row['document_type']),
            status=DocumentStatus(row['status']),
            uploaded_at=datetime.fromisoformat(row['uploaded_at']),
            indexed_at=datetime.fromisoformat(row['indexed_at']) if row['indexed_at'] else None,
            page_count=row['page_count'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )

    def _row_to_analysis(self, row: sqlite3.Row) -> AnalysisInfo:
        """Convert SQLite row to AnalysisInfo."""
        return AnalysisInfo(
            analysis_id=row['analysis_id'],
            status=AnalysisStatus(row['status']),
            project_name=row['project_name'],
            drawing_filename=row['drawing_filename'],
            uploaded_at=datetime.fromisoformat(row['uploaded_at']),
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            quality_mode=row['quality_mode'],
            exception_count=row['exception_count'],
            executive_report_url=row['executive_report_url'],
            detailed_report_url=row['detailed_report_url'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )


# Global instance
_db = None


def get_db() -> SQLiteDB:
    """
    Get singleton database instance.

    Returns:
        SQLiteDB instance
    """
    global _db
    if _db is None:
        _db = SQLiteDB()
    return _db

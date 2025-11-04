"""
Simple JSON-based database for development.
Stores documents and analyses as JSON files.
Can be easily migrated to SQLite/PostgreSQL later.
"""
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from src.models.schemas import DocumentInfo, AnalysisInfo, DocumentType, DocumentStatus, AnalysisStatus

logger = structlog.get_logger()


class SimpleDB:
    """Simple JSON file-based database."""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.documents_file = os.path.join(data_dir, "documents.json")
        self.analyses_file = os.path.join(data_dir, "analyses.json")

        # Create data directory if not exists
        os.makedirs(data_dir, exist_ok=True)

        # Initialize files if they don't exist
        self._init_files()

        logger.info("simple_db_initialized", data_dir=data_dir)

    def _init_files(self):
        """Initialize JSON files if they don't exist."""
        if not os.path.exists(self.documents_file):
            with open(self.documents_file, 'w') as f:
                json.dump([], f)

        if not os.path.exists(self.analyses_file):
            with open(self.analyses_file, 'w') as f:
                json.dump([], f)

    def _read_documents(self) -> List[Dict]:
        """Read all documents from file."""
        try:
            with open(self.documents_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error("read_documents_failed", error=str(e))
            return []

    def _write_documents(self, documents: List[Dict]):
        """Write all documents to file."""
        try:
            with open(self.documents_file, 'w') as f:
                json.dump(documents, f, indent=2, default=str)
        except Exception as e:
            logger.error("write_documents_failed", error=str(e))
            raise

    def _read_analyses(self) -> List[Dict]:
        """Read all analyses from file."""
        try:
            with open(self.analyses_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error("read_analyses_failed", error=str(e))
            return []

    def _write_analyses(self, analyses: List[Dict]):
        """Write all analyses to file."""
        try:
            with open(self.analyses_file, 'w') as f:
                json.dump(analyses, f, indent=2, default=str)
        except Exception as e:
            logger.error("write_analyses_failed", error=str(e))
            raise

    # Document operations
    def save_document(self, doc_info: DocumentInfo):
        """Save or update a document."""
        documents = self._read_documents()

        # Convert to dict
        doc_dict = doc_info.model_dump(mode='json')

        # Check if exists
        existing_idx = None
        for idx, doc in enumerate(documents):
            if doc.get('document_id') == doc_info.document_id:
                existing_idx = idx
                break

        if existing_idx is not None:
            documents[existing_idx] = doc_dict
        else:
            documents.append(doc_dict)

        self._write_documents(documents)
        logger.info("document_saved", document_id=doc_info.document_id)

    def get_document(self, document_id: str) -> Optional[DocumentInfo]:
        """Get a document by ID."""
        documents = self._read_documents()
        for doc in documents:
            if doc.get('document_id') == document_id:
                return DocumentInfo(**doc)
        return None

    def list_documents(
        self,
        document_type: Optional[DocumentType] = None,
        status_filter: Optional[DocumentStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentInfo]:
        """List documents with optional filters."""
        documents = self._read_documents()

        # Apply filters
        filtered = documents
        if document_type:
            filtered = [d for d in filtered if d.get('document_type') == document_type.value]
        if status_filter:
            filtered = [d for d in filtered if d.get('status') == status_filter.value]

        # Apply pagination
        filtered = filtered[offset:offset + limit]

        # Convert to models
        return [DocumentInfo(**doc) for doc in filtered]

    def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID."""
        documents = self._read_documents()
        original_len = len(documents)

        documents = [d for d in documents if d.get('document_id') != document_id]

        if len(documents) < original_len:
            self._write_documents(documents)
            logger.info("document_deleted", document_id=document_id)
            return True

        return False

    def get_documents_stats(self) -> Dict[str, Any]:
        """Get statistics about documents."""
        documents = self._read_documents()

        stats = {
            "total_documents": len(documents),
            "documents_by_type": {},
            "total_pages_indexed": 0,
            "last_updated": None
        }

        for doc in documents:
            doc_type = doc.get('document_type', 'unknown')
            stats["documents_by_type"][doc_type] = stats["documents_by_type"].get(doc_type, 0) + 1

            page_count = doc.get('page_count', 0)
            if page_count:
                stats["total_pages_indexed"] += page_count

            indexed_at = doc.get('indexed_at')
            if indexed_at:
                if not stats["last_updated"] or indexed_at > stats["last_updated"]:
                    stats["last_updated"] = indexed_at

        return stats

    # Analysis operations
    def save_analysis(self, analysis_info: AnalysisInfo):
        """Save or update an analysis."""
        analyses = self._read_analyses()

        # Convert to dict
        analysis_dict = analysis_info.model_dump(mode='json')

        # Check if exists
        existing_idx = None
        for idx, analysis in enumerate(analyses):
            if analysis.get('analysis_id') == analysis_info.analysis_id:
                existing_idx = idx
                break

        if existing_idx is not None:
            analyses[existing_idx] = analysis_dict
        else:
            analyses.append(analysis_dict)

        self._write_analyses(analyses)
        logger.info("analysis_saved", analysis_id=analysis_info.analysis_id)

    def get_analysis(self, analysis_id: str) -> Optional[AnalysisInfo]:
        """Get an analysis by ID."""
        analyses = self._read_analyses()
        for analysis in analyses:
            if analysis.get('analysis_id') == analysis_id:
                return AnalysisInfo(**analysis)
        return None

    def list_analyses(
        self,
        status_filter: Optional[AnalysisStatus] = None,
        project_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AnalysisInfo]:
        """List analyses with optional filters."""
        analyses = self._read_analyses()

        # Apply filters
        filtered = analyses
        if status_filter:
            filtered = [a for a in filtered if a.get('status') == status_filter.value]
        if project_name:
            filtered = [a for a in filtered if a.get('project_name') == project_name]

        # Apply pagination
        filtered = filtered[offset:offset + limit]

        # Convert to models
        return [AnalysisInfo(**analysis) for analysis in filtered]

    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete an analysis by ID."""
        analyses = self._read_analyses()
        original_len = len(analyses)

        analyses = [a for a in analyses if a.get('analysis_id') != analysis_id]

        if len(analyses) < original_len:
            self._write_analyses(analyses)
            logger.info("analysis_deleted", analysis_id=analysis_id)
            return True

        return False


# Global instance
_db = None


def get_db() -> SimpleDB:
    """Get global database instance."""
    global _db
    if _db is None:
        _db = SimpleDB()
    return _db

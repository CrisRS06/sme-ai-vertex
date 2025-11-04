"""
Queued Knowledge Base Service
Handles document imports with queuing system to avoid RAG Engine concurrency limits.
"""
import asyncio
import json
import uuid
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import structlog
import sqlite3

from google.cloud import pubsub_v1
from google.api_core import exceptions
from vertexai.preview import rag

from src.config.settings import settings
from src.models.schemas import DocumentType, DocumentStatus, DocumentInfo
from src.services.knowledge_base import KnowledgeBaseService

logger = structlog.get_logger()


class ImportJobStatus:
    """Status tracking for import jobs."""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class QueuedKnowledgeBaseService:
    """
    Knowledge Base service with queuing system for concurrent imports.
    
    Prevents RAG Engine's 3 concurrent import limit by using Pub/Sub.
    """

    def __init__(self):
        self.kb_service = KnowledgeBaseService()
        self.db_path = "data/import_jobs.db"
        self.max_concurrent_imports = 2  # Conservative limit
        
        # Initialize Pub/Sub
        self.publisher = None
        self.subscriber = None
        self._init_pubsub()
        
        # Initialize database for job tracking
        self._init_job_db()
        
        logger.info(
            "queued_kb_initialized",
            max_concurrent=self.max_concurrent_imports
        )

    def _init_pubsub(self):
        """Initialize Pub/Sub clients."""
        try:
            self.publisher = pubsub_v1.PublisherClient()
            self.subscriber = pubsub_v1.SubscriberClient()
            
            # Define topic and subscription names
            self.topic_path = self.publisher.topic_path(
                settings.gcp_project_id, 
                "rag-import-jobs"
            )
            self.subscription_path = self.subscriber.subscription_path(
                settings.gcp_project_id,
                "rag-import-jobs-sub"
            )
            
            logger.info("pubsub_initialized", 
                       topic=self.topic_path,
                       subscription=self.subscription_path)
                       
        except Exception as e:
            logger.error("pubsub_init_failed", error=str(e))
            raise

    def _init_job_db(self):
        """Initialize job tracking database."""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_jobs (
                job_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                gcs_uri TEXT NOT NULL,
                document_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_status 
            ON import_jobs(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_created 
            ON import_jobs(created_at)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("job_db_initialized", db_path=self.db_path)

    async def create_topic_and_subscription(self):
        """Create Pub/Sub topic and subscription if they don't exist."""
        try:
            # Create topic
            try:
                self.publisher.create_topic(name=self.topic_path)
                logger.info("pubsub_topic_created", topic=self.topic_path)
            except exceptions.AlreadyExists:
                logger.info("pubsub_topic_exists", topic=self.topic_path)
            
            # Create subscription
            try:
                self.subscriber.create_subscription(
                    name=self.subscription_path,
                    topic=self.topic_path
                )
                logger.info("pubsub_subscription_created", subscription=self.subscription_path)
            except exceptions.AlreadyExists:
                logger.info("pubsub_subscription_exists", subscription=self.subscription_path)
                
        except Exception as e:
            logger.error("pubsub_setup_failed", error=str(e))
            raise

    async def queue_document_import(
        self,
        document_id: str,
        gcs_uri: str,
        document_type: DocumentType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Queue a document import job for asynchronous processing.
        
        Args:
            document_id: Document identifier
            gcs_uri: GCS URI of the document
            document_type: Type of document
            metadata: Optional metadata
            
        Returns:
            Job information with queue status
        """
        job_id = str(uuid.uuid4())
        
        # Store job in database
        self._store_job(
            job_id=job_id,
            document_id=document_id,
            gcs_uri=gcs_uri,
            document_type=document_type.value,
            status=ImportJobStatus.PENDING,
            metadata=metadata
        )
        
        # Publish to Pub/Sub
        message = {
            "job_id": job_id,
            "document_id": document_id,
            "gcs_uri": gcs_uri,
            "document_type": document_type.value,
            "metadata": metadata or {}
        }
        
        try:
            future = self.publisher.publish(
                self.topic_path,
                json.dumps(message).encode('utf-8')
            )
            message_id = future.result()
            
            logger.info(
                "import_job_queued",
                job_id=job_id,
                document_id=document_id,
                message_id=message_id
            )
            
            return {
                "job_id": job_id,
                "status": ImportJobStatus.PENDING,
                "message": "Import job queued successfully",
                "queue_position": self._get_queue_position(job_id)
            }
            
        except Exception as e:
            logger.error("publish_job_failed", job_id=job_id, error=str(e))
            
            # Update job status to failed
            self._update_job_status(
                job_id, 
                ImportJobStatus.FAILED,
                error_message=str(e)
            )
            
            raise

    def _store_job(
        self,
        job_id: str,
        document_id: str,
        gcs_uri: str,
        document_type: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store job in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO import_jobs 
            (job_id, document_id, gcs_uri, document_type, status, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job_id, document_id, gcs_uri, document_type, status,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        conn.close()

    def _update_job_status(
        self,
        job_id: str,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        retry_count: Optional[int] = None
    ):
        """Update job status in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = ["status = ?"]
        values = [status]
        
        if started_at:
            updates.append("started_at = ?")
            values.append(started_at.isoformat())
            
        if completed_at:
            updates.append("completed_at = ?")
            values.append(completed_at.isoformat())
            
        if error_message:
            updates.append("error_message = ?")
            values.append(error_message)
            
        if retry_count is not None:
            updates.append("retry_count = ?")
            values.append(retry_count)
        
        values.append(job_id)
        
        query = f"""
            UPDATE import_jobs 
            SET {', '.join(updates)}
            WHERE job_id = ?
        """
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()

    def _get_queue_position(self, job_id: str) -> int:
        """Get queue position for a job."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM import_jobs 
            WHERE status IN (?, ?) 
            AND created_at < (
                SELECT created_at FROM import_jobs WHERE job_id = ?
            )
        """, (ImportJobStatus.PENDING, ImportJobStatus.RETRYING, job_id))
        
        position = cursor.fetchone()[0] + 1
        conn.close()
        
        return position

    async def process_import_jobs(self, max_workers: int = None):
        """
        Process queued import jobs in background.
        Should be run as a background task.
        
        Args:
            max_workers: Maximum concurrent processing jobs
        """
        if max_workers is None:
            max_workers = self.max_concurrent_imports
        
        logger.info("starting_job_processor", max_workers=max_workers)
        
        while True:
            try:
                # Get pending jobs
                pending_jobs = self._get_pending_jobs(max_workers)
                
                if not pending_jobs:
                    await asyncio.sleep(5)  # Wait if no jobs
                    continue
                
                # Process jobs concurrently
                tasks = []
                for job in pending_jobs:
                    task = asyncio.create_task(
                        self._process_single_job(job)
                    )
                    tasks.append(task)
                
                # Wait for completion
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
            except Exception as e:
                logger.error("job_processor_error", error=str(e))
                await asyncio.sleep(10)

    def _get_pending_jobs(self, limit: int) -> List[Dict[str, Any]]:
        """Get pending jobs to process."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM import_jobs 
            WHERE status = ? 
            ORDER BY created_at ASC 
            LIMIT ?
        """, (ImportJobStatus.PENDING, limit))
        
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jobs

    async def _process_single_job(self, job: Dict[str, Any]):
        """Process a single import job."""
        job_id = job['job_id']
        
        try:
            logger.info("processing_job", job_id=job_id)
            
            # Update status to processing
            self._update_job_status(
                job_id, 
                ImportJobStatus.PROCESSING,
                started_at=datetime.now()
            )
            
            # Get corpus
            corpus = await self.kb_service.create_or_get_corpus()
            
            # Parse metadata
            metadata = json.loads(job['metadata']) if job['metadata'] else {}
            metadata.update({
                "job_id": job_id,
                "imported_via": "queued_system"
            })
            
            # Import file with retry logic
            success = await self._import_with_retry(
                corpus.name,
                [job['gcs_uri']],
                metadata,
                max_retries=3
            )
            
            if success:
                self._update_job_status(
                    job_id,
                    ImportJobStatus.COMPLETED,
                    completed_at=datetime.now()
                )
                logger.info("job_completed", job_id=job_id)
            else:
                raise Exception("Import failed after all retries")
                
        except Exception as e:
            logger.error("job_failed", job_id=job_id, error=str(e))
            self._update_job_status(
                job_id,
                ImportJobStatus.FAILED,
                completed_at=datetime.now(),
                error_message=str(e)
            )

    async def _import_with_retry(
        self,
        corpus_name: str,
        gcs_uris: List[str],
        metadata: Dict[str, Any],
        max_retries: int = 3
    ) -> bool:
        """Import files with retry logic."""
        for attempt in range(max_retries):
            try:
                # Use chunking configuration
                from vertexai.preview.rag import ChunkingConfig
                
                transformation_config = rag.TransformationConfig(
                    chunking_config=ChunkingConfig(
                        chunk_size=512,
                        chunk_overlap=100
                    )
                )
                
                # Attempt import
                response = rag.import_files(
                    corpus_name=corpus_name,
                    paths=gcs_uris,
                    transformation_config=transformation_config,
                    max_embedding_requests_per_min=900
                )
                
                # Check if successful
                if response.failed_rag_files_count == 0:
                    logger.info("import_successful", 
                               files_imported=response.imported_rag_files_count)
                    return True
                else:
                    logger.warning("import_partial_success",
                                 imported=response.imported_rag_files_count,
                                 failed=response.failed_rag_files_count)
                    return False
                    
            except Exception as e:
                logger.warning("import_attempt_failed",
                             attempt=attempt + 1,
                             max_retries=max_retries,
                             error=str(e))
                
                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    raise

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM import_jobs WHERE job_id = ?
        """, (job_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            job = dict(row)
            # Parse metadata
            if job['metadata']:
                job['metadata'] = json.loads(job['metadata'])
            return job
        
        return None

    def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List import jobs with optional status filter."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM import_jobs"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        jobs = []
        for row in rows:
            job = dict(row)
            if job['metadata']:
                job['metadata'] = json.loads(job['metadata'])
            jobs.append(job)
        
        return jobs

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        for status in [ImportJobStatus.PENDING, ImportJobStatus.PROCESSING, 
                      ImportJobStatus.COMPLETED, ImportJobStatus.FAILED]:
            cursor.execute(
                "SELECT COUNT(*) FROM import_jobs WHERE status = ?",
                (status,)
            )
            stats[status] = cursor.fetchone()[0]
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute(
            "SELECT COUNT(*) FROM import_jobs WHERE created_at > ?",
            (yesterday.isoformat(),)
        )
        stats['last_24h'] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats


# Global instance
_queued_kb = None


def get_queued_knowledge_base() -> QueuedKnowledgeBaseService:
    """Get singleton queued KB instance."""
    global _queued_kb
    if _queued_kb is None:
        _queued_kb = QueuedKnowledgeBaseService()
    return _queued_kb

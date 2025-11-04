"""
Knowledge Base Service
Gestiona la ingesta y el indexado de documentos de referencia en Vertex AI RAG Engine.
"""
import io
from typing import Optional, Dict, Any
from datetime import datetime

import PyPDF2
import structlog

from src.config.settings import settings
from src.config.gcp_clients import (
    get_storage_client,
    init_vertex_ai,
    get_rag_module,
)
from src.models.schemas import DocumentType, DocumentStatus, DocumentInfo

try:
    from vertexai.generative_models import Tool  # GA 2025
except ImportError:  # pragma: no cover - fallback previo
    from vertexai.preview.generative_models import Tool  # type: ignore

logger = structlog.get_logger()


class KnowledgeBaseService:
    """Service for managing the knowledge base of molding documents."""

    def __init__(self):
        self.storage_client = get_storage_client()
        init_vertex_ai()
        self.corpus_name = settings.rag_corpus_name

        try:
            self.rag = get_rag_module()
        except RuntimeError as exc:
            logger.error("rag_module_unavailable", error=str(exc))
            self.rag = None

    async def upload_to_storage(
        self,
        document_id: str,
        content: bytes,
        filename: str,
        document_type: DocumentType
    ) -> str:
        """
        Upload document to Cloud Storage.

        Args:
            document_id: Unique document identifier
            content: PDF file content
            filename: Original filename
            document_type: Type of document (manual, spec, etc.)

        Returns:
            GCS URI of uploaded document
        """
        try:
            bucket = self.storage_client.bucket(settings.gcs_bucket_manuals)

            # Create blob path: {document_type}/{document_id}/{filename}
            blob_path = f"{document_type.value}/{document_id}/{filename}"
            blob = bucket.blob(blob_path)

            # Upload with metadata
            blob.metadata = {
                "document_id": document_id,
                "document_type": document_type.value,
                "upload_date": datetime.now().isoformat(),
                "original_filename": filename
            }

            blob.upload_from_string(content, content_type="application/pdf")

            gcs_uri = f"gs://{settings.gcs_bucket_manuals}/{blob_path}"

            logger.info(
                "document_uploaded_to_gcs",
                document_id=document_id,
                gcs_uri=gcs_uri,
                size_bytes=len(content)
            )

            return gcs_uri

        except Exception as e:
            logger.error("upload_to_storage_failed", error=str(e), document_id=document_id)
            raise

    def extract_text_from_pdf(self, content: bytes) -> tuple[str, int]:
        """
        Extract text from PDF.

        Args:
            content: PDF file content

        Returns:
            Tuple of (extracted_text, page_count)
        """
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            page_count = len(pdf_reader.pages)
            text_parts = []

            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()
                if text.strip():
                    text_parts.append(f"\n--- Page {page_num} ---\n{text}")

            full_text = "\n".join(text_parts)

            logger.info(
                "text_extracted_from_pdf",
                page_count=page_count,
                text_length=len(full_text)
            )

            return full_text, page_count

        except Exception as e:
            logger.error("extract_text_failed", error=str(e))
            raise

    async def create_or_get_corpus(self):
        """
        Get existing RAG corpus using configured RAG_DATA_STORE_ID.

        Returns:
            RAG corpus instance
        """
        try:
            if not self.rag:
                raise RuntimeError("Vertex AI RAG Engine module not initialized")

            # Use the configured RAG Data Store ID directly
            if settings.rag_data_store_id:
                logger.info("using_existing_corpus", corpus_id=settings.rag_data_store_id)
                corpus = self.rag.get_corpus(name=settings.rag_data_store_id)
                return corpus

            # Fallback: List existing corpora (will use default region)
            logger.warning("rag_data_store_id_not_configured", message="Falling back to corpus search by name")
            corpora = self.rag.list_corpora()

            # Check if corpus exists
            for corpus in corpora:
                if corpus.display_name == self.corpus_name:
                    logger.info("corpus_found", corpus_name=self.corpus_name)
                    return corpus

            # Error if no corpus found and no RAG_DATA_STORE_ID configured
            raise ValueError(
                "No RAG corpus found. Please configure RAG_DATA_STORE_ID or create a corpus first. "
                "Run: ./scripts/setup_rag_engine.sh PROJECT_ID REGION"
            )

        except Exception as e:
            logger.error("create_or_get_corpus_failed", error=str(e))
            raise

    async def index_document(
        self,
        document_id: str,
        gcs_uri: str,
        document_type: DocumentType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Index document in RAG Engine.

        Args:
            document_id: Unique document identifier
            gcs_uri: GCS URI of the document
            document_type: Type of document
            metadata: Optional metadata to attach

        Returns:
            RAG file ID
        """
        try:
            # Get or create corpus
            corpus = await self.create_or_get_corpus()

            # Prepare metadata
            file_metadata = metadata or {}
            file_metadata.update({
                "document_id": document_id,
                "document_type": document_type.value,
                "indexed_at": datetime.now().isoformat()
            })

            if not self.rag:
                raise RuntimeError("Vertex AI RAG Engine module not initialized")

            # Import file into RAG corpus
            logger.info(
                "importing_file_to_rag",
                document_id=document_id,
                gcs_uri=gcs_uri
            )

            response = self.rag.import_files(
                corpus_name=corpus.name,
                paths=[gcs_uri],
                chunking_config=self.rag.ChunkingConfig(
                    chunk_size=512,
                    chunk_overlap=100
                ),
            )

            imported_files = response.imported_rag_files_count if hasattr(
                response, "imported_rag_files_count"
            ) else None

            logger.info(
                "document_indexed",
                document_id=document_id,
                files_imported=imported_files
            )

            return document_id

        except Exception as e:
            logger.error("index_document_failed", error=str(e), document_id=document_id)
            raise

    async def process_document(
        self,
        document_id: str,
        content: bytes,
        filename: str,
        document_type: DocumentType
    ) -> DocumentInfo:
        """
        Complete document processing pipeline:
        1. Upload to Cloud Storage
        2. Extract text and metadata
        3. Index in RAG Engine

        Args:
            document_id: Unique document identifier
            content: PDF file content
            filename: Original filename
            document_type: Type of document

        Returns:
            DocumentInfo with processing results
        """
        try:
            logger.info(
                "processing_document_started",
                document_id=document_id,
                filename=filename,
                type=document_type
            )

            # Upload to storage
            gcs_uri = await self.upload_to_storage(
                document_id, content, filename, document_type
            )

            # Extract text and get page count
            text, page_count = self.extract_text_from_pdf(content)

            # Index in RAG Engine
            rag_file_id = await self.index_document(
                document_id,
                gcs_uri,
                document_type,
                metadata={"page_count": page_count, "filename": filename}
            )

            logger.info(
                "document_processing_completed",
                document_id=document_id,
                page_count=page_count
            )

            return DocumentInfo(
                document_id=document_id,
                filename=filename,
                document_type=document_type,
                status=DocumentStatus.INDEXED,
                uploaded_at=datetime.now(),
                indexed_at=datetime.now(),
                page_count=page_count,
                metadata={
                    "gcs_uri": gcs_uri,
                    "rag_file_id": rag_file_id,
                    "text_length": len(text)
                }
            )

        except Exception as e:
            logger.error(
                "process_document_failed",
                error=str(e),
                document_id=document_id
            )
            raise

    def get_rag_tool(self) -> Tool:
        """
        Get RAG tool for use with Gemini models.

        Returns:
            Vertex AI RAG Tool configured with the knowledge base corpus
        """
        try:
            if not self.rag:
                raise RuntimeError("Vertex AI RAG Engine module not initialized")

            # Use configured RAG_DATA_STORE_ID directly
            if settings.rag_data_store_id:
                corpus_id = settings.rag_data_store_id
                logger.info("using_configured_corpus_for_rag_tool", corpus_id=corpus_id)
            else:
                # Fallback: search by name
                corpora = self.rag.list_corpora()
                corpus_id = None

                for c in corpora:
                    if c.display_name == self.corpus_name:
                        corpus_id = c.name
                        break

                if not corpus_id:
                    logger.warning("corpus_not_found", corpus_name=self.corpus_name)
                    return None

            # Create RAG retrieval tool
            rag_tool = Tool.from_retrieval(
                retrieval=self.rag.Retrieval(
                    source=self.rag.VertexRagStore(
                        rag_resources=[self.rag.RagResource(rag_corpus=corpus_id)],
                        rag_retrieval_config=self.rag.RagRetrievalConfig(
                            top_k=5
                        ),
                    ),
                )
            )

            logger.info("rag_tool_created", corpus_id=corpus_id)
            return rag_tool

        except Exception as e:
            logger.error("get_rag_tool_failed", error=str(e))
            return None

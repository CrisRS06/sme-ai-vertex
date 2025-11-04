"""
Drawing Processor Service
Handles conversion of technical drawings (PDF → PNG) and embedding generation.
"""
import io
import base64
from typing import List, Tuple
from pdf2image import convert_from_bytes
from PIL import Image
import structlog

from google.cloud import storage
from vertexai.vision_models import MultiModalEmbeddingModel, Image as VertexImage

from src.config.settings import settings
from src.config.gcp_clients import get_storage_client, init_vertex_ai
from src.services.vector_search import get_vector_search
import numpy as np

logger = structlog.get_logger()


class DrawingProcessor:
    """Service for processing technical drawings."""

    def __init__(self):
        self.storage_client = get_storage_client()
        init_vertex_ai()
        self.embedding_model = MultiModalEmbeddingModel.from_pretrained(
            settings.vertex_ai_embedding_model
        )

    async def pdf_to_images(
        self,
        pdf_content: bytes,
        dpi: int = 300
    ) -> List[Image.Image]:
        """
        Convert PDF pages to high-resolution PNG images.

        Args:
            pdf_content: PDF file bytes
            dpi: Resolution in DPI (default: 300 for engineering drawings)

        Returns:
            List of PIL Image objects, one per page
        """
        try:
            logger.info("converting_pdf_to_images", dpi=dpi)

            # Convert PDF to images
            images = convert_from_bytes(
                pdf_content,
                dpi=dpi,
                fmt='PNG',
                thread_count=4  # Parallel processing
            )

            logger.info(
                "pdf_converted",
                page_count=len(images),
                dpi=dpi
            )

            return images

        except Exception as e:
            logger.error("pdf_to_images_failed", error=str(e))
            raise

    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')

    async def upload_images_to_storage(
        self,
        analysis_id: str,
        images: List[Image.Image],
        filename: str
    ) -> List[str]:
        """
        Upload drawing images to Cloud Storage.

        Args:
            analysis_id: Analysis identifier
            images: List of PIL Images
            filename: Original filename

        Returns:
            List of GCS URIs for each page
        """
        try:
            bucket = self.storage_client.bucket(settings.gcs_bucket_drawings)
            gcs_uris = []

            for page_num, image in enumerate(images, start=1):
                # Convert image to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG', optimize=True)
                img_byte_arr = img_byte_arr.getvalue()

                # Create blob path
                blob_path = f"{analysis_id}/page_{page_num}.png"
                blob = bucket.blob(blob_path)

                # Upload with metadata
                blob.metadata = {
                    "analysis_id": analysis_id,
                    "page_number": str(page_num),
                    "original_filename": filename,
                    "format": "PNG"
                }

                blob.upload_from_string(img_byte_arr, content_type="image/png")

                gcs_uri = f"gs://{settings.gcs_bucket_drawings}/{blob_path}"
                gcs_uris.append(gcs_uri)

                logger.info(
                    "page_uploaded",
                    analysis_id=analysis_id,
                    page=page_num,
                    gcs_uri=gcs_uri
                )

            return gcs_uris

        except Exception as e:
            logger.error("upload_images_failed", error=str(e), analysis_id=analysis_id)
            raise

    async def generate_image_embedding(
        self,
        image,  # Union[Image.Image, bytes]
        contextual_text: str = None
    ) -> List[float]:
        """
        Generate multimodal embedding for an image.

        Args:
            image: PIL Image or image bytes
            contextual_text: Optional text context (e.g., "technical engineering drawing")

        Returns:
            Embedding vector
        """
        try:
            # Convert to bytes if PIL Image
            if isinstance(image, Image.Image):
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
            else:
                # Already bytes
                img_bytes = image

            # Create VertexAI Image
            vertex_image = VertexImage(img_bytes)

            # Generate embedding
            if contextual_text:
                embeddings = self.embedding_model.get_embeddings(
                    image=vertex_image,
                    contextual_text=contextual_text
                )
            else:
                embeddings = self.embedding_model.get_embeddings(
                    image=vertex_image
                )

            embedding_vector = embeddings.image_embedding

            logger.info(
                "embedding_generated",
                dimension=len(embedding_vector),
                has_context=bool(contextual_text)
            )

            return embedding_vector

        except Exception as e:
            logger.error("generate_embedding_failed", error=str(e))
            raise

    async def process_drawing(
        self,
        analysis_id: str,
        pdf_content: bytes,
        filename: str
    ) -> Tuple[List[str], List[List[float]]]:
        """
        Complete drawing processing pipeline:
        1. Convert PDF → PNG images (300 DPI)
        2. Upload images to Cloud Storage
        3. Generate embeddings for each page

        Args:
            analysis_id: Unique analysis identifier
            pdf_content: PDF file bytes
            filename: Original filename

        Returns:
            Tuple of (gcs_uris, embeddings) for each page
        """
        try:
            logger.info(
                "processing_drawing_started",
                analysis_id=analysis_id,
                filename=filename
            )

            # Convert PDF to images
            images = await self.pdf_to_images(pdf_content, dpi=300)

            # Upload images to storage
            gcs_uris = await self.upload_images_to_storage(
                analysis_id, images, filename
            )

            # Generate embeddings for each page
            embeddings = []
            contextual_text = "Technical engineering drawing for injection molding part"

            for page_num, image in enumerate(images, start=1):
                logger.info(
                    "generating_embedding_for_page",
                    page=page_num,
                    total_pages=len(images)
                )

                embedding = await self.generate_image_embedding(
                    image, contextual_text
                )
                embeddings.append(embedding)

            # Store embeddings in vector search
            vector_search = get_vector_search()
            embedding_records = []
            for page_num, (gcs_uri, embedding) in enumerate(
                zip(gcs_uris, embeddings), start=1
            ):
                metadata = {
                    "filename": filename,
                    "type": "drawing",
                    "page_number": page_num,
                    "gcs_uri": gcs_uri,
                }
                embedding_records.append(
                    (
                        page_num,
                        gcs_uri,
                        np.asarray(embedding, dtype=np.float32),
                        metadata,
                    )
                )

            vector_search.store_embeddings(
                document_id=analysis_id,
                embeddings=embedding_records,
            )

            logger.info(
                "drawing_processing_completed",
                analysis_id=analysis_id,
                page_count=len(images),
                embeddings_count=len(embeddings)
            )

            return gcs_uris, embeddings

        except Exception as e:
            logger.error(
                "process_drawing_failed",
                error=str(e),
                analysis_id=analysis_id
            )
            raise

    def get_image_from_gcs(self, gcs_uri: str) -> Image.Image:
        """
        Load image from Cloud Storage.

        Args:
            gcs_uri: GCS URI (gs://bucket/path)

        Returns:
            PIL Image
        """
        try:
            # Parse GCS URI
            parts = gcs_uri.replace("gs://", "").split("/", 1)
            bucket_name = parts[0]
            blob_path = parts[1]

            # Download image
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            img_bytes = blob.download_as_bytes()

            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_bytes))

            return image

        except Exception as e:
            logger.error("get_image_from_gcs_failed", error=str(e), gcs_uri=gcs_uri)
            raise

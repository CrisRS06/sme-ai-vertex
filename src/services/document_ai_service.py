"""
Document AI Service for OCR fallback.
Used when VLM has low confidence on micr text (dimensions, tolerances).
"""
from google.cloud import documentai_v1 as documentai
from typing import List, Dict, Any, Optional, Tuple
import structlog
import re

from src.config.settings import settings

logger = structlog.get_logger()


class DocumentAIService:
    """
    Document AI service for high-precision OCR.

    Used as fallback when Gemini VLM has low confidence
    on microtext like dimensions and tolerances.
    """

    def __init__(self):
        """Initialize Document AI client."""
        self.client = documentai.DocumentProcessorServiceClient()

        # Processor format: projects/{project}/locations/{location}/processors/{processor}
        # This needs to be created in GCP Console first
        self.processor_name = (
            f"projects/{settings.gcp_project_id}/locations/us/"
            f"processors/{settings.document_ai_processor_id}"
            if hasattr(settings, 'document_ai_processor_id') and settings.document_ai_processor_id
            else None
        )

        logger.info(
            "document_ai_initialized",
            project=settings.gcp_project_id,
            processor=self.processor_name
        )

    def is_enabled(self) -> bool:
        """Check if Document AI is properly configured."""
        return self.processor_name is not None

    async def process_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png"
    ) -> documentai.Document:
        """
        Process image with Document AI OCR.

        Args:
            image_bytes: Image content as bytes
            mime_type: MIME type (image/png, image/jpeg, application/pdf)

        Returns:
            Document AI Document object with OCR results
        """
        try:
            if not self.is_enabled():
                raise ValueError("Document AI processor not configured")

            # Create request
            raw_document = documentai.RawDocument(
                content=image_bytes,
                mime_type=mime_type
            )

            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )

            # Process document
            result = self.client.process_document(request=request)

            document = result.document

            logger.info(
                "document_ai_processed",
                pages=len(document.pages),
                text_length=len(document.text)
            )

            return document

        except Exception as e:
            logger.error("document_ai_process_failed", error=str(e))
            raise

    def extract_dimensions(
        self,
        document: documentai.Document
    ) -> List[Dict[str, Any]]:
        """
        Extract dimension-like text from OCR results.

        Looks for patterns like:
        - "10.5mm"
        - "0.75±0.01"
        - "2.5 +0.1/-0.05"

        Args:
            document: Document AI Document

        Returns:
            List of dimension dictionaries
        """
        try:
            dimensions = []

            # Regex patterns for dimensions
            dimension_patterns = [
                r'(\d+\.?\d*)\s*mm',  # 10.5mm
                r'(\d+\.?\d*)\s*±\s*(\d+\.?\d*)',  # 0.75±0.01
                r'(\d+\.?\d*)\s*\+(\d+\.?\d*)\s*/\s*-(\d+\.?\d*)',  # 2.5 +0.1/-0.05
                r'(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)',  # 10x20
                r'∅\s*(\d+\.?\d*)',  # ∅10 (diameter)
                r'R\s*(\d+\.?\d*)',  # R5 (radius)
            ]

            for page in document.pages:
                for block in page.blocks:
                    text = self._get_text_from_layout(document.text, block.layout)

                    for pattern in dimension_patterns:
                        matches = re.finditer(pattern, text)

                        for match in matches:
                            # Get bounding box
                            bbox = self._get_bbox(block.layout.bounding_poly)

                            dimensions.append({
                                "value": match.group(0),
                                "text": text,
                                "bbox": bbox,
                                "page": page.page_number,
                                "confidence": block.layout.confidence if hasattr(block.layout, 'confidence') else None
                            })

            logger.info("dimensions_extracted_from_ocr", count=len(dimensions))

            return dimensions

        except Exception as e:
            logger.error("extract_dimensions_failed", error=str(e))
            return []

    def extract_all_text_with_positions(
        self,
        document: documentai.Document
    ) -> List[Dict[str, Any]]:
        """
        Extract all text with bounding boxes.

        Args:
            document: Document AI Document

        Returns:
            List of text blocks with positions
        """
        try:
            text_blocks = []

            for page in document.pages:
                for block in page.blocks:
                    text = self._get_text_from_layout(document.text, block.layout)

                    if text.strip():
                        bbox = self._get_bbox(block.layout.bounding_poly)

                        text_blocks.append({
                            "text": text,
                            "bbox": bbox,
                            "page": page.page_number,
                            "confidence": block.layout.confidence if hasattr(block.layout, 'confidence') else None
                        })

            logger.info("text_blocks_extracted", count=len(text_blocks))

            return text_blocks

        except Exception as e:
            logger.error("extract_text_blocks_failed", error=str(e))
            return []

    def _get_text_from_layout(
        self,
        full_text: str,
        layout: documentai.Document.Page.Layout
    ) -> str:
        """Extract text from layout text anchor."""
        if not layout.text_anchor:
            return ""

        text_segments = []
        for segment in layout.text_anchor.text_segments:
            start_idx = int(segment.start_index) if hasattr(segment, 'start_index') else 0
            end_idx = int(segment.end_index) if hasattr(segment, 'end_index') else len(full_text)
            text_segments.append(full_text[start_idx:end_idx])

        return "".join(text_segments)

    def _get_bbox(
        self,
        bounding_poly: documentai.BoundingPoly
    ) -> Optional[List[float]]:
        """
        Convert Document AI bounding poly to [x_min, y_min, x_max, y_max] format.

        Args:
            bounding_poly: Document AI BoundingPoly

        Returns:
            Bounding box as [x_min, y_min, x_max, y_max] or None
        """
        try:
            if not bounding_poly or not bounding_poly.normalized_vertices:
                return None

            # Get all vertices
            x_coords = [v.x for v in bounding_poly.normalized_vertices if hasattr(v, 'x')]
            y_coords = [v.y for v in bounding_poly.normalized_vertices if hasattr(v, 'y')]

            if not x_coords or not y_coords:
                return None

            return [
                min(x_coords),
                min(y_coords),
                max(x_coords),
                max(y_coords)
            ]

        except Exception as e:
            logger.error("bbox_extraction_failed", error=str(e))
            return None

    def merge_with_vlm_results(
        self,
        vlm_dimensions: List[Dict[str, Any]],
        ocr_dimensions: List[Dict[str, Any]],
        confidence_threshold: float = 0.8
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Merge OCR dimensions with VLM results.

        Strategy:
        1. Keep high-confidence VLM dimensions
        2. Add OCR dimensions that aren't already in VLM results
        3. Replace low-confidence VLM dimensions with OCR if available

        Args:
            vlm_dimensions: Dimensions from VLM
            ocr_dimensions: Dimensions from OCR
            confidence_threshold: Threshold for "high confidence"

        Returns:
            Tuple of (merged_dimensions, fields_recovered_count)
        """
        try:
            merged = []
            fields_recovered = 0

            # Index OCR dimensions by approximate position (rounded bbox)
            ocr_by_position = {}
            for ocr_dim in ocr_dimensions:
                if ocr_dim.get('bbox'):
                    # Round bbox to nearest 0.1 for matching
                    bbox = ocr_dim['bbox']
                    key = tuple(round(c, 1) for c in bbox)
                    ocr_by_position[key] = ocr_dim

            # Process VLM dimensions
            for vlm_dim in vlm_dimensions:
                vlm_confidence = vlm_dim.get('confidence', 1.0)

                # If high confidence, keep VLM result
                if vlm_confidence >= confidence_threshold:
                    merged.append(vlm_dim)
                else:
                    # Try to find OCR match
                    match_found = False

                    if vlm_dim.get('bbox'):
                        bbox = vlm_dim['bbox']
                        key = tuple(round(c, 1) for c in bbox)

                        if key in ocr_by_position:
                            # Replace with OCR result
                            ocr_dim = ocr_by_position[key]
                            merged_dim = {
                                **vlm_dim,
                                "value": ocr_dim['value'],
                                "confidence": ocr_dim.get('confidence', 0.95),
                                "source": "ocr_fallback"
                            }
                            merged.append(merged_dim)
                            fields_recovered += 1
                            match_found = True
                            del ocr_by_position[key]  # Remove used OCR result

                    if not match_found:
                        # Keep VLM result even with low confidence
                        merged.append({**vlm_dim, "low_confidence": True})

            # Add remaining OCR dimensions that weren't matched
            for ocr_dim in ocr_by_position.values():
                merged.append({
                    "value": ocr_dim['value'],
                    "bbox": ocr_dim['bbox'],
                    "confidence": ocr_dim.get('confidence', 0.9),
                    "source": "ocr_only",
                    "unit": "mm"  # Default assumption
                })
                fields_recovered += 1

            logger.info(
                "results_merged",
                vlm_count=len(vlm_dimensions),
                ocr_count=len(ocr_dimensions),
                merged_count=len(merged),
                fields_recovered=fields_recovered
            )

            return merged, fields_recovered

        except Exception as e:
            logger.error("merge_results_failed", error=str(e))
            return vlm_dimensions, 0  # Return original on error


# Global instance
_document_ai = None


def get_document_ai() -> DocumentAIService:
    """Get singleton Document AI instance."""
    global _document_ai
    if _document_ai is None:
        _document_ai = DocumentAIService()
    return _document_ai

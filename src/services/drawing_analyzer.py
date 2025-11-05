"""
Drawing Analyzer Service - FIXED VERSION
Analyzes technical drawings using Gemini 2.5 VLM with timeout and better error handling.
"""
import json
from typing import List, Optional, Dict, Any
import structlog
from PIL import Image
import io
import asyncio
import time

from vertexai.generative_models import GenerativeModel, Part
from vertexai.preview.generative_models import GenerationConfig

from src.config.settings import settings
from src.config.gcp_clients import init_vertex_ai
from src.models.drawing_analysis import (
    DrawingAnalysis,
    Dimension,
    DRAWING_ANALYSIS_RESPONSE_SCHEMA
)
from src.services.drawing_processor import DrawingProcessor
from src.services.document_ai_service import get_document_ai
from src.services.metrics_service import get_metrics

logger = structlog.get_logger()


class DrawingAnalyzer:
    """Service for analyzing technical drawings with Gemini VLM."""

    def __init__(self, enable_context_caching: bool = True):
        """Initialize drawing analyzer with context caching support.

        Args:
            enable_context_caching: Enable context caching for 75% cost reduction
        """
        init_vertex_ai()

        # Store quality mode
        self.quality_mode = settings.quality_mode

        # Select model based on quality mode
        model_name = (
            settings.vertex_ai_model_pro
            if self.quality_mode == "pro"
            else settings.vertex_ai_model_flash
        )

        # Use context caching to reduce costs by 75% for repeated prompts
        if enable_context_caching:
            from src.config.gcp_clients import get_generative_model
            # Cache analysis prompts for 30 minutes (1800 seconds)
            self.model = get_generative_model(
                model_name,
                cache_ttl_seconds=1800,
                max_context_cache_entries=16
            )
            logger.info(
                "drawing_analyzer_initialized_with_caching",
                model=model_name,
                quality_mode=self.quality_mode,
                cache_ttl_seconds=1800
            )
        else:
            self.model = GenerativeModel(model_name)
            logger.info(
                "drawing_analyzer_initialized",
                model=model_name,
                quality_mode=self.quality_mode
            )

        self.processor = DrawingProcessor()

    def _create_analysis_prompt(self) -> str:
        """
        Create detailed prompt for drawing analysis.

        Based on Michael's requirements:
        - Extract ALL dimensions with tolerances
        - Identify GD&T specifications
        - Note any ambiguities or missing specs
        - Be thorough and accurate
        """
        return """
You are an expert injection molding engineer analyzing a technical drawing.

TASK: Extract ALL technical specifications from this drawing with high accuracy.

EXTRACT:

1. **Part Information**
   - Part ID/Number
   - Part name/description
   - Material specification (e.g., "ABS", "PP+30GF", "PC/ABS")
   - Material grade if specified

2. **Dimensions** (CRITICAL - Extract ALL)
   - Feature being measured (e.g., "wall thickness", "overall length", "hole diameter")
   - Numerical value
   - Unit (mm or in)
   - Tolerance (e.g., "±0.05", "+0.1/-0.0", "±0.002")
   - Location on drawing (bounding box coordinates if visible)

   IMPORTANT:
   - Extract EVERY dimension, even if seems minor
   - Include nominal dimensions without explicit tolerances
   - Note if dimension is critical (e.g., in tolerance box)

3. **GD&T Specifications** (Geometric Dimensioning and Tolerancing)
   - Symbol (e.g., ⌖ for position, ⏊ for perpendicularity, ∥ for parallelism)
   - Tolerance value
   - Datum references (A, B, C, etc.)
   - Feature it applies to
   - Feature control frame location

4. **Surface Finish**
   - Finish specification (e.g., "Ra 1.6", "32 RMS", "N6")
   - Location/surfaces it applies to

5. **Injection Molding Analysis** (NEW - CRITICAL for manufacturability)

   a) **Draft Angles**
      - Identify vertical/sloped surfaces
      - Extract draft angle specifications if shown
      - Evaluate if draft appears adequate (min 0.5°, recommend 1.5°)
      - Note surfaces with no draft or insufficient draft

   b) **Undercuts**
      - Identify any features that prevent straight pull from mold:
        * Internal threads
        * Holes perpendicular to draw direction
        * Snap fits
        * Side holes or features
        * Recesses that require side action
      - Specify what tooling action is required (slide, lifter, hand load, unscrewing device)
      - Assess complexity (simple/moderate/complex)

   c) **Wall Thickness Analysis**
      - Identify minimum wall thickness (mm)
      - Identify maximum wall thickness (mm)
      - Calculate nominal/average wall thickness
      - Assess if wall thickness is uniform (variation ratio <2:1 is ideal)
      - Flag any problematically thin sections (<0.8mm)
      - Flag any problematically thick sections (>4mm - sink risk)

   d) **Parting Line Suggestions**
      - Based on part geometry, suggest where mold should split
      - Describe orientation (horizontal/vertical/angled)
      - Assess complexity (straight/stepped/complex)
      - Provide reasoning for suggested parting line

   e) **Gating Points**
      - If gate location is specified in drawing, extract it
      - If runner system is shown, describe it
      - Note gate type if specified (edge/sub/pin/hot runner)
      - Suggest optimal gate location based on geometry if not specified

   f) **Ejection System**
      - If ejector pin locations are marked, extract them
      - Note ejection method if specified (pins/stripper plate/air)
      - Flag any ejection-related notes

6. **General Notes**
   - Manufacturing instructions
   - Material specifications
   - Finish requirements
   - Assembly notes
   - ANY specifications or requirements mentioned

7. **Drawing Metadata**
   - Scale
   - Default units
   - Projection type (First Angle / Third Angle)
   - Number of pages/views

IMPORTANT RULES:
- If you cannot read a dimension clearly, return null for that field and note in analysis_notes
- Include confidence score (0-1) for dimensions if uncertain
- For bounding boxes, use [x1, y1, x2, y2] normalized coordinates (0-1)
- Extract text EXACTLY as shown (don't interpret or convert)
- If something is ambiguous, note it in analysis_notes

CRITICAL - EXCEPTION ONLY PRINCIPLE:
- Your analysis is for EXCEPTION REPORTING, not redesign
- Identify what's NOT viable or risky "as specified"
- Parting line and gating suggestions are for MOLD DESIGNER, not part changes
- Do NOT suggest modifying part geometry
- Do NOT recommend redesigning features
- Only mark problems and assess manufacturability of the specified design

ACCURACY IS CRITICAL: This analysis determines if the part can be manufactured.
Missing or incorrect dimensions can cause million-dollar mistakes.

Be thorough. Be accurate. Extract everything.
""".strip()

    def _create_concise_prompt(self) -> str:
        """
        Create a more concise prompt for retry cases to avoid truncation.
        """
        return """
Analyze this technical drawing and extract specifications in JSON format.

Required fields:
- part_id: Part number if visible
- part_name: Part description
- material: Material specification
- dimensions: Array of {feature, value, unit, tolerance, bbox, confidence, page}
- analysis_notes: Any important notes

Keep response under 2000 characters to avoid truncation.

Return ONLY valid JSON, no additional text.
""".strip()

    def _repair_truncated_json(self, response_text: str) -> Optional[str]:
        """
        Attempt to repair truncated JSON responses from Gemini.
        
        Args:
            response_text: Potentially truncated JSON string
            
        Returns:
            Repaired JSON string or None if repair failed
        """
        try:
            # First try to parse as-is
            json.loads(response_text)
            return response_text
        except json.JSONDecodeError:
            pass
            
        # Try to fix common truncation patterns
        try:
            # Remove trailing incomplete content
            repaired = response_text.rstrip()
            
            # If response ends with incomplete array/object, close it
            if repaired.count('[') > repaired.count(']'):
                repaired += ']' * (repaired.count('[') - repaired.count(']'))
            if repaired.count('{') > repaired.count('}'):
                repaired += '}' * (repaired.count('{') - repaired.count('}'))
            
            # If response ends with incomplete coordinate array like [0.76, fix it
            if repaired.rstrip().endswith('['):
                # Remove the trailing incomplete bracket
                repaired = repaired.rstrip()[:-1]
                # Add a safe default closing
                repaired += ', "page_number": 1 }]'
            
            # If response ends with incomplete number like [0.768, 0.078, 0.796, add closing
            if ', ' in repaired and not repaired.rstrip().endswith('}'):
                if repaired.count('[') > repaired.count(']'):
                    repaired += ', 0.1], "page_number": 1 }]'
                else:
                    repaired += '}'
            
            # Try to parse the repaired version
            json.loads(repaired)
            logger.info("json_repair_successful", original_length=len(response_text), repaired_length=len(repaired))
            return repaired
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("json_repair_failed", error=str(e))
            return None

    async def _call_gemini_with_timeout(self, contents: List, generation_config: GenerationConfig, timeout_seconds: int = 180) -> any:
        """
        Call Gemini with timeout to prevent hanging.
        
        Args:
            contents: Content for Gemini (prompt + images)
            generation_config: Generation configuration
            timeout_seconds: Timeout in seconds (default: 3 minutes)
            
        Returns:
            Gemini response
        """
        try:
            # Create a task for the Gemini call
            gemini_task = asyncio.create_task(
                self.model.generate_content_async(contents, generation_config=generation_config)
            )
            
            # Wait for the task with timeout
            logger.info("gemini_call_started", timeout_seconds=timeout_seconds)
            start_time = time.time()
            
            response = await asyncio.wait_for(gemini_task, timeout=timeout_seconds)
            
            elapsed_time = time.time() - start_time
            logger.info("gemini_call_completed", elapsed_seconds=elapsed_time)
            
            return response
            
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(
                "gemini_call_timeout", 
                timeout_seconds=timeout_seconds, 
                elapsed_seconds=elapsed
            )
            raise ValueError(
                f"Gemini model timed out after {timeout_seconds} seconds. "
                f"This can happen with complex drawings. Try a simpler drawing or reduce quality mode."
            )
        except Exception as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            logger.error(
                "gemini_call_failed", 
                error=str(e), 
                elapsed_seconds=elapsed
            )
            raise

    async def analyze_drawing_from_images(
        self,
        images: List[Image.Image],
        custom_prompt: Optional[str] = None,
        retry_with_concise: bool = False
    ) -> DrawingAnalysis:
        """
        Analyze drawing using Gemini VLM with structured output and timeout.

        Args:
            images: List of PIL Images (one per page)
            custom_prompt: Optional custom prompt (uses default if not provided)
            retry_with_concise: Whether to use concise prompt for retry

        Returns:
            DrawingAnalysis with structured data
        """
        try:
            logger.info(
                "analyzing_drawing",
                num_pages=len(images),
                model=self.model._model_name,
                retry_mode=retry_with_concise
            )

            # Prepare prompt
            if retry_with_concise:
                prompt = custom_prompt or self._create_concise_prompt()
            else:
                prompt = custom_prompt or self._create_analysis_prompt()

            # Convert PIL Images to bytes for Vertex AI
            image_parts = []
            for idx, img in enumerate(images):
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()

                image_part = Part.from_data(
                    data=img_bytes,
                    mime_type="image/png"
                )
                image_parts.append(image_part)

            # Build content: text prompt + all images
            contents = [prompt] + image_parts

            # Configure max output tokens - FIXED: Increased to prevent JSON truncation
            # Complex technical drawings require sufficient tokens to complete JSON responses
            max_tokens = 16384  # Increased from 8192 to prevent JSON truncation

            # Configure generation with response schema
            generation_config = GenerationConfig(
                temperature=0.1,  # Low temperature for accuracy
                top_p=0.95,
                top_k=40,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
                response_schema=DRAWING_ANALYSIS_RESPONSE_SCHEMA
            )

            # Generate analysis with timeout
            logger.info(
                "calling_gemini_vlm",
                num_images=len(images),
                max_output_tokens=max_tokens,
                quality_mode=self.quality_mode
            )

            response = await self._call_gemini_with_timeout(contents, generation_config)

            # Check if response was complete
            response_text = response.text
            response_length = len(response_text)

            logger.info(
                "gemini_response_received",
                response_length_chars=response_length,
                response_length_tokens_approx=response_length // 4,  # Rough estimate
                response_complete=not response_text.endswith("...")
            )

            # Parse JSON response with repair attempt
            try:
                analysis_dict = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.warning(
                    "json_decode_failed_initial",
                    error=str(e),
                    response_length=response_length
                )
                
                # Try to repair truncated JSON
                repaired_text = self._repair_truncated_json(response_text)
                if repaired_text:
                    try:
                        analysis_dict = json.loads(repaired_text)
                        logger.info("json_repaired_and_parsed_successfully")
                    except json.JSONDecodeError as repair_error:
                        logger.error(
                            "json_repair_failed_then_parse",
                            repair_error=str(repair_error)
                        )
                        # If repair failed, raise original error
                        raise ValueError(
                            f"Failed to parse Gemini response as JSON after repair attempt: {str(e)}. "
                            f"Response length: {response_length} chars. "
                            f"This may indicate the response was truncated due to token limits. "
                            f"Try with fewer images or simpler drawings."
                        )
                else:
                    # Repair failed, try concise retry if not already in retry mode
                    if not retry_with_concise:
                        logger.info("attempting_retry_with_concise_prompt")
                        return await self.analyze_drawing_from_images(
                            images, 
                            custom_prompt=None, 
                            retry_with_concise=True
                        )
                    else:
                        # Both attempts failed
                        logger.error(
                            "json_decode_failed_both_attempts",
                            error=str(e),
                            response_start=response_text[:500] if len(response_text) > 500 else response_text,
                            response_end=response_text[-500:] if len(response_text) > 500 else "",
                            response_length=response_length
                        )
                        raise ValueError(
                            f"Failed to parse Gemini response as JSON after retry with concise prompt: {str(e)}. "
                            f"Response length: {response_length} chars. "
                            f"This drawing may be too complex for current token limits."
                        )

            # Convert to Pydantic model
            analysis = DrawingAnalysis(**analysis_dict)

            logger.info(
                "drawing_analysis_completed",
                dimensions_found=len(analysis.dimensions),
                gdandt_found=len(analysis.gdandt),
                notes_found=len(analysis.notes),
                material=analysis.material
            )

            return analysis

        except ValueError:
            # ValueError from JSON parsing or timeout - already logged above
            raise
        except Exception as e:
            logger.error("drawing_analysis_failed", error=str(e))
            raise

    async def analyze_drawing_from_gcs(
        self,
        gcs_uris: List[str],
        custom_prompt: Optional[str] = None
    ) -> DrawingAnalysis:
        """
        Analyze drawing from GCS URIs.

        Args:
            gcs_uris: List of GCS URIs to drawing pages
            custom_prompt: Optional custom prompt

        Returns:
            DrawingAnalysis
        """
        try:
            # Load images from GCS
            images = []
            for uri in gcs_uris:
                img = self.processor.get_image_from_gcs(uri)
                images.append(img)

            # Analyze
            return await self.analyze_drawing_from_images(images, custom_prompt)

        except Exception as e:
            logger.error("analyze_from_gcs_failed", error=str(e))
            raise

    async def analyze_drawing_from_pdf(
        self,
        pdf_content: bytes,
        custom_prompt: Optional[str] = None,
        analysis_id: Optional[str] = None
    ) -> DrawingAnalysis:
        """
        Analyze drawing directly from PDF bytes.

        Args:
            pdf_content: PDF file bytes
            custom_prompt: Optional custom prompt
            analysis_id: Optional analysis ID for OCR metrics tracking

        Returns:
            DrawingAnalysis (with OCR fallback if enabled)
        """
        try:
            # Convert PDF to images
            images = await self.processor.pdf_to_images(pdf_content, dpi=300)

            # Analyze with VLM
            analysis = await self.analyze_drawing_from_images(images, custom_prompt)

            # Apply OCR fallback if enabled and needed
            if settings.enable_document_ai_fallback:
                analysis = await self.apply_ocr_fallback(
                    analysis=analysis,
                    images=images,
                    analysis_id=analysis_id
                )

            return analysis

        except Exception as e:
            logger.error("analyze_from_pdf_failed", error=str(e))
            raise

    async def apply_ocr_fallback(
        self,
        analysis: DrawingAnalysis,
        images: List[Image.Image],
        analysis_id: Optional[str] = None
    ) -> DrawingAnalysis:
        """
        Apply Document AI OCR fallback for low-confidence dimensions.

        Args:
            analysis: Initial VLM analysis
            images: Original images
            analysis_id: Optional analysis ID for metrics

        Returns:
            Enhanced analysis with OCR-recovered fields
        """
        try:
            document_ai = get_document_ai()

            if not document_ai.is_enabled():
                logger.info("document_ai_not_configured_skipping_fallback")
                return analysis

            # Check if OCR is needed
            low_confidence_dims = [
                d for d in analysis.dimensions
                if d.confidence and d.confidence < settings.ocr_confidence_threshold
            ]

            if not low_confidence_dims:
                logger.info("no_low_confidence_dimensions_skipping_ocr")
                return analysis

            logger.info(
                "ocr_fallback_triggered",
                low_confidence_count=len(low_confidence_dims),
                threshold=settings.ocr_confidence_threshold
            )

            # Process each page with OCR
            for page_idx, image in enumerate(images):
                # Check if this page needs OCR
                page_dims = [d for d in low_confidence_dims if d.page == page_idx + 1]

                if not page_dims:
                    continue

                logger.info("processing_page_with_ocr", page=page_idx + 1)

                # Convert PIL image to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()

                # Process with Document AI
                doc = await document_ai.process_image(img_bytes, "image/png")

                # Extract dimensions from OCR
                ocr_dimensions = document_ai.extract_dimensions(doc)

                # Calculate metrics before merge
                avg_vlm_confidence = (
                    sum(d.confidence for d in page_dims if d.confidence) / len(page_dims)
                    if page_dims else 0
                )

                # Merge results
                vlm_dims_dict = [
                    {
                        "value": f"{d.value} {d.unit}" if d.unit else str(d.value),
                        "bbox": d.bbox,
                        "confidence": d.confidence
                    }
                    for d in analysis.dimensions if d.page == page_idx + 1
                ]

                merged_dims, fields_recovered = document_ai.merge_with_vlm_results(
                    vlm_dimensions=vlm_dims_dict,
                    ocr_dimensions=ocr_dimensions,
                    confidence_threshold=settings.ocr_confidence_threshold
                )

                # Calculate metrics after merge
                avg_merged_confidence = (
                    sum(d.get('confidence', 0) for d in merged_dims) / len(merged_dims)
                    if merged_dims else 0
                )

                # Update analysis dimensions for this page
                # Remove old dimensions for this page
                analysis.dimensions = [
                    d for d in analysis.dimensions if d.page != page_idx + 1
                ]

                # Add merged dimensions
                for merged_dim in merged_dims:
                    # Parse value and unit
                    value_str = merged_dim['value']
                    value_parts = value_str.split()
                    value = value_parts[0] if value_parts else value_str
                    unit = value_parts[1] if len(value_parts) > 1 else merged_dim.get('unit', 'mm')

                    analysis.dimensions.append(
                        Dimension(
                            value=value,
                            unit=unit,
                            tolerance=None,
                            bbox=merged_dim.get('bbox'),
                            confidence=merged_dim.get('confidence'),
                            page=page_idx + 1
                        )
                    )

                # Track OCR metrics
                if analysis_id:
                    metrics = get_metrics()
                    metrics.track_ocr_fallback(
                        analysis_id=analysis_id,
                        page_number=page_idx + 1,
                        ocr_triggered=True,
                        ocr_reason=f"low_confidence_dimensions_{len(page_dims)}",
                        fields_recovered=fields_recovered,
                        vlm_confidence_before=avg_vlm_confidence,
                        merged_confidence_after=avg_merged_confidence,
                        ocr_cost=0.0015,  # Document AI cost: ~$1.50 per 1000 pages
                        metadata={
                            "low_conf_dims": len(page_dims),
                            "ocr_dims_found": len(ocr_dimensions),
                            "merged_count": len(merged_dims)
                        }
                    )

                logger.info(
                    "ocr_fallback_completed",
                    page=page_idx + 1,
                    fields_recovered=fields_recovered,
                    confidence_improved=avg_merged_confidence - avg_vlm_confidence
                )

            return analysis

        except Exception as e:
            logger.error("ocr_fallback_failed", error=str(e))
            # Return original analysis on error
            return analysis

    def validate_analysis(self, analysis: DrawingAnalysis) -> Dict[str, Any]:
        """
        Validate analysis for completeness and quality.

        Args:
            analysis: DrawingAnalysis object

        Returns:
            Validation report with warnings/issues
        """
        issues = []
        warnings = []

        # Check for critical missing data
        if not analysis.dimensions:
            issues.append("No dimensions extracted - drawing may be unreadable or invalid")

        if not analysis.material:
            warnings.append("Material not specified in drawing")

        if not analysis.part_id:
            warnings.append("Part ID/number not found")

        # Check dimension quality
        low_confidence_dims = [
            d for d in analysis.dimensions
            if d.confidence and d.confidence < 0.7
        ]
        if low_confidence_dims:
            warnings.append(
                f"{len(low_confidence_dims)} dimensions have low confidence (<0.7)"
            )

        # Check for missing tolerances
        dims_without_tolerance = [
            d for d in analysis.dimensions
            if not d.tolerance
        ]
        if dims_without_tolerance:
            warnings.append(
                f"{len(dims_without_tolerance)} dimensions missing tolerance specifications"
            )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "metrics": {
                "dimensions_count": len(analysis.dimensions),
                "gdandt_count": len(analysis.gdandt),
                "surface_finishes_count": len(analysis.surface_finishes),
                "notes_count": len(analysis.notes),
                "has_material": bool(analysis.material),
                "has_part_id": bool(analysis.part_id),
                "avg_confidence": (
                    sum(d.confidence for d in analysis.dimensions if d.confidence) /
                    len([d for d in analysis.dimensions if d.confidence])
                    if any(d.confidence for d in analysis.dimensions)
                    else None
                )
            }
        }

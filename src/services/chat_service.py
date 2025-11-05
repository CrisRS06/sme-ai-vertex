"""
Chat Service for conversational interface.
Uses Gemini with grounding on RAG Engine and analysis results.
"""
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part, Content
from vertexai.preview.generative_models import grounding
from typing import List, Dict, Any, Optional
import structlog
import uuid
import json
from datetime import datetime
from jinja2 import Template, TemplateError

from src.config.settings import settings
from src.config.gcp_clients import get_storage_client
from src.models.schemas import ChatMessage, ChatResponse
from src.services.sqlite_db import get_db

logger = structlog.get_logger()


class ChatService:
    """
    Chat service for discussing analysis results with AI expert.

    Features:
    - Grounded responses using Vertex AI RAG Engine
    - Context from analysis results (dimensions, GD&T, exceptions)
    - Citation of sources from knowledge base
    - Conversation history support
    """

    def __init__(self, enable_context_caching: bool = True):
        """Initialize chat service with Gemini model and context caching.

        Args:
            enable_context_caching: Enable context caching for 75% cost reduction on repeated context
        """
        vertexai.init(
            project=settings.gcp_project_id,
            location=settings.gcp_region
        )
        self.storage_client = get_storage_client()

        # Select model based on quality_mode setting
        model_name = (
            settings.vertex_ai_model_pro if settings.quality_mode == "pro"
            else settings.vertex_ai_model_flash
        )

        # Context caching reduces costs by 75% for repeated context (knowledge base docs)
        if enable_context_caching:
            from src.config.gcp_clients import get_generative_model
            # Cache context for 1 hour (3600 seconds)
            self.model = get_generative_model(
                model_name,
                cache_ttl_seconds=3600,
                max_context_cache_entries=32
            )
            logger.info(
                "chat_service_initialized_with_caching",
                project=settings.gcp_project_id,
                model=model_name,
                quality_mode=settings.quality_mode,
                cache_ttl_seconds=3600
            )
        else:
            self.model = GenerativeModel(model_name)
            logger.info(
                "chat_service_initialized",
                project=settings.gcp_project_id,
                model=model_name,
                quality_mode=settings.quality_mode
            )

    def _build_analysis_context(self, analysis_id: str) -> str:
        """
        Build context string from analysis results.

        Args:
            analysis_id: Analysis ID to retrieve

        Returns:
            Formatted context string with analysis details
        """
        db = get_db()
        analysis = db.get_analysis(analysis_id)

        if not analysis:
            return "No analysis found."

        context_parts = [
            f"Analysis ID: {analysis.analysis_id}",
            f"Drawing: {analysis.drawing_filename}",
            f"Status: {analysis.status}",
            f"Quality Mode: {analysis.quality_mode}"
        ]

        if analysis.project_name:
            context_parts.append(f"Project: {analysis.project_name}")

        if analysis.exception_count is not None:
            context_parts.append(f"Total Exceptions: {analysis.exception_count}")

        # TODO: In a real implementation, we would load the full DrawingAnalysis
        # and ExceptionReport objects from storage (GCS or database)
        # For now, we provide basic metadata

        context_parts.extend([
            "",
            "This drawing has been analyzed for injection molding feasibility.",
            "The analysis includes dimensions, GD&T specifications, tolerances, and surface finishes.",
            "Exceptions have been generated based on best practices for injection molding."
        ])

        return "\n".join(context_parts)

    def _format_chat_history(self, history: List[ChatMessage]) -> List[Content]:
        """
        Convert chat history to Vertex AI format.

        Args:
            history: List of ChatMessage objects

        Returns:
            List of Content objects for Gemini
        """
        contents = []

        for msg in history:
            role = "user" if msg.role == "user" else "model"
            contents.append(
                Content(
                    role=role,
                    parts=[Part.from_text(msg.content)]
                )
            )

        return contents

    def _build_system_prompt(self, analysis_context: str) -> str:
        """
        Build system prompt for the chat.

        Args:
            analysis_context: Context from analysis results

        Returns:
            System prompt string
        """
        return f"""You are an expert injection molding engineer with deep knowledge of:
- Design for Manufacturability (DFM) principles
- GD&T (Geometric Dimensioning and Tolerancing)
- Material properties and selection
- Mold design and tooling
- Common molding defects and their root causes
- Industry standards and best practices

You are helping analyze technical drawings for injection molding feasibility.

**Current Analysis Context:**
{analysis_context}

**Instructions:**
1. Provide clear, technical, and actionable advice
2. Always cite sources from the knowledge base when applicable
3. If you don't have enough information, say so clearly
4. Focus on practical solutions and recommendations
5. Explain technical concepts clearly
6. Reference specific dimensions, tolerances, or GD&T callouts when relevant
7. Identify potential molding defects and suggest mitigation strategies

**Response Style:**
- Be concise but thorough
- Use technical terminology correctly
- Provide examples when helpful
- Structure responses with bullet points or numbered lists for clarity
"""

    async def chat(
        self,
        analysis_id: str,
        message: str,
        history: List[ChatMessage]
    ) -> ChatResponse:
        """
        Process a chat message about an analysis.

        Args:
            analysis_id: ID of analysis to discuss
            message: User's question or message
            history: Previous conversation messages

        Returns:
            ChatResponse with AI response and sources
        """
        try:
            logger.info(
                "chat_processing",
                analysis_id=analysis_id,
                message_preview=message[:100]
            )

            # Build context from analysis
            analysis_context = self._build_analysis_context(analysis_id)

            # Build system prompt
            system_prompt = self._build_system_prompt(analysis_context)

            # Format history
            contents = self._format_chat_history(history)

            # Add system prompt as first user message if history is empty
            if not contents:
                contents.append(
                    Content(
                        role="user",
                        parts=[Part.from_text(system_prompt)]
                    )
                )
                contents.append(
                    Content(
                        role="model",
                        parts=[Part.from_text(
                            "I understand. I'm ready to help analyze this injection molding drawing. "
                            "What would you like to know?"
                        )]
                    )
                )

            # Add current message
            contents.append(
                Content(
                    role="user",
                    parts=[Part.from_text(message)]
                )
            )

            # Configure generation with grounding
            generation_config = GenerationConfig(
                temperature=0.3,  # Low for factual responses
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048,
            )

            # Enable grounding (always enabled, but requires RAG_DATA_STORE_ID)
            tools = []
            if settings.rag_data_store_id:
                try:
                    from vertexai.preview.generative_models import Tool
                    from vertexai.preview import rag

                    # Create Vertex AI Search grounding tool
                    grounding_tool = Tool.from_retrieval(
                        retrieval=rag.Retrieval(
                            source=rag.VertexRagStore(
                                rag_resources=[
                                    rag.RagResource(
                                        rag_corpus=settings.rag_data_store_id,
                                    )
                                ],
                                similarity_top_k=10,  # More results
                                vector_distance_threshold=0.5,  # More lenient
                            )
                        )
                    )
                    tools.append(grounding_tool)

                    logger.info("grounding_enabled", data_store=settings.rag_data_store_id)
                except ImportError as e:
                    logger.warning("grounding_import_failed", error=str(e))
                except Exception as e:
                    logger.error("grounding_setup_failed", error=str(e))

            # Generate response
            if tools:
                response = self.model.generate_content(
                    contents=contents,
                    generation_config=generation_config,
                    tools=tools
                )
            else:
                response = self.model.generate_content(
                    contents=contents,
                    generation_config=generation_config
                )

            # Extract text
            response_text = response.text

            # Extract sources from grounding metadata (in candidates)
            sources = []
            try:
                if hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                            gm = candidate.grounding_metadata

                            # Extract from grounding_chunks
                            if hasattr(gm, 'grounding_chunks'):
                                for chunk in gm.grounding_chunks:
                                    source_info = {"type": "knowledge_base"}

                                    if hasattr(chunk, 'retrieved_context'):
                                        ctx = chunk.retrieved_context
                                        if hasattr(ctx, 'title'):
                                            source_info["title"] = ctx.title
                                        if hasattr(ctx, 'uri'):
                                            source_info["uri"] = ctx.uri

                                    if hasattr(chunk, 'relevance_score'):
                                        source_info["relevance_score"] = chunk.relevance_score

                                    sources.append(source_info)

                logger.info("sources_extracted", count=len(sources))
            except Exception as e:
                logger.error("source_extraction_failed", error=str(e), exc_info=True)

            logger.info(
                "chat_response_generated",
                analysis_id=analysis_id,
                response_length=len(response_text),
                sources_count=len(sources)
            )

            return ChatResponse(
                message=response_text,
                sources=sources,
                grounded=len(sources) > 0
            )

        except Exception as e:
            logger.error(
                "chat_generation_failed",
                error=str(e),
                analysis_id=analysis_id
            )
            raise

    async def chat_without_analysis(
        self,
        message: str,
        history: List[ChatMessage]
    ) -> ChatResponse:
        """
        General chat about injection molding (no specific analysis).

        Args:
            message: User's question
            history: Previous conversation messages

        Returns:
            ChatResponse with AI response
        """
        try:
            logger.info("general_chat_processing", message_preview=message[:100])

            # System prompt for general molding questions
            system_prompt = """You are an expert injection molding engineer with deep knowledge of:
- Design for Manufacturability (DFM) principles
- GD&T (Geometric Dimensioning and Tolerancing)
- Material properties and selection
- Mold design and tooling
- Common molding defects and their root causes
- Industry standards and best practices

Provide clear, technical, and actionable advice about injection molding.
Always cite sources when applicable.
"""

            # Format history
            contents = self._format_chat_history(history)

            # Add system prompt if history is empty
            if not contents:
                contents.append(
                    Content(
                        role="user",
                        parts=[Part.from_text(system_prompt)]
                    )
                )
                contents.append(
                    Content(
                        role="model",
                        parts=[Part.from_text(
                            "I'm here to help with injection molding questions. What would you like to know?"
                        )]
                    )
                )

            # Add current message
            contents.append(
                Content(
                    role="user",
                    parts=[Part.from_text(message)]
                )
            )

            # Generate response with grounding
            generation_config = GenerationConfig(
                temperature=0.4,
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048,
            )

            # Enable grounding with RAG
            tools = []
            if settings.rag_data_store_id:
                try:
                    from vertexai.preview.generative_models import Tool
                    from vertexai.preview import rag

                    grounding_tool = Tool.from_retrieval(
                        retrieval=rag.Retrieval(
                            source=rag.VertexRagStore(
                                rag_resources=[
                                    rag.RagResource(
                                        rag_corpus=settings.rag_data_store_id,
                                    )
                                ],
                                similarity_top_k=10,
                                vector_distance_threshold=0.5,  # More lenient
                            )
                        )
                    )
                    tools.append(grounding_tool)
                    logger.info("general_chat_grounding_enabled")
                except ImportError as e:
                    logger.warning("grounding_import_failed", error=str(e))
                except Exception as e:
                    logger.error("grounding_setup_failed", error=str(e))

            # Generate response
            if tools:
                response = self.model.generate_content(
                    contents=contents,
                    generation_config=generation_config,
                    tools=tools
                )
            else:
                response = self.model.generate_content(
                    contents=contents,
                    generation_config=generation_config
                )

            response_text = response.text

            # Extract sources from grounding metadata (in candidates)
            sources = []
            try:
                if hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                            gm = candidate.grounding_metadata

                            # Extract from grounding_chunks
                            if hasattr(gm, 'grounding_chunks'):
                                for chunk in gm.grounding_chunks:
                                    source_info = {"type": "knowledge_base"}

                                    if hasattr(chunk, 'retrieved_context'):
                                        ctx = chunk.retrieved_context
                                        if hasattr(ctx, 'title'):
                                            source_info["title"] = ctx.title
                                        if hasattr(ctx, 'uri'):
                                            source_info["uri"] = ctx.uri

                                    sources.append(source_info)

                logger.info("general_chat_sources_extracted", count=len(sources))
            except Exception as e:
                logger.error("general_source_extraction_failed", error=str(e), exc_info=True)

            logger.info(
                "general_chat_response_generated",
                response_length=len(response_text),
                grounded=len(tools) > 0,
                sources_count=len(sources)
            )

            return ChatResponse(
                message=response_text,
                sources=sources,
                grounded=len(tools) > 0  # Grounded if RAG tools were used
            )

        except Exception as e:
            logger.error("general_chat_failed", error=str(e))
            raise

    async def unified_chat(
        self,
        message: str,
        history: List[ChatMessage],
        file: Optional[Any] = None
    ) -> ChatResponse:
        """
        Unified chat that handles both general chat and file analysis in one flow.
        
        Args:
            message: User's message
            history: Conversation history
            file: Optional PDF file for analysis
            
        Returns:
            ChatResponse with AI response and sources
        """
        try:
            logger.info(
                "unified_chat_processing",
                message_preview=message[:100],
                has_file=file is not None
            )

            # If file is provided, analyze it first
            analysis_context = ""
            if file:
                from src.services.drawing_analyzer import DrawingAnalyzer
                drawing_analyzer = DrawingAnalyzer()
                
                # Read file content
                file_content = await file.read()
                file.filename = file.filename  # Ensure filename is set
                
                # Analyze the drawing
                analysis = await drawing_analyzer.analyze_drawing_from_pdf(file_content)
                
                # Build context from analysis
                analysis_context = self._build_analysis_from_object(analysis)
                
                # Reset file pointer
                await file.seek(0)

            # Use the analysis context to build enhanced system prompt
            system_prompt = self._build_enhanced_system_prompt(analysis_context)

            # Format history
            contents = self._format_chat_history(history)

            # Add system prompt if history is empty
            if not contents:
                contents.append(
                    Content(
                        role="user",
                        parts=[Part.from_text(system_prompt)]
                    )
                )
                contents.append(
                    Content(
                        role="model",
                        parts=[Part.from_text(
                            "¡Hola! Soy tu experto en moldeo por inyección. Puedo ayudarte con análisis de planos técnicos y responder preguntas sobre diseño de moldeo. ¿En qué puedo ayudarte hoy?"
                        )]
                    )
                )

            # Add current message
            contents.append(
                Content(
                    role="user",
                    parts=[Part.from_text(message)]
                )
            )

            # Generate response with grounding
            generation_config = GenerationConfig(
                temperature=0.3,  # Balance between creativity and accuracy
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,  # Increased for detailed responses
            )

            # Enable grounding with RAG
            tools = []
            if settings.rag_data_store_id:
                try:
                    from vertexai.preview.generative_models import Tool
                    from vertexai.preview import rag

                    grounding_tool = Tool.from_retrieval(
                        retrieval=rag.Retrieval(
                            source=rag.VertexRagStore(
                                rag_resources=[
                                    rag.RagResource(
                                        rag_corpus=settings.rag_data_store_id,
                                    )
                                ],
                                similarity_top_k=10,
                                vector_distance_threshold=0.5,  # More lenient
                            )
                        )
                    )
                    tools.append(grounding_tool)
                    logger.info("unified_chat_grounding_enabled")
                except ImportError as e:
                    logger.warning("grounding_import_failed", error=str(e))
                except Exception as e:
                    logger.error("grounding_setup_failed", error=str(e))

            # Generate response
            if tools:
                response = self.model.generate_content(
                    contents=contents,
                    generation_config=generation_config,
                    tools=tools
                )
            else:
                response = self.model.generate_content(
                    contents=contents,
                    generation_config=generation_config
                )

            response_text = response.text

            # Extract sources from grounding metadata (in candidates)
            sources = []
            try:
                if hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                            gm = candidate.grounding_metadata

                            # Extract from grounding_chunks
                            if hasattr(gm, 'grounding_chunks'):
                                for chunk in gm.grounding_chunks:
                                    source_info = {"type": "knowledge_base"}

                                    if hasattr(chunk, 'retrieved_context'):
                                        ctx = chunk.retrieved_context
                                        if hasattr(ctx, 'title'):
                                            source_info["title"] = ctx.title
                                        if hasattr(ctx, 'uri'):
                                            source_info["uri"] = ctx.uri

                                    sources.append(source_info)

                logger.info("unified_chat_sources_extracted", count=len(sources))
            except Exception as e:
                logger.error("unified_source_extraction_failed", error=str(e), exc_info=True)

            logger.info(
                "unified_chat_response_generated",
                response_length=len(response_text),
                sources_count=len(sources),
                has_analysis_context=bool(analysis_context)
            )

            return ChatResponse(
                message=response_text,
                sources=sources,
                grounded=len(sources) > 0
            )

        except Exception as e:
            logger.error("unified_chat_failed", error=str(e))
            raise

    async def _upload_pdf_to_gcs(self, file_content: bytes, filename: str) -> str:
        """
        Upload PDF to GCS for use with Part.from_uri (File API approach).

        This enables preprocessing like gemini.google.com:
        - Automatic page scaling (768x768 to 3072x3072)
        - Chunking optimization
        - Format standardization

        Args:
            file_content: PDF bytes
            filename: Original filename

        Returns:
            GCS URI (gs://bucket/path)
        """
        try:
            # Use temporary chat uploads bucket
            bucket = self.storage_client.bucket(settings.gcs_bucket_manuals)

            # Create temporary path: temp-chat/{uuid}/{filename}
            temp_id = str(uuid.uuid4())
            blob_path = f"temp-chat/{temp_id}/{filename}"
            blob = bucket.blob(blob_path)

            # Upload with metadata
            blob.metadata = {
                "uploaded_at": datetime.now().isoformat(),
                "purpose": "temporary_chat_analysis",
                "ttl_hours": "24"  # For cleanup
            }

            blob.upload_from_string(file_content, content_type="application/pdf")

            gcs_uri = f"gs://{settings.gcs_bucket_manuals}/{blob_path}"

            logger.info(
                "pdf_uploaded_to_gcs_for_chat",
                gcs_uri=gcs_uri,
                size_bytes=len(file_content)
            )

            return gcs_uri

        except Exception as e:
            logger.error("pdf_upload_to_gcs_failed", error=str(e))
            raise

    async def unified_chat_with_file(
        self,
        message: str,
        history: List[ChatMessage],
        file: Any
    ) -> ChatResponse:
        """
        Two-stage analysis: PDF extraction + Knowledge Base analysis.

        Stage 1: Extract technical specifications from PDF (using GCS + Part.from_uri)
        Stage 2: Analyze extracted specs with RAG grounding from Knowledge Base

        This combines visual PDF analysis with expert knowledge from manuals.
        Uses File API approach (GCS) for optimal multimodal processing like gemini.google.com.

        Args:
            message: User's message
            history: Conversation history
            file: PDF file to analyze

        Returns:
            ChatResponse with unified analysis + sources
        """
        try:
            logger.info(
                "two_stage_pdf_analysis_start",
                filename=file.filename,
                message_preview=message[:100]
            )

            # Read file content
            file_content = await file.read()

            # Upload PDF to GCS for File API approach (preprocessing like gemini.google.com)
            gcs_uri = await self._upload_pdf_to_gcs(file_content, file.filename)

            # ═══════════════════════════════════════════════════════════════
            # STAGE 1: Extract technical specs from PDF (using GCS URI)
            # ═══════════════════════════════════════════════════════════════

            from src.config.prompts import prompts_config

            extraction_prompt = prompts_config.get_prompt("pdf_extraction")

            logger.info("stage_1_extracting_specs", filename=file.filename, gcs_uri=gcs_uri)

            # Create extraction request with Part.from_uri (File API approach)
            extraction_contents = [
                Content(
                    role="user",
                    parts=[
                        Part.from_uri(
                            uri=gcs_uri,  # Correct parameter: 'uri' not 'file_uri'
                            mime_type="application/pdf"
                        ),
                        Part.from_text(extraction_prompt)
                    ]
                )
            ]

            generation_config = GenerationConfig(
                temperature=0.3,  # Lower for precise extraction
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048,
            )

            # Extract specs (no grounding needed)
            extraction_response = self.model.generate_content(
                contents=extraction_contents,
                generation_config=generation_config
            )

            extracted_specs = extraction_response.text
            logger.info("stage_1_complete", specs_length=len(extracted_specs))

            # ═══════════════════════════════════════════════════════════════
            # STAGE 2: Analyze with Knowledge Base grounding
            # ═══════════════════════════════════════════════════════════════

            kb_analysis_prompt_template = prompts_config.get_prompt("kb_analysis")
            # Use replace() instead of format() to avoid conflicts with literal curly braces in prompt
            kb_analysis_prompt = kb_analysis_prompt_template.replace(
                "{extracted_specs}", extracted_specs
            )

            logger.info("stage_2_kb_analysis", prompt_length=len(kb_analysis_prompt))

            # Format history for stage 2
            contents = self._format_chat_history(history)
            contents.append(
                Content(
                    role="user",
                    parts=[Part.from_text(kb_analysis_prompt)]
                )
            )

            # Enable RAG grounding for stage 2
            tools = []
            if settings.rag_data_store_id:
                try:
                    from vertexai.preview.generative_models import Tool
                    from vertexai.preview import rag

                    grounding_tool = Tool.from_retrieval(
                        retrieval=rag.Retrieval(
                            source=rag.VertexRagStore(
                                rag_resources=[
                                    rag.RagResource(
                                        rag_corpus=settings.rag_data_store_id,
                                    )
                                ],
                                similarity_top_k=10,
                                vector_distance_threshold=0.5,
                            )
                        )
                    )
                    tools.append(grounding_tool)
                    logger.info("stage_2_grounding_enabled")
                except Exception as e:
                    logger.warning("grounding_setup_failed", error=str(e))

            # Generate KB analysis with grounding
            generation_config.temperature = 0.4  # Slightly higher for analysis
            generation_config.max_output_tokens = 3072  # More tokens for detailed analysis

            if tools:
                kb_response = self.model.generate_content(
                    contents=contents,
                    generation_config=generation_config,
                    tools=tools
                )
            else:
                kb_response = self.model.generate_content(
                    contents=contents,
                    generation_config=generation_config
                )

            kb_analysis = kb_response.text
            logger.info("stage_2_complete", analysis_length=len(kb_analysis))

            # Extract sources from KB grounding
            sources = []
            try:
                if hasattr(kb_response, 'candidates') and kb_response.candidates:
                    for candidate in kb_response.candidates:
                        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                            gm = candidate.grounding_metadata

                            if hasattr(gm, 'grounding_chunks'):
                                for chunk in gm.grounding_chunks:
                                    source_info = {"type": "knowledge_base"}

                                    if hasattr(chunk, 'retrieved_context'):
                                        ctx = chunk.retrieved_context
                                        if hasattr(ctx, 'title'):
                                            source_info["title"] = ctx.title
                                        if hasattr(ctx, 'uri'):
                                            source_info["uri"] = ctx.uri

                                    sources.append(source_info)

                logger.info("sources_extracted_from_kb", count=len(sources))
            except Exception as e:
                logger.error("source_extraction_failed", error=str(e))

            # Add PDF as source
            sources.insert(0, {
                "type": "uploaded_pdf",
                "title": file.filename
            })

            # ═══════════════════════════════════════════════════════════════
            # Combine results using template (Jinja2 for complex templates)
            # ═══════════════════════════════════════════════════════════════

            unified_template_str = prompts_config.get_prompt("unified_response")

            # Try to parse as JSON if template uses Jinja2 syntax
            try:
                # Attempt to parse extraction and analysis as JSON
                try:
                    extraction_data = json.loads(extracted_specs) if isinstance(extracted_specs, str) else extracted_specs
                except (json.JSONDecodeError, TypeError):
                    extraction_data = {"raw": extracted_specs}

                try:
                    kb_analysis_data = json.loads(kb_analysis) if isinstance(kb_analysis, str) else kb_analysis
                except (json.JSONDecodeError, TypeError):
                    kb_analysis_data = {"raw": kb_analysis}

                # Try Jinja2 rendering first (for complex templates)
                jinja_template = Template(unified_template_str)
                final_response = jinja_template.render(
                    extraction_result=extraction_data,
                    kb_analysis_result=kb_analysis_data,
                    conclusion="El análisis está completo. Si necesitas más detalles sobre algún aspecto específico, pregúntame."
                )
            except (TemplateError, Exception) as e:
                # Fallback to simple format() for simple templates
                logger.warning("jinja2_render_failed_using_format", error=str(e))
                final_response = unified_template_str.format(
                    extraction_result=extracted_specs,
                    kb_analysis_result=kb_analysis,
                    conclusion="El análisis está completo. Si necesitas más detalles sobre algún aspecto específico, pregúntame."
                )

            logger.info(
                "two_stage_analysis_complete",
                total_response_length=len(final_response),
                sources_count=len(sources),
                pdf_filename=file.filename
            )

            return ChatResponse(
                message=final_response,
                sources=sources,
                grounded=True
            )

        except Exception as e:
            logger.error("two_stage_analysis_failed", error=str(e), filename=file.filename)
            raise

    async def chat_stream(
        self,
        analysis_id: str,
        message: str,
        history: List[ChatMessage]
    ):
        """
        Stream chat responses for better UX.

        Yields response chunks as they are generated.
        Recommended by Vertex AI guide for interactive chat experiences.

        Args:
            analysis_id: ID of analysis to discuss
            message: User's question or message
            history: Previous conversation messages

        Yields:
            str: Response chunks as they are generated
        """
        try:
            logger.info(
                "chat_stream_processing",
                analysis_id=analysis_id,
                message_preview=message[:100]
            )

            # Build context from analysis
            analysis_context = self._build_analysis_context(analysis_id)

            # Build system prompt
            system_prompt = self._build_system_prompt(analysis_context)

            # Format history
            contents = self._format_chat_history(history)

            # Add system prompt if history is empty
            if not contents:
                contents.append(
                    Content(
                        role="user",
                        parts=[Part.from_text(system_prompt)]
                    )
                )
                contents.append(
                    Content(
                        role="model",
                        parts=[Part.from_text(
                            "I understand. I'm ready to help analyze this injection molding drawing. "
                            "What would you like to know?"
                        )]
                    )
                )

            # Add current message
            contents.append(
                Content(
                    role="user",
                    parts=[Part.from_text(message)]
                )
            )

            # Configure generation with grounding
            generation_config = GenerationConfig(
                temperature=0.3,
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048,
            )

            # Enable grounding
            tools = []
            if settings.rag_data_store_id:
                try:
                    from vertexai.preview.generative_models import Tool
                    from vertexai.preview import rag

                    grounding_tool = Tool.from_retrieval(
                        retrieval=rag.Retrieval(
                            source=rag.VertexRagStore(
                                rag_resources=[
                                    rag.RagResource(
                                        rag_corpus=settings.rag_data_store_id,
                                    )
                                ],
                                similarity_top_k=10,
                                vector_distance_threshold=0.5,  # More lenient
                            )
                        )
                    )
                    tools.append(grounding_tool)
                    logger.info("streaming_grounding_enabled")
                except Exception as e:
                    logger.error("streaming_grounding_failed", error=str(e))

            # Generate streaming response
            response = self.model.generate_content(
                contents=contents,
                generation_config=generation_config,
                tools=tools if tools else None,
                stream=True  # Enable streaming
            )

            # Stream chunks as they arrive
            for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text

            logger.info("chat_stream_completed", analysis_id=analysis_id)

        except Exception as e:
            logger.error(
                "chat_stream_failed",
                error=str(e),
                analysis_id=analysis_id
            )
            raise

    def _build_analysis_from_object(self, analysis) -> str:
        """Build context string from DrawingAnalysis object."""
        context_parts = [
            "=== ANÁLISIS DE PLANO TÉCNICO ===",
            f"Parte: {analysis.part_name or 'No especificada'}",
            f"ID: {analysis.part_id or 'No especificado'}",
            f"Material: {analysis.material or 'No especificado'}",
            "",
            "DIMENSIONES ENCONTRADAS:"
        ]
        
        # Add dimensions
        if analysis.dimensions:
            for i, dim in enumerate(analysis.dimensions[:10], 1):  # Limit to first 10
                context_parts.append(
                    f"{i}. {dim.feature}: {dim.value} {dim.unit}"
                    + (f" ±{dim.tolerance}" if dim.tolerance else "")
                    + f" (confianza: {dim.confidence:.2f})" if dim.confidence else ""
                )
        
        context_parts.extend([
            "",
            "ESPECIFICACIONES GD&T:",
        ])
        
        # Add GD&T
        if analysis.gdandt:
            for i, gd in enumerate(analysis.gdandt[:5], 1):  # Limit to first 5
                context_parts.append(f"{i}. {gd.symbol}: {gd.value}")
                if gd.datum_reference:
                    context_parts.append(f"   Referencia: {gd.datum_reference}")
        else:
            context_parts.append("No se encontraron especificaciones GD&T.")
            
        # Add notes
        if analysis.notes:
            context_parts.extend([
                "",
                "NOTAS Y ESPECIFICACIONES:"
            ])
            for note in analysis.notes[:5]:  # Limit to first 5
                context_parts.append(f"• {note}")
        
        context_parts.extend([
            "",
            "Este análisis ha sido generado usando IA avanzada y debe ser validado por un ingeniero experto.",
            "Proporciona consejos específicos basados en este análisis cuando respondas."
        ])
        
        return "\n".join(context_parts)

    def _build_enhanced_system_prompt(self, analysis_context: str) -> str:
        """Build enhanced system prompt with analysis context."""
        base_prompt = """Eres un experto ingeniero en moldeo por inyección con conocimiento profundo de:
- Diseño para Manufacturabilidad (DFM)
- GD&T (Geometric Dimensioning and Tolerancing)  
- Propiedades y selección de materiales
- Diseño de moldes y herramientas
- Defectos comunes de moldeo y sus causas raíz
- Estándares y mejores prácticas de la industria

Tu especialidad es analizar planos técnicos y proporcionar consejos prácticos para viabilidad de moldeo por inyección.

INSTRUCCIONES:
1. Proporciona consejos claros, técnicos y accionables
2. Siempre cita fuentes de la base de conocimiento cuando sea aplicable
3. Si no tienes suficiente información, dilo claramente
4. Enfócate en soluciones prácticas y recomendaciones
5. Explica conceptos técnicos claramente
6. Referencia dimensiones, tolerancias o llamadas GD&T específicas cuando sea relevante
7. Identifica defectos potenciales de moldeo y sugiere estrategias de mitigación

ESTILO DE RESPUESTA:
- Sé conciso pero completo
- Usa terminología técnica correctamente
- Proporciona ejemplos cuando sea útil
- Estructura respuestas con puntos o listas numeradas para claridad
- Responde en español"""
        
        if analysis_context:
            base_prompt += f"""

=== CONTEXTO DE ANÁLISIS TÉCNICO ===
{analysis_context}

Cuando respondas, usa este análisis como base principal para tus recomendaciones.
Compara las dimensiones y especificaciones encontradas con las mejores prácticas.
Si encuentras problemas potenciales, explícalos claramente con soluciones."""
        
        return base_prompt

    def _format_analysis_summary(self, analysis) -> str:
        """Format analysis summary for user-facing responses."""
        summary = f"📋 **Análisis Completo del Plano: {analysis.part_name or 'Sin nombre'}**\n\n"
        
        # Basic info
        summary += f"**🏷️ Identificación:**\n"
        if analysis.part_id:
            summary += f"- **ID:** {analysis.part_id}\n"
        if analysis.material:
            summary += f"- **Material:** {analysis.material}\n"
        
        # Dimensions summary
        summary += f"\n**📏 Dimensiones Encontradas:** {len(analysis.dimensions)} dimensiones extraídas\n"
        if analysis.dimensions:
            # Show first few key dimensions
            key_dims = analysis.dimensions[:3]
            for dim in key_dims:
                summary += f"- **{dim.feature}:** {dim.value} {dim.unit}"
                if dim.tolerance:
                    summary += f" ±{dim.tolerance}"
                summary += "\n"
        
        # GD&T summary
        summary += f"\n**🎯 Especificaciones GD&T:** {len(analysis.gdandt)} elementos encontrados\n"
        if analysis.gdandt:
            for gd in analysis.gdandt[:2]:  # Show first 2
                summary += f"- **{gd.symbol}:** {gd.value}\n"
        
        # Analysis notes
        if analysis.analysis_notes:
            summary += f"\n**💡 Observaciones:**\n{analysis.analysis_notes}\n"
            
        summary += "\n¿Qué aspecto específico del diseño te gustaría que analice o mejore?"
        
        return summary

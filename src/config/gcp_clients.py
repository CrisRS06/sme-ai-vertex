"""
Centralized initialization for Google Cloud Platform clients.
Sets up Vertex AI (RAG Engine GA 2025), context caching and vector search access.
"""
from functools import lru_cache
from threading import Lock
from typing import Optional

import vertexai
from google.cloud import documentai_v1, storage
from google.cloud.aiplatform import MatchingEngineIndex, MatchingEngineIndexEndpoint

try:
    # GA 2025 RAG Engine surface
    from vertexai import rag as vertex_rag
except ImportError:  # pragma: no cover - fallback for older SDKs
    vertex_rag = None

try:
    from vertexai.generative_models import GenerativeModel
    # Context caching (GA 2025). Keep optional for older SDKs.
    from vertexai.generative_models import caching as context_caching  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - graceful fallback
    try:
        from vertexai.preview.generative_models import GenerativeModel  # type: ignore[assignment]
    except ImportError:
        GenerativeModel = None  # type: ignore[assignment]
    context_caching = None  # type: ignore[assignment]

from src.config.settings import settings

_vertex_ai_lock = Lock()
_vertex_ai_initialized = False


def init_vertex_ai(force: bool = False) -> None:
    """
    Initialize Vertex AI once per process.

    Args:
        force: Re-run initialization even if it already ran.
    """
    global _vertex_ai_initialized
    if _vertex_ai_initialized and not force:
        return

    with _vertex_ai_lock:
        if _vertex_ai_initialized and not force:
            return

        vertexai.init(
            project=settings.gcp_project_id,
            location=settings.gcp_location,
        )
        _vertex_ai_initialized = True


@lru_cache()
def get_storage_client() -> storage.Client:
    """Return a singleton Google Cloud Storage client."""
    return storage.Client(project=settings.gcp_project_id)


@lru_cache()
def get_documentai_client() -> documentai_v1.DocumentProcessorServiceClient:
    """Return a singleton Document AI client."""
    return documentai_v1.DocumentProcessorServiceClient()


def get_rag_module():
    """
    Expose the GA Vertex AI RAG module, ensuring Vertex AI is initialized.

    Returns:
        vertexai.rag module ready for use.

    Raises:
        RuntimeError: if RAG Engine is not available in the current SDK.
    """
    init_vertex_ai()

    if vertex_rag is None:
        raise RuntimeError(
            "Vertex AI RAG Engine is not available. "
            "Upgrade google-cloud-aiplatform to >=1.82.0."
        )
    return vertex_rag


def get_generative_model(
    model_name: str,
    *,
    cache_ttl_seconds: Optional[int] = None,
    max_context_cache_entries: int = 32,
) -> GenerativeModel:
    """
    Create a GenerativeModel instance with optional context caching.

    Args:
        model_name: Vertex AI model identifier (e.g., gemini-2.5-flash).
        cache_ttl_seconds: Enable context caching when provided.
        max_context_cache_entries: Max cached contexts retained by Vertex AI.

    Returns:
        Configured GenerativeModel instance.
    """
    init_vertex_ai()

    if GenerativeModel is None:
        raise RuntimeError(
            "GenerativeModel class not available. "
            "Ensure google-cloud-aiplatform>=1.82.0 is installed."
        )

    if cache_ttl_seconds and context_caching:
        try:
            cache = context_caching.ContextCache(
                max_context_entries=max_context_cache_entries,
                ttl_seconds=cache_ttl_seconds,
            )
            return GenerativeModel(
                model_name=model_name,
                caching_config=context_caching.CachingConfig(context_cache=cache),
            )
        except Exception:  # noqa: BLE001 - fallback to default instantiation
            pass

    return GenerativeModel(model_name=model_name)


def get_vector_search_index():
    """Return the configured Vertex AI Vector Search index, if any."""
    if not settings.vector_search_index_id:
        return None

    init_vertex_ai()
    return MatchingEngineIndex(index_name=settings.vector_search_index_id)


def get_vector_search_endpoint():
    """Return the configured Vertex AI Vector Search endpoint, if any."""
    if not settings.vector_search_endpoint_id:
        return None

    init_vertex_ai()
    return MatchingEngineIndexEndpoint(
        index_endpoint_name=settings.vector_search_endpoint_id
    )

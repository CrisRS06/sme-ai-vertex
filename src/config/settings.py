"""
Application settings and configuration.
Loads environment variables and provides centralized config access.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google Cloud Platform
    gcp_project_id: str
    gcp_region: str = "us-central1"
    gcp_location: str = "us-central1"
    google_application_credentials: str = "./service-account-key.json"

    # Cloud Storage Buckets
    gcs_bucket_manuals: str = "sme-ai-manuals"
    gcs_bucket_drawings: str = "sme-ai-drawings"
    gcs_bucket_reports: str = "sme-ai-reports"

    # Vertex AI Models
    vertex_ai_model_flash: str = "gemini-2.5-flash"
    vertex_ai_model_pro: str = "gemini-2.5-pro"
    vertex_ai_embedding_model: str = "multimodalembedding@001"

    # RAG Engine
    rag_corpus_name: str = "molding-knowledge-base"
    vector_search_index_id: str = ""
    vector_search_endpoint_id: str = ""
    vector_search_deployed_index_id: str = ""

    # Document AI
    documentai_processor_id: str = ""

    # API Configuration
    api_key: str = "development-key-change-in-production"
    jwt_secret_key: str = "super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # Application Settings
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "INFO"
    max_upload_size_mb: int = 50

    # RAG Engine (Vertex AI Search) - REQUIRED for production
    # Run: ./scripts/setup_rag_engine.sh PROJECT_ID REGION
    rag_data_store_id: Optional[str] = None
    enable_grounding: bool = True  # Always use grounding (Gemini knowledge + RAG)

    # Document AI (OCR Fallback) - REQUIRED for production (no data loss)
    # Run: ./scripts/setup_document_ai.sh PROJECT_ID
    document_ai_processor_id: Optional[str] = None
    ocr_confidence_threshold: float = 0.7  # Trigger OCR if VLM confidence < threshold
    enable_document_ai_fallback: bool = True  # Always enabled

    # Feature Flags
    quality_mode: Literal["flash", "pro"] = "flash"
    enable_chat: bool = True

    # Rate Limiting
    rate_limit_per_minute: int = 10

    # Report Generation
    report_template_dir: str = "./templates"
    report_output_format: Literal["pdf", "html"] = "pdf"

    # Database
    sqlite_db_path: str = "./data/sme_ai.db"
    vector_registry_db_path: str = "./data/vector_registry.db"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to load settings only once.
    """
    return Settings()


# Convenience accessor
settings = get_settings()

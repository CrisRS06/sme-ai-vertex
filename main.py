"""
SME AI Vertex - Injection Molding Feasibility Analysis
FastAPI application entry point.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog
from datetime import datetime

from src.config.settings import settings
from src.api import knowledgebase, analysis, chat, search, metrics

# Initialize structured logger
logger = structlog.get_logger()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="SME AI Vertex - Molding Feasibility Analysis",
    description="""
    AI-powered injection molding feasibility analysis system.

    **Features:**
    - Upload and index molding knowledge base (manuals, specifications)
    - Analyze technical drawings for feasibility
    - Generate exception reports (Executive & Detailed)
    - Chat with AI expert about analysis

    **Aligned with Michael's priorities:**
    - Accuracy and thoroughness
    - Exception detection (dimensions, GD&T, tolerances)
    - Pre-acceptance technical assessment
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup."""
    logger.info("sme_ai_startup", version="0.1.0")

    # Check production-critical configurations
    warnings = []

    if not settings.rag_data_store_id:
        warnings.append("⚠️  RAG_DATA_STORE_ID not configured - Chat will not be grounded in knowledge base")
        warnings.append("   Run: ./scripts/setup_rag_engine.sh PROJECT_ID REGION")

    if not settings.document_ai_processor_id:
        warnings.append("⚠️  DOCUMENT_AI_PROCESSOR_ID not configured - OCR fallback disabled")
        warnings.append("   Run: ./scripts/setup_document_ai.sh PROJECT_ID")

    if warnings:
        logger.warning("production_features_not_configured")
        print("\n" + "=" * 80)
        print("⚠️  PRODUCTION-CRITICAL FEATURES NOT CONFIGURED")
        print("=" * 80)
        for warning in warnings:
            print(warning)
        print("=" * 80)
        print("System will work but with reduced capabilities.")
        print("Configure these for production use.\n")
    else:
        logger.info("all_production_features_configured")
        print("\n✅ All production features configured!\n")


# Include routers
app.include_router(
    knowledgebase.router,
    prefix="/knowledgebase",
    tags=["Knowledge Base"]
)

app.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["Analysis"]
)

app.include_router(
    chat.router,
    prefix="/analysis",
    tags=["Chat"]
)

app.include_router(
    search.router,
    prefix="/search",
    tags=["Vector Search"]
)

app.include_router(
    metrics.router,
    prefix="/metrics",
    tags=["Metrics"]
)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs."""
    return {
        "message": "SME AI Vertex API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    from src.models.schemas import HealthCheck

    # Check production-critical services
    rag_status = "configured" if settings.rag_data_store_id else "not_configured_warning"
    ocr_status = "configured" if settings.document_ai_processor_id else "not_configured_warning"

    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version="0.1.0",
        services={
            "gcp": "configured" if settings.gcp_project_id else "not_configured",
            "vertex_ai": "enabled",
            "knowledge_base": "ready",
            "rag_grounding": rag_status,
            "document_ai_ocr": ocr_status,
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc)
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

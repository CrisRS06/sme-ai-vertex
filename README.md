# SME AI Vertex - Injection Molding Feasibility Analysis

AI-powered system for analyzing technical drawings and generating feasibility exception reports for injection molding projects.

**Aligned with Michael's Vision:**
- Accuracy and thoroughness in technical assessment
- Pre-acceptance exception reports
- Detect dimensioning issues, GD&T problems, molding defect risks
- Executive + Detailed reports for client sign-off
- AI expert chat with grounding

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Deployment](#deployment)
- [Usage Examples](#usage-examples)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)

---

## Overview

This system provides:

1. **Knowledge Base Management**
   - Upload molding manuals, specifications, material libraries
   - Automatic indexing with RAG Engine
   - Semantic search across documentation

2. **Drawing Analysis**
   - Upload technical drawings (PDF)
   - Extract dimensions, tolerances, GD&T specifications
   - Visual analysis with Gemini 2.5 VLM
   - Structured JSON output with response_schema

3. **Exception Detection**
   - Validate against molding best practices
   - Detect: dimensional issues, draft problems, undercuts, material concerns
   - Identify molding defect risks: flash, short shot, warp, knit lines
   - Categorize by severity (critical, warning, info)
   

4. **Report Generation**
   - **Executive Report**: Summary for client sign-off (1-2 pages)
   - **Detailed Report**: Complete technical analysis with evidence
   - PDF/HTML export with signed URLs

5. **AI Expert Chat**
   - Conversational interface about analysis
   - Grounded responses with source citations
   - Context-aware using RAG + analysis results

---

## Architecture

### Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **AI/ML**: Google Vertex AI
  - Gemini 2.5 Flash/Pro (VLM for drawing analysis)
  - Multimodal Embeddings (visual search)
  - RAG Engine (knowledge base)
- **Storage**: Google Cloud Storage
- **Deployment**: Cloud Run (serverless containers)
- **Frontend**: Vercel (separate repo, connects via API)

### System Flow

```
1. Knowledge Base Setup
   Manuals (PDF) → GCS → RAG Engine → Vector Search Index

2. Drawing Analysis Pipeline
   Drawing (PDF) → PNG (300 DPI) → Multimodal Embeddings → Vector Search
                  ↓
   Gemini 2.5 VLM → JSON (response_schema)
                  ↓
   Exception Engine → Best Practices Validation
                  ↓
   Report Generator → Executive + Detailed Reports → GCS (signed URLs)

3. Chat Interface
   User Query → RAG Retrieval (KB + Drawing) → Gemini 2.5 → Grounded Response
```

---

## Prerequisites

### Required Tools

- **Python 3.11+**
- **gcloud CLI** ([install](https://cloud.google.com/sdk/docs/install))
- **Docker** (for Cloud Run deployment)
- **Git**

### GCP Account

- Active GCP project with billing enabled
- Project Editor or Owner permissions
- APIs to enable (automated by setup script):
  - Vertex AI
  - Cloud Storage
  - Document AI
  - Cloud Run
  - Cloud Build

---

## Quick Start

### 1. Clone & Setup

```bash
# Clone repository
git clone <your-repo-url>
cd "SME AI Vertex"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure GCP

Run the automated setup script:

```bash
./scripts/setup_gcp.sh YOUR_PROJECT_ID us-central1
./scripts/setup_vector_search.sh YOUR_PROJECT_ID us-central1 sme-vector-index
```

This script will:
- Enable required APIs
- Create Cloud Storage buckets
- Create service account with proper permissions
- Generate service account key
- Create `.env` file with configuration
- Provision Vertex AI Vector Search index + endpoint and output env variables

### 3. Run Locally

```bash
# Make sure .env file exists (created by setup script)
# Or copy from .env.example and fill in values

# Run the application
python main.py
```

The API will be available at http://localhost:8080

- Docs: http://localhost:8080/docs
- Health: http://localhost:8080/health

### 4. Deploy to Cloud Run

```bash
./scripts/deploy_cloudrun.sh YOUR_PROJECT_ID us-central1
```

---

## Project Structure

```
SME AI Vertex/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container definition for Cloud Run
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
│
├── src/
│   ├── api/                     # API endpoints (routers)
│   │   ├── knowledgebase.py     # Knowledge base management
│   │   ├── analysis.py          # Drawing analysis
│   │   └── chat.py              # Chat interface
│   │
│   ├── models/                  # Pydantic models
│   │   ├── schemas.py           # API request/response schemas
│   │   ├── drawing_analysis.py  # VLM response schema
│   │   └── exceptions.py        # Exception models
│   │
│   ├── services/                # Business logic
│   │   ├── knowledge_base.py    # KB ingestion & RAG
│   │   ├── drawing_processor.py # PDF→PNG, embeddings
│   │   ├── drawing_analyzer.py  # [TODO] VLM analysis
│   │   ├── exception_engine.py  # [TODO] Best practices validation
│   │   ├── report_generator.py  # [TODO] Report generation
│   │   ├── chat_service.py      # [TODO] Chat implementation
│   │   ├── vector_search.py     # Vertex AI / SQLite vector search services
│   │   └── vector_registry.py   # Registro auxiliar de embeddings
│   │
│   ├── config/                  # Configuration
│   │   ├── settings.py          # Environment variables loader
│   │   └── gcp_clients.py       # GCP client initialization
│   │
│   └── utils/                   # Helper utilities
│
├── scripts/                     # Automation scripts
│   ├── setup_gcp.sh             # GCP environment setup
│   ├── setup_vector_search.sh   # Provision Vertex AI Vector Search (Tree-AH)
│   ├── migrate_embeddings_to_vertex.py  # Reindex embeddings to Vertex AI
│   └── deploy_cloudrun.sh       # Cloud Run deployment
│
├── templates/                   # Jinja2 templates for reports
│   ├── executive_report.html    # [TODO]
│   └── detailed_report.html     # [TODO]
│
└── tests/                       # Unit & integration tests
```

---

## API Endpoints

### Knowledge Base

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/knowledgebase/upload` | Upload manual/specification |
| `GET` | `/knowledgebase/documents` | List all documents |
| `GET` | `/knowledgebase/documents/{id}` | Get document details |
| `DELETE` | `/knowledgebase/documents/{id}` | Delete document |
| `GET` | `/knowledgebase/stats` | Get KB statistics |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analysis/upload` | Upload drawing for analysis |
| `GET` | `/analysis/documents` | List all analyses |
| `GET` | `/analysis/{id}` | Get analysis details |
| `GET` | `/analysis/{id}/report` | Get report (executive/detailed) |
| `DELETE` | `/analysis/{id}` | Delete analysis |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analysis/{id}/chat` | Chat about analysis |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/` | API info |

Full API documentation available at `/docs` (Swagger UI) when running.

---

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
# Format code
black src/

# Lint
pylint src/
```

### Adding New Services

1. Create service file in `src/services/`
2. Import and use in API routers (`src/api/`)
3. Add tests in `tests/`
4. Update README

### Environment Variables

Key variables in `.env`:

```bash
# GCP
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Buckets
GCS_BUCKET_MANUALS=project-id-manuals
GCS_BUCKET_DRAWINGS=project-id-drawings
GCS_BUCKET_REPORTS=project-id-reports

# Models
VERTEX_AI_MODEL_FLASH=gemini-2.5-flash
VERTEX_AI_MODEL_PRO=gemini-2.5-pro

# Feature Flags
QUALITY_MODE=flash  # or 'pro' for higher accuracy
ENABLE_DOCUMENT_AI_FALLBACK=true
ENABLE_CHAT=true
```

---

## Deployment

### Local Development

```bash
python main.py
# or
uvicorn main:app --reload --port 8080
```

### Cloud Run

```bash
# One-command deploy
./scripts/deploy_cloudrun.sh YOUR_PROJECT_ID us-central1

# Manual deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/sme-ai-vertex
gcloud run deploy sme-ai-vertex \
  --image gcr.io/PROJECT_ID/sme-ai-vertex \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Migrar embeddings existentes

Para mover los embeddings históricos del fallback local SQLite a Vertex AI Vector Search:

```bash
python scripts/migrate_embeddings_to_vertex.py --batch-size 200
```

El script leerá `data/vector_search.db`, upserteará los vectores en el índice gestionado y registrará una copia auxiliar en `data/vector_registry.db`, habilitando funciones como `get_document_embeddings` en modo Vertex AI.

### CI/CD (GitHub Actions)

[TODO] Add GitHub Actions workflow for automated testing and deployment.

---

## Usage Examples

### 1. Upload Knowledge Base

```bash
curl -X POST "http://localhost:8080/knowledgebase/upload" \
  -F "file=@molding_manual.pdf" \
  -F "document_type=manual"
```

### 2. Analyze Drawing

```bash
curl -X POST "http://localhost:8080/analysis/upload" \
  -F "file=@technical_drawing.pdf" \
  -F "project_name=Gen6" \
  -F "quality_mode=flash"
```

Response:
```json
{
  "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "uploaded_at": "2025-11-02T10:30:00Z",
  "drawing_filename": "technical_drawing.pdf"
}
```

### 3. Get Report

```bash
# Executive report
curl "http://localhost:8080/analysis/123e4567.../report?report_type=executive"

# Detailed report
curl "http://localhost:8080/analysis/123e4567.../report?report_type=detailed"
```

### 4. Chat About Analysis

```bash
curl -X POST "http://localhost:8080/analysis/123e4567.../chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Why is dimension X flagged as critical?",
    "history": []
  }'
```

---

## Roadmap

### Phase 1: MVP (Weeks 1-2) ✅ IN PROGRESS
- [x] Project structure & configuration
- [x] FastAPI endpoints (stubs)
- [x] GCP setup automation
- [x] Knowledge base ingestion (RAG Engine)
- [x] Drawing processing (PDF→PNG, embeddings)
- [ ] VLM analysis with Gemini 2.5
- [ ] Exception Engine (best practices)
- [ ] Report generation

### Phase 2: Core Features (Weeks 3-4)
- [ ] Vector Search integration
- [ ] Chat interface
- [ ] Metrics & logging
- [ ] Testing with Gen6 case
- [ ] Frontend (Vercel) integration

### Phase 3: Polish & Optimization (Week 5+)
- [ ] Performance optimization
- [ ] Cost optimization (Flash vs Pro)
- [ ] Advanced exception rules
- [ ] User authentication
- [ ] Admin dashboard
- [ ] Batch processing

### Future Enhancements
- [ ] SigmaSoft integration
- [ ] Automated FEMA generation
- [ ] Multi-language support
- [ ] Mobile app

---

## Troubleshooting

### Common Issues

**1. Import errors when running locally**
```bash
# Make sure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python main.py
```

**2. GCP authentication errors**
```bash
# Check credentials
gcloud auth application-default login

# Verify service account
gcloud iam service-accounts list
```

**3. PDF processing fails**
```bash
# Install system dependencies (Linux/Mac)
sudo apt-get install poppler-utils libpoppler-dev

# Mac with Homebrew
brew install poppler
```

**4. Vertex AI quota errors**
- Check quotas in GCP Console
- Request quota increase if needed
- Use `quality_mode=flash` to reduce costs

### Logs

```bash
# Local logs
# Check console output

# Cloud Run logs
gcloud run logs tail sme-ai-vertex --region us-central1
```

### Support

- Check `/docs` endpoint for API documentation
- Review GCP logs in Cloud Console
- Contact: [your-email@example.com]

---

## License

[Your License]

---

## Contributors

- Christian Ramirez - Lead Developer
- Michael - Product Vision & Requirements

---

## Acknowledgments

- Inspired by Michael's vision for AI-powered molding feasibility analysis
- Built to solve real-world problems at Micro Manufacturing
- Leveraging cutting-edge Vertex AI capabilities

---

**Status**: MVP in development | **Version**: 0.1.0 | **Last Updated**: 2025-11-02

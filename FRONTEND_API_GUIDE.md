# Frontend API Integration Guide

## 🎯 Overview

Esta guía contiene **todos** los endpoints de la API con ejemplos completos de request/response para que puedas integrarlos en tu frontend de Vercel.

**Base URL (Local):** `http://localhost:8080`
**Base URL (Production):** `https://your-cloud-run-url.run.app`

**Formato:** Todos los endpoints aceptan/retornan JSON, excepto los uploads que usan `multipart/form-data`.

---

## 📚 Knowledge Base Endpoints

### 1. Upload Document

Sube un manual, especificación o documento a la knowledge base.

**Endpoint:** `POST /knowledgebase/upload`

**Request:**
```bash
curl -X POST "http://localhost:8080/knowledgebase/upload" \
  -F "file=@molding_manual.pdf" \
  -F "document_type=manual"
```

**Request (JavaScript/Fetch):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('document_type', 'manual'); // or 'specification', 'quality_manual'

const response = await fetch('http://localhost:8080/knowledgebase/upload', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log(data);
```

**Response (200 Created):**
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "molding_manual.pdf",
  "document_type": "manual",
  "size_bytes": 2458972,
  "status": "indexed",
  "uploaded_at": "2025-11-02T14:30:00Z",
  "gcs_uri": "gs://sustained-truck-408014-manuals/manual/123e4567.../molding_manual.pdf"
}
```

**Document Types:**
- `manual` - Injection molding manuals, textbooks
- `specification` - Material specifications, standards
- `quality_manual` - Quality manuals, procedures

---

### 2. List Documents

Obtiene la lista de documentos en la knowledge base con filtros opcionales.

**Endpoint:** `GET /knowledgebase/documents`

**Query Parameters:**
- `document_type` (optional): Filter by type (`manual`, `specification`, `quality_manual`)
- `status_filter` (optional): Filter by status (`uploading`, `processing`, `indexed`, `failed`)
- `limit` (optional): Max results (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Request:**
```bash
# Get all documents
curl "http://localhost:8080/knowledgebase/documents"

# Get only manuals
curl "http://localhost:8080/knowledgebase/documents?document_type=manual"

# Pagination
curl "http://localhost:8080/knowledgebase/documents?limit=10&offset=0"
```

**Request (JavaScript):**
```javascript
// Get all documents
const response = await fetch('http://localhost:8080/knowledgebase/documents');
const documents = await response.json();

// With filters
const params = new URLSearchParams({
  document_type: 'manual',
  limit: 20,
  offset: 0
});
const response = await fetch(`http://localhost:8080/knowledgebase/documents?${params}`);
const documents = await response.json();
```

**Response (200 OK):**
```json
[
  {
    "document_id": "123e4567-e89b-12d3-a456-426614174000",
    "filename": "molding_manual.pdf",
    "document_type": "manual",
    "status": "indexed",
    "uploaded_at": "2025-11-02T14:30:00Z",
    "indexed_at": "2025-11-02T14:31:30Z",
    "page_count": 250,
    "metadata": {
      "gcs_uri": "gs://...",
      "rag_file_id": "xyz",
      "text_length": 150000
    }
  },
  {
    "document_id": "456e7890-e89b-12d3-a456-426614174001",
    "filename": "material_specs.pdf",
    "document_type": "specification",
    "status": "indexed",
    "uploaded_at": "2025-11-02T15:00:00Z",
    "indexed_at": "2025-11-02T15:01:00Z",
    "page_count": 50,
    "metadata": {}
  }
]
```

---

### 3. Get Document Details

Obtiene detalles de un documento específico por ID.

**Endpoint:** `GET /knowledgebase/documents/{document_id}`

**Request:**
```bash
curl "http://localhost:8080/knowledgebase/documents/123e4567-e89b-12d3-a456-426614174000"
```

**Request (JavaScript):**
```javascript
const documentId = '123e4567-e89b-12d3-a456-426614174000';
const response = await fetch(`http://localhost:8080/knowledgebase/documents/${documentId}`);
const document = await response.json();
```

**Response (200 OK):**
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "molding_manual.pdf",
  "document_type": "manual",
  "status": "indexed",
  "uploaded_at": "2025-11-02T14:30:00Z",
  "indexed_at": "2025-11-02T14:31:30Z",
  "page_count": 250,
  "metadata": {
    "gcs_uri": "gs://sustained-truck-408014-manuals/...",
    "rag_file_id": "xyz-123",
    "text_length": 150000
  }
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Document not found"
}
```

---

### 4. Delete Document

Elimina un documento de la knowledge base.

**Endpoint:** `DELETE /knowledgebase/documents/{document_id}`

**Request:**
```bash
curl -X DELETE "http://localhost:8080/knowledgebase/documents/123e4567-e89b-12d3-a456-426614174000"
```

**Request (JavaScript):**
```javascript
const documentId = '123e4567-e89b-12d3-a456-426614174000';
const response = await fetch(`http://localhost:8080/knowledgebase/documents/${documentId}`, {
  method: 'DELETE'
});

if (response.status === 204) {
  console.log('Document deleted successfully');
}
```

**Response (204 No Content):**
```
(No body)
```

**Response (404 Not Found):**
```json
{
  "detail": "Document not found"
}
```

---

### 5. Get Knowledge Base Stats

Obtiene estadísticas de la knowledge base.

**Endpoint:** `GET /knowledgebase/stats`

**Request:**
```bash
curl "http://localhost:8080/knowledgebase/stats"
```

**Request (JavaScript):**
```javascript
const response = await fetch('http://localhost:8080/knowledgebase/stats');
const stats = await response.json();
```

**Response (200 OK):**
```json
{
  "total_documents": 15,
  "documents_by_type": {
    "manual": 10,
    "specification": 3,
    "quality_manual": 2
  },
  "total_pages_indexed": 1250,
  "last_updated": "2025-11-02T15:30:00Z"
}
```

---

## 🔍 Analysis Endpoints

### 1. Upload Drawing for Analysis

Sube un plano técnico para análisis de factibilidad.

**Endpoint:** `POST /analysis/upload`

**Request:**
```bash
curl -X POST "http://localhost:8080/analysis/upload" \
  -F "file=@technical_drawing.pdf" \
  -F "project_name=Gen6" \
  -F "include_quality_manual=false" \
  -F "quality_mode=flash"
```

**Request (JavaScript):**
```javascript
const formData = new FormData();
formData.append('file', drawingFile);
formData.append('project_name', 'Gen6'); // optional
formData.append('include_quality_manual', 'false'); // optional
formData.append('quality_mode', 'flash'); // 'flash' or 'pro'

const response = await fetch('http://localhost:8080/analysis/upload', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log('Analysis ID:', data.analysis_id);
```

**Parameters:**
- `file` (required): PDF drawing file
- `project_name` (optional): Project identifier
- `include_quality_manual` (optional): Include quality manual in analysis
- `quality_mode` (optional): `flash` (fast/cheap) or `pro` (accurate/expensive)

**Response (201 Created):**
```json
{
  "analysis_id": "789e0123-e89b-12d3-a456-426614174002",
  "status": "processing",
  "uploaded_at": "2025-11-02T16:00:00Z",
  "drawing_filename": "technical_drawing.pdf"
}
```

**Status Values:**
- `pending`: Analysis queued
- `processing`: Currently analyzing
- `completed`: Analysis finished
- `failed`: Analysis failed

---

### 2. List Analyses

Obtiene lista de análisis con filtros opcionales.

**Endpoint:** `GET /analysis/documents`

**Query Parameters:**
- `status_filter` (optional): Filter by status
- `project_name` (optional): Filter by project name
- `limit` (optional): Max results (default: 100)
- `offset` (optional): Pagination offset

**Request:**
```bash
# All analyses
curl "http://localhost:8080/analysis/documents"

# Filter by project
curl "http://localhost:8080/analysis/documents?project_name=Gen6"

# Filter by status
curl "http://localhost:8080/analysis/documents?status_filter=completed"
```

**Request (JavaScript):**
```javascript
const params = new URLSearchParams({
  project_name: 'Gen6',
  status_filter: 'completed',
  limit: 20
});
const response = await fetch(`http://localhost:8080/analysis/documents?${params}`);
const analyses = await response.json();
```

**Response (200 OK):**
```json
[
  {
    "analysis_id": "789e0123-e89b-12d3-a456-426614174002",
    "status": "completed",
    "project_name": "Gen6",
    "drawing_filename": "technical_drawing.pdf",
    "uploaded_at": "2025-11-02T16:00:00Z",
    "started_at": "2025-11-02T16:00:05Z",
    "completed_at": "2025-11-02T16:02:30Z",
    "quality_mode": "flash",
    "exception_count": 7,
    "executive_report_url": "https://storage.googleapis.com/...",
    "detailed_report_url": "https://storage.googleapis.com/..."
  }
]
```

---

### 3. Get Analysis Details

Obtiene detalles de un análisis específico.

**Endpoint:** `GET /analysis/{analysis_id}`

**Request:**
```bash
curl "http://localhost:8080/analysis/789e0123-e89b-12d3-a456-426614174002"
```

**Request (JavaScript):**
```javascript
const analysisId = '789e0123-e89b-12d3-a456-426614174002';
const response = await fetch(`http://localhost:8080/analysis/${analysisId}`);
const analysis = await response.json();
```

**Response (200 OK):**
```json
{
  "analysis_id": "789e0123-e89b-12d3-a456-426614174002",
  "status": "completed",
  "project_name": "Gen6",
  "drawing_filename": "technical_drawing.pdf",
  "uploaded_at": "2025-11-02T16:00:00Z",
  "started_at": "2025-11-02T16:00:05Z",
  "completed_at": "2025-11-02T16:02:30Z",
  "quality_mode": "flash",
  "exception_count": 7,
  "executive_report_url": "https://storage.googleapis.com/sustained-truck-408014-reports/789e0123_executive.pdf?...",
  "detailed_report_url": "https://storage.googleapis.com/sustained-truck-408014-reports/789e0123_detailed.pdf?..."
}
```

---

### 4. Get Report

Obtiene el reporte de análisis (Executive o Detailed).

**Endpoint:** `GET /analysis/{analysis_id}/report`

**Query Parameters:**
- `report_type` (optional): `executive` or `detailed` (default: `executive`)

**Request:**
```bash
# Executive report
curl "http://localhost:8080/analysis/789e0123-e89b-12d3-a456-426614174002/report?report_type=executive"

# Detailed report
curl "http://localhost:8080/analysis/789e0123-e89b-12d3-a456-426614174002/report?report_type=detailed"
```

**Request (JavaScript):**
```javascript
// Executive report
const analysisId = '789e0123-e89b-12d3-a456-426614174002';
const response = await fetch(`http://localhost:8080/analysis/${analysisId}/report?report_type=executive`);
const reportData = await response.json();

// Redirect to signed URL
window.open(reportData.report_url, '_blank');
```

**Response (200 OK):**
```json
{
  "analysis_id": "789e0123-e89b-12d3-a456-426614174002",
  "report_type": "executive",
  "report_url": "https://storage.googleapis.com/sustained-truck-408014-reports/789e0123_executive.pdf?X-Goog-Algorithm=...",
  "expires_at": "2025-11-02T17:02:30Z",
  "generated_at": "2025-11-02T16:02:30Z"
}
```

**Note:** El `report_url` es una signed URL que expira en 1 hora. Úsala para descargar o mostrar el PDF.

---

### 5. Delete Analysis

Elimina un análisis y sus reportes asociados.

**Endpoint:** `DELETE /analysis/{analysis_id}`

**Request:**
```bash
curl -X DELETE "http://localhost:8080/analysis/789e0123-e89b-12d3-a456-426614174002"
```

**Request (JavaScript):**
```javascript
const analysisId = '789e0123-e89b-12d3-a456-426614174002';
const response = await fetch(`http://localhost:8080/analysis/${analysisId}`, {
  method: 'DELETE'
});

if (response.status === 204) {
  console.log('Analysis deleted successfully');
}
```

**Response (204 No Content):**
```
(No body)
```

---

## 💬 Chat Endpoints

### 1. Chat About Analysis

Chat con AI expert sobre un análisis específico.

**Endpoint:** `POST /analysis/{analysis_id}/chat`

**Request:**
```bash
curl -X POST "http://localhost:8080/analysis/789e0123.../chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Why is dimension X flagged as critical?",
    "history": []
  }'
```

**Request (JavaScript):**
```javascript
const analysisId = '789e0123-e89b-12d3-a456-426614174002';
const chatData = {
  message: "Why is dimension X flagged as critical?",
  history: [
    {
      "role": "user",
      "content": "Previous question"
    },
    {
      "role": "assistant",
      "content": "Previous answer"
    }
  ]
};

const response = await fetch(`http://localhost:8080/analysis/${analysisId}/chat`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(chatData)
});

const chatResponse = await response.json();
console.log(chatResponse.message);
```

**Response (200 OK):**
```json
{
  "message": "Dimension X is flagged as critical because it specifies a tolerance of ±0.03mm, which is below the minimum achievable tolerance of ±0.05mm for ABS material in injection molding. This tight tolerance would require secondary machining operations.",
  "sources": [
    {
      "type": "knowledge_base",
      "title": "Injection Molding Handbook - Chapter 5",
      "page": 47,
      "snippet": "Standard tolerance for ABS: ±0.05mm to ±0.10mm"
    },
    {
      "type": "drawing_analysis",
      "page": 1,
      "feature": "Dimension X",
      "bbox": [0.2, 0.5, 0.4, 0.6]
    }
  ],
  "grounded": true
}
```

---

## 🏥 Health & System Endpoints

### 1. Health Check

Verifica que el sistema esté funcionando.

**Endpoint:** `GET /health`

**Request:**
```bash
curl "http://localhost:8080/health"
```

**Request (JavaScript):**
```javascript
const response = await fetch('http://localhost:8080/health');
const health = await response.json();
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-02T16:30:00Z",
  "version": "0.1.0",
  "services": {
    "gcp": "configured",
    "vertex_ai": "enabled",
    "knowledge_base": "ready"
  }
}
```

---

### 2. API Info

Información básica de la API.

**Endpoint:** `GET /`

**Response (200 OK):**
```json
{
  "message": "SME AI Vertex API",
  "docs": "/docs",
  "health": "/health"
}
```

---

## 🔐 Authentication (Future)

**Current Status:** La API está configurada sin autenticación para desarrollo.

**Production:** Necesitarás agregar:
- JWT tokens
- API keys
- Rate limiting por usuario

**Headers que necesitarás agregar:**
```javascript
const response = await fetch('http://localhost:8080/analysis/upload', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    // or
    'X-API-Key': 'YOUR_API_KEY'
  },
  body: formData
});
```

---

## 📊 Frontend Components Recomendados

### Knowledge Base Manager
```javascript
// Upload component
function KnowledgeBaseUploader() {
  const handleUpload = async (file, type) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', type);

    const response = await fetch(`${API_URL}/knowledgebase/upload`, {
      method: 'POST',
      body: formData
    });

    return await response.json();
  };

  return <FileUploader onUpload={handleUpload} />;
}

// List component
function KnowledgeBaseList() {
  const [documents, setDocuments] = useState([]);

  useEffect(() => {
    fetch(`${API_URL}/knowledgebase/documents`)
      .then(res => res.json())
      .then(setDocuments);
  }, []);

  const handleDelete = async (id) => {
    await fetch(`${API_URL}/knowledgebase/documents/${id}`, {
      method: 'DELETE'
    });
    // Refresh list
  };

  return <DocumentList documents={documents} onDelete={handleDelete} />;
}
```

### Drawing Analyzer
```javascript
function DrawingAnalyzer() {
  const [analysisId, setAnalysisId] = useState(null);
  const [status, setStatus] = useState('idle');

  const handleUpload = async (file, projectName, qualityMode) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_name', projectName);
    formData.append('quality_mode', qualityMode);

    const response = await fetch(`${API_URL}/analysis/upload`, {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    setAnalysisId(data.analysis_id);
    setStatus('processing');

    // Poll for completion
    pollAnalysis(data.analysis_id);
  };

  const pollAnalysis = async (id) => {
    const interval = setInterval(async () => {
      const response = await fetch(`${API_URL}/analysis/${id}`);
      const data = await response.json();

      if (data.status === 'completed') {
        clearInterval(interval);
        setStatus('completed');
        // Load reports
      } else if (data.status === 'failed') {
        clearInterval(interval);
        setStatus('failed');
      }
    }, 3000); // Poll every 3 seconds
  };

  return <AnalyzerUI onUpload={handleUpload} status={status} />;
}
```

---

## 🚨 Error Handling

Todos los endpoints pueden retornar estos errores:

**400 Bad Request:**
```json
{
  "detail": "Only PDF files are supported"
}
```

**404 Not Found:**
```json
{
  "detail": "Document not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Upload failed: Connection timeout"
}
```

**JavaScript Error Handler:**
```javascript
async function apiCall(url, options) {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API Error');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    // Show user notification
    throw error;
  }
}
```

---

## 📝 Complete Example: Full Workflow

```javascript
// 1. Upload knowledge base documents
async function setupKnowledgeBase(manuals) {
  for (const manual of manuals) {
    await fetch('http://localhost:8080/knowledgebase/upload', {
      method: 'POST',
      body: createFormData(manual, 'manual')
    });
  }
}

// 2. Upload drawing for analysis
async function analyzeDrawing(drawingFile, projectName) {
  const formData = new FormData();
  formData.append('file', drawingFile);
  formData.append('project_name', projectName);
  formData.append('quality_mode', 'flash');

  const response = await fetch('http://localhost:8080/analysis/upload', {
    method: 'POST',
    body: formData
  });

  const { analysis_id } = await response.json();
  return analysis_id;
}

// 3. Poll for completion
async function waitForAnalysis(analysisId) {
  while (true) {
    const response = await fetch(`http://localhost:8080/analysis/${analysisId}`);
    const data = await response.json();

    if (data.status === 'completed') {
      return data;
    } else if (data.status === 'failed') {
      throw new Error('Analysis failed');
    }

    await new Promise(resolve => setTimeout(resolve, 3000));
  }
}

// 4. Get reports
async function getReports(analysisId) {
  const executive = await fetch(
    `http://localhost:8080/analysis/${analysisId}/report?report_type=executive`
  ).then(res => res.json());

  const detailed = await fetch(
    `http://localhost:8080/analysis/${analysisId}/report?report_type=detailed`
  ).then(res => res.json());

  return { executive, detailed };
}

// Complete workflow
async function completeWorkflow() {
  // Setup
  await setupKnowledgeBase(manualFiles);

  // Analyze
  const analysisId = await analyzeDrawing(drawingFile, 'Gen6');

  // Wait
  const analysis = await waitForAnalysis(analysisId);

  // Get reports
  const { executive, detailed } = await getReports(analysisId);

  // Open reports
  window.open(executive.report_url, '_blank');
  window.open(detailed.report_url, '_blank');
}
```

---

## 🔗 Swagger UI

Para testing interactivo, usa Swagger UI:

**Local:** http://localhost:8080/docs

Aquí puedes probar todos los endpoints directamente desde el navegador.

---

**¿Preguntas?** Todos estos endpoints están funcionando y listos para integrarse con tu frontend! 🚀

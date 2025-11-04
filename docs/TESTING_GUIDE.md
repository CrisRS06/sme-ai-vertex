# Guía de Testing - SME AI Vertex

**Cómo probar el programa paso a paso**

Esta guía te muestra cómo probar cada componente del sistema, desde testing local hasta deployment en GCP.

---

## 🎯 Opción 1: Testing Local Rápido (Desarrollo)

**Tiempo**: 10-15 minutos
**Ideal para**: Desarrollo, debugging, familiarización

### Paso 1: Requisitos Previos

```bash
# Verificar versiones
python --version  # Debe ser 3.11+
git --version
```

### Paso 2: Clonar y Setup

```bash
# Clonar repositorio
git clone https://github.com/CrisRS06/sme-ai-vertex.git
cd sme-ai-vertex

# Crear virtual environment
python -m venv venv

# Activar (Linux/Mac)
source venv/bin/activate

# Activar (Windows)
# venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 3: Configurar Credenciales (Mínimo)

```bash
# Copiar template
cp .env.example .env

# Editar .env con tu editor favorito
nano .env  # o vim, code, etc.
```

**Configuración mínima para testing local**:

```bash
# .env
GCP_PROJECT_ID=tu-project-id
GCP_REGION=us-central1
GCP_LOCATION=us-central1

# Credenciales (opción 1: service account)
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# O (opción 2: usar gcloud auth)
# export GOOGLE_APPLICATION_CREDENTIALS="" (vacío)

# Buckets (crear con nombres únicos)
GCS_BUCKET_MANUALS=tu-project-manuals
GCS_BUCKET_DRAWINGS=tu-project-drawings
GCS_BUCKET_REPORTS=tu-project-reports

# Modelos
VERTEX_AI_MODEL_FLASH=gemini-2.5-flash
VERTEX_AI_MODEL_PRO=gemini-2.5-pro

# Testing mode
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
```

### Paso 4: Crear Buckets (Una sola vez)

```bash
# Autenticarse con gcloud
gcloud auth application-default login
gcloud config set project tu-project-id

# Crear buckets
gsutil mb -p tu-project-id -c STANDARD -l us-central1 gs://tu-project-manuals
gsutil mb -p tu-project-id -c STANDARD -l us-central1 gs://tu-project-drawings
gsutil mb -p tu-project-id -c STANDARD -l us-central1 gs://tu-project-reports

# Habilitar APIs necesarias
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage-api.googleapis.com
```

### Paso 5: Ejecutar Servidor Local

```bash
# Ejecutar con auto-reload
python main.py

# Output esperado:
# INFO:     Started server process
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Paso 6: Verificar que Funciona

**Abrir en navegador**:
- Health Check: http://localhost:8080/health
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

**Resultado esperado en `/health`**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-04T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "gcp": "configured",
    "vertex_ai": "enabled",
    "knowledge_base": "ready",
    "rag_grounding": "not_configured_warning",
    "document_ai_ocr": "not_configured_warning"
  }
}
```

**Warnings son OK** para testing local. RAG y Document AI son opcionales.

---

## 🧪 Opción 2: Testing de Componentes Individuales

### Test 1: Upload de Documento a Knowledge Base

**Preparar archivo de prueba**:

```bash
# Crear un PDF de prueba simple (o usar uno existente)
echo "Test document for knowledge base" > test_manual.txt

# Convertir a PDF (si tienes pandoc)
pandoc test_manual.txt -o test_manual.pdf

# O simplemente usa cualquier PDF técnico que tengas
```

**Probar con cURL**:

```bash
curl -X POST "http://localhost:8080/knowledgebase/upload" \
  -F "file=@test_manual.pdf" \
  -F "document_type=manual"

# Respuesta esperada:
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "test_manual.pdf",
  "document_type": "manual",
  "size_bytes": 12345,
  "status": "indexed",
  "uploaded_at": "2025-11-04T10:35:00Z",
  "gcs_uri": "gs://tu-project-manuals/manual/123e4567.../test_manual.pdf"
}
```

**Verificar en GCS**:

```bash
gsutil ls gs://tu-project-manuals/manual/
```

### Test 2: Análisis de Dibujo Técnico (Sin RAG)

**Preparar PDF de prueba**:

```bash
# Opción 1: Usar un dibujo técnico real (recomendado)
# Busca cualquier PDF con dimensiones y texto

# Opción 2: Crear un PDF simple con texto
echo "Test drawing with dimensions: 100mm x 50mm" > test_drawing.txt
pandoc test_drawing.txt -o test_drawing.pdf
```

**Probar análisis**:

```bash
curl -X POST "http://localhost:8080/analysis/upload" \
  -F "file=@test_drawing.pdf" \
  -F "project_name=TestProject" \
  -F "quality_mode=flash"

# Respuesta inmediata:
{
  "analysis_id": "abc123-def456-...",
  "status": "processing",
  "uploaded_at": "2025-11-04T10:40:00Z",
  "drawing_filename": "test_drawing.pdf"
}
```

**Esperar 30-60 segundos** y verificar status:

```bash
curl "http://localhost:8080/analysis/abc123-def456-..."

# Respuesta:
{
  "analysis_id": "abc123-def456-...",
  "status": "completed",  # ✅ Cambió de "processing" a "completed"
  "project_name": "TestProject",
  "drawing_filename": "test_drawing.pdf",
  "uploaded_at": "2025-11-04T10:40:00Z",
  "completed_at": "2025-11-04T10:41:30Z",
  "exception_count": 5,
  "executive_report_url": "https://storage.googleapis.com/...",
  "detailed_report_url": "https://storage.googleapis.com/..."
}
```

**Descargar reportes**:

```bash
# Copiar URLs de la respuesta anterior
curl "https://storage.googleapis.com/tu-project-reports/..." -o executive_report.pdf
curl "https://storage.googleapis.com/tu-project-reports/..." -o detailed_report.pdf

# Abrir PDFs
open executive_report.pdf  # Mac
xdg-open executive_report.pdf  # Linux
start executive_report.pdf  # Windows
```

### Test 3: Chat (Sin RAG configurado)

```bash
curl -X POST "http://localhost:8080/analysis/general" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the minimum wall thickness for ABS?",
    "history": []
  }'

# Respuesta:
{
  "message": "For ABS (Acrylonitrile Butadiene Styrene) injection molding, the recommended minimum wall thickness is typically:\n\n• **1.5mm (0.060 inches)** - Standard minimum\n• **2.0-2.5mm** - Ideal range for optimal strength and moldability...",
  "sources": [],
  "grounded": false  # Sin RAG configurado
}
```

---

## 🚀 Opción 3: Testing en GCP (Producción)

**Tiempo**: 30-45 minutos (setup completo)
**Ideal para**: Testing de producción, performance real, features completas

### Paso 1: Setup Completo de GCP

```bash
cd sme-ai-vertex

# 1. Setup básico de GCP
./scripts/setup_gcp.sh tu-project-id us-central1

# Output esperado:
# ✅ APIs habilitadas
# ✅ Buckets creados
# ✅ Service account creada
# ✅ .env generado

# 2. Setup de RAG Engine (para chat con grounding)
./scripts/setup_rag_engine.sh tu-project-id us-central1

# Output esperado:
# ✅ RAG corpus creado
# ✅ RAG_DATA_STORE_ID añadido a .env

# 3. Setup de Vector Search (para búsqueda visual)
./scripts/setup_vector_search.sh tu-project-id us-central1 sme-vector-index

# Output esperado:
# ✅ Índice TreeAH creado
# ✅ Endpoint desplegado
# ✅ VECTOR_SEARCH_* variables añadidas a .env

# 4. (Opcional) Setup de Document AI (OCR fallback)
./scripts/setup_document_ai_processor.sh tu-project-id us-central1

# Output esperado:
# ✅ Processor creado
# ✅ DOCUMENT_AI_PROCESSOR_ID añadido a .env
```

**Total setup time**: ~30 minutos (la mayoría es tiempo de provisioning de GCP)

### Paso 2: Deploy a Cloud Run

```bash
./scripts/deploy_cloudrun.sh tu-project-id us-central1

# Output esperado:
# Building using Dockerfile and uploading it to Google Container Registry
# ✅ Image built: gcr.io/tu-project-id/sme-ai-vertex
# Deploying container to Cloud Run service [sme-ai-vertex]
# ✅ Service deployed!
# URL: https://sme-ai-vertex-xxx-uc.a.run.app
```

### Paso 3: Testing en Producción

**Health check**:

```bash
# Guardar URL
export API_URL="https://sme-ai-vertex-xxx-uc.a.run.app"

# Test health
curl "$API_URL/health"

# Debe mostrar todos los servicios "configured":
{
  "status": "healthy",
  "services": {
    "gcp": "configured",
    "vertex_ai": "enabled",
    "knowledge_base": "ready",
    "rag_grounding": "configured",  # ✅ Ahora sí
    "document_ai_ocr": "configured"  # ✅ Si ejecutaste setup
  }
}
```

**Upload de manual**:

```bash
curl -X POST "$API_URL/knowledgebase/upload" \
  -F "file=@Molding_Best_Practices.pdf" \
  -F "document_type=manual"
```

**Análisis de dibujo**:

```bash
curl -X POST "$API_URL/analysis/upload" \
  -F "file=@Technical_Drawing.pdf" \
  -F "project_name=ProductionTest" \
  -F "quality_mode=flash"
```

**Chat con grounding**:

```bash
curl -X POST "$API_URL/analysis/general" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the minimum draft angle for injection molding?",
    "history": []
  }'

# Ahora debe tener sources:
{
  "message": "For injection molding, the minimum draft angle...",
  "sources": [
    {
      "type": "knowledge_base",
      "title": "Molding_Best_Practices.pdf",
      "relevance_score": 0.92
    }
  ],
  "grounded": true  # ✅ Con RAG
}
```

---

## 🎨 Opción 4: Testing con Frontend (Vercel)

Si tienes el frontend desplegado:

### Setup del Frontend

```bash
# En directorio separado
git clone https://github.com/tu-org/sme-ai-frontend
cd sme-ai-frontend

# Configurar API URL
echo "NEXT_PUBLIC_API_URL=https://sme-ai-vertex-xxx-uc.a.run.app" > .env.local

# Instalar y ejecutar
npm install
npm run dev
```

**Abrir**: http://localhost:3000

### Flujo de Testing en UI

1. **Upload Manual**:
   - Navigate to "Knowledge Base"
   - Drop PDF file
   - Wait for "Indexed" status

2. **Analyze Drawing**:
   - Navigate to "New Analysis"
   - Drop drawing PDF
   - Enter project name
   - Click "Analyze"
   - Wait ~40 seconds

3. **View Results**:
   - See extraction summary
   - See exception list
   - Download reports

4. **Chat**:
   - Click "Chat with AI Expert"
   - Ask questions
   - See streaming responses

---

## 📋 Ejemplos de Datos de Prueba

### PDFs Simples para Testing

**1. Manual de prueba (`test_manual.md` → PDF)**:

```markdown
# Injection Molding Best Practices

## Wall Thickness

For ABS material:
- Minimum: 1.5mm
- Recommended: 2.0-2.5mm
- Maximum: 4.0mm

## Draft Angle

- Minimum: 1-2 degrees
- Recommended: 2-3 degrees for deep pockets

## Tolerances

- Standard: ±0.1mm
- Tight: ±0.05mm (requires precision tooling)
```

**2. Drawing simple (`test_drawing.md` → PDF)**:

```markdown
# Test Part Drawing

Part Number: TEST-001
Material: ABS

## Dimensions

- Overall length: 100.0 ±0.2 mm
- Overall width: 50.0 ±0.2 mm
- Wall thickness: 2.5 ±0.1 mm
- Draft angle: 2°

## Notes

- All dimensions in millimeters
- Tolerances per ISO 2768-m
```

### Convertir a PDF

```bash
# Con pandoc
pandoc test_manual.md -o test_manual.pdf
pandoc test_drawing.md -o test_drawing.pdf

# O usar cualquier herramienta: Word, Pages, LibreOffice, etc.
```

---

## 🐛 Troubleshooting Común

### Error: "Module 'google.cloud.aiplatform' has no attribute 'rag'"

**Causa**: SDK version antigua

**Solución**:
```bash
pip install --upgrade google-cloud-aiplatform==1.82.0
```

### Error: "Bucket does not exist"

**Causa**: Buckets no creados o nombre incorrecto en .env

**Solución**:
```bash
# Verificar buckets
gsutil ls

# Crear si faltan
gsutil mb -p tu-project-id gs://tu-project-manuals
gsutil mb -p tu-project-id gs://tu-project-drawings
gsutil mb -p tu-project-id gs://tu-project-reports
```

### Error: "Permission denied"

**Causa**: Service account sin permisos

**Solución**:
```bash
# Re-ejecutar setup que configura permisos
./scripts/setup_gcp.sh tu-project-id us-central1

# O manualmente:
gcloud projects add-iam-policy-binding tu-project-id \
  --member="serviceAccount:sme-ai-app@tu-project-id.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Error: "Analysis stuck in 'processing'"

**Causa**: Error en pipeline de análisis

**Solución**:
```bash
# Ver logs
python main.py  # Local

# O en Cloud Run:
gcloud run logs tail sme-ai-vertex --region=us-central1

# Buscar líneas con "error" o "failed"
```

### Warning: "RAG_DATA_STORE_ID not configured"

**Es OK** si:
- Estás en testing local básico
- No necesitas chat con grounding aún

**Para habilitar**:
```bash
./scripts/setup_rag_engine.sh tu-project-id us-central1
```

### Análisis muy lento (>2 minutos)

**Causas posibles**:
- Dibujo muy complejo (muchas páginas)
- Network latency
- Cold start en Cloud Run

**Soluciones**:
- Usar `quality_mode=flash` (más rápido)
- Configurar min-instances en Cloud Run
- Reducir número de páginas para testing

---

## ✅ Checklist de Testing Completo

### Testing Local Básico
- [ ] ✅ Servidor corre en localhost:8080
- [ ] ✅ /health responde "healthy"
- [ ] ✅ /docs muestra Swagger UI
- [ ] ✅ Upload de manual funciona
- [ ] ✅ Análisis de drawing funciona
- [ ] ✅ Reportes se generan
- [ ] ✅ Chat responde (sin grounding OK)

### Testing en GCP (Opcional)
- [ ] ✅ Todos los scripts de setup ejecutados
- [ ] ✅ Cloud Run deployment exitoso
- [ ] ✅ Health check muestra todos "configured"
- [ ] ✅ RAG grounding funciona (sources en chat)
- [ ] ✅ Vector Search funciona
- [ ] ✅ Document AI OCR funciona (opcional)

### Testing de Features Avanzadas
- [ ] ✅ Context caching activo (ver logs)
- [ ] ✅ Streaming chat funciona
- [ ] ✅ RAG evaluation funciona
- [ ] ✅ Métricas se trackean

---

## 🚀 Quick Start (Comando Único)

Si quieres la experiencia más rápida:

```bash
# 1. Clone
git clone https://github.com/CrisRS06/sme-ai-vertex.git
cd sme-ai-vertex

# 2. Setup virtual env
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# 3. Configure (mínimo)
cp .env.example .env
# Editar: GCP_PROJECT_ID, buckets

# 4. Authenticate
gcloud auth application-default login

# 5. Run
python main.py

# 6. Test
curl http://localhost:8080/health
```

**Listo para testing básico en 5 minutos!**

---

## 📊 Monitorear Testing

### Ver Logs en Tiempo Real

```bash
# Local
tail -f logs/app.log  # Si configurado

# Cloud Run
gcloud run logs tail sme-ai-vertex --region=us-central1 --follow
```

### Ver Métricas

```bash
# Llamar endpoint de métricas
curl http://localhost:8080/metrics/summary

# Response:
{
  "total_analyses": 5,
  "avg_processing_time": 38.2,
  "avg_dimensions_count": 42,
  "cache_hit_rate": 0.45
}
```

### Verificar Costos

```bash
# Ver costos actuales
gcloud billing accounts list

# Ver uso de Vertex AI
gcloud alpha billing accounts describe ACCOUNT_ID
```

---

## 💡 Tips para Testing Efectivo

1. **Empezar simple**: Testing local → GCP básico → Features avanzadas
2. **Usar PDFs pequeños**: 1-5 páginas para testing rápido
3. **Modo Flash primero**: Más rápido y barato para iteración
4. **Logs son tu amigo**: Siempre revisar logs si algo falla
5. **Testing incremental**: Probar cada componente individualmente

---

## 🎯 Próximos Pasos Después de Testing

Una vez que hayas probado y todo funciona:

1. **Indexar manuales reales**: Upload de PDFs de molding
2. **Analizar dibujos reales**: Testing con casos reales
3. **Ajustar configuraciones**: Optimizar según tus necesidades
4. **Deploy a producción**: Seguir docs/PRODUCTION_DEPLOYMENT.md
5. **Monitorear métricas**: Trackear calidad y costos

---

**¿Necesitas ayuda?**
- 📖 Ver docs/USER_EXPERIENCE.md para flujos completos
- 🐛 Ver logs para debugging
- 💬 GitHub Issues para reportar problemas

---

**Última actualización**: 4 de Noviembre, 2025
**Versión**: 1.0.0
**Status**: Production-Ready

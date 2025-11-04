# 🚀 Setup Completo - Orden Correcto

Este documento te guía paso a paso para configurar el sistema **COMPLETO** con todas las features obligatorias.

---

## ✅ Features Obligatorias (No Opcionales)

1. **RAG Grounding** → Chat siempre usa TUS manuales + conocimiento de Gemini
2. **Document AI OCR** → Fallback automático para no perder información en microtexto

**Ambas son REQUERIDAS para producción.**

---

## 📋 Orden de Setup (45-60 minutos total)

### Paso 1: GCP Base Setup (20 min) ⭐ PRIMERO

```bash
cd "/Users/christianramirez/Programas/Micro/SME AI Vertex"

# Autenticar
gcloud auth login
gcloud config set project sustained-truck-408014
gcloud auth application-default login

# Setup base (buckets, service account, APIs básicas)
./scripts/setup_gcp.sh sustained-truck-408014 us-central1

# Verificar
ls -la service-account-key.json  # Debe existir
cat .env  # Debe tener GCP_PROJECT_ID
```

**Resultado:**
- ✅ Buckets creados (manuals, drawings, reports)
- ✅ Service account configurado
- ✅ APIs básicas habilitadas (Vertex AI, Cloud Storage)
- ✅ Credentials en `service-account-key.json`

---

### Paso 2: Instalar Dependencias (10 min)

```bash
# Crear virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Si hay error de PDF en macOS:
brew install poppler
```

**Resultado:**
- ✅ Todas las librerías instaladas
- ✅ Vertex AI SDK listo
- ✅ Document AI SDK listo

---

### Paso 3: RAG Engine Setup (15 min) ⭐ OBLIGATORIO

```bash
# Crear RAG Data Store
./scripts/setup_rag_engine.sh sustained-truck-408014 us-central1
```

**El script va a:**
1. Habilitar Vertex AI Search API
2. Crear Data Store para manuales
3. Darte el RAG_DATA_STORE_ID

**Output esperado:**
```
✓ RAG Engine Setup Complete!
RAG Corpus Resource Name:
projects/sustained-truck-408014/locations/us-central1/collections/default_collection/dataStores/manuals-knowledge-base

Add this to your .env file:
RAG_DATA_STORE_ID=projects/sustained-truck-408014/locations/us-central1/collections/default_collection/dataStores/manuals-knowledge-base
ENABLE_GROUNDING=true
```

**Agrega a .env:**
```bash
# Copiar el valor del script
RAG_DATA_STORE_ID=projects/sustained-truck-408014/locations/us-central1/collections/default_collection/dataStores/manuals-knowledge-base
ENABLE_GROUNDING=true
```

**Subir Manuales (IMPORTANTE):**

Opción A - Via Console (Recomendado primera vez):
1. Ir a: https://console.cloud.google.com/gen-app-builder/engines
2. Seleccionar tu data store
3. Click "Import" → "Cloud Storage"
4. Seleccionar bucket: `sustained-truck-408014-manuals`
5. Subir PDFs de manuales de moldeo
6. Esperar 5-10 min para indexing

Opción B - Via CLI:
```bash
# Primero sube manuales al bucket
gsutil cp manual1.pdf gs://sustained-truck-408014-manuals/
gsutil cp manual2.pdf gs://sustained-truck-408014-manuals/

# Importar al data store
gcloud alpha discovery-engine documents import \
  --data-store=manuals-knowledge-base \
  --location=us-central1 \
  --project=sustained-truck-408014 \
  --gcs-uri="gs://sustained-truck-408014-manuals/*.pdf"
```

**Resultado:**
- ✅ RAG Data Store creado
- ✅ Manuales indexados
- ✅ Chat usará tus manuales reales

---

### Paso 4: Document AI Setup (10 min) ⭐ OBLIGATORIO

```bash
# Crear Document AI Processor
./scripts/setup_document_ai.sh sustained-truck-408014
```

**El script va a:**
1. Habilitar Document AI API
2. Crear Form Parser Processor (mejor para drawings)
3. Darte el PROCESSOR_ID

**Output esperado:**
```
✓ Document AI Setup Complete!
Processor ID:
abc123def456

Add this to your .env file:
DOCUMENT_AI_PROCESSOR_ID=abc123def456
ENABLE_DOCUMENT_AI_FALLBACK=true
OCR_CONFIDENCE_THRESHOLD=0.7
```

**Agrega a .env:**
```bash
# Copiar el valor del script
DOCUMENT_AI_PROCESSOR_ID=abc123def456
ENABLE_DOCUMENT_AI_FALLBACK=true
OCR_CONFIDENCE_THRESHOLD=0.7
```

**Resultado:**
- ✅ Document AI Processor listo
- ✅ OCR fallback automático configurado
- ✅ No se perderá información de microtexto

---

### Paso 5: Verificar Configuración (2 min)

```bash
# Ver .env completo
cat .env
```

**Debe tener (MÍNIMO):**
```bash
# GCP Base
GCP_PROJECT_ID=sustained-truck-408014
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Buckets
GCS_BUCKET_MANUALS=sustained-truck-408014-manuals
GCS_BUCKET_DRAWINGS=sustained-truck-408014-drawings
GCS_BUCKET_REPORTS=sustained-truck-408014-reports

# Models
VERTEX_AI_MODEL_FLASH=gemini-2.0-flash-exp
VERTEX_AI_MODEL_PRO=gemini-1.5-pro-002

# ⭐ RAG (OBLIGATORIO)
RAG_DATA_STORE_ID=projects/sustained-truck-408014/locations/us-central1/collections/default_collection/dataStores/manuals-knowledge-base
ENABLE_GROUNDING=true

# ⭐ Document AI (OBLIGATORIO)
DOCUMENT_AI_PROCESSOR_ID=abc123def456
ENABLE_DOCUMENT_AI_FALLBACK=true
OCR_CONFIDENCE_THRESHOLD=0.7
```

---

### Paso 6: Correr Sistema (2 min) 🚀

```bash
# Asegúrate de estar en venv
source venv/bin/activate

# Ejecutar
python main.py
```

**Output esperado (TODO configurado):**
```
INFO:     Started server process
INFO:     Waiting for application startup.

✅ All production features configured!

INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

**Output si falta algo:**
```
⚠️  PRODUCTION-CRITICAL FEATURES NOT CONFIGURED
================================================================================
⚠️  RAG_DATA_STORE_ID not configured - Chat will not be grounded in knowledge base
   Run: ./scripts/setup_rag_engine.sh PROJECT_ID REGION
⚠️  DOCUMENT_AI_PROCESSOR_ID not configured - OCR fallback disabled
   Run: ./scripts/setup_document_ai.sh PROJECT_ID
================================================================================
System will work but with reduced capabilities.
Configure these for production use.
```

---

### Paso 7: Probar Sistema Completo (10 min) ✅

```bash
# Health check (en otra terminal)
curl http://localhost:8080/health
```

**Debe mostrar:**
```json
{
  "status": "healthy",
  "services": {
    "gcp": "configured",
    "vertex_ai": "enabled",
    "knowledge_base": "ready",
    "rag_grounding": "configured",      ✅
    "document_ai_ocr": "configured"     ✅
  }
}
```

**Probar análisis completo:**
```bash
# Subir drawing
curl -X POST "http://localhost:8080/analysis/upload" \
  -F "file=@test_drawing.pdf" \
  -F "project_name=Test" \
  -F "quality_mode=flash"

# Response:
# {
#   "analysis_id": "abc-123-def",
#   "status": "processing",
#   ...
# }

# Esperar ~20 segundos

# Ver resultado
curl "http://localhost:8080/analysis/abc-123-def"

# Ver métricas (incluye OCR usage si se activó)
curl "http://localhost:8080/metrics/analysis/abc-123-def"
```

**Probar chat con grounding:**
```bash
curl -X POST "http://localhost:8080/analysis/abc-123-def/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Por qué esta dimensión está marcada como crítica?",
    "history": []
  }'

# Response debe incluir:
# {
#   "message": "Según tu manual de moldeo...",
#   "sources": [
#     {
#       "title": "Manual.pdf",
#       "uri": "gs://...",
#       "relevance_score": 0.92
#     }
#   ],
#   "grounded": true  ← IMPORTANTE: debe ser true
# }
```

---

## 📊 Cómo Saber que Todo Funciona

### 1. RAG Grounding Funciona ✅
```bash
# Chat response debe tener:
"grounded": true
"sources": [...]  # No vacío

# Logs deben mostrar:
INFO: grounding_enabled data_store=projects/...
INFO: sources_extracted count=3
```

### 2. Document AI OCR Funciona ✅
```bash
# Si hay dimensiones con low confidence:
# Logs deben mostrar:
INFO: ocr_fallback_triggered low_confidence_count=5
INFO: processing_page_with_ocr page=1
INFO: ocr_fallback_completed fields_recovered=3

# Métricas deben mostrar:
{
  "ocr": {
    "ocr_triggered_count": 1,
    "ocr_trigger_rate_pct": 20,
    "avg_fields_recovered": 3.0
  }
}
```

### 3. Sistema Completo ✅
- Health check: todos los services "configured"
- Análisis: extrae dimensiones + GD&T
- Chat: grounded=true con sources
- Métricas: tracking completo
- Reports: Executive + Detailed generados

---

## 🔥 Troubleshooting

### RAG no funciona (grounded=false)

**Problema:** Chat no usa manuales

**Solución:**
```bash
# 1. Verificar data store ID en .env
cat .env | grep RAG_DATA_STORE_ID

# 2. Verificar manuales subidos
gcloud alpha discovery-engine documents list \
  --data-store=manuals-knowledge-base \
  --location=us-central1 \
  --project=sustained-truck-408014

# 3. Esperar indexing (5-10 min después de subir)

# 4. Verificar en logs:
# Debe aparecer: "grounding_enabled"
# Si no aparece, revisar imports en chat_service.py
```

### Document AI no se activa

**Problema:** OCR nunca se ejecuta

**Solución:**
```bash
# 1. Verificar processor ID en .env
cat .env | grep DOCUMENT_AI_PROCESSOR_ID

# 2. Verificar que hay dimensiones con low confidence
# (Si todas tienen confidence > 0.7, OCR no se activa - es correcto)

# 3. Probar con drawing difícil (texto pequeño)

# 4. Ajustar threshold temporalmente:
OCR_CONFIDENCE_THRESHOLD=0.9  # En .env (fuerza OCR)
```

### Service account permissions

**Problema:** Access denied en APIs

**Solución:**
```bash
# Re-ejecutar setup base
./scripts/setup_gcp.sh sustained-truck-408014 us-central1

# Verificar permisos manualmente
gcloud projects get-iam-policy sustained-truck-408014 \
  --flatten="bindings[].members" \
  --filter="bindings.members:sme-ai-vertex-sa@*"
```

---

## 💰 Costos con TODO Configurado

**Por análisis de 5 páginas:**
- Gemini Flash VLM: $0.10
- Multimodal embeddings: $0.001
- RAG retrieval: GRATIS (solo storage)
- Document AI (si activa): $0.0075
- **Total: ~$0.11**

**Por chat:**
- Gemini Flash: $0.002
- RAG retrieval: GRATIS
- **Total: ~$0.002**

**Estimado mensual (100 análisis + 500 chats):**
- Análisis: $11
- Chat: $1
- **Total: $12/mes** 🎉

---

## 🎯 Checklist Final

Setup completo cuando:
- [ ] GCP base configurado (buckets, service account)
- [ ] Dependencies instaladas (requirements.txt)
- [ ] RAG Data Store creado y manuales subidos
- [ ] Document AI Processor creado
- [ ] .env tiene RAG_DATA_STORE_ID
- [ ] .env tiene DOCUMENT_AI_PROCESSOR_ID
- [ ] `python main.py` muestra "All production features configured"
- [ ] Health check muestra todo "configured"
- [ ] Chat response tiene `grounded: true`
- [ ] Métricas trackean OCR usage

**Cuando tengas todos ✅ → Sistema 100% funcional para producción!** 🚀

---

## 📞 Siguientes Pasos

1. ✅ **Completa este setup** (45-60 min)
2. 🧪 **Prueba con drawing real** de Gen6
3. 📊 **Revisa métricas** para validar accuracy
4. 🎯 **Ajusta thresholds** si es necesario
5. 🚀 **Deploy a Cloud Run** cuando esté listo

---

**¡Todo listo para NO perder información y tener grounding REAL!** ✨

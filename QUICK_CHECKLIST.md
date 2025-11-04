# ✅ Quick Setup Checklist

## Setup Completo en 45-60 minutos

### ☐ Paso 1: GCP Base (20 min)
```bash
./scripts/setup_gcp.sh sustained-truck-408014 us-central1
```
✅ Verifica: `ls -la service-account-key.json`

---

### ☐ Paso 2: RAG Engine (15 min) ⭐ OBLIGATORIO
```bash
./scripts/setup_rag_engine.sh sustained-truck-408014 us-central1
```
✅ Copia `RAG_DATA_STORE_ID` a `.env`
✅ Sube manuales al data store

**Sin esto:** Chat no tendrá grounding en tus manuales

---

### ☐ Paso 3: Document AI (10 min) ⭐ OBLIGATORIO
```bash
./scripts/setup_document_ai.sh sustained-truck-408014
```
✅ Copia `DOCUMENT_AI_PROCESSOR_ID` a `.env`

**Sin esto:** Se perderá información de microtexto

---

### ☐ Paso 4: Dependencias (10 min)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### ☐ Paso 5: Verificar .env

Debe tener MÍNIMO:
```bash
# Base
GCP_PROJECT_ID=sustained-truck-408014
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Buckets
GCS_BUCKET_MANUALS=sustained-truck-408014-manuals
GCS_BUCKET_DRAWINGS=sustained-truck-408014-drawings
GCS_BUCKET_REPORTS=sustained-truck-408014-reports

# ⭐ OBLIGATORIO: RAG
RAG_DATA_STORE_ID=projects/sustained-truck-408014/...
ENABLE_GROUNDING=true

# ⭐ OBLIGATORIO: Document AI
DOCUMENT_AI_PROCESSOR_ID=abc123...
ENABLE_DOCUMENT_AI_FALLBACK=true
```

---

### ☐ Paso 6: Correr
```bash
source venv/bin/activate
python main.py
```

Debe mostrar:
```
✅ All production features configured!
```

---

### ☐ Paso 7: Probar
```bash
# Health check
curl http://localhost:8080/health

# Debe mostrar:
# "rag_grounding": "configured"
# "document_ai_ocr": "configured"
```

---

## 🔥 Si algo falla:

**Ver guía completa:** `SETUP_COMPLETE.md`

**Logs de startup:** El sistema te avisa qué falta

**Health check:** Muestra status de cada feature

---

## ✨ Cuando todo esté ✅

Sistema 100% funcional:
- ✅ RAG grounding (chat usa TUS manuales)
- ✅ OCR fallback (no pierde información)
- ✅ Métricas (tracking completo)
- ✅ Reports (Executive + Detailed)
- ✅ Vector Search (similarity visual)

**Tiempo total: 45-60 min**
**Costo: ~$0.11 por análisis**

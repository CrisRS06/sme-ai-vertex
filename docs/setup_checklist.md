# 🚀 Checklist: Lo Que Falta Para Hacer Pruebas End-to-End

**Última actualización:** 2025-11-05
**Estado actual:** Backend arranca en modo MOCK, Frontend funciona, pero falta configuración GCP REAL para features completos

---

## 🎯 Resumen Ejecutivo

**Para hacer pruebas básicas (AHORA):**
- ✅ Backend puede arrancar en modo MOCK
- ✅ Frontend puede arrancar
- ❌ **FALTA:** Configurar GCP REAL para Gemini VLM
- ❌ **FALTA:** Configurar Document AI para OCR
- ❌ **FALTA:** Probar con plano PDF real

**Para pruebas completas (después):**
- ❌ RAG Engine (chat con knowledge base)
- ❌ Vector Search (búsqueda semántica)
- ❌ Cloud Storage (almacenamiento de reportes)

---

## 📋 Checklist por Categoría

### 🔴 CRÍTICO - Necesario para análisis básico

#### 1. Google Cloud Platform Setup
**Estado:** ❌ NO CONFIGURADO

**Qué hacer:**
```bash
# 1. Autenticar con GCP
gcloud auth login
gcloud auth application-default login

# 2. Configurar proyecto
gcloud config set project TU_PROJECT_ID

# 3. Habilitar APIs requeridas
gcloud services enable \
  aiplatform.googleapis.com \
  storage-api.googleapis.com \
  documentai.googleapis.com
```

**Tiempo:** 5-10 minutos
**Costo:** Gratis (solo habilitar APIs)

**Actualizar .env:**
```bash
# Cambiar de MOCK a REAL
GCP_PROJECT_ID=tu-project-id-real  # NO "sme-ai-dev-mock"
```

---

#### 2. Vertex AI (Gemini VLM) - REQUERIDO para análisis
**Estado:** ✅ Código listo, ⏳ Necesita GCP configurado

**Qué se necesita:**
- GCP project con billing habilitado
- Vertex AI API enabled (paso anterior)
- Service account con permisos (opcional si usas gcloud auth)

**Verificar que funciona:**
```python
python -c "
from google.cloud import aiplatform
aiplatform.init(project='TU_PROJECT_ID', location='us-central1')
print('✅ Vertex AI configured')
"
```

**Costo por análisis:**
- Gemini Flash: ~$0.01 por plano
- Gemini Pro: ~$0.04 por plano

---

#### 3. Document AI (OCR Fallback) - CRÍTICO para precisión
**Estado:** ❌ NO CONFIGURADO

**Qué hacer:**
```bash
# Ejecutar script de setup
./scripts/setup_document_ai.sh TU_PROJECT_ID

# Output te da:
# DOCUMENT_AI_PROCESSOR_ID=abc123xyz

# Agregar a .env:
DOCUMENT_AI_PROCESSOR_ID=abc123xyz  # El real
ENABLE_DOCUMENT_AI_FALLBACK=true    # Cambiar a true
```

**Tiempo:** 5 minutos
**Costo:** $1.50 per 1,000 pages (se activa solo cuando necesario)

---

#### 4. Cloud Storage Buckets - Para guardar reportes
**Estado:** ⚠️ MOCK (funciona pero no guarda real)

**Qué hacer:**
```bash
PROJECT_ID="tu-project-id"

# Crear buckets
gsutil mb gs://sme-ai-manuals-$PROJECT_ID
gsutil mb gs://sme-ai-drawings-$PROJECT_ID
gsutil mb gs://sme-ai-reports-$PROJECT_ID

# Actualizar .env:
GCS_BUCKET_MANUALS=sme-ai-manuals-tu-project-id
GCS_BUCKET_DRAWINGS=sme-ai-drawings-tu-project-id
GCS_BUCKET_REPORTS=sme-ai-reports-tu-project-id
```

**Tiempo:** 2 minutos
**Costo:** ~$0.02/GB/mes (storage), casi gratis al inicio

---

### 🟡 IMPORTANTE - Para features completos

#### 5. RAG Engine (Chat con Knowledge Base)
**Estado:** ❌ NO CONFIGURADO (sistema funciona sin esto)

**Qué hace:**
- Chat puede hacer preguntas sobre análisis
- Respuestas groundeadas en knowledge base
- Referencias a secciones específicas de manuales

**Qué hacer:**
```bash
# Ejecutar script de setup
./scripts/setup_rag_engine.sh TU_PROJECT_ID us-central1

# Output te da:
# RAG_DATA_STORE_ID=xyz789

# Agregar a .env:
RAG_DATA_STORE_ID=xyz789
```

**Tiempo:** 10 minutos
**Costo:** $0 (primera carga), luego ~$0.001 por query

**Opcional por ahora:** Sistema funciona sin chat groundeado

---

#### 6. Datos de Prueba
**Estado:** ⚠️ FALTAN PLANOS DE PRUEBA

**Qué necesitas:**
- 1-2 planos técnicos en PDF
- Pueden ser simples al inicio
- Idealmente uno que conozcas bien

**Opciones:**
```bash
# Opción A: Descargar ejemplo público
curl -o sample.pdf https://example.com/technical-drawing.pdf

# Opción B: Usar tus propios planos
# Copiar a: ./samples/parte_123.pdf
```

---

### 🟢 OPCIONAL - Para producción

#### 7. Service Account (Mejor que user auth)
**Estado:** ⏳ OPCIONAL (usa gcloud auth por ahora)

**Para producción (después):**
```bash
# Crear service account
gcloud iam service-accounts create sme-ai-vertex \
  --display-name="SME AI Vertex Service Account"

# Dar permisos
gcloud projects add-iam-policy-binding TU_PROJECT_ID \
  --member="serviceAccount:sme-ai-vertex@TU_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Crear key
gcloud iam service-accounts keys create service-account-key.json \
  --iam-account=sme-ai-vertex@TU_PROJECT_ID.iam.gserviceaccount.com

# Actualizar .env:
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
```

---

#### 8. Vector Search (Búsqueda semántica de precedentes)
**Estado:** ❌ NO CONFIGURADO (opcional)

**Qué hace:**
- Buscar partes similares analizadas anteriormente
- "¿Qué otros análisis tenemos de ABS con wall thickness <1mm?"

**Setup:** Similar a RAG Engine, usa script existente

**Opcional por ahora**

---

## ✅ Lo Que YA ESTÁ Listo

### Backend
- ✅ FastAPI app funcionando
- ✅ API routes definidos:
  - `/analysis/upload` - Subir plano
  - `/analysis/documents` - Listar análisis
  - `/analysis/{id}` - Ver análisis específico
  - `/health` - Health check
- ✅ Models (Pydantic) para todos los datos
- ✅ Services implementados:
  - DrawingAnalyzer (Gemini VLM)
  - ExceptionEngine (validaciones)
  - ReportGenerator (HTML reports)
  - DocumentAI (OCR fallback)
- ✅ Templates HTML para reportes
- ✅ 13/13 categorías técnicas implementadas

### Frontend
- ✅ Next.js 16 app
- ✅ Pages implementadas:
  - Upload page
  - Analysis list
  - Analysis detail
  - Chat interface
- ✅ API client (`lib/api.ts`) completo
- ✅ TypeScript types

### Scripts
- ✅ `setup_document_ai.sh`
- ✅ `setup_rag_engine.sh`
- ✅ `test_drawing_precision.py`
- ✅ `smoke_test.sh`

---

## 🚀 Pasos Para Hacer Primera Prueba

### Opción A: Prueba Rápida (30 min)

**Solo para ver que arranca:**

```bash
# 1. Arrancar backend (modo MOCK - sin GCP)
python main.py

# Debería mostrar:
# ⚠️  PRODUCTION-CRITICAL FEATURES NOT CONFIGURED
# System will work but with reduced capabilities.

# 2. En otra terminal, arrancar frontend
cd frontend
npm run dev

# 3. Abrir browser
http://localhost:3000

# 4. Probar upload page
# - Seleccionar PDF
# - Click "Upload"
# - Verás error porque GCP no está configurado
```

**Resultado:** Confirmas que el código arranca, pero no funciona sin GCP

---

### Opción B: Prueba Funcional (1-2 horas)

**Para que REALMENTE funcione:**

```bash
# 1. Configurar GCP (15 min)
gcloud auth login
gcloud auth application-default login
gcloud config set project TU_PROJECT_ID

# Habilitar APIs
gcloud services enable \
  aiplatform.googleapis.com \
  documentai.googleapis.com \
  storage-api.googleapis.com

# 2. Crear Document AI processor (5 min)
./scripts/setup_document_ai.sh TU_PROJECT_ID

# 3. Actualizar .env (2 min)
# Cambiar:
GCP_PROJECT_ID=tu-project-id-real
DOCUMENT_AI_PROCESSOR_ID=el-que-te-dio-el-script
ENABLE_DOCUMENT_AI_FALLBACK=true

# 4. Crear storage buckets (5 min)
gsutil mb gs://sme-ai-reports-TU_PROJECT_ID

# Actualizar .env:
GCS_BUCKET_REPORTS=sme-ai-reports-TU_PROJECT_ID

# 5. Arrancar backend
python main.py

# Debería mostrar:
# ✅ All production features configured!
# (o solo warning sobre RAG si no lo configuraste)

# 6. Arrancar frontend
cd frontend
npm run dev

# 7. Probar con plano real
# - Ir a http://localhost:3000
# - Upload → seleccionar PDF
# - Esperar análisis (~30-60 segundos)
# - Ver reporte de excepciones
```

**Resultado:** Sistema completamente funcional end-to-end ✅

---

## 💰 Costos Estimados (Pruebas)

**Setup (una vez):**
- Habilitar APIs: $0
- Crear processors: $0
- Crear buckets: $0
**Total setup:** $0

**Por análisis:**
- Gemini Flash VLM: ~$0.01
- Document AI OCR (10-20% del tiempo): ~$0.0003
- Cloud Storage: ~$0.0001
**Total por plano:** ~$0.01

**Para 100 pruebas:** ~$1.00 USD

**Muy económico para validar el sistema** ✅

---

## ⚠️ Errores Comunes y Soluciones

### Error 1: "Credentials not found"
```
❌ Error: Could not load default credentials
```
**Solución:**
```bash
gcloud auth application-default login
```

### Error 2: "API not enabled"
```
❌ Error: aiplatform.googleapis.com is not enabled
```
**Solución:**
```bash
gcloud services enable aiplatform.googleapis.com
```

### Error 3: "Permission denied"
```
❌ Error: Permission 'aiplatform.endpoints.predict' denied
```
**Solución:**
```bash
# Asegúrate que tu user tiene permisos
gcloud projects add-iam-policy-binding TU_PROJECT_ID \
  --member="user:TU_EMAIL" \
  --role="roles/aiplatform.user"
```

### Error 4: "Bucket not found"
```
❌ Error: Bucket sme-ai-reports-mock does not exist
```
**Solución:**
```bash
# Crear bucket real
gsutil mb gs://sme-ai-reports-TU_PROJECT_ID

# Actualizar .env
GCS_BUCKET_REPORTS=sme-ai-reports-TU_PROJECT_ID
```

---

## 📊 Resumen: Qué Priorizar

### Para prueba MÍNIMA (solo ver que arranca):
1. ✅ Ya está listo - solo `python main.py`
2. ⚠️ Verás warnings pero arranca

### Para prueba FUNCIONAL (análisis real):
1. 🔴 **CRÍTICO:** Configurar GCP (gcloud auth)
2. 🔴 **CRÍTICO:** Habilitar Vertex AI API
3. 🔴 **CRÍTICO:** Setup Document AI processor
4. 🔴 **CRÍTICO:** Tener 1-2 planos PDF de prueba

### Para prueba COMPLETA (todos los features):
5. 🟡 Crear Cloud Storage buckets
6. 🟡 Configurar RAG Engine (chat)
7. 🟢 Service account (opcional, mejor usar gcloud auth)

---

## 🎯 Recomendación

**Empieza con Opción B - Prueba Funcional:**

1. **Hoy (1 hora):**
   - Configurar GCP básico
   - Setup Document AI
   - Probar con 1 plano PDF

2. **Después (cuando funcione):**
   - Agregar más planos de prueba
   - Configurar RAG Engine para chat
   - Optimizar prompts basado en resultados

**No necesitas TODO configurado para empezar** - con GCP básico + Document AI ya puedes hacer análisis reales y ver qué tan preciso es el sistema.

---

## 📝 Checklist Rápido

Marca ✅ lo que ya tienes:

**Prerequisitos:**
- [ ] Google Cloud project creado
- [ ] Billing habilitado en GCP project
- [ ] gcloud CLI instalado
- [ ] Python 3.11+ instalado
- [ ] Node.js 18+ instalado

**Configuración GCP:**
- [ ] `gcloud auth login` ejecutado
- [ ] `gcloud auth application-default login` ejecutado
- [ ] Vertex AI API habilitada
- [ ] Document AI API habilitada
- [ ] Document AI processor creado
- [ ] DOCUMENT_AI_PROCESSOR_ID en .env

**Código:**
- [x] Backend dependencies instaladas
- [x] Frontend dependencies instaladas
- [x] .env configurado (mock o real)
- [x] frontend/.env.local configurado

**Datos de Prueba:**
- [ ] 1-2 planos PDF disponibles
- [ ] Planos copiados a ./samples/

**Listo para probar cuando tengas:** ✅ en GCP setup + planos PDF

---

**Siguiente paso:** ¿Ya tienes un GCP project? Si sí → configuremos GCP ahora mismo. Si no → créalo primero (5 min) y luego continuamos.

# ☑️ Checklist para Arrancar en Google Cloud

**Fecha de revisión**: 2025-11-05
**Estado del proyecto**: Código listo, falta configuración de infraestructura

---

## 📋 Resumen Ejecutivo

El código de la aplicación está completo y listo para producción. Lo que **FALTA** son los pasos de configuración de infraestructura en Google Cloud Platform (GCP).

**Tiempo estimado de setup**: 30-45 minutos
**Costo estimado mensual**: ~$589 USD (con optimizaciones)

---

## ✅ Estado Actual

### Lo que YA ESTÁ listo:
- ✅ Código de la aplicación (FastAPI)
- ✅ Dockerfile configurado
- ✅ Scripts de automatización creados
- ✅ Documentación completa
- ✅ Dependencias definidas (requirements.txt)
- ✅ Estructura del proyecto lista

### Lo que FALTA configurar:
- ❌ Archivo `.env` con configuración
- ❌ Service Account y credenciales
- ❌ Buckets de Cloud Storage
- ❌ APIs de GCP habilitadas
- ❌ Vector Search Index
- ❌ RAG Engine Corpus
- ❌ Document AI Processor (opcional)
- ❌ Despliegue a Cloud Run

---

## 🚀 Pasos para Arrancar (Orden Recomendado)

### 📍 PASO 1: Prerequisitos (5 minutos)

**Acción requerida:**
```bash
# 1. Verificar que tienes instalado:
gcloud --version    # Google Cloud CLI
docker --version    # Docker
python --version    # Python 3.11+

# 2. Autenticarte en GCP
gcloud auth login
gcloud auth application-default login

# 3. Verificar que el proyecto GCP tiene facturación habilitada
# (Ir a: https://console.cloud.google.com/billing)
```

**Checklist:**
- [ ] gcloud CLI instalado y actualizado
- [ ] Docker instalado (para deploy)
- [ ] Python 3.11+ instalado (para testing local)
- [ ] Cuenta GCP con facturación habilitada
- [ ] Permisos de Project Editor o Owner

**¿Por qué es necesario?**
Estos son los requisitos mínimos para ejecutar los scripts de configuración.

---

### 📍 PASO 2: Configuración Base de GCP (10 minutos)

**Acción requerida:**
```bash
# Define tu PROJECT_ID
export PROJECT_ID="tu-project-id-aqui"  # ⚠️ CAMBIAR ESTO
export REGION="us-central1"

# Ejecutar script de setup
./scripts/setup_gcp.sh $PROJECT_ID $REGION
```

**Lo que hace este script:**
- ✅ Habilita APIs necesarias (Vertex AI, Storage, Document AI, Cloud Run, Cloud Build)
- ✅ Crea 3 buckets de Cloud Storage:
  - `${PROJECT_ID}-manuals` (para manuales y documentación)
  - `${PROJECT_ID}-drawings` (para dibujos técnicos)
  - `${PROJECT_ID}-reports` (para reportes generados)
- ✅ Crea Service Account `sme-ai-vertex-sa`
- ✅ Asigna roles IAM necesarios
- ✅ Genera archivo `service-account-key.json` con credenciales
- ✅ Crea archivo `.env` con configuración base

**Checklist:**
- [ ] Script ejecutado sin errores
- [ ] Archivo `.env` creado
- [ ] Archivo `service-account-key.json` creado (⚠️ NO COMMITEAR)
- [ ] Buckets creados (verificar con `gsutil ls`)

**Verificación:**
```bash
# Verificar que los buckets existen
gsutil ls | grep $PROJECT_ID

# Verificar service account
gcloud iam service-accounts list | grep sme-ai-vertex

# Verificar que .env existe
cat .env
```

---

### 📍 PASO 3: Setup RAG Engine (5 minutos)

**Acción requerida:**
```bash
# Ejecutar script de setup RAG
./scripts/setup_rag_engine.sh $PROJECT_ID $REGION
```

**Lo que hace este script:**
- ✅ Crea un RAG Corpus para el knowledge base
- ✅ Configura chunking óptimo (512 tokens, overlap 100)
- ✅ Actualiza `.env` con el nombre del corpus

**Checklist:**
- [ ] RAG Corpus creado
- [ ] Variable `RAG_CORPUS_NAME` en `.env` actualizada

**¿Por qué es necesario?**
El RAG Engine permite hacer búsqueda semántica en los manuales de moldeo y responder preguntas con grounding.

---

### 📍 PASO 4: Setup Vector Search (15 minutos)

**Acción requerida:**
```bash
# Ejecutar script de setup Vector Search
./scripts/setup_vector_search.sh $PROJECT_ID $REGION sme-vector-index
```

**Lo que hace este script:**
- ✅ Crea índice de Vector Search con configuración TreeAH
- ✅ Despliega endpoint con e2-standard-16 (auto-scaling)
- ✅ Actualiza `.env` con IDs del índice y endpoint

**Checklist:**
- [ ] Vector Search Index creado
- [ ] Vector Search Endpoint desplegado
- [ ] Variables `VECTOR_SEARCH_INDEX_ID` y `VECTOR_SEARCH_ENDPOINT_ID` en `.env` actualizadas

**Tiempo de despliegue:** ~10-15 minutos (Vertex AI despliega el endpoint)

**⚠️ IMPORTANTE:**
- Este es el componente más costoso (~$547/mes para e2-standard-16)
- Si solo quieres probar, puedes **OMITIR** este paso inicialmente
- La app funcionará con fallback local (menos eficiente pero gratis)

**Verificación:**
```bash
# Verificar que el índice existe
gcloud ai indexes list --region=$REGION --project=$PROJECT_ID

# Verificar que el endpoint existe
gcloud ai index-endpoints list --region=$REGION --project=$PROJECT_ID
```

---

### 📍 PASO 5: Setup Document AI (Opcional, 5 minutos)

**Acción requerida:**
```bash
# Ejecutar script de setup Document AI
./scripts/setup_document_ai.sh $PROJECT_ID $REGION
```

**Lo que hace este script:**
- ✅ Crea un procesador de Document AI para OCR
- ✅ Actualiza `.env` con el PROCESSOR_ID

**Checklist:**
- [ ] Document AI Processor creado
- [ ] Variable `DOCUMENTAI_PROCESSOR_ID` en `.env` actualizada

**¿Por qué es opcional?**
Document AI es un fallback para cuando el procesamiento de PDF falla. La app puede funcionar sin él usando solo el procesamiento local de PDFs.

**Costo:** ~$1.50 por cada 1000 páginas procesadas

---

### 📍 PASO 6: Testing Local (5 minutos)

**Acción requerida:**
```bash
# Instalar dependencias
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Ejecutar la aplicación localmente
python main.py
```

**En otra terminal:**
```bash
# Test rápido
curl http://localhost:8080/health

# Abrir documentación
open http://localhost:8080/docs
```

**Checklist:**
- [ ] Servidor arranca sin errores
- [ ] `/health` responde con status "healthy"
- [ ] Swagger UI carga en `/docs`
- [ ] Puedes hacer upload de un documento de prueba

**¿Por qué hacer testing local primero?**
Es más rápido iterar y debuggear localmente antes de desplegar a la nube.

---

### 📍 PASO 7: Deploy a Cloud Run (10 minutos)

**Acción requerida:**
```bash
# Deploy a producción
./scripts/deploy_cloudrun.sh $PROJECT_ID $REGION
```

**Lo que hace este script:**
- ✅ Construye la imagen Docker con Cloud Build
- ✅ Pushea la imagen a Container Registry
- ✅ Despliega el servicio en Cloud Run
- ✅ Configura auto-scaling (0-10 instancias)
- ✅ Asigna el service account correcto

**Checklist:**
- [ ] Build exitoso
- [ ] Deploy exitoso
- [ ] Service URL generada
- [ ] Health check responde en producción

**Verificación:**
```bash
# Guardar la URL del servicio
export SERVICE_URL=$(gcloud run services describe sme-ai-vertex \
  --region=$REGION \
  --format='value(status.url)')

# Test en producción
curl $SERVICE_URL/health

# Ver logs
gcloud run logs tail sme-ai-vertex --region=$REGION
```

---

### 📍 PASO 8: Testing End-to-End (5 minutos)

**Acción requerida:**
```bash
# Test automatizado del sistema completo
./scripts/test_system.sh $SERVICE_URL
```

**Este script prueba:**
- ✅ Health check
- ✅ Upload de documento al knowledge base
- ✅ Upload de dibujo técnico
- ✅ Análisis completo
- ✅ Generación de reporte
- ✅ Chat interactivo

**Checklist:**
- [ ] Todos los tests pasan
- [ ] Puedes ver documentos en los buckets GCS
- [ ] Los reportes se generan correctamente
- [ ] El chat responde con contexto

---

## 📊 Configuración de Variables de Entorno

Después de ejecutar los scripts, tu archivo `.env` debería verse así:

```bash
# Google Cloud Platform
GCP_PROJECT_ID=tu-project-id              # ✅ Configurado por setup_gcp.sh
GCP_REGION=us-central1                     # ✅ Configurado por setup_gcp.sh
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json  # ✅ Creado

# Cloud Storage Buckets
GCS_BUCKET_MANUALS=tu-project-manuals      # ✅ Creado por setup_gcp.sh
GCS_BUCKET_DRAWINGS=tu-project-drawings    # ✅ Creado por setup_gcp.sh
GCS_BUCKET_REPORTS=tu-project-reports      # ✅ Creado por setup_gcp.sh

# Vertex AI Models (no requieren configuración)
VERTEX_AI_MODEL_FLASH=gemini-2.5-flash     # ✅ Disponible en Vertex AI
VERTEX_AI_MODEL_PRO=gemini-2.5-pro         # ✅ Disponible en Vertex AI
VERTEX_AI_EMBEDDING_MODEL=multimodalembedding@001  # ✅ Disponible

# RAG Engine
RAG_CORPUS_NAME=molding-knowledge-base     # ✅ Configurado por setup_rag_engine.sh

# Vector Search
VECTOR_SEARCH_INDEX_ID=1234567890          # ⚠️ Configurado por setup_vector_search.sh
VECTOR_SEARCH_ENDPOINT_ID=9876543210       # ⚠️ Configurado por setup_vector_search.sh

# Document AI (opcional)
DOCUMENTAI_PROCESSOR_ID=abc123def456       # ⚠️ Configurado por setup_document_ai.sh (opcional)

# API Configuration (generados automáticamente)
API_KEY=auto-generated-secure-key          # ✅ Generado por setup_gcp.sh
JWT_SECRET_KEY=auto-generated-secret       # ✅ Generado por setup_gcp.sh

# Application Settings
ENVIRONMENT=production                      # ✅ OK
DEBUG=False                                 # ⚠️ Cambiar a False en producción
LOG_LEVEL=INFO                             # ✅ OK

# Feature Flags
QUALITY_MODE=flash                         # ✅ OK (flash es más económico)
ENABLE_DOCUMENT_AI_FALLBACK=true          # ⚠️ Solo si creaste Document AI
ENABLE_CHAT=true                           # ✅ OK
```

---

## 💰 Costos Estimados

### Con Vector Search (Recomendado para producción):
| Componente | Costo/mes |
|------------|-----------|
| Vector Search (e2-standard-16) | $547 |
| Gemini Flash (con caching) | $30 |
| Document AI | $2 |
| Cloud Storage | $10 |
| Cloud Run | $0 (free tier) |
| **TOTAL** | **~$589/mes** |

### Sin Vector Search (Solo para desarrollo/testing):
| Componente | Costo/mes |
|------------|-----------|
| Gemini Flash (con caching) | $30 |
| Cloud Storage | $10 |
| Cloud Run | $0 (free tier) |
| **TOTAL** | **~$40/mes** |

**Recomendación:**
- **Desarrollo**: Empezar sin Vector Search para testing
- **Producción**: Habilitar Vector Search para mejor performance

---

## 🔒 Seguridad

### ⚠️ CRÍTICO - Archivos que NUNCA debes commitear:

```bash
# Verificar que estos archivos están en .gitignore
cat .gitignore | grep -E "\.env|service-account-key\.json"
```

**Archivos sensibles:**
- ❌ `.env` - Contiene configuración sensible
- ❌ `service-account-key.json` - Credenciales de acceso completo
- ❌ `.env.backup` - Puede contener secrets

**Ya están protegidos en `.gitignore`** ✅

---

## 🐛 Troubleshooting

### Error: "Permission denied"
```bash
# Solución: Re-autenticarte
gcloud auth application-default login
```

### Error: "Bucket already exists"
```bash
# Normal si re-ejecutas el script. Los buckets se reusan.
# Solo asegúrate que el nombre en .env coincida.
```

### Error: "API not enabled"
```bash
# Solución: Habilitar manualmente
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
```

### Error: "Quota exceeded"
```bash
# Solución: Solicitar aumento de cuota en GCP Console
# O cambiar a QUALITY_MODE=flash (más económico)
```

### Error en deploy: "Image not found"
```bash
# Solución: Verificar que Cloud Build completó
gcloud builds list --limit=5 --project=$PROJECT_ID
```

---

## 📚 Próximos Pasos Después del Deploy

### 1. Indexar Knowledge Base Real
```bash
# Upload manuales de moldeo
curl -X POST "$SERVICE_URL/knowledgebase/upload" \
  -F "file=@molding_manual.pdf" \
  -F "document_type=manual"
```

### 2. Analizar Primer Dibujo
```bash
curl -X POST "$SERVICE_URL/analysis/upload" \
  -F "file=@drawing.pdf" \
  -F "project_name=Gen6" \
  -F "quality_mode=flash"
```

### 3. Configurar Frontend
- Ver: `FRONTEND_API_GUIDE.md`
- Deploy en Vercel
- Conectar con el SERVICE_URL

### 4. Configurar Autenticación (Producción)
```bash
# En .env, cambiar:
ENVIRONMENT=production
DEBUG=False
# Y configurar JWT/API Keys adecuados
```

### 5. Monitoreo
```bash
# Ver logs en tiempo real
gcloud run logs tail sme-ai-vertex --region=$REGION

# O en GCP Console:
# https://console.cloud.google.com/run
```

---

## ✅ Checklist Final

Marca cada item cuando esté completo:

### Infraestructura Base
- [ ] GCP project con facturación habilitada
- [ ] gcloud CLI instalado y autenticado
- [ ] Archivo `.env` configurado
- [ ] Service account creado con credenciales
- [ ] 3 buckets de Cloud Storage creados

### APIs y Servicios
- [ ] Vertex AI API habilitada
- [ ] Cloud Storage API habilitada
- [ ] Cloud Run API habilitada
- [ ] Cloud Build API habilitada
- [ ] Document AI API habilitada (opcional)

### Vertex AI Services
- [ ] RAG Engine corpus creado
- [ ] Vector Search index creado (opcional para desarrollo)
- [ ] Vector Search endpoint desplegado (opcional)
- [ ] Document AI processor creado (opcional)

### Deployment
- [ ] Testing local exitoso
- [ ] Docker image construida
- [ ] Cloud Run service desplegado
- [ ] Health check responde en producción
- [ ] Test end-to-end completado

### Seguridad
- [ ] `.env` NO está en git
- [ ] `service-account-key.json` NO está en git
- [ ] API keys rotadas (no usar las de ejemplo)
- [ ] Autenticación configurada para producción

---

## 📞 Soporte

**Documentación completa:**
- `README.md` - Overview general
- `QUICKSTART.md` - Setup rápido
- `docs/TESTING_GUIDE.md` - Guía de testing
- `docs/PRODUCTION_DEPLOYMENT.md` - Deploy a producción
- `FRONTEND_API_GUIDE.md` - Integración con frontend

**Scripts de automatización:**
- `scripts/setup_gcp.sh` - Setup base
- `scripts/setup_rag_engine.sh` - RAG corpus
- `scripts/setup_vector_search.sh` - Vector Search
- `scripts/setup_document_ai.sh` - Document AI
- `scripts/deploy_cloudrun.sh` - Deploy a Cloud Run
- `scripts/test_system.sh` - Testing automatizado

---

**Status:** 📝 Checklist creado
**Próxima acción:** Ejecutar `./scripts/setup_gcp.sh <PROJECT_ID> us-central1`

---

## 🎯 Comando Rápido para Arrancar Todo

Si ya revisaste todo y quieres ejecutar el setup completo de una vez:

```bash
# ⚠️ CAMBIAR ESTOS VALORES
export PROJECT_ID="tu-project-id"
export REGION="us-central1"

# Setup completo (30 minutos)
./scripts/setup_gcp.sh $PROJECT_ID $REGION && \
./scripts/setup_rag_engine.sh $PROJECT_ID $REGION && \
./scripts/setup_vector_search.sh $PROJECT_ID $REGION sme-index && \
./scripts/deploy_cloudrun.sh $PROJECT_ID $REGION

# Guardar URL del servicio
export SERVICE_URL=$(gcloud run services describe sme-ai-vertex \
  --region=$REGION --format='value(status.url)')

# Test
./scripts/test_system.sh $SERVICE_URL
```

**¡Listo para producción! 🚀**

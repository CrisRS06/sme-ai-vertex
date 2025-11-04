# Quickstart Guide - Get Running in 15 Minutes

## 🚀 Objetivo
Tener el sistema funcionando localmente y hacer tu primer análisis de prueba.

---

## Paso 1: Prerequisites (5 min)

### Instalar herramientas necesarias

```bash
# 1. Verifica Python 3.11+
python --version  # Debe ser 3.11 o superior

# 2. Instala gcloud CLI (si no lo tienes)
# Mac:
brew install --cask google-cloud-sdk

# Linux:
curl https://sdk.cloud.google.com | bash

# 3. Autentica con GCP
gcloud auth login
gcloud auth application-default login
```

---

## Paso 2: Setup del Proyecto (5 min)

```bash
# 1. Ya estás en el directorio correcto
cd "/Users/christianramirez/Programas/Micro/SME AI Vertex"

# 2. Crea virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# En Windows: venv\Scripts\activate

# 3. Instala dependencias
pip install -r requirements.txt

# 4. Configura GCP (reemplaza YOUR_PROJECT_ID)
./scripts/setup_gcp.sh YOUR_PROJECT_ID us-central1
```

El script de setup hará:
- ✅ Habilitar APIs necesarias
- ✅ Crear buckets de Cloud Storage
- ✅ Crear service account
- ✅ Generar archivo `.env`

**IMPORTANTE:** No hagas commit de `service-account-key.json` (ya está en .gitignore)

---

## Paso 3: Verifica la Configuración (2 min)

```bash
# 1. Verifica que .env existe
cat .env | head -n 5

# Deberías ver:
# GCP_PROJECT_ID=tu-proyecto
# GCP_REGION=us-central1
# GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
# ...

# 2. Verifica que el service account key existe
ls -la service-account-key.json

# 3. Test de autenticación
gcloud auth list
```

---

## Paso 4: Run Locally (1 min)

```bash
# Inicia el servidor
python main.py
```

Deberías ver:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**¡Felicidades!** Tu API está corriendo.

---

## Paso 5: Test Básico (2 min)

Abre otra terminal y prueba:

```bash
# 1. Health check
curl http://localhost:8080/health

# Deberías ver:
# {
#   "status": "healthy",
#   "timestamp": "2025-11-02T...",
#   "version": "0.1.0",
#   "services": {
#     "gcp": "configured",
#     "vertex_ai": "enabled",
#     "knowledge_base": "ready"
#   }
# }

# 2. Abre la documentación interactiva
open http://localhost:8080/docs
```

En `/docs` verás todos los endpoints con Swagger UI.

---

## Paso 6: Primer Upload - Knowledge Base

### Opción A: Via cURL

```bash
# Sube un manual de moldeo (reemplaza con tu archivo)
curl -X POST "http://localhost:8080/knowledgebase/upload" \
  -F "file=@/path/to/molding_manual.pdf" \
  -F "document_type=manual"
```

### Opción B: Via Swagger UI

1. Ve a http://localhost:8080/docs
2. Expande `POST /knowledgebase/upload`
3. Click "Try it out"
4. Sube un PDF
5. Selecciona `document_type`: "manual"
6. Click "Execute"

**Resultado esperado:**
```json
{
  "document_id": "abc-123-...",
  "filename": "molding_manual.pdf",
  "document_type": "manual",
  "size_bytes": 2458972,
  "status": "processing",
  "uploaded_at": "2025-11-02T10:30:00Z",
  "gcs_uri": "gs://your-project-manuals/manual/abc-123-.../molding_manual.pdf"
}
```

---

## Paso 7: Primer Análisis de Plano (Cuando esté implementado)

```bash
# Sube un plano técnico
curl -X POST "http://localhost:8080/analysis/upload" \
  -F "file=@/path/to/technical_drawing.pdf" \
  -F "project_name=Test_Gen6" \
  -F "quality_mode=flash"

# Obtendrás un analysis_id
# {
#   "analysis_id": "xyz-456-...",
#   "status": "processing",
#   ...
# }

# Espera unos segundos y obtén el reporte
curl "http://localhost:8080/analysis/xyz-456.../report?report_type=executive"
```

---

## 🎯 ¿Qué Hacer Ahora?

### Si todo funciona:
1. ✅ Lee `NEXT_STEPS.md` para ver qué implementar
2. ✅ Revisa `src/services/drawing_analyzer.py` (próximo servicio a crear)
3. ✅ Prueba con archivos reales de Gen6

### Si encuentras errores:

#### Error: "gcloud: command not found"
```bash
# Instala gcloud CLI
brew install --cask google-cloud-sdk  # Mac
# O sigue: https://cloud.google.com/sdk/docs/install
```

#### Error: "Permission denied" en scripts
```bash
chmod +x scripts/setup_gcp.sh
chmod +x scripts/deploy_cloudrun.sh
```

#### Error: "Module not found"
```bash
# Reinstala dependencias
pip install -r requirements.txt

# O instala la que falta:
pip install <module_name>
```

#### Error: "Authentication failed"
```bash
# Re-autentica
gcloud auth login
gcloud auth application-default login

# Verifica proyecto
gcloud config get-value project
```

#### Error en PDF processing
```bash
# Mac: Instala poppler
brew install poppler

# Linux:
sudo apt-get install poppler-utils libpoppler-dev
```

---

## 📊 Verifica los Recursos en GCP Console

1. Ve a: https://console.cloud.google.com
2. Selecciona tu proyecto
3. Verifica:
   - **Cloud Storage**: Deberías ver 3 buckets (manuals, drawings, reports)
   - **IAM & Admin → Service Accounts**: `sme-ai-vertex-sa`
   - **APIs & Services**: Vertex AI, Cloud Storage, Document AI habilitados

---

## 🧪 Testing Avanzado

Una vez que tengas servicios implementados:

```python
# En Python REPL
from src.services.knowledge_base import KnowledgeBaseService

kb = KnowledgeBaseService()

# Test de RAG tool
rag_tool = kb.get_rag_tool()
print(rag_tool)  # Debería retornar un Tool o None
```

---

## 📚 Documentación Adicional

- **README.md**: Documentación completa del proyecto
- **NEXT_STEPS.md**: Qué implementar a continuación
- **API Docs**: http://localhost:8080/docs (cuando esté corriendo)
- **Vertex AI Docs**: https://cloud.google.com/vertex-ai/docs

---

## 🎉 ¡Éxito!

Si llegaste aquí, tienes:
- ✅ Proyecto configurado
- ✅ GCP setup completo
- ✅ API corriendo localmente
- ✅ Endpoints funcionando
- ✅ Primer documento subido

**Próximo paso:** Implementa `DrawingAnalyzer` para empezar a analizar planos con Gemini 2.5.

---

## 💬 ¿Necesitas Ayuda?

1. Revisa los logs de la aplicación
2. Verifica Cloud Run logs: `gcloud run logs tail sme-ai-vertex`
3. Consulta el README para troubleshooting
4. Revisa los comentarios en el código (TODO markers)

---

**Happy Coding!** 🚀

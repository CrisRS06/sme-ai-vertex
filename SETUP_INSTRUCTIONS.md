# Setup Instructions for Christian

## 🎯 Tu Configuración Personalizada

**Project ID:** `sustained-truck-408014`
**Region:** `us-central1`
**Environment:** Development → Production

---

## ✅ Paso 1: Setup de GCP (30 minutos)

### 1.1 Autentica con GCP

```bash
# Login
gcloud auth login

# Set project
gcloud config set project sustained-truck-408014

# Application default credentials
gcloud auth application-default login
```

### 1.2 Ejecuta el Script de Setup

```bash
cd "/Users/christianramirez/Programas/Micro/SME AI Vertex"

# Make script executable (ya debería estarlo)
chmod +x ./scripts/setup_gcp.sh

# Run setup
./scripts/setup_gcp.sh sustained-truck-408014 us-central1
```

**Este script va a:**
- ✅ Habilitar todas las APIs necesarias (Vertex AI, Cloud Storage, etc.)
- ✅ Crear 3 buckets:
  - `sustained-truck-408014-manuals` (knowledge base)
  - `sustained-truck-408014-drawings` (planos a analizar)
  - `sustained-truck-408014-reports` (reportes generados)
- ✅ Crear service account `sme-ai-vertex-sa`
- ✅ Dar permisos necesarios
- ✅ Generar `service-account-key.json`
- ✅ Tu archivo `.env` ya está creado con el Project ID correcto

**Tiempo estimado:** 5-10 minutos

---

## ✅ Paso 2: Instalar Dependencias (10 minutos)

### 2.1 Verifica Python

```bash
# Debe ser 3.11 o superior
python --version
# o
python3 --version
```

Si necesitas instalar Python 3.11:
```bash
# macOS con Homebrew
brew install python@3.11

# O descarga desde python.org
```

### 2.2 Crea Virtual Environment

```bash
cd "/Users/christianramirez/Programas/Micro/SME AI Vertex"

# Crear venv
python3 -m venv venv

# Activar
source venv/bin/activate

# Verifica que estás en el venv (deberías ver (venv) en el prompt)
```

### 2.3 Instala Dependencias

```bash
# Upgrade pip primero
pip install --upgrade pip

# Instala todas las dependencias
pip install -r requirements.txt
```

**Nota:** Esto puede tomar 5-10 minutos. Si hay errores:
- PDF processing: `brew install poppler` (macOS)
- Build errors: `xcode-select --install` (macOS)

---

## ✅ Paso 3: Verifica el Archivo .env

Tu archivo `.env` ya está creado con tu Project ID. Verifícalo:

```bash
cat .env
```

Deberías ver:
```
GCP_PROJECT_ID=sustained-truck-408014
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
...
```

**Importante:** El archivo `service-account-key.json` se creará cuando ejecutes el script de setup.

---

## ✅ Paso 4: Ejecuta la Aplicación Localmente (5 minutos)

### 4.1 Primera Ejecución

```bash
# Asegúrate de estar en el venv
source venv/bin/activate

# Ejecuta la aplicación
python main.py
```

Deberías ver:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### 4.2 Verifica que Funciona

En otra terminal:

```bash
# Health check
curl http://localhost:8080/health

# Deberías ver:
# {
#   "status": "healthy",
#   "timestamp": "...",
#   "version": "0.1.0",
#   ...
# }
```

### 4.3 Abre la Documentación

En tu navegador:
```
http://localhost:8080/docs
```

Deberías ver la interfaz de Swagger con todos los endpoints listos para probar! 🎉

---

## ✅ Paso 5: Prueba los Endpoints (15 minutos)

### 5.1 Upload un Manual (Knowledge Base)

Desde Swagger UI (`http://localhost:8080/docs`):

1. Expande `POST /knowledgebase/upload`
2. Click "Try it out"
3. Sube un PDF (cualquier manual de moldeo que tengas)
4. Selecciona `document_type`: "manual"
5. Click "Execute"

O desde terminal:
```bash
curl -X POST "http://localhost:8080/knowledgebase/upload" \
  -F "file=@/path/to/your/manual.pdf" \
  -F "document_type=manual"
```

### 5.2 Lista Documentos

```bash
curl "http://localhost:8080/knowledgebase/documents"
```

Deberías ver el documento que subiste.

### 5.3 Get Stats

```bash
curl "http://localhost:8080/knowledgebase/stats"
```

Deberías ver:
```json
{
  "total_documents": 1,
  "documents_by_type": {
    "manual": 1
  },
  "total_pages_indexed": X,
  "last_updated": "..."
}
```

---

## ✅ Paso 6: Testing con Frontend (Opcional)

Si ya tienes tu frontend en Vercel, úsalo para conectar a la API local:

**Frontend .env:**
```
NEXT_PUBLIC_API_URL=http://localhost:8080
```

**En producción:**
```
NEXT_PUBLIC_API_URL=https://your-cloudrun-url.run.app
```

Todos los ejemplos de código están en `FRONTEND_API_GUIDE.md`.

---

## 🚀 Paso 7: Deploy a Production (Cuando estés listo)

### 7.1 Deploy a Cloud Run

```bash
cd "/Users/christianramirez/Programas/Micro/SME AI Vertex"

# Deploy (esto toma 5-10 minutos)
./scripts/deploy_cloudrun.sh sustained-truck-408014 us-central1
```

Este script va a:
- Build la imagen Docker
- Push a Google Container Registry
- Deploy a Cloud Run
- Configurar auto-scaling

### 7.2 Obtén la URL

Al final del deploy verás:
```
Service URL: https://sme-ai-vertex-XXXXX-uc.a.run.app
```

### 7.3 Verifica Production

```bash
# Replace with your Cloud Run URL
curl https://sme-ai-vertex-XXXXX-uc.a.run.app/health
```

---

## 📁 Estructura de Archivos Importantes

```
/Users/christianramirez/Programas/Micro/SME AI Vertex/
├── .env                     ← Tu configuración (YA CREADO)
├── service-account-key.json ← Se crea con setup script
├── main.py                  ← Entry point de la app
├── requirements.txt         ← Dependencias Python
│
├── src/
│   ├── api/                 ← Endpoints REST
│   │   ├── knowledgebase.py ← ✅ TOTALMENTE FUNCIONAL
│   │   ├── analysis.py      ← Stubs (pendiente integrar)
│   │   └── chat.py          ← Stubs (pendiente integrar)
│   │
│   ├── services/            ← Lógica de negocio
│   │   ├── knowledge_base.py    ← ✅ COMPLETO
│   │   ├── drawing_processor.py ← ✅ COMPLETO
│   │   ├── drawing_analyzer.py  ← ✅ COMPLETO
│   │   ├── exception_engine.py  ← ✅ COMPLETO
│   │   ├── report_generator.py  ← ✅ COMPLETO
│   │   └── simple_db.py         ← ✅ COMPLETO (JSON-based)
│   │
│   ├── models/              ← Schemas Pydantic
│   └── config/              ← Configuración GCP
│
├── scripts/
│   ├── setup_gcp.sh         ← Setup automático
│   └── deploy_cloudrun.sh   ← Deploy automático
│
├── templates/               ← Templates de reportes
│   ├── executive_report.html ← ✅ COMPLETO
│   └── detailed_report.html  ← ✅ COMPLETO
│
├── data/                    ← DB local (se crea automáticamente)
│   ├── documents.json       ← Lista de documentos
│   └── analyses.json        ← Lista de análisis
│
└── Documentación/
    ├── README.md                  ← Overview completo
    ├── QUICKSTART.md              ← Guía rápida
    ├── SETUP_INSTRUCTIONS.md      ← Este archivo
    ├── FRONTEND_API_GUIDE.md      ← Guía para frontend
    └── NEXT_STEPS.md              ← Siguientes pasos
```

---

## 🔧 Troubleshooting

### Error: "gcloud: command not found"

```bash
# macOS
brew install --cask google-cloud-sdk

# Luego
gcloud init
```

### Error: "Permission denied" en scripts

```bash
chmod +x scripts/setup_gcp.sh
chmod +x scripts/deploy_cloudrun.sh
```

### Error: Module not found

```bash
# Asegúrate de estar en el venv
source venv/bin/activate

# Reinstala
pip install -r requirements.txt
```

### Error en PDF processing

```bash
# macOS
brew install poppler

# Linux
sudo apt-get install poppler-utils libpoppler-dev
```

### Error: "No module named 'vertexai'"

```bash
# Reinstala con upgrade
pip install --upgrade google-cloud-aiplatform vertexai
```

### La app no inicia

```bash
# Verifica el .env
cat .env

# Verifica que service-account-key.json existe
ls -la service-account-key.json

# Verifica logs
python main.py 2>&1 | tee app.log
```

---

## 📝 Checklist de Setup

- [ ] Autenticado con GCP (`gcloud auth login`)
- [ ] Proyecto configurado (`gcloud config set project sustained-truck-408014`)
- [ ] Script de setup ejecutado (`./scripts/setup_gcp.sh ...`)
- [ ] Service account key creado (`service-account-key.json` existe)
- [ ] Virtual environment creado (`python -m venv venv`)
- [ ] Virtual environment activado (`source venv/bin/activate`)
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Archivo `.env` verificado
- [ ] App corriendo localmente (`python main.py`)
- [ ] Health check OK (`curl http://localhost:8080/health`)
- [ ] Swagger UI funciona (`http://localhost:8080/docs`)
- [ ] Primer documento subido (prueba upload)
- [ ] Stats verificadas

---

## 🎯 Siguiente Paso INMEDIATO

**Una vez que termines el setup:**

1. Lee `FRONTEND_API_GUIDE.md` para integrar con tu frontend
2. Prueba subir varios documentos para knowledge base
3. Cuando esté listo, prueba análisis de planos (cuando integre el pipeline completo)

---

## 💬 Si Necesitas Ayuda

1. Verifica los logs de la aplicación
2. Busca en `README.md` troubleshooting
3. Revisa Cloud Console para errores de GCP
4. Pregúntame lo que sea!

---

**Estado Actual:**
- ✅ Knowledge Base: TOTALMENTE FUNCIONAL
- ✅ Upload/Delete/List/Stats: LISTO
- 🚧 Analysis Pipeline: Servicios listos, falta integración final
- 🚧 Chat: Endpoint existe, implementación pendiente

**Próximo:** Integrar pipeline completo de análisis (Drawing → Analyzer → Exception Engine → Reports)

---

¡Éxito con el setup! 🚀

# Setup Local - SME AI Vertex

Guía completa para ejecutar el sistema SME AI Vertex localmente en tu máquina.

## Requisitos Previos

### 1. Instalar Python 3.11+
Verificar versión:
```bash
python --version
# Debe ser 3.11 o superior
```

### 2. Instalar Node.js (para frontend)
Verificar versión:
```bash
node --version
# Debe ser 18 o superior
```

### 3. Instalar Google Cloud CLI
```bash
# Mac
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows
# Descargar desde: https://cloud.google.com/sdk/docs/install
```

### 4. Configurar Google Cloud
```bash
# Autenticar
gcloud auth application-default login

# Verificar proyecto (si tienes uno configurado)
gcloud config get-value project
```

## Configuración Paso a Paso

### Paso 1: Clonar y Configurar Backend

```bash
# Ir al directorio del proyecto
cd /Users/christianramirez/Programas/Micro/SME\ AI\ Vertex

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
source venv/bin/activate  # Mac/Linux
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env (USAR TUS DATOS REALES)
nano .env
```

**Contenido mínimo del .env:**
```bash
# Google Cloud (REQUERIDO)
GCP_PROJECT_ID=tu-project-id
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Buckets (se crean automáticamente)
GCS_BUCKET_MANUALS=tu-project-manuals
GCS_BUCKET_DRAWINGS=tu-project-drawings  
GCS_BUCKET_REPORTS=tu-project-reports

# Configuración local
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Opcional - para desarrollo local
QUALITY_MODE=flash  # Más rápido y barato
ENABLE_DOCUMENT_AI_FALLBACK=false  # Deshabilitar para evitar costos
```

### Paso 3: Configurar Google Cloud (Si no tienes proyecto)

Si no tienes un proyecto GCP configurado:

```bash
# Crear proyecto
gcloud projects create SME-AI-LOCAL --name="SME AI Local"

# Establecer como proyecto activo
gcloud config set project SME-AI-LOCAL

# Habilitar APIs requeridas
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable documentai.googleapis.com

# Crear service account
gcloud iam service-accounts create sme-ai-vertex-sa

# Asignar roles
gcloud projects add-iam-policy-binding SME-AI-LOCAL \
  --member="serviceAccount:sme-ai-vertex-sa@SME-AI-LOCAL.iam.gserviceaccount.com" \
  --role="roles/aiplatform.admin"

gcloud projects add-iam-policy-binding SME-AI-LOCAL \
  --member="serviceAccount:sme-ai-vertex-sa@SME-AI-LOCAL.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Crear y descargar key
gcloud iam service-accounts keys create ./service-account-key.json \
  --iam-account=sme-ai-vertex-sa@SME-AI-LOCAL.iam.gserviceaccount.com

# Actualizar .env con tu project ID
echo "GCP_PROJECT_ID=SME-AI-LOCAL" >> .env
```

### Paso 4: Ejecutar Backend

```bash
# Asegurar que el entorno virtual esté activo
source venv/bin/activate

# Verificar que el archivo .env existe
ls -la .env

# Ejecutar el servidor
python main.py
```

**Si todo funciona correctamente, deberías ver:**
```
INFO: Started server process [PID]
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### Paso 5: Probar la API

Abrir navegador en: **http://localhost:8080/docs**

Deberías ver la documentación Swagger de la API.

#### Probar endpoints:

**1. Health Check**
```bash
curl http://localhost:8080/health
```

**2. Listar conocimiento base** (debería estar vacío inicialmente)
```bash
curl http://localhost:8080/knowledgebase/documents
```

### Paso 6: Configurar Frontend (Opcional)

```bash
# Ir al directorio frontend
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.local.example .env.local

# Editar .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.local

# Ejecutar frontend
npm run dev
```

Abrir navegador en: **http://localhost:3000**

## Solución de Problemas Comunes

### Error: "Module not found"
```bash
# Asegurar que estás en el directorio correcto
cd /Users/christianramirez/Programas/Micro/SME\ AI\ Vertex

# Exportar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Re-ejecutar
python main.py
```

### Error: "GCP credentials not found"
```bash
# Verificar que el archivo de credenciales existe
ls -la service-account-key.json

# Verificar autenticación
gcloud auth application-default login
```

### Error: "API rate limit exceeded"
- Reducir frecuencia de requests
- Verificar cuotas en Google Cloud Console

### Error: "PDF processing failed"
```bash
# Mac - instalar poppler
brew install poppler

# Linux
sudo apt-get install poppler-utils libpoppler-dev
```

## Estado de Funcionalidades

### ✅ Funciona sin configuración adicional:
- FastAPI server
- Documentación API (/docs)
- Health checks
- Logging estructurado

### ⚠️ Requiere Google Cloud configurado:
- Base de conocimiento (upload de PDFs)
- Análisis de dibujos
- Generación de embeddings
- RAG Engine
- Chat con IA

### ❌ No funciona localmente (requiere despliegue):
- Generación de reportes PDF
- Almacenamiento persistente en la nube

## Próximos Pasos

1. **Configurar Google Cloud** (project, APIs, service account)
2. **Ejecutar backend local**
3. **Probar API endpoints**
4. **Subir documento de prueba a la base de conocimiento**
5. **Analizar un dibujo de prueba**
6. **Revisar logs** para entender el flujo completo

## Archivos Importantes para Revisar

- `main.py` - Punto de entrada de la aplicación
- `src/config/settings.py` - Configuración del sistema
- `src/api/knowledgebase.py` - Endpoints de base de conocimiento
- `src/api/analysis.py` - Endpoints de análisis

¡El sistema está listo para ejecutarse localmente una vez que tengas configurado Google Cloud!

# 🚀 Quick Start - 5 Minutos

**La forma más rápida de probar SME AI Vertex**

---

## ⚡ Opción 1: Testing Local (Recomendado para empezar)

### 1. Clone & Install (2 minutos)

```bash
# Clone
git clone https://github.com/CrisRS06/sme-ai-vertex.git
cd sme-ai-vertex

# Setup Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure (1 minuto)

```bash
# Copiar template
cp .env.example .env

# Editar .env (solo lo mínimo):
# - GCP_PROJECT_ID=tu-project-id
# - GCS_BUCKET_MANUALS=tu-project-manuals
# - GCS_BUCKET_DRAWINGS=tu-project-drawings
# - GCS_BUCKET_REPORTS=tu-project-reports
```

### 3. Authenticate & Create Buckets (1 minuto)

```bash
# Autenticar
gcloud auth application-default login
gcloud config set project tu-project-id

# Habilitar API
gcloud services enable aiplatform.googleapis.com storage-api.googleapis.com

# Crear buckets
gsutil mb -p tu-project-id gs://tu-project-manuals
gsutil mb -p tu-project-id gs://tu-project-drawings
gsutil mb -p tu-project-id gs://tu-project-reports
```

### 4. Run! (30 segundos)

```bash
# Ejecutar servidor
python main.py

# Servidor corriendo en:
# http://localhost:8080
```

### 5. Test (30 segundos)

```bash
# En otra terminal
./scripts/test_system.sh http://localhost:8080

# O manualmente:
curl http://localhost:8080/health
# Abrir: http://localhost:8080/docs
```

**¡Listo! 🎉**

---

## 🧪 Probar con Datos Reales

### Crear PDF de Prueba

```bash
# Crear archivo markdown
cat > test_manual.md <<'EOFINNER'
# Injection Molding Guide

## Wall Thickness for ABS
- Minimum: 1.5mm
- Recommended: 2.0-2.5mm

## Draft Angle
- Minimum: 1-2 degrees
EOFINNER

# Convertir a PDF (necesitas pandoc o cualquier herramienta)
pandoc test_manual.md -o test_manual.pdf

# O simplemente usa cualquier PDF que tengas
```

### Upload Manual

```bash
curl -X POST "http://localhost:8080/knowledgebase/upload" \
  -F "file=@test_manual.pdf" \
  -F "document_type=manual"
```

### Analyze Drawing

```bash
# Usa cualquier PDF técnico que tengas
curl -X POST "http://localhost:8080/analysis/upload" \
  -F "file=@tu_drawing.pdf" \
  -F "project_name=Test" \
  -F "quality_mode=flash"
```

### Chat

```bash
curl -X POST "http://localhost:8080/analysis/general" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the minimum wall thickness for ABS?",
    "history": []
  }'
```

---

## 🚀 Opción 2: Deploy a GCP (Para Producción)

### Setup Completo (30 minutos)

```bash
# 1. Setup GCP
./scripts/setup_gcp.sh tu-project-id us-central1

# 2. Setup RAG (para chat con grounding)
./scripts/setup_rag_engine.sh tu-project-id us-central1

# 3. Setup Vector Search (para búsqueda visual)
./scripts/setup_vector_search.sh tu-project-id us-central1 sme-index

# 4. Deploy
./scripts/deploy_cloudrun.sh tu-project-id us-central1
```

### Test en Producción

```bash
# Guardar URL del deploy
export API_URL="https://sme-ai-vertex-xxx-uc.a.run.app"

# Test
./scripts/test_system.sh $API_URL
```

---

## 📚 Próximos Pasos

Una vez funcionando:

1. **Leer docs completa**:
   - `docs/TESTING_GUIDE.md` - Guía completa de testing
   - `docs/USER_EXPERIENCE.md` - Experiencia end-to-end
   - `docs/PRODUCTION_DEPLOYMENT.md` - Deploy a producción

2. **Explorar API**:
   - Swagger UI: `http://localhost:8080/docs`
   - Probar cada endpoint
   - Ver ejemplos de requests/responses

3. **Indexar manuales reales**:
   - Upload PDFs de molding practices
   - Upload material specifications
   - Upload GD&T references

4. **Analizar dibujos reales**:
   - Start con drawings simples
   - Revisar exception reports
   - Iterar diseños

---

## 🐛 Problemas Comunes

### "Module has no attribute 'rag'"
```bash
pip install --upgrade google-cloud-aiplatform==1.82.0
```

### "Permission denied"
```bash
gcloud auth application-default login
```

### "Bucket not found"
```bash
gsutil ls
gsutil mb -p tu-project-id gs://bucket-name
```

---

## ✅ Verificación Rápida

Sistema funcionando si:
- ✅ `/health` responde "healthy"
- ✅ `/docs` muestra Swagger UI
- ✅ Upload funciona
- ✅ Análisis completa
- ✅ Chat responde

---

**¡Listo para probar! 🎉**

#!/bin/bash
# Check System Readiness for SME AI Vertex
# Verifies all prerequisites and configurations

set -e

echo "=========================================="
echo "🔍 SME AI VERTEX - READINESS CHECK"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0
OK=0

# Helper functions
check_ok() {
    echo "✅ $1"
    ((OK++))
}

check_warning() {
    echo "⚠️  $1"
    ((WARNINGS++))
}

check_error() {
    echo "❌ $1"
    ((ERRORS++))
}

echo "📦 PREREQUISITOS"
echo "----------------------------------------"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    check_ok "Python instalado: $PYTHON_VERSION"
else
    check_error "Python 3.11+ requerido"
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    check_ok "Node.js instalado: $NODE_VERSION"
else
    check_error "Node.js 18+ requerido"
fi

# Check gcloud CLI
if command -v gcloud &> /dev/null; then
    GCLOUD_VERSION=$(gcloud version --format="value(core)" 2>/dev/null || echo "unknown")
    check_ok "gcloud CLI instalado: $GCLOUD_VERSION"
else
    check_error "gcloud CLI requerido: https://cloud.google.com/sdk/docs/install"
fi

echo ""
echo "🔐 AUTENTICACIÓN GCP"
echo "----------------------------------------"

# Check gcloud auth
if gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q .; then
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -n1)
    check_ok "gcloud autenticado: $ACCOUNT"
else
    check_error "gcloud NO autenticado - ejecuta: gcloud auth login"
fi

# Check application-default auth
if [ -f "$HOME/.config/gcloud/application_default_credentials.json" ]; then
    check_ok "Application default credentials configuradas"
else
    check_error "Application default credentials faltantes - ejecuta: gcloud auth application-default login"
fi

# Check project
if gcloud config get-value project 2>/dev/null | grep -q .; then
    PROJECT=$(gcloud config get-value project 2>/dev/null)
    check_ok "GCP project configurado: $PROJECT"
else
    check_error "GCP project NO configurado - ejecuta: gcloud config set project YOUR_PROJECT_ID"
fi

echo ""
echo "🌐 APIs HABILITADAS"
echo "----------------------------------------"

if [ -n "$PROJECT" ]; then
    # Check Vertex AI API
    if gcloud services list --enabled --filter="name:aiplatform.googleapis.com" --format="value(name)" 2>/dev/null | grep -q aiplatform; then
        check_ok "Vertex AI API habilitada"
    else
        check_error "Vertex AI API NO habilitada - ejecuta: gcloud services enable aiplatform.googleapis.com"
    fi

    # Check Document AI API
    if gcloud services list --enabled --filter="name:documentai.googleapis.com" --format="value(name)" 2>/dev/null | grep -q documentai; then
        check_ok "Document AI API habilitada"
    else
        check_warning "Document AI API NO habilitada (opcional para OCR)"
    fi

    # Check Storage API
    if gcloud services list --enabled --filter="name:storage.googleapis.com" --format="value(name)" 2>/dev/null | grep -q storage; then
        check_ok "Cloud Storage API habilitada"
    else
        check_warning "Cloud Storage API NO habilitada (opcional para reportes)"
    fi
else
    check_warning "No se pueden verificar APIs (project no configurado)"
fi

echo ""
echo "📁 ARCHIVOS DE CONFIGURACIÓN"
echo "----------------------------------------"

# Check .env
if [ -f ".env" ]; then
    check_ok ".env existe"

    # Check if GCP_PROJECT_ID is set to real value
    if grep -q "GCP_PROJECT_ID=sme-ai-dev-mock" .env; then
        check_warning ".env usa PROJECT_ID MOCK - actualiza a tu project real"
    else
        check_ok ".env tiene GCP_PROJECT_ID real"
    fi

    # Check Document AI processor
    if grep -q "DOCUMENT_AI_PROCESSOR_ID=$" .env || grep -q "DOCUMENT_AI_PROCESSOR_ID=$" .env; then
        check_warning "DOCUMENT_AI_PROCESSOR_ID no configurado"
    else
        check_ok "DOCUMENT_AI_PROCESSOR_ID configurado"
    fi
else
    check_error ".env NO existe"
fi

# Check frontend .env.local
if [ -f "frontend/.env.local" ]; then
    check_ok "frontend/.env.local existe"
else
    check_warning "frontend/.env.local faltante (usar default)"
fi

echo ""
echo "📦 DEPENDENCIAS"
echo "----------------------------------------"

# Check backend dependencies
if [ -d "venv" ] || [ -d ".venv" ]; then
    check_ok "Virtual environment existe"
else
    check_warning "Virtual environment no detectado - recomendado crear uno"
fi

# Check if requirements installed (rough check)
if python3 -c "import fastapi" 2>/dev/null; then
    check_ok "Backend dependencies parecen instaladas"
else
    check_error "Backend dependencies NO instaladas - ejecuta: pip install -r requirements.txt"
fi

# Check frontend dependencies
if [ -d "frontend/node_modules" ]; then
    check_ok "Frontend dependencies instaladas"
else
    check_error "Frontend dependencies NO instaladas - ejecuta: cd frontend && npm install"
fi

echo ""
echo "🏗️ SERVICIOS GCP CREADOS"
echo "----------------------------------------"

# Check Document AI processor (if we have project)
if [ -n "$PROJECT" ]; then
    PROCESSOR_COUNT=$(gcloud alpha documentai processors list --location=us --project=$PROJECT 2>/dev/null | grep -c "name:" || echo "0")
    if [ "$PROCESSOR_COUNT" -gt 0 ]; then
        check_ok "Document AI processor(s) creado(s): $PROCESSOR_COUNT"
    else
        check_warning "Ningún Document AI processor - ejecuta: ./scripts/setup_document_ai.sh $PROJECT"
    fi
else
    check_warning "No se pueden verificar processors (project no configurado)"
fi

echo ""
echo "📄 DATOS DE PRUEBA"
echo "----------------------------------------"

# Check for sample PDFs
if [ -d "samples" ] && [ "$(ls -A samples/*.pdf 2>/dev/null | wc -l)" -gt 0 ]; then
    PDF_COUNT=$(ls -1 samples/*.pdf 2>/dev/null | wc -l)
    check_ok "Planos de prueba encontrados: $PDF_COUNT"
else
    check_warning "No hay planos PDF en ./samples/ - necesitas algunos para probar"
fi

echo ""
echo "=========================================="
echo "📊 RESUMEN"
echo "=========================================="
echo ""
echo "✅ OK:       $OK"
echo "⚠️  WARNINGS: $WARNINGS"
echo "❌ ERRORS:   $ERRORS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "🔴 SISTEMA NO LISTO - Corrige los errores arriba"
    echo ""
    echo "Comandos rápidos:"
    echo "  gcloud auth login"
    echo "  gcloud auth application-default login"
    echo "  gcloud config set project YOUR_PROJECT_ID"
    echo "  gcloud services enable aiplatform.googleapis.com"
    echo "  pip install -r requirements.txt"
    echo "  cd frontend && npm install"
    echo ""
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo "🟡 SISTEMA FUNCIONAL CON LIMITACIONES"
    echo ""
    echo "Puedes arrancar el sistema pero algunos features no funcionarán."
    echo "Revisa warnings arriba para habilitar features adicionales."
    echo ""
    echo "Para arrancar:"
    echo "  Terminal 1: python main.py"
    echo "  Terminal 2: cd frontend && npm run dev"
    echo "  Browser:    http://localhost:3000"
    echo ""
    exit 0
else
    echo "🟢 SISTEMA COMPLETAMENTE LISTO ✅"
    echo ""
    echo "Todo configurado! Puedes arrancar el sistema:"
    echo ""
    echo "  Terminal 1: python main.py"
    echo "  Terminal 2: cd frontend && npm run dev"
    echo "  Browser:    http://localhost:3000"
    echo ""
    echo "Para probar análisis:"
    echo "  python scripts/test_drawing_precision.py samples/tu_plano.pdf"
    echo ""
    exit 0
fi

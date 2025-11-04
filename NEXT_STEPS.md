# Next Steps - SME AI Vertex Implementation

## ✅ Completed (Phase 1 - Foundation)

1. **Project Structure** - Complete directory structure with proper organization
2. **Configuration** - GCP settings, environment variables, client initialization
3. **API Endpoints** - All REST endpoints with stubs (knowledge base, analysis, chat)
4. **Data Models** - Pydantic schemas including response_schema for Gemini
5. **Knowledge Base Service** - Upload, indexing, RAG Engine integration
6. **Drawing Processor** - PDF→PNG conversion, multimodal embeddings
7. **Deployment** - Dockerfile, Cloud Run scripts, automated setup
8. **Documentation** - Complete README with setup instructions

## 🚧 Pending (Phase 1 - Core MVP)

## 🚀 Upcoming (Phase 2 - RAG Multimodal 2025 Alignment)

1. **Vertex AI Vector Search Hardening**
   - [x] Crear script `scripts/setup_vector_search.sh` para automatizar índice Tree-AH/ScaNN y endpoint
   - [ ] Definir y exportar `VECTOR_SEARCH_INDEX_ID`, `ENDPOINT_ID`, `DEPLOYED_INDEX_ID` en `.env`
   - [ ] Migrar embeddings existentes desde SQLite (`data/vector_search.db`) usando job de reindexado
   - [ ] Configurar pruebas de carga (`neighbor_count`, filtros) y monitoreo de latencia/costos

2. **Ingesta Multimodal Orquestada**
   - [ ] Diseñar pipeline asíncrono (Workflows/Cloud Tasks) para PDFs, imágenes y video
   - [ ] Enriquecer metadatos por chunk con `ChunkMetadata` y almacenar control en BigQuery/Firestore
   - [ ] Integrar Document AI Layout Parser + Vision API para extraer texto/tablas/imágenes antes de indexar

3. **Compatibilidad Vertex AI Vector Search**
   - [x] Implementar registro auxiliar en `vector_registry` para soportar `get_document_embeddings`
   - [ ] Añadir reenrutamiento automático: si Vertex AI no soporta enumeración, regenerar embedding on-demand desde GCS
   - [ ] Ajustar `search` API para soportar filtros avanzados (RRF, top_k dinámico, metadata prefilter)

4. **Validaciones**
   - [ ] Ejecutar `pip install -r requirements.txt` con SDK >= 1.82.0 y validar acceso a `vertexai.rag`
   - [ ] Verificar `get_vector_search()` selecciona modo Vertex AI al detectar configuración completa
   - [ ] Añadir pruebas unitarias para `SQLiteVectorSearchService` y tests de smoke para Vertex AI (mock)


### High Priority - Completar para MVP funcional

#### 1. Drawing Analyzer Service (`src/services/drawing_analyzer.py`)
**Objetivo:** Extraer dimensiones, GD&T, tolerancias de planos usando Gemini 2.5

**Tasks:**
- [ ] Implementar método `analyze_drawing()` que:
  - Carga imágenes PNG del drawing desde GCS
  - Llama Gemini 2.5 (Flash/Pro) con response_schema
  - Pasa el `DRAWING_ANALYSIS_RESPONSE_SCHEMA`
  - Retorna objeto `DrawingAnalysis` estructurado
- [ ] Implementar fallback a Document AI para microtexto (opcional)
- [ ] Agregar campos de `confidence` y `evidence` (bbox, page)
- [ ] Testing con planos de Gen6

**Referencias:**
- `src/models/drawing_analysis.py` - Ya tiene el schema
- `src/services/drawing_processor.py` - Ya procesa PDF→PNG
- Vertex AI Gemini docs: https://cloud.google.com/vertex-ai/docs/generative-ai/multimodal

**Ejemplo de código:**
```python
from vertexai.generative_models import GenerativeModel
from src.models.drawing_analysis import DRAWING_ANALYSIS_RESPONSE_SCHEMA

model = GenerativeModel("gemini-2.5-flash")
response = model.generate_content(
    [image, prompt],
    generation_config={"response_schema": DRAWING_ANALYSIS_RESPONSE_SCHEMA}
)
```

---

#### 2. Exception Engine (`src/services/exception_engine.py`)
**Objetivo:** Validar análisis contra best practices de moldeo

**Tasks:**
- [ ] Crear clase `ExceptionEngine`
- [ ] Definir reglas de best practices:
  - Wall thickness ranges por material
  - Draft angle requirements (por material/superficie)
  - Tolerance limits por proceso
  - Undercut detection
  - Surface finish feasibility
- [ ] Implementar método `validate_analysis()`:
  - Recibe `DrawingAnalysis`
  - Aplica reglas
  - Genera lista de `MoldingException`
  - Clasifica por severity (critical, warning, info)
- [ ] Detectar riesgos de defectos:
  - Flash (tight clearances)
  - Short shot (thin walls, long flow paths)
  - Warp (dimensiones críticas, geometría)
  - Knit lines (múltiples gates, geometría compleja)
- [ ] Testing con casos conocidos (Gen6)

**Estructura sugerida:**
```python
class ExceptionEngine:
    def __init__(self):
        self.rules = self._load_rules()

    def validate_analysis(self, analysis: DrawingAnalysis) -> ExceptionReport:
        exceptions = []
        # Validar dimensiones
        exceptions.extend(self._check_dimensions(analysis.dimensions))
        # Validar GD&T
        exceptions.extend(self._check_gdandt(analysis.gdandt))
        # Detectar riesgos
        exceptions.extend(self._check_defect_risks(analysis))
        return self._generate_report(exceptions)
```

---

#### 3. Report Generator (`src/services/report_generator.py`)
**Objetivo:** Generar reportes Executive y Detailed en PDF/HTML

**Tasks:**
- [ ] Crear clase `ReportGenerator`
- [ ] Implementar templates Jinja2:
  - `templates/executive_report.html` - Resumen (1-2 páginas)
  - `templates/detailed_report.html` - Análisis completo
- [ ] Método `generate_executive_report()`:
  - Summary de excepciones por categoría
  - Lista de critical issues
  - Action items requeridos
  - Sección de firma del cliente
- [ ] Método `generate_detailed_report()`:
  - Todas las dimensiones con bboxes
  - Todas las especificaciones GD&T
  - Todas las excepciones con evidencia
  - Referencias a best practices
  - Páginas del drawing con anotaciones
- [ ] Exportar a PDF usando WeasyPrint
- [ ] Upload a GCS con signed URLs (1 hour expiry)

**Template structure (executive):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Executive Feasibility Report - {{ part_id }}</title>
    <style>
        /* CSS for professional report */
    </style>
</head>
<body>
    <h1>Exception Report - Pre-Acceptance</h1>
    <section class="summary">
        <h2>Summary</h2>
        <p>Critical: {{ critical_count }} | Warning: {{ warning_count }}</p>
    </section>
    <section class="exceptions">
        {% for exc in critical_exceptions %}
        <div class="exception critical">
            <h3>{{ exc.title }}</h3>
            <p>{{ exc.description }}</p>
            <p><strong>Recommended:</strong> {{ exc.recommended_change }}</p>
        </div>
        {% endfor %}
    </section>
    <section class="signature">
        <p>Client sign-off required before proceeding...</p>
    </section>
</body>
</html>
```

---

#### 4. Integrar servicios en API endpoints

**Tasks:**
- [ ] Actualizar `src/api/analysis.py`:
  - En `upload_drawing()`: llamar pipeline completo
    ```python
    # 1. Process drawing
    processor = DrawingProcessor()
    gcs_uris, embeddings = await processor.process_drawing(...)

    # 2. Analyze with VLM
    analyzer = DrawingAnalyzer()
    drawing_analysis = await analyzer.analyze_drawing(...)

    # 3. Validate with Exception Engine
    engine = ExceptionEngine()
    exception_report = engine.validate_analysis(drawing_analysis)

    # 4. Generate reports
    report_gen = ReportGenerator()
    await report_gen.generate_reports(analysis_id, exception_report)
    ```
  - Actualizar status a `COMPLETED` o `FAILED`
  - Guardar resultados en database/storage

- [ ] Actualizar `src/api/knowledgebase.py`:
  - Integrar `KnowledgeBaseService` (ya creado)
  - Implementar métodos reales en lugar de stubs

---

### Medium Priority - Mejorar funcionalidad

#### 5. Database Layer
**Actualmente:** No hay persistencia (excepto GCS)

**Tasks:**
- [ ] Elegir DB: SQLite (local) o Cloud SQL (production)
- [ ] Crear modelos SQLAlchemy o usar simple JSON storage
- [ ] Persistir:
  - `DocumentInfo` (knowledge base)
  - `AnalysisInfo` (análisis status, metadata)
  - `ExceptionReport` (resultados)
  - Chat history

#### 6. Chat Service (`src/services/chat_service.py`)
**Tasks:**
- [ ] Implementar `ChatService`
- [ ] Integrar RAG tool (ya existe en `knowledge_base.py`)
- [ ] Retrieval de:
  - Manuales (RAG Engine)
  - Análisis del drawing específico
  - Exception report
- [ ] Llamar Gemini con contexto completo
- [ ] Citar fuentes (page, section, confidence)
- [ ] Mantener history de conversación

#### 7. Vector Search Integration (Opcional para MVP)
**Tasks:**
- [ ] Crear Vector Search Index para embeddings visuales
- [ ] Crear Endpoint para queries
- [ ] Implementar retrieval de páginas similares
- [ ] Usar para mejorar análisis (encontrar casos similares)

---

### Low Priority - Polish

#### 8. Testing
- [ ] Unit tests para cada service
- [ ] Integration tests para pipelines completos
- [ ] Test con Gen6 (caso conocido)
- [ ] Comparar con análisis humano (Ulrich/Carlos)

#### 9. Metrics & Monitoring
- [ ] Logging estructurado (ya configurado)
- [ ] Métricas:
  - Precision/recall por categoría
  - Tiempo de procesamiento
  - Costo por análisis (Flash vs Pro)
  - % de excepciones detectadas
- [ ] Dashboard simple

#### 10. Security & Auth
- [ ] Implementar JWT authentication
- [ ] API key management
- [ ] Rate limiting (ya configurado)
- [ ] Input validation & sanitization

---

## 📅 Timeline Sugerido

### Semana 1 (Días 1-5)
- ✅ Setup base (completado)
- [ ] Drawing Analyzer (día 1-2)
- [ ] Exception Engine (día 3-4)
- [ ] Report Generator básico (día 5)

### Semana 2 (Días 6-10)
- [ ] Integración en API endpoints
- [ ] Templates de reportes
- [ ] Testing con Gen6
- [ ] Ajustes basados en feedback

### Semana 3 (Días 11-14)
- [ ] Chat service
- [ ] Database layer
- [ ] Metrics básicas
- [ ] Deploy a production
- [ ] Demo con Michael

---

## 🔧 Comandos Útiles

```bash
# Setup inicial (si aún no lo hiciste)
./scripts/setup_gcp.sh YOUR_PROJECT_ID us-central1

# Instalar deps
pip install -r requirements.txt

# Correr localmente
python main.py

# Deploy
./scripts/deploy_cloudrun.sh YOUR_PROJECT_ID us-central1

# Testing
pytest tests/ -v

# Logs (Cloud Run)
gcloud run logs tail sme-ai-vertex --region us-central1
```

---

## 💡 Tips de Implementación

1. **Empieza simple**: Implementa Drawing Analyzer con casos básicos primero
2. **Itera rápido**: No busques perfección, valida con Gen6 temprano
3. **Usa Flash primero**: Más barato, más rápido para desarrollo
4. **Log everything**: structlog ya está configurado, úsalo
5. **Response schema es crítico**: Asegura JSON válido de Gemini
6. **Testing con casos reales**: Gen6 es tu golden test case

---

## 📚 Recursos

- **Vertex AI Gemini**: https://cloud.google.com/vertex-ai/docs/generative-ai/start/quickstarts/quickstart-multimodal
- **RAG Engine**: https://cloud.google.com/vertex-ai/docs/generative-ai/rag/create-rag-corpus
- **Multimodal Embeddings**: https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings/get-multimodal-embeddings
- **FastAPI**: https://fastapi.tiangolo.com
- **Jinja2 Templates**: https://jinja.palletsprojects.com

---

## ❓ Preguntas Frecuentes

**Q: ¿Por qué algunos servicios están vacíos?**
A: Este es el setup base (Phase 1 - Foundation). Los servicios core (Analyzer, Exception Engine, Reports) son Phase 1 - Core MVP.

**Q: ¿Puedo usar modelos diferentes?**
A: Sí, en `.env` cambia `VERTEX_AI_MODEL_FLASH` o `VERTEX_AI_MODEL_PRO`. También puedes usar Claude via Anthropic API.

**Q: ¿Qué pasa con Document AI?**
A: Es fallback opcional para microtexto (cotas minúsculas). Gemini 2.5 VLM es suficiente para la mayoría de casos.

**Q: ¿Cómo pruebo sin GCP?**
A: Difícil, el sistema depende fuertemente de Vertex AI. Puedes mockear los clientes para unit tests.

---

**Siguiente paso recomendado:** Implementar Drawing Analyzer con Gemini 2.5 y probar con un plano simple.

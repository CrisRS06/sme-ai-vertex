# Experiencia de Usuario End-to-End

**SME AI Vertex - Injection Molding Feasibility Analysis**

Este documento describe la experiencia completa del usuario desde la configuración inicial hasta el análisis de dibujos y generación de reportes.

---

## 👥 Personas (Tipos de Usuarios)

1. **Administrador del Sistema** - Configura el sistema y la knowledge base
2. **Ingeniero de Manufactura** - Analiza dibujos técnicos
3. **Cliente/Designer** - Revisa reportes y recibe feedback
4. **Experto SME (Subject Matter Expert)** - Supervisa y valida resultados

---

## 🚀 Fase 1: Setup Inicial (Administrador)

### 1.1 Configuración de Infraestructura

**Tiempo estimado**: 30-45 minutos (one-time)

```bash
# Paso 1: Clonar repositorio
git clone https://github.com/CrisRS06/sme-ai-vertex
cd sme-ai-vertex

# Paso 2: Setup de GCP (automático)
./scripts/setup_gcp.sh PROJECT_ID us-central1
# ✅ Crea buckets, service accounts, habilita APIs

# Paso 3: Setup de RAG Engine
./scripts/setup_rag_engine.sh PROJECT_ID us-central1
# ✅ Crea corpus RAG para knowledge base

# Paso 4: Setup de Vector Search
./scripts/setup_vector_search.sh PROJECT_ID us-central1 sme-vector-index
# ✅ Provisiona índice TreeAH optimizado

# Paso 5: Setup de Document AI (OCR)
./scripts/setup_document_ai_processor.sh PROJECT_ID us-central1
# ✅ Crea processor para OCR fallback
```

**Resultado**:
- ✅ Infraestructura GCP completamente configurada
- ✅ `.env` generado con todas las credenciales
- ✅ Sistema listo para indexar documentos

### 1.2 Deploy del Backend

```bash
# Deploy a Cloud Run
./scripts/deploy_cloudrun.sh PROJECT_ID us-central1

# Salida esperada:
# ✅ Container image construido
# ✅ Servicio desplegado en Cloud Run
# 🌐 URL: https://sme-ai-vertex-xxx-uc.a.run.app
```

**Resultado**:
- 🌐 API REST disponible públicamente
- 📊 Swagger UI: `https://API_URL/docs`
- ❤️ Health check: `https://API_URL/health`

---

## 📚 Fase 2: Construcción de Knowledge Base (Administrador)

### 2.1 Upload de Manuales y Especificaciones

**Experiencia en Frontend (Vercel UI)**:

```
┌────────────────────────────────────────────────────┐
│  📚 Knowledge Base Management                      │
├────────────────────────────────────────────────────┤
│                                                    │
│  Upload Documents                                  │
│  ┌──────────────────────────────────────────────┐ │
│  │  📄 Drop PDF files here or click to browse  │ │
│  │     (Manuals, Specs, Quality Guidelines)    │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  Document Type: [Manual ▼]                        │
│                                                    │
│  [Upload Documents]                                │
│                                                    │
│  Recent Uploads:                                   │
│  ✅ Molding_Best_Practices_2024.pdf (123 pages)   │
│  ✅ Material_Specifications_ABS.pdf (45 pages)    │
│  ✅ GD&T_Reference_Guide.pdf (89 pages)           │
│                                                    │
│  Total Documents: 3 | Total Pages: 257            │
└────────────────────────────────────────────────────┘
```

**Lo que pasa detrás de escenas** (automático):

```
1. Upload PDF → Cloud Storage
   └─ gs://project-manuals/manual/doc-id/filename.pdf

2. Extract Text (PyPDF2)
   └─ "Page 1: Wall thickness should be...\n"

3. Chunking (512 tokens, overlap 100)
   └─ Chunk 1: "Wall thickness should be uniform..."
   └─ Chunk 2: "...uniform across the part. Minimum..."
   └─ Chunk 3: "...Minimum draft angle for ABS..."

4. Generate Embeddings (text-embedding-005)
   └─ [0.123, -0.456, 0.789, ...] (768 dimensions)

5. Index in RAG Engine
   └─ Vertex AI RAG corpus + Vector Search
   └─ ✅ Searchable en <1 segundo

6. Update Database
   └─ Status: INDEXED ✅
```

**Tiempo de procesamiento**:
- 100 páginas PDF: ~2-3 minutos
- Costo: ~$0.10 por documento

**API Call (equivalente)**:

```bash
curl -X POST "https://API_URL/knowledgebase/upload" \
  -F "file=@Molding_Best_Practices.pdf" \
  -F "document_type=manual"

# Response:
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "Molding_Best_Practices.pdf",
  "status": "indexed",
  "page_count": 123,
  "uploaded_at": "2025-11-04T10:30:00Z"
}
```

### 2.2 Verificar Knowledge Base

```
┌────────────────────────────────────────────────────┐
│  📊 Knowledge Base Statistics                      │
├────────────────────────────────────────────────────┤
│                                                    │
│  Total Documents: 15                               │
│  Total Pages: 1,247                                │
│  Total Chunks: 12,458                              │
│                                                    │
│  Documents by Type:                                │
│  ├─ Manuals: 8                                     │
│  ├─ Specifications: 5                              │
│  └─ Quality Manuals: 2                             │
│                                                    │
│  Last Updated: 2 hours ago                         │
│  ✅ Ready for RAG queries                          │
└────────────────────────────────────────────────────┘
```

**Resultado**:
- ✅ Knowledge base completa y searchable
- ✅ Lista para responder preguntas técnicas
- ✅ Grounding para chat con IA

---

## 🎯 Fase 3: Análisis de Dibujo Técnico (Ingeniero)

### 3.1 Upload de Dibujo

**Experiencia en Frontend**:

```
┌────────────────────────────────────────────────────┐
│  🔍 New Drawing Analysis                           │
├────────────────────────────────────────────────────┤
│                                                    │
│  Upload Technical Drawing                          │
│  ┌──────────────────────────────────────────────┐ │
│  │  📐 Drop PDF drawing here                    │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  Project Name: [Gen6 Housing__________]           │
│                                                    │
│  Quality Mode:                                     │
│  ● Flash (Fast, $0.15/1M tokens) ✅               │
│  ○ Pro (Accurate, $1.25/1M tokens)                │
│                                                    │
│  [Analyze Drawing]                                 │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Usuario sube**: `Gen6_Housing_Rev3.pdf` (5 páginas)

**Click en "Analyze Drawing"**

### 3.2 Procesamiento en Tiempo Real

**UI muestra progreso**:

```
┌────────────────────────────────────────────────────┐
│  ⏳ Analyzing Gen6_Housing_Rev3.pdf                │
├────────────────────────────────────────────────────┤
│                                                    │
│  Status: Processing...                             │
│                                                    │
│  ✅ Uploaded to Cloud Storage                     │
│  ✅ Converted PDF → PNG (5 pages)                 │
│  ✅ Generated visual embeddings                   │
│  🔄 Analyzing with Gemini 2.5 Flash...            │
│     └─ Extracting dimensions...                   │
│     └─ Identifying GD&T specs...                  │
│     └─ Detecting tolerances...                    │
│                                                    │
│  Estimated time: 30-45 seconds                     │
│                                                    │
│  [View Progress Details]                           │
└────────────────────────────────────────────────────┘
```

**Pipeline de procesamiento** (automático, 30-45 segundos):

```
Step 1: PDF Processing (5-10s)
├─ Convert PDF → PNG at 300 DPI
│  └─ page_1.png, page_2.png, ..., page_5.png
├─ Upload to GCS
│  └─ gs://project-drawings/analysis-id/page_*.png
└─ Generate multimodal embeddings (1408 dims)
   └─ Store in Vector Search

Step 2: Visual Analysis with Gemini 2.5 Flash (15-25s)
├─ Send all 5 PNG images to Gemini
├─ Use detailed analysis prompt (optimized)
├─ Extract structured JSON:
│  ├─ Part Info (name, material, ID)
│  ├─ Dimensions (value, unit, tolerance, bbox, confidence)
│  ├─ GD&T specs (symbol, value, datum, feature)
│  ├─ Surface finish requirements
│  └─ Notes and annotations
└─ OCR fallback (si confidence < 0.7)
   └─ Document AI Layout Parser

Step 3: Exception Engine Validation (2-5s)
├─ Check wall thickness (min 1.5mm for ABS)
├─ Check draft angles (min 1-2°)
├─ Validate tolerances (achievable for injection molding)
├─ Check for undercuts
├─ Identify molding defect risks:
│  ├─ Flash risk (parting line issues)
│  ├─ Short shot risk (thin walls)
│  ├─ Warp risk (non-uniform thickness)
│  └─ Knit line risk (flow patterns)
└─ Categorize by severity (critical, high, medium, low)

Step 4: Report Generation (5-8s)
├─ Executive Report (1-2 pages)
│  └─ Summary, critical issues, sign-off section
├─ Detailed Report (5-10 pages)
│  └─ All dimensions, GD&T, exceptions with evidence
└─ Upload to GCS + generate signed URLs
```

**Resultado de análisis**:

```json
{
  "part_name": "Gen6 Housing Cover",
  "part_id": "P/N 12345-REV3",
  "material": "ABS",

  "dimensions": [
    {
      "feature": "Overall length",
      "value": "120.5",
      "unit": "mm",
      "tolerance": "±0.2",
      "bbox": [0.15, 0.23, 0.45, 0.26],
      "confidence": 0.95,
      "page": 1
    },
    {
      "feature": "Wall thickness (side wall)",
      "value": "2.5",
      "unit": "mm",
      "tolerance": "±0.1",
      "bbox": [0.62, 0.45, 0.78, 0.48],
      "confidence": 0.92,
      "page": 2
    },
    // ... 47 more dimensions
  ],

  "gdandt": [
    {
      "symbol": "⌖",
      "value": "0.05",
      "datum_reference": "A|B|C",
      "feature": "Mounting holes",
      "confidence": 0.88
    },
    // ... 12 more GD&T specs
  ],

  "surface_finishes": [
    {
      "specification": "Ra 1.6",
      "location": "Outer surface",
      "page": 1
    }
  ]
}
```

### 3.3 Ver Resultados del Análisis

**UI muestra análisis completado**:

```
┌────────────────────────────────────────────────────┐
│  ✅ Analysis Complete - Gen6_Housing_Rev3.pdf      │
├────────────────────────────────────────────────────┤
│                                                    │
│  📊 Extraction Summary                             │
│  ├─ Dimensions Found: 49                           │
│  ├─ GD&T Specifications: 12                        │
│  ├─ Surface Finishes: 3                            │
│  └─ Notes & Annotations: 8                         │
│                                                    │
│  ⚠️  Exception Summary                             │
│  ├─ 🔴 Critical Issues: 2                          │
│  ├─ 🟡 High Priority: 5                            │
│  ├─ 🟢 Medium Priority: 8                          │
│  └─ ℹ️  Low Priority: 3                            │
│                                                    │
│  📄 Reports Available                              │
│  ├─ [Download Executive Report] (PDF)              │
│  └─ [Download Detailed Report] (PDF)               │
│                                                    │
│  💬 [Chat with AI Expert about this analysis]     │
│                                                    │
│  Analyzed: Just now | Quality: Flash               │
│  Processing Time: 42 seconds                       │
└────────────────────────────────────────────────────┘
```

### 3.4 Excepciones Detectadas

**Vista detallada de excepciones**:

```
┌────────────────────────────────────────────────────┐
│  ⚠️  Critical Issues (2)                           │
├────────────────────────────────────────────────────┤
│                                                    │
│  🔴 Wall Thickness Below Minimum                   │
│  └─ Location: Side wall (Page 2)                  │
│     Current: 1.2mm | Required: 1.5mm (ABS)        │
│     Impact: High risk of short shot, weak part    │
│     Recommendation: Increase to minimum 1.5mm     │
│                                                    │
│  🔴 Insufficient Draft Angle                       │
│  └─ Location: Inner ribs (Page 3)                 │
│     Current: 0.5° | Required: 1-2° minimum        │
│     Impact: Ejection problems, surface damage     │
│     Recommendation: Increase to 2° minimum        │
│                                                    │
├────────────────────────────────────────────────────┤
│  🟡 High Priority Issues (5)                       │
├────────────────────────────────────────────────────┤
│                                                    │
│  🟡 Non-uniform Wall Thickness                     │
│  └─ Variation: 1.5mm to 3.5mm (133% difference)   │
│     Impact: Warp risk, sink marks                 │
│     Recommendation: Keep variation <25%           │
│                                                    │
│  🟡 Sharp Corner Detected                          │
│  └─ Location: Bottom edge (Page 2)                │
│     Recommendation: Add radius (min 0.5mm)        │
│     Impact: Stress concentration, mold wear       │
│                                                    │
│  // ... 3 more high priority issues                │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 📄 Fase 4: Revisión de Reportes (Cliente/Designer)

### 4.1 Executive Report (Para Sign-off)

**Formato**: PDF de 1-2 páginas

```
═══════════════════════════════════════════════════════
          EXECUTIVE FEASIBILITY REPORT
═══════════════════════════════════════════════════════

Project: Gen6 Housing Cover
Part Number: P/N 12345-REV3
Material: ABS
Analyzed: November 4, 2025
Quality Mode: Gemini 2.5 Flash

─────────────────────────────────────────────────────

EXECUTIVE SUMMARY

This report assesses the injection molding feasibility
of the Gen6 Housing Cover design based on industry
best practices and material specifications.

FEASIBILITY RATING: ⚠️  CONDITIONAL APPROVAL
(Design requires modifications before tooling)

─────────────────────────────────────────────────────

CRITICAL ISSUES REQUIRING CHANGES (2)

🔴 Wall Thickness Below Minimum
   Location: Side wall (Page 2, Detail B)
   Current: 1.2mm | Required: 1.5mm minimum for ABS

   IMPACT: High risk of incomplete fill (short shot)
   ACTION REQUIRED: Increase to 1.5mm minimum

🔴 Insufficient Draft Angle
   Location: Inner ribs (Page 3)
   Current: 0.5° | Required: 1-2° minimum

   IMPACT: Ejection problems, potential part damage
   ACTION REQUIRED: Increase to 2° minimum

─────────────────────────────────────────────────────

HIGH PRIORITY RECOMMENDATIONS (5)

🟡 Non-uniform wall thickness (133% variation)
🟡 Sharp corners detected (stress concentration risk)
🟡 Long flow path (>150mm) for thin walls
🟡 Potential knit line at gate convergence
🟡 Surface finish may be challenging on Class A

See Detailed Report for full analysis and solutions.

─────────────────────────────────────────────────────

SIGN-OFF SECTION

We acknowledge the issues identified and will:
□ Make required design changes
□ Review detailed technical report
□ Submit revised design for re-analysis

Customer Signature: ________________  Date: ________

Manufacturing Approval: ____________  Date: ________

═══════════════════════════════════════════════════════
```

### 4.2 Detailed Report (Para Ingenieros)

**Formato**: PDF de 5-10 páginas con:

- Tabla completa de dimensiones (49 entries)
- Todas las especificaciones GD&T con bboxes
- Excepciones con evidencia visual
- Referencias a best practices
- Soluciones recomendadas con ejemplos

```
Page 1: Cover + Summary
Page 2-3: All Dimensions Table
Page 4: GD&T Specifications
Page 5-7: Detailed Exception Analysis with Screenshots
Page 8: Recommendations & Best Practice References
Page 9: Material Specifications (ABS)
Page 10: Sign-off & Revision History
```

---

## 💬 Fase 5: Chat con Experto AI (Todos los usuarios)

### 5.1 Chat sobre Análisis Específico

**UI de Chat** (streaming en tiempo real):

```
┌────────────────────────────────────────────────────┐
│  💬 Chat with AI Expert - Gen6 Housing Analysis    │
├────────────────────────────────────────────────────┤
│                                                    │
│  👤 You:                                           │
│  Why is the wall thickness of 1.2mm too thin?     │
│  What problems will this cause?                   │
│                                                    │
│  🤖 AI Expert: (typing...)                         │
│  ▌                                                 │
└────────────────────────────────────────────────────┘
```

**Respuesta streaming** (chunks llegan en tiempo real):

```
┌────────────────────────────────────────────────────┐
│  🤖 AI Expert:                                      │
│                                                    │
│  The 1.2mm wall thickness is below the recommended│
│  minimum of 1.5mm for ABS material for several    │
│  critical reasons:                                 │
│                                                    │
│  **Material Flow Issues:**                         │
│  • ABS has a relatively high viscosity when       │
│    molten. Thin walls (<1.5mm) create high flow   │
│    resistance                                      │
│  • At 1.2mm, the material may freeze before       │
│    completely filling the cavity, causing "short  │
│    shot" defects                                   │
│                                                    │
│  **Mechanical Strength:**                          │
│  • Parts with walls <1.5mm have significantly     │
│    reduced structural integrity                    │
│  • Risk of brittle failure under load             │
│  • Warping more likely during cooling             │
│                                                    │
│  **Manufacturing Challenges:**                     │
│  • Higher injection pressure required (may exceed │
│    machine capacity)                               │
│  • Faster cycle times needed (less time to fill)  │
│  • Quality consistency issues                     │
│                                                    │
│  **Recommendation:**                               │
│  Increase to 1.5mm minimum. Ideally 2.0-2.5mm for │
│  optimal balance of strength, cost, and cycle time│
│                                                    │
│  📚 Sources:                                       │
│  • Molding_Best_Practices_2024.pdf (Page 23)     │
│  • ABS_Material_Spec.pdf (Page 12)                │
│  • Your drawing analysis (Page 2, Detail B)       │
└────────────────────────────────────────────────────┘
```

**Features del chat**:
- ✅ **Grounding**: Respuestas basadas en knowledge base
- ✅ **Context Caching**: Reduce costos en 75%
- ✅ **Streaming**: UX mejorada, respuesta incremental
- ✅ **Sources**: Cita documentos y páginas específicas
- ✅ **Analysis Context**: Conoce el análisis actual

### 5.2 Chat General (Sin Análisis)

```
┌────────────────────────────────────────────────────┐
│  💬 General Molding Expert Chat                    │
├────────────────────────────────────────────────────┤
│                                                    │
│  👤 You:                                           │
│  What's the difference between draft angle and    │
│  taper? When should I use each?                   │
│                                                    │
│  🤖 AI Expert:                                      │
│                                                    │
│  Great question! While often confused, draft and  │
│  taper serve different purposes:                  │
│                                                    │
│  **Draft Angle** (Molding Necessity):             │
│  • Purpose: Enable part ejection from mold        │
│  • Applied to: Vertical walls parallel to pull    │
│    direction                                       │
│  • Typical values: 1-3° minimum                   │
│  • Why needed: Prevents drag/scratches during     │
│    ejection                                        │
│                                                    │
│  **Taper** (Design Feature):                      │
│  • Purpose: Intentional slope for function        │
│  • Applied to: Any surface by design choice       │
│  • Can be any angle                               │
│  • Examples: Conical shapes, wedges               │
│                                                    │
│  **Key Difference:**                               │
│  Draft is a manufacturing requirement added to    │
│  ALL vertical faces. Taper is a design intent.    │
│                                                    │
│  In your CAD:                                      │
│  1. Design your part shape (including tapers)     │
│  2. Then add draft angle to vertical walls        │
│                                                    │
│  📚 Reference: Molding_Best_Practices_2024.pdf    │
│     (Chapter 4: "Draft and Taper Guidelines")     │
└────────────────────────────────────────────────────┘
```

### 5.3 Upload + Chat (Flujo Unificado)

**Nuevo en GA 2025**:

```
┌────────────────────────────────────────────────────┐
│  💬 Quick Analysis Chat                            │
├────────────────────────────────────────────────────┤
│                                                    │
│  [📎 Attach PDF Drawing]  Gen6_Cover_v2.pdf       │
│                                                    │
│  Your message:                                     │
│  ┌────────────────────────────────────────────┐   │
│  │ I updated the wall thickness to 1.5mm.     │   │
│  │ Can you check if this design is now ready  │   │
│  │ for tooling?                                │   │
│  └────────────────────────────────────────────┘   │
│                                                    │
│  [Send]                                            │
│                                                    │
└────────────────────────────────────────────────────┘
```

**AI analiza PDF + responde en una sola interacción**:

```
🤖 AI Expert:

Let me analyze your updated design...

✅ Analysis complete! I can see you've made the following
   improvements:

**Wall Thickness:**
✅ Updated to 1.5mm (meets ABS minimum)
   Previously: 1.2mm ❌ → Now: 1.5mm ✅

**Remaining Issues:**
🟡 Draft angle still 0.5° on inner ribs (Page 3)
   Recommendation: Increase to 2° minimum

🟢 All other critical issues resolved

**Tooling Readiness:** 90%
The design is nearly ready. Just need to address the
draft angle issue and you'll be good to go!

Would you like me to explain how to add draft in your
CAD software?
```

---

## 📊 Fase 6: Métricas y Monitoreo (Administrador)

### 6.1 Dashboard de Métricas

```
┌────────────────────────────────────────────────────┐
│  📊 System Metrics Dashboard                       │
├────────────────────────────────────────────────────┤
│                                                    │
│  Last 30 Days                                      │
│                                                    │
│  Analyses Completed: 127                           │
│  ├─ Flash Mode: 102 (80%)                          │
│  └─ Pro Mode: 25 (20%)                             │
│                                                    │
│  RAG Quality Metrics                               │
│  ├─ Avg Groundedness: 0.87                         │
│  ├─ Avg Relevance: 0.92                            │
│  ├─ Avg Coherence: 0.89                            │
│  └─ Avg Safety: 1.00                               │
│                                                    │
│  Performance                                       │
│  ├─ Avg Analysis Time: 38s                         │
│  ├─ Cache Hit Rate: 56%                            │
│  └─ p95 Latency: 52s                               │
│                                                    │
│  Costs (Month-to-date)                             │
│  ├─ Gemini Models: $28                             │
│  ├─ Vector Search: $547                            │
│  ├─ Document AI: $2                                │
│  └─ Total: $577 (13% under budget)                 │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 🎬 Flujos Completos de Usuario

### Flujo A: Primera Vez (Nuevo Cliente)

1. **Upload Drawing** → `Gen6_Housing_Rev3.pdf`
2. **Wait 40s** → Procesamiento automático
3. **Review Executive Report** → 2 issues críticos identificados
4. **Chat**: "¿Cómo soluciono el problema de wall thickness?"
5. **AI Responde**: Recomendación detallada con referencias
6. **Update CAD** → Corrige dimensiones
7. **Re-upload Drawing** → `Gen6_Housing_Rev4.pdf`
8. **Review New Report** → ✅ Solo 1 warning menor
9. **Download Detailed Report** → Para records
10. **Sign-off** → Enviar a fabricación

**Tiempo total**: 15-20 minutos (incluye correcciones CAD)

### Flujo B: Consulta Rápida (Usuario Experimentado)

1. **Chat General**: "Mejor material para housing con alta resistencia"
2. **AI Responde**: Compara ABS, PC, PC/ABS con pros/cons
3. **Follow-up**: "¿Y si necesito resistencia química?"
4. **AI**: Recomienda PP o PBT con justificación
5. **Done**: Decisión informada en 2 minutos

**Tiempo total**: 2-3 minutos

### Flujo C: Review de Múltiples Variantes

1. **Upload** `Part_A_v1.pdf`, `Part_A_v2.pdf`, `Part_A_v3.pdf`
2. **Review 3 Reports** en paralelo
3. **Compare Exceptions**: v3 tiene menos issues
4. **Chat**: "¿Por qué v3 es mejor que v2?"
5. **AI Explica**: Diferencias técnicas con evidencia
6. **Decision**: Aprobar v3 para tooling

**Tiempo total**: 10 minutos (vs 2-3 horas manual)

---

## 💡 Ventajas de la Experiencia UX

### Para Ingenieros

✅ **Rápido**: 40s vs 2-3 horas manual
✅ **Completo**: Encuentra 95%+ de issues
✅ **Consistent**: Mismos criterios siempre
✅ **Documentado**: Reportes profesionales automáticos
✅ **Educativo**: Chat explica el "por qué"

### Para Clientes

✅ **Transparente**: Executive report fácil de entender
✅ **Accionable**: Issues claros con soluciones
✅ **Professional**: PDFs listos para sign-off
✅ **Iterativo**: Re-análisis rápido después de cambios

### Para la Empresa

✅ **Escalable**: 100+ análisis/día posible
✅ **Económico**: $0.50-2.00 por análisis
✅ **Quality**: Reduce defectos en tooling
✅ **Knowledge**: KB centralizada y searchable
✅ **Metrics**: ROI medible y trackeable

---

## 🔄 Mejora Continua

### Sistema Aprende con Uso

```
Más análisis → Más feedback → Mejor KB → Mejores respuestas
     ↑                                           ↓
     └──────────────  Loop continuo  ────────────┘
```

**Ejemplos de mejora**:
- Nuevos manuales → Más contexto en chat
- Feedback de ingenieros → Refinar Exception Engine
- Casos edge → Entrenar con ejemplos reales

---

## 📱 Acceso Multi-Plataforma

```
Web (Vercel)     Mobile App      API Direct
     ↓               ↓               ↓
     └───────────────┴───────────────┘
                     ↓
            Backend (Cloud Run)
                     ↓
            Vertex AI (Gemini + RAG)
```

---

**Última actualización**: 4 de Noviembre, 2025
**Versión**: 1.0.0
**Status**: Production-Ready (GA 2025)

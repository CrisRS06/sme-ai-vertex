# ✅ Checklist de Alineación con Requisitos de Michael

**Proyecto:** AI-SME - Injection Molding Feasibility Analysis
**Owner:** Michael (Micro Manufacturing)
**Fecha:** 2025-11-05
**Auditor:** Principal Engineer (Autonomous)

---

## 📋 Base de Verdad - Requisitos de Michael

### REQ-1: Exception Report de Fabricabilidad

| # | Requisito | Criterio de Verificación | Prioridad |
|---|-----------|--------------------------|-----------|
| 1.1 | **Enfoque "Exception Only"** - Marcar solo lo que NO es viable | Sistema identifica y reporta solo desviaciones/problemas | 🔴 CRÍTICO |
| 1.2 | **No proponer rediseño** - No sugerir cambios de diseño | Reportes no incluyen "should redesign to..." | 🔴 CRÍTICO |
| 1.3 | **No "tighten" tolerancias** - Solo "loosen" o condiciones | Recomendaciones solo relajan, nunca endurecen specs | 🔴 CRÍTICO |
| 1.4 | **Identificar condiciones para viabilizar** - Si algo no es viable, qué se necesita para hacerlo viable | Cada excepción incluye "Conditions to proceed" | 🟡 ALTA |

**Test Case REQ-1:**
```
Input: Drawing con tolerancia ±0.001" en pared delgada
Expected Output:
  ✓ "Exception: Tolerance ±0.001" too tight for 1mm wall"
  ✓ "Condition: Loosen to ±0.005" OR use precision tooling"
  ✗ NO: "Redesign wall to 2mm thickness"
```

---

### REQ-2: Exactitud + Exhaustividad (Métrica #1)

| # | Categoría Técnica | Criterio de Verificación | Prioridad |
|---|-------------------|--------------------------|-----------|
| 2.1 | **Draft angles** | Sistema detecta ángulos de desmoldeo insuficientes | 🔴 CRÍTICO |
| 2.2 | **Espesores de pared** | Detecta paredes demasiado delgadas/gruesas, variaciones | 🔴 CRÍTICO |
| 2.3 | **Tolerancias dimensionales** | Verifica cada tolerancia contra capacidad de proceso | 🔴 CRÍTICO |
| 2.4 | **GD&T (Geometric Dimensioning & Tolerancing)** | Interpreta y valida símbolos GD&T (flatness, perpendicularity, etc.) | 🔴 CRÍTICO |
| 2.5 | **Materiales** | Valida material especificado vs aplicación y moldeo | 🔴 CRÍTICO |
| 2.6 | **Warpage & Shrinkage** | Predice/identifica riesgos de deformación y contracción | 🟡 ALTA |
| 2.7 | **Acabado superficial** | Verifica especificaciones de acabado (Ra, textura) | 🟡 ALTA |
| 2.8 | **Cavidades & Balanceo** | Evalúa número de cavidades y balance de llenado | 🟡 ALTA |
| 2.9 | **Undercuts & Eyección** | Detecta undercuts y verifica viabilidad de eyección | 🔴 CRÍTICO |
| 2.10 | **Líneas de partición** | Identifica ubicación óptima y problemas potenciales | 🟡 ALTA |
| 2.11 | **Gating & Runner** | Evalúa sistema de alimentación propuesto/sugerido | 🟢 MEDIA |
| 2.12 | **Requisitos críticos** | Distingue áreas cosméticas vs funcionales | 🟡 ALTA |
| 2.13 | **Capacidades de prensa** | Valida contra shot size, fuerza de cierre, plato disponible | 🔴 CRÍTICO |

**Test Case REQ-2:**
```
Input: Drawing completo con todas las especificaciones
Expected Coverage: 13/13 categorías evaluadas
Allowed Misses: 0 categorías críticas, ≤2 categorías alta/media
```

---

### REQ-3: Dos Estilos de Oferta

| # | Requisito | Criterio de Verificación | Prioridad |
|---|-----------|--------------------------|-----------|
| 3.1 | **Especificaciones exhaustivas** | Sistema procesa drawings con specs completas (dimensiones, GD&T, materiales, acabados) | 🔴 CRÍTICO |
| 3.2 | **Especificaciones mínimas** | Sistema funciona con drawings con info limitada (solo geometría básica) | 🔴 CRÍTICO |
| 3.3 | **Adaptación del análisis** | Nivel de detalle del análisis se ajusta a info disponible | 🟡 ALTA |
| 3.4 | **Indicar datos faltantes** | Reporte menciona claramente qué info falta y su impacto | 🟡 ALTA |

**Test Case REQ-3:**
```
Scenario A (Exhaustive):
  Input: Full drawing package (3D CAD + GD&T + material spec + finish)
  Expected: Detailed exception report covering all 13 categories

Scenario B (Minimal):
  Input: Simple 2D sketch with basic dimensions only
  Expected: Analysis based on visible geometry + assumptions listed
```

---

### REQ-4: Conocimiento Fuente

| # | Requisito | Criterio de Verificación | Prioridad |
|---|-----------|--------------------------|-----------|
| 4.1 | **Libros/normas de moldeo** | Knowledge base incluye "Injection Molding Handbook", DFM guidelines | 🔴 CRÍTICO |
| 4.2 | **Datasheets de materiales** | KB tiene propiedades de materiales comunes (ABS, PP, PC, PA, etc.) | 🔴 CRÍTICO |
| 4.3 | **Capacidades reales de planta** | Sistema conoce specs de prensas, equipos, limitaciones actuales | 🔴 CRÍTICO |
| 4.4 | **Referencias en reportes** | Cada hallazgo cita fuente (libro, norma, datasheet, capacidad) | 🟡 ALTA |
| 4.5 | **Actualización de KB** | Proceso documentado para agregar nuevos manuales/datasheets | 🟢 MEDIA |

**Test Case REQ-4:**
```
Expected KB Contents:
  ✓ ≥3 injection molding reference books indexed
  ✓ ≥10 material datasheets (common plastics)
  ✓ Equipment capabilities documented (press specs, tonnage, shot size)
  ✓ Citations in report: "Per Injection Molding Handbook p.127..."
```

---

### REQ-5: CAD/Prints Primero, Simulación Opcional

| # | Requisito | Criterio de Verificación | Prioridad |
|---|-----------|--------------------------|-----------|
| 5.1 | **Leer prints (PDF)** | Sistema procesa technical drawings en PDF | 🔴 CRÍTICO |
| 5.2 | **Leer CAD (STEP/IGES)** | Sistema acepta archivos 3D CAD nativos | 🟡 ALTA |
| 5.3 | **Aceptar PDFs de simulación** | Sistema puede ingerir reportes de Moldflow/Moldex3D | 🟢 MEDIA |
| 5.4 | **Aceptar CSVs de simulación** | Sistema procesa datos tabulares de simulación | 🟢 MEDIA |
| 5.5 | **Enriquecer con simulación** | Análisis mejora si se provee data de simulación | 🟢 MEDIA |
| 5.6 | **No bloquear sin simulación** | MVP funciona sin integración directa con software de simulación | 🔴 CRÍTICO |

**Test Case REQ-5:**
```
Scenario 1 (Print only):
  Input: PDF technical drawing
  Expected: Full analysis based on VLM + KB

Scenario 2 (Print + Simulation):
  Input: PDF + Moldflow report PDF
  Expected: Analysis enriched with simulation data (warp, flow, etc.)
```

---

### REQ-6: UX "Drag-and-Drop"

| # | Requisito | Criterio de Verificación | Prioridad |
|---|-----------|--------------------------|-----------|
| 6.1 | **Subir archivo** | UI permite drag-drop o file picker para PDFs/CAD | 🔴 CRÍTICO |
| 6.2 | **Proceso automático** | Análisis se ejecuta sin configuración manual | 🔴 CRÍTICO |
| 6.3 | **Obtener informe** | Usuario descarga/visualiza reporte al finalizar | 🔴 CRÍTICO |
| 6.4 | **Indicador de progreso** | UI muestra estado (uploading/processing/analyzing) | 🟡 ALTA |
| 6.5 | **Sin campos complejos** | No requiere llenar formularios extensos antes de analizar | 🟡 ALTA |

**Test Case REQ-6:**
```
User Flow:
  1. User drags PDF to dropzone → File uploads
  2. System auto-starts analysis → Shows "Analyzing..." with progress
  3. Analysis completes → Shows "Download Report" button
  4. User clicks → Gets Exception Report PDF/HTML

Max Clicks: ≤3 (upload, wait, download)
```

---

### REQ-7: Validación Ciega

| # | Requisito | Criterio de Verificación | Prioridad |
|---|-----------|--------------------------|-----------|
| 7.1 | **Dataset de referencia** | Conjunto de ≥5 casos con informes humanos históricos | 🟡 ALTA |
| 7.2 | **Comparación AI vs Humano** | Tabla lado-a-lado mostrando hallazgos AI vs Expert | 🟡 ALTA |
| 7.3 | **Precision por tópico** | TP/(TP+FP) por categoría (draft, thickness, etc.) | 🟡 ALTA |
| 7.4 | **Recall por tópico** | TP/(TP+FN) - ¿captó todo lo que el experto encontró? | 🔴 CRÍTICO |
| 7.5 | **Métricas agregadas** | Precision/Recall global ≥ 85% | 🟡 ALTA |

**Test Case REQ-7:**
```
Evaluation Protocol:
  1. Run AI on 5 historical parts (blind to human reports)
  2. Extract findings: categorize by type (draft, tolerance, etc.)
  3. Compare vs human expert findings
  4. Calculate:
     - Precision = Correct AI findings / All AI findings
     - Recall = Correct AI findings / All expert findings

Target: Precision ≥85%, Recall ≥85% (avg across categories)
```

---

### REQ-8: Entregables para Cliente

| # | Requisito | Criterio de Verificación | Prioridad |
|---|-----------|--------------------------|-----------|
| 8.1 | **One-pager teaser** | Documento de 1 página con highlights para cotización | 🔴 CRÍTICO |
| 8.2 | **Contenido teaser** | Enfatiza valor sin revelar detalles técnicos completos | 🟡 ALTA |
| 8.3 | **Exception/Technical Assessment completo** | Reporte detallado con todas las excepciones encontradas | 🔴 CRÍTICO |
| 8.4 | **Secciones estructuradas** | Reporte organizado por categorías (draft, tolerances, etc.) | 🔴 CRÍTICO |
| 8.5 | **Evidencia por hallazgo** | Cada excepción muestra imagen/referencia del drawing | 🟡 ALTA |
| 8.6 | **Referencias a normas** | Citas a libros, datasheets, capacidades de planta | 🟡 ALTA |
| 8.7 | **Caja de firma (sign-off)** | Espacio para cliente firmar aceptación de desviaciones | 🔴 CRÍTICO |
| 8.8 | **Formato profesional** | PDF con logo, formato corporativo, legible | 🟡 ALTA |

**Test Case REQ-8:**
```
One-Pager Structure:
  ✓ Header: Part name, date, project
  ✓ Summary: "3 critical exceptions, 5 recommendations"
  ✓ Highlights: Bullet points of main issues
  ✓ Next steps: "Review full report for details"

Technical Assessment Structure:
  ✓ Executive Summary (1 page)
  ✓ Part Overview (geometry, material, specs)
  ✓ Exceptions by Category (draft, tolerances, etc.)
    - Each with: Description, Evidence (image), Impact, Condition to proceed
  ✓ References (standards, datasheets cited)
  ✓ Sign-Off Box: "Acknowledged by: ___ Date: ___"
```

---

## 📊 Scoring System

### Coverage Index (0-100)
```
Score = (Categories Evaluated / Total Categories) × 100
Target: ≥95% (12/13 categories)
```

### Precision & Recall (0-100)
```
Precision = True Positives / (True Positives + False Positives) × 100
Recall = True Positives / (True Positives + False Negatives) × 100
Target: Both ≥85%
```

### Alignment Score (0-100)
```
Weighted Average:
  - Exactitud (Precision): 40%
  - Exhaustividad (Recall): 40%
  - Formato Entregables: 10%
  - Robustez de Ingesta: 10%

Target: ≥85 (equivale a "B+" grade)
```

---

## ✅ Checklist Rápida (Para Auditoría)

### Funcionalidad Core
- [ ] Sistema identifica excepciones (no propone rediseño)
- [ ] Cubre 13 categorías técnicas (draft, thickness, GD&T, etc.)
- [ ] Funciona con specs exhaustivas Y mínimas
- [ ] Conocimiento basado en libros/normas de moldeo
- [ ] Ingiere PDFs (prints/simulación) y CAD (opcional MVP)
- [ ] UX drag-and-drop funcional
- [ ] Genera dos entregables: teaser + assessment completo
- [ ] Assessment tiene sign-off box

### Calidad
- [ ] Precision ≥85% en evaluación ciega
- [ ] Recall ≥85% en evaluación ciega
- [ ] Coverage Index ≥95% (12/13 categorías)
- [ ] Alignment Score ≥85

### Entregables
- [ ] `/templates/one_pager.md` (estructura definida)
- [ ] `/templates/exception_report.md` (con secciones + sign-off)
- [ ] `/eval/harness/` (datasets, scripts, métricas)
- [ ] `/docs/checklist_alineacion.md` (este documento)
- [ ] `/reports/alignment_report.pdf` (resumen ejecutivo)

---

**Próximo Paso:** Auditar sistema actual contra esta checklist → Identificar brechas → Priorizar fixes.

*Generado: 2025-11-05*
*Auditor: Principal Engineer (Autonomous)*

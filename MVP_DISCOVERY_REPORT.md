# 🔍 MVP Discovery Report - SME AI Vertex

**Fecha:** 2025-11-05
**Ingeniero:** Principal Engineer (Autónomo)
**Objetivo:** Auditoría funcional MVP - End-to-end functionality first

---

## 📋 Executive Summary

Sistema de análisis de viabilidad de moldeo por inyección con IA, utilizando:
- **Frontend:** Next.js 16 + React 19 + TypeScript + Tailwind CSS
- **Backend:** FastAPI (Python 3.11) + Google Cloud Platform (Vertex AI)
- **Estado:** Código base completo, pero **NO funcional** (dependencias no instaladas, API layer faltante)

### 🚨 Blockers Críticos Identificados

1. **[BLOCKER]** Frontend: Capa de integración API faltante (`@/lib/api.ts`)
2. **[BLOCKER]** Backend: Dependencias Python no instaladas
3. **[BLOCKER]** Frontend: Dependencias Node no instaladas
4. **[BLOCKER]** Configuración: `.env` no existe (GCP credentials requeridas)

---

## 🏗️ Architecture Map

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  Next.js 16 (App Router) + React 19 + TypeScript           │
├─────────────────────────────────────────────────────────────┤
│  Pages:                                                      │
│  • /                  → Unified Chat (app/page.tsx)        │
│  • /analyze           → Drawing Upload (app/analyze/)      │
│  • /results           → Analysis List (app/results/)       │
│  • /knowledge-base    → KB Management (app/knowledge-base/)│
│                                                              │
│  ❌ MISSING: /lib/api.ts (API integration layer)           │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
│         FastAPI + Python 3.11 + GCP Services                │
├─────────────────────────────────────────────────────────────┤
│  API Routes:                                                 │
│  • /knowledgebase     → KB upload/list/delete/stats        │
│  • /analysis          → Drawing upload/list/get/report     │
│  • /analysis/upload   → Unified chat with PDF analysis     │
│  • /search            → Vector search                       │
│  • /metrics           → System metrics                      │
│  • /health            → Health check                        │
│                                                              │
│  Services:                                                   │
│  • DrawingProcessor   → PDF→PNG, embeddings                │
│  • DrawingAnalyzer    → Gemini 2.5 VLM analysis            │
│  • ExceptionEngine    → Best practices validation          │
│  • ReportGenerator    → Executive/Detailed reports         │
│  • ChatService        → RAG-grounded chat                  │
│  • VectorSearch       → Vertex AI Vector Search            │
│  • KnowledgeBase      → RAG Engine integration             │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD PLATFORM                     │
├─────────────────────────────────────────────────────────────┤
│  • Vertex AI          → Gemini 2.5 Flash/Pro, Embeddings   │
│  • RAG Engine         → Knowledge base managed              │
│  • Vector Search      → TreeAH indices, sub-10ms latency    │
│  • Document AI        → OCR fallback (layout parser)        │
│  • Cloud Storage      → Buckets (manuals, drawings, reports)│
│  • Context Caching    → 75% cost reduction                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Critical User Journeys (5 MVP Flows)

### Journey 1: 📄 Unified Chat with PDF Analysis
**Path:** `/` (main page)
**User Flow:**
1. User lands on chat interface
2. User drags/drops PDF or clicks attach button
3. User types message or uses default "Analiza este plano"
4. Frontend calls `POST /analysis/upload` with file + message
5. Backend:
   - Processes PDF → PNG (DrawingProcessor)
   - Analyzes with Gemini VLM (DrawingAnalyzer)
   - Validates with ExceptionEngine
   - Returns chat response with sources
6. User sees AI response with analysis embedded in chat

**Acceptance Criteria:**
- ✅ PDF upload works (drag-drop + file picker)
- ✅ Loading states shown during upload/processing/analysis
- ✅ AI response appears in chat with markdown formatting
- ✅ Sources cited (if RAG grounding enabled)
- ✅ Error handling for invalid files, large files, API errors

**Status:** ⚠️ **BLOCKED** - API call presente en código pero no testeada

---

### Journey 2: 📊 Dedicated Drawing Analysis
**Path:** `/analyze` → `/results`
**User Flow:**
1. User navigates to `/analyze`
2. User selects PDF file
3. User enters project name (optional)
4. User selects quality mode (Flash/Pro)
5. User clicks "Start Analysis"
6. Frontend calls `POST /analysis/upload` via `analysisAPI.uploadDrawing()`
7. Backend processes (same pipeline as Journey 1)
8. Frontend shows success + analysis_id
9. User clicks "View Results" → redirects to `/results?id={analysis_id}`

**Acceptance Criteria:**
- ✅ File picker accepts only PDFs
- ✅ Quality mode selector works
- ✅ Upload progress indication
- ✅ Success screen with analysis ID
- ✅ Redirect to results page works

**Status:** 🚨 **BLOCKED** - `@/lib/api` no existe, página no funciona

---

### Journey 3: 📋 View Analysis Results
**Path:** `/results`
**User Flow:**
1. User navigates to `/results` (or redirected from `/analyze`)
2. Frontend calls `GET /analysis/documents` via `analysisAPI.listAnalyses()`
3. Backend returns list of all analyses from SQLite DB
4. Frontend displays table with:
   - Drawing filename
   - Project name
   - Status (completed/processing/failed)
   - Quality mode
   - Exception count
   - Created date/time
5. User can click on analysis to view details (future: `/results/{id}`)

**Acceptance Criteria:**
- ✅ Analyses list loads
- ✅ Status badges colored correctly (green/yellow/red)
- ✅ Empty state shown if no analyses
- ✅ Loading spinner during fetch
- ✅ Filters work (if implemented)

**Status:** 🚨 **BLOCKED** - `@/lib/api` no existe, página no funciona

---

### Journey 4: 📚 Upload Knowledge Base Document
**Path:** `/knowledge-base`
**User Flow:**
1. User navigates to `/knowledge-base`
2. User drags/drops PDF or clicks upload area
3. User selects document type (manual/specification/quality_manual)
4. User clicks "Upload Document"
5. Frontend calls `POST /knowledgebase/upload` via `knowledgeBaseAPI.uploadDocument()`
6. Backend:
   - Uploads to GCS bucket
   - Indexes with RAG Engine
   - Stores metadata in SQLite
7. Frontend shows success message
8. Document appears in list below

**Acceptance Criteria:**
- ✅ Drag-drop and file picker work
- ✅ Document type selector functional
- ✅ Upload progress indication
- ✅ Success/error notifications
- ✅ Document list refreshes after upload
- ✅ Delete button works
- ✅ Stats update (total docs, pages indexed, by type)

**Status:** 🚨 **BLOCKED** - `@/lib/api` no existe, página no funciona

---

### Journey 5: 💬 Chat About Analysis (RAG-Grounded)
**Path:** `/` (main chat, after PDF analyzed)
**User Flow:**
1. User has already uploaded PDF (Journey 1)
2. User types follow-up question (e.g., "Why is this dimension critical?")
3. Frontend calls `POST /analysis/` with message + chat_history
4. Backend:
   - Retrieves analysis context from DB
   - Queries RAG Engine for relevant KB chunks
   - Sends to Gemini with context + RAG results
   - Returns grounded response with sources
5. User sees AI response with citations

**Acceptance Criteria:**
- ✅ Chat history maintained in session
- ✅ Follow-up questions work with context
- ✅ Sources cited from KB (if RAG enabled)
- ✅ Streaming response (if enabled)
- ✅ Error handling for API failures

**Status:** ⚠️ **BLOCKED** - API call presente, pero sin RAG configurado (RAG_DATA_STORE_ID vacío)

---

## 🐛 Issues & Bugs Detected

### 🔴 Critical (Blocks ALL journeys)

| ID | Issue | Impact | Fix Required |
|----|-------|--------|--------------|
| C1 | Frontend `@/lib/api.ts` missing | Journeys 2, 3, 4 don't work | Create API layer with type-safe fetch wrappers |
| C2 | Backend dependencies not installed | Backend won't start | `pip install -r requirements.txt` |
| C3 | Frontend dependencies not installed | Frontend won't build/run | `cd frontend && npm install` |
| C4 | `.env` file missing | Backend can't load config | Create minimal `.env` for local dev (mock GCP) |

### 🟡 High (Degrades functionality)

| ID | Issue | Impact | Fix Required |
|----|-------|--------|--------------|
| H1 | RAG_DATA_STORE_ID not configured | Journey 5 chat not grounded | Setup RAG Engine or use fallback |
| H2 | DOCUMENT_AI_PROCESSOR_ID not set | OCR fallback disabled | Setup Document AI or mark optional |
| H3 | No error boundaries in frontend | Crashes show blank screen | Add React error boundaries |
| H4 | API base URL hardcoded | Won't work in production | Use env var `NEXT_PUBLIC_API_URL` |

### 🟢 Medium (UX issues)

| ID | Issue | Impact | Fix Required |
|----|-------|--------|--------------|
| M1 | No loading skeletons | Poor perceived performance | Add skeleton loaders |
| M2 | No toast notifications | Errors shown in console only | Add toast library |
| M3 | No pagination on results | Slow with many analyses | Add pagination/infinite scroll |
| M4 | Dark mode not persisted | Resets on refresh | Use localStorage |

---

## 🔧 Technical Decisions (Autonomous)

### Testing Stack
- **E2E:** Playwright (TypeScript, fast, reliable, cross-browser)
- **API Contract:** pytest + httpx (Python native, fast)
- **Smoke:** Custom shell script (zero dependencies, CI-friendly)

**Rationale:** Playwright best-in-class for modern web apps; pytest standard for Python APIs; shell script for max portability.

### API Integration Layer Design
```typescript
// /home/user/sme-ai-vertex/frontend/lib/api.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

// Type-safe fetch wrapper
async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Exported APIs
export const analysisAPI = {
  uploadDrawing: async (file, projectName?, qualityMode?) => { ... },
  listAnalyses: async () => { ... },
  getAnalysis: async (id) => { ... },
};

export const knowledgeBaseAPI = {
  uploadDocument: async (file, documentType) => { ... },
  listDocuments: async () => { ... },
  deleteDocument: async (id) => { ... },
  getStats: async () => { ... },
};

export const chatAPI = {
  sendMessage: async (message, history) => { ... },
  uploadWithChat: async (file, message, history) => { ... },
};
```

**Rationale:** Single source of truth for API calls; type-safe; centralized error handling; easy to mock for tests.

### Local Development Strategy (No GCP)
For MVP testing without GCP credentials:
- **Mock mode:** Backend returns fake data if `ENVIRONMENT=mock`
- **Fixtures:** Pre-generated sample PDFs, analyses, KB documents
- **Stubs:** Mock Vertex AI calls with deterministic responses

**Rationale:** Enables full E2E testing without GCP costs/setup; faster iteration; deterministic tests.

### Performance Budgets (MVP)
- **Frontend initial load:** <3s (4G)
- **API response time:** <2s (analysis), <500ms (list/get)
- **VLM analysis:** <30s (Flash), <90s (Pro)
- **Bundle size:** <500KB (JS), <200KB (CSS)

**Rationale:** User doesn't wait >3s; analysis can be async; bundle affects mobile users.

---

## 📊 Current State Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Backend Code | ✅ Complete | All services implemented |
| Frontend Code | ⚠️ 80% Complete | Missing API layer |
| Dependencies | ❌ Not Installed | Backend + Frontend |
| Configuration | ❌ Missing | No `.env` |
| Tests | ❌ None | Need smoke, E2E, contract |
| Documentation | ✅ Excellent | README, guides complete |
| Can Run? | ❌ **NO** | Multiple blockers |

---

## 🎯 Next Steps (Autonomous Execution Plan)

### Phase 1: Environment Setup (ETA: 15 min)
1. ✅ Create minimal `.env` for local dev (mock mode)
2. ✅ Install backend dependencies (`pip install -r requirements.txt`)
3. ✅ Install frontend dependencies (`cd frontend && npm install`)
4. ✅ Verify backend starts (`python main.py`)
5. ✅ Verify frontend builds (`cd frontend && npm run dev`)

### Phase 2: Critical Fixes (ETA: 30 min)
1. ✅ Create `/frontend/lib/api.ts` with all endpoints
2. ✅ Add error boundaries to frontend layout
3. ✅ Fix hardcoded API URL (use env var)
4. ✅ Add basic loading states (spinners)

### Phase 3: Test Harness (ETA: 45 min)
1. ✅ Create smoke test script (`scripts/smoke_test.sh`)
2. ✅ Setup Playwright + write 5 E2E tests (1 per journey)
3. ✅ Setup pytest + write 10 API contract tests
4. ✅ Create data fixtures (sample PDFs, responses)

### Phase 4: Run & Triage (ETA: 20 min)
1. ✅ Run smoke test → document failures
2. ✅ Run E2E tests → document failures
3. ✅ Run contract tests → document failures
4. ✅ Create prioritized bug list (triage)

### Phase 5: Fix & Verify (ETA: 60 min)
1. ✅ Fix all blocking bugs (C1-C4)
2. ✅ Re-run smoke test → should pass
3. ✅ Re-run E2E tests → measure pass rate
4. ✅ Fix remaining high-priority bugs (H1-H4)
5. ✅ Re-run all tests → target 100% pass

### Phase 6: Performance & Docs (ETA: 30 min)
1. ✅ Measure performance budgets (Lighthouse)
2. ✅ Add basic optimizations (lazy loading, etc.)
3. ✅ Create `README_MVP.md` with all commands
4. ✅ Package regression suite (CI-ready)

### Phase 7: Deliverables (ETA: 20 min)
1. ✅ Generate journey status table (Markdown)
2. ✅ Create before/after metrics (JSON + table)
3. ✅ Update architecture map (diagram + decisions)
4. ✅ Commit & push to feature branch

---

## 📈 Success Criteria

**Definition of Done:**
- [ ] All 5 critical journeys work end-to-end
- [ ] Smoke test passes (all services healthy)
- [ ] E2E tests: 100% pass rate (5/5 journeys)
- [ ] API contract tests: 100% pass rate
- [ ] Performance budgets met (measured with Lighthouse)
- [ ] Single-command setup: `./scripts/setup_mvp.sh`
- [ ] Single-command test: `./scripts/test_mvp.sh`
- [ ] README_MVP.md complete with:
  - Setup instructions
  - Test commands
  - Architecture diagram
  - Journey status table
  - Known limitations

---

**Total Estimated Time:** ~3.5 hours
**Priority:** Fix blockers → Add tests → Fix bugs → Optimize → Document

---

*Report Generated: 2025-11-05*
*Engineer: Principal Engineer (Autonomous)*
*Next Action: Phase 1 - Environment Setup*

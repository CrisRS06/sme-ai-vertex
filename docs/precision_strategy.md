# 🎯 Technical Drawing Precision Strategy

**Date:** 2025-11-05
**Priority:** 🔴 CRITICAL (Prerequisite for Phase 2)
**Goal:** Ensure accurate extraction of dimensions, tolerances, and technical specs from drawings

---

## 🏗️ Two-Step Reading Architecture (Google Cloud Stack)

```
📄 Technical Drawing (PDF)
   │
   ↓
┌──────────────────────────────────────────────┐
│ STEP 1: Gemini VLM (Visual Understanding)   │
├──────────────────────────────────────────────┤
│ • Vertex AI - Gemini 2.5 Flash/Pro          │
│ • Visual reasoning like an engineer          │
│ • Context: part geometry, relationships       │
│ • Extracts: dimensions, GD&T, material       │
│ • Output: JSON with confidence scores        │
└──────────────────────────────────────────────┘
   │
   ↓ confidence < 0.7 on any dimension?
   ↓
┌──────────────────────────────────────────────┐
│ STEP 2: Document AI (Precision OCR)         │
├──────────────────────────────────────────────┤
│ • Document AI Form Parser                    │
│ • Pixel-perfect text extraction               │
│ • Regex patterns for dimensions              │
│ • Replaces low-confidence values             │
│ • Output: Merged high-confidence results     │
└──────────────────────────────────────────────┘
   │
   ↓
📊 DrawingAnalysis (Final Result)
```

**Status:** ✅ Code implemented, ⏳ Configuration pending

---

## ✅ What's Already Implemented

### 1. Gemini VLM Integration (`DrawingAnalyzer`)
- ✅ Gemini 2.5 Flash/Pro support
- ✅ Structured JSON output via `response_schema`
- ✅ Context caching (75% cost reduction)
- ✅ Timeout handling (180s)
- ✅ Confidence scoring per dimension
- ✅ **NEW:** Expanded prompt with 13 technical categories

**Location:** `src/services/drawing_analyzer.py` (lines 76-197)

### 2. Document AI OCR Fallback (`DocumentAIService`)
- ✅ Automatic trigger when confidence < 0.7
- ✅ Regex patterns for dimensions/tolerances
- ✅ Bounding box extraction
- ✅ Smart merge with VLM results
- ✅ Metrics tracking (fields recovered)

**Location:** `src/services/document_ai_service.py` (345 lines)

### 3. Test Script (`test_drawing_precision.py`)
- ✅ End-to-end analysis test
- ✅ Detailed output of all extracted fields
- ✅ Confidence analysis
- ✅ Exception engine validation
- ✅ JSON export

**Location:** `scripts/test_drawing_precision.py` (just created)

---

## ⏳ What Needs Configuration

### 🔴 STEP 1: Setup Document AI Processor (Required)

**Current Status:** `DOCUMENT_AI_PROCESSOR_ID=None` → OCR disabled

**Action Required:**

```bash
# 1. Run setup script
./scripts/setup_document_ai.sh YOUR_PROJECT_ID

# Script will:
# - Enable Document AI API
# - Create Form Parser processor (optimized for technical drawings)
# - Output processor ID

# 2. Add to .env file
DOCUMENT_AI_PROCESSOR_ID=a1b2c3d4e5f6g7h8  # Replace with actual ID
ENABLE_DOCUMENT_AI_FALLBACK=true
OCR_CONFIDENCE_THRESHOLD=0.7
```

**Estimated Time:** 5 minutes
**Cost:** ~$0.0015 per page when triggered
**Typical Usage:** 10-20% of pages need OCR fallback

---

## 🧪 Testing Plan

### Phase 1: Baseline Test (Quick - 15 min)

**Goal:** Verify Gemini VLM can read a simple drawing

```bash
# 1. Get a sample drawing
# - Use any technical drawing PDF (CAD export, scanned print)
# - Simpler is better for first test
# - Example: https://www.engineeringtoolbox.com/docs/sample-drawing.pdf

# 2. Run test script
python scripts/test_drawing_precision.py path/to/sample_drawing.pdf

# 3. Review output:
#    - Are dimensions extracted?
#    - Are values correct? (compare to PDF)
#    - What's the average confidence?
#    - Which fields are missing?
```

**Expected Output:**
```
📏 Dimensions Extracted: 15-30 (for typical part)
📊 Confidence Metrics:
   Average:     0.85-0.95 (good)
   Low (<0.7):  2-5 dimensions (normal, OCR will fix)
   High (≥0.7): 10-25 dimensions

📋 Part Information: Correctly identified
🎯 GD&T: 3-8 specs (if present in drawing)
```

### Phase 2: Precision Validation (Thorough - 1 hour)

**Goal:** Measure extraction accuracy on 3-5 drawings

**Process:**

1. **Select test drawings:**
   - 1 simple part (3-5 dimensions)
   - 1 medium complexity (10-20 dimensions)
   - 1 complex part (30+ dimensions, GD&T)

2. **Create ground truth:**
   - Manually list all dimensions from PDF
   - Note tolerances, GD&T specs, material
   - Save in `tests/ground_truth/part_xyz.json`

3. **Run analysis:**
   ```bash
   for drawing in samples/*.pdf; do
       python scripts/test_drawing_precision.py "$drawing"
   done
   ```

4. **Compare results:**
   - Dimensions: How many extracted vs ground truth?
   - Values: Are numbers correct? (±0.001 tolerance)
   - Tolerances: Correctly parsed?
   - Material: Identified correctly?

5. **Calculate metrics:**
   - **Precision:** Of extracted dims, how many are correct?
   - **Recall:** Of all dims in drawing, how many extracted?
   - **Target:** Precision >95%, Recall >90%

### Phase 3: Prompt Optimization (If needed - 2-4 hours)

**If Phase 2 results are <90% precision/recall:**

**Common issues and fixes:**

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| Missing dimensions | VLM didn't see them | Add emphasis in prompt: "Extract EVERY dimension" |
| Wrong values | OCR misread number | Lower `OCR_CONFIDENCE_THRESHOLD` to 0.6 |
| No tolerances | VLM skipped them | Add examples in prompt |
| Missing GD&T | Symbol not recognized | Add GD&T symbol reference table |
| Wrong material | Abbreviation not understood | Add material alias list |

**Prompt tuning locations:**
- `src/services/drawing_analyzer.py` line 86: `_create_analysis_prompt()`
- Test iteratively with one drawing
- Commit changes with precision metrics in message

---

## 📊 Success Criteria

### Minimum Acceptable Performance (MVP)
- ✅ **Precision:** ≥85% (of extracted values are correct)
- ✅ **Recall:** ≥80% (of all values in drawing are extracted)
- ✅ **Confidence:** Average ≥0.75
- ✅ **Critical Fields:** Part ID, Material, Key dimensions 100%

### Target Performance (Production)
- 🎯 **Precision:** ≥95%
- 🎯 **Recall:** ≥90%
- 🎯 **Confidence:** Average ≥0.85
- 🎯 **OCR Fallback:** Successfully recovers <0.7 confidence fields

---

## 🚨 Known Limitations (Google Cloud Stack)

### Gemini VLM
- **Strength:** Excellent visual understanding, context reasoning
- **Weakness:** Microtext (<10pt) can have low confidence
- **Solution:** Document AI OCR fallback

### Document AI Form Parser
- **Strength:** Industry-leading OCR accuracy (~99%)
- **Weakness:** Requires well-structured layout
- **Solution:** Combine with VLM for context

### Combined Approach
- **Result:** Best of both worlds
- **VLM:** Sees the big picture (geometry, relationships)
- **OCR:** Captures precise text (dimensions, tolerances)

---

## 🔧 Debugging Tools

### 1. Verbose Logging
```python
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# Output shows:
# - Gemini prompt sent
# - Response received (with truncation warnings)
# - OCR trigger events
# - Merge decisions
```

### 2. Confidence Analysis
```python
# In test script output:
📊 Confidence Metrics:
   Average:     0.876
   Low (<0.7):  3 dimensions  # These trigger OCR
   High (≥0.7): 17 dimensions
```

### 3. JSON Inspection
```bash
# Full analysis saved to JSON
cat samples/part_123_analysis.json | jq '.dimensions[] | select(.confidence < 0.7)'

# Shows low-confidence fields that need OCR
```

### 4. Visual Bounding Boxes (Future Enhancement)
```python
# TODO: Overlay bounding boxes on PDF
# - Green: High confidence
# - Yellow: Medium confidence
# - Red: Low confidence (OCR triggered)
```

---

## 📈 Improvement Roadmap

### Immediate (This Session)
1. ✅ Create test script → **DONE**
2. ⏳ Configure Document AI processor
3. ⏳ Test with 1-2 sample drawings
4. ⏳ Document baseline precision metrics

### Short-term (Next Session)
1. Collect 5-10 historical drawings with known good reports
2. Create ground truth dataset
3. Run evaluation harness
4. Calculate precision/recall metrics
5. Tune prompts if needed

### Medium-term (Phase 2)
1. Add visual bounding box overlay tool
2. Implement dimension sanity checks (e.g., wall thickness 0.1mm flag)
3. Add unit conversion validation
4. Create precision dashboard

### Long-term (Production)
1. A/B test Gemini Flash vs Pro (cost vs accuracy)
2. Fine-tune confidence thresholds per field type
3. Add human-in-the-loop for critical dimensions
4. Build continuous evaluation pipeline

---

## 💡 Key Insights

### Why Two-Step Approach Works

**VLM Alone (Problem):**
- Great at visual understanding
- Can miss microtext (tiny dimensions)
- Confidence varies by drawing quality

**OCR Alone (Problem):**
- Accurate text extraction
- No context (which number is what?)
- Struggles with handwritten notes

**VLM + OCR (Solution):**
- VLM identifies **what** each field is (context)
- OCR ensures **values** are precise (accuracy)
- Confidence-based triggering (cost-effective)

### Cost Optimization

**Gemini VLM:**
- Flash: $0.075 per 1M input tokens (~$0.01 per drawing)
- Pro: $0.30 per 1M tokens (~$0.04 per drawing)
- Context caching: 75% discount on repeated content

**Document AI OCR:**
- $1.50 per 1,000 pages
- Only triggered for low-confidence fields (10-20%)
- Effective cost: ~$0.0003 per drawing

**Total Cost per Drawing:** ~$0.01 - $0.04 (very affordable)

---

## 📋 Action Checklist

### For User (Required)
- [ ] Run `./scripts/setup_document_ai.sh YOUR_PROJECT_ID`
- [ ] Add `DOCUMENT_AI_PROCESSOR_ID` to `.env`
- [ ] Provide 1-2 sample drawings for testing
- [ ] Verify GCP credentials are configured
- [ ] Run test script: `python scripts/test_drawing_precision.py sample.pdf`

### For Development (Next Steps)
- [ ] Review test output and identify gaps
- [ ] Tune Gemini prompt if precision <90%
- [ ] Create ground truth dataset (5-10 drawings)
- [ ] Implement evaluation harness
- [ ] Document baseline metrics

---

## 📚 References

**Google Cloud Docs:**
- [Vertex AI Gemini API](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [Document AI Form Parser](https://cloud.google.com/document-ai/docs/processors-list#processor_form-parser)
- [Vertex AI Context Caching](https://cloud.google.com/vertex-ai/docs/generative-ai/context-cache/context-cache-overview)

**Code Locations:**
- VLM: `src/services/drawing_analyzer.py`
- OCR: `src/services/document_ai_service.py`
- Test: `scripts/test_drawing_precision.py`
- Setup: `scripts/setup_document_ai.sh`

---

**Status:** 📝 Documentation complete, awaiting testing with real drawings
**Next:** Configure Document AI → Test with sample → Measure precision → Optimize if needed


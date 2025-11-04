# Guía de Optimización de Costos

**Alineada con la Guía Técnica Vertex AI RAG Multimodal - Noviembre 2025**

Esta guía proporciona estrategias específicas para optimizar costos del sistema SME AI Vertex según las mejores prácticas de Google Cloud.

## Tabla de Contenidos

- [Resumen de Costos](#resumen-de-costos)
- [Optimización de Embeddings](#optimización-de-embeddings)
- [Optimización de Modelos](#optimización-de-modelos)
- [Optimización de Vector Search](#optimización-de-vector-search)
- [Optimización de Retrieval](#optimización-de-retrieval)
- [Estimador de Costos](#estimador-de-costos)

---

## Resumen de Costos

Los costos de RAG multimodal se distribuyen en cuatro componentes principales:

### 1. Embeddings
- **text-embedding-005**: $0.0001 por 1,000 caracteres
- **multimodalembedding@001 (imágenes)**: $0.0001 por imagen
- **Ejemplo**: 1M documentos × 1,000 caracteres = **$100**

### 2. Vector Search (Vertex AI)

| Embeddings | Dimensiones | QPS | Tipo máquina | Nodos | Costo/mes |
|------------|-------------|-----|--------------|-------|-----------|
| 2M | 128 | 100 | e2-standard-2 | 1 | $68 |
| 20M | 256 | 1,000 | e2-standard-16 | 1 | $547 |
| 100M | 256 | 500 | e2-highmem-16 | 2 | $1,477 |
| 1B | 100 | 500 | e2-highmem-16 | 8 | $5,910 |

**Adicionales:**
- Construcción/actualización: **$3.00 por GiB** procesado
- Actualizaciones streaming: **$0.45 por GiB** ingerido

### 3. Modelos Gemini (Vertex AI)

#### Gemini 2.5 Flash (Recomendado para RAG)
- Input: **$0.15/1M tokens** (≤200K contexto)
- Input: **$0.30/1M tokens** (>200K contexto)
- Output: **$0.60/1M tokens**

#### Gemini 2.0 Flash (Más económico)
- Input: **$0.15/1M tokens**
- Output: **$0.60/1M tokens**

#### Gemini 2.5 Pro (Casos complejos)
- Input: **$1.25/1M tokens** (≤200K contexto)
- Input: **$2.50/1M tokens** (>200K contexto)
- Output: **$10-15/1M tokens**

### 4. Document AI (OCR)
- Layout Parser: **~$1.50 por 1,000 páginas** (primeras 500 páginas incluidas)

---

## Optimización de Embeddings

### 1. Optimizar Tamaño de Chunks

**Problema**: Chunks grandes = más tokens = mayor costo

**Solución**:
```python
# ❌ MAL: Chunks muy grandes
chunking_config = rag.ChunkingConfig(
    chunk_size=2048,  # Muy grande
    chunk_overlap=500
)

# ✅ BIEN: Chunks óptimos
chunking_config = rag.ChunkingConfig(
    chunk_size=512,   # Óptimo para balance calidad/costo
    chunk_overlap=100  # Suficiente para contexto
)
```

**Ahorro estimado**: 50-60% en costos de embeddings

### 2. Deduplicar Documentos

**Problema**: Documentos duplicados generan embeddings redundantes

**Solución**:
```python
import hashlib

def deduplicate_documents(documents: List[str]) -> List[str]:
    """Eliminar documentos duplicados antes de generar embeddings."""
    seen_hashes = set()
    unique_docs = []

    for doc in documents:
        # Hash del contenido
        doc_hash = hashlib.sha256(doc.encode()).hexdigest()

        if doc_hash not in seen_hashes:
            seen_hashes.add(doc_hash)
            unique_docs.append(doc)

    logger.info(
        "deduplication_completed",
        original_count=len(documents),
        unique_count=len(unique_docs),
        duplicates_removed=len(documents) - len(unique_docs)
    )

    return unique_docs
```

**Ahorro estimado**: Variable, típicamente 10-30%

### 3. Usar text-embedding para Texto Puro

**Problema**: multimodalembedding es más caro que text-embedding

**Solución**:
```python
# Para contenido solo texto
embedding_model = "text-embedding-005"  # Más barato

# Solo usar multimodal para:
# - Imágenes
# - PDFs con diagramas importantes
# - Búsqueda cross-modal (texto→imagen o viceversa)
```

**Ahorro estimado**: Usar text-embedding cuando sea posible

### 4. Batch Embeddings

**Problema**: Generar embeddings uno por uno es ineficiente

**Solución**:
```python
from vertexai.language_models import TextEmbeddingModel

model = TextEmbeddingModel.from_pretrained("text-embedding-005")

# ✅ BIEN: Procesar en batches
batch_size = 100
all_embeddings = []

for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    embeddings = model.get_embeddings(batch)
    all_embeddings.extend(embeddings)
```

**Ahorro estimado**: 30-40% reducción en costos por procesamiento batch

---

## Optimización de Modelos

### 1. **Context Caching (75% reducción)**

**Más importante**: Context caching reduce costos en **75%** para contexto repetido.

**Implementación**:
```python
from src.config.gcp_clients import get_generative_model

# ✅ IMPLEMENTADO: Context caching habilitado
model = get_generative_model(
    "gemini-2.5-flash",
    cache_ttl_seconds=3600,  # 1 hora
    max_context_cache_entries=32
)
```

**Ejemplo de ahorro**:
- Sin caching: 100K tokens × $0.30 = **$0.03** por request
- Con caching: 100K tokens × $0.075 = **$0.0075** por request
- **Ahorro: 75%**

### 2. Usar Gemini 2.0/2.5 Flash por Defecto

**Problema**: Gemini Pro es 8x más caro que Flash

**Solución**:
```python
# ✅ BIEN: Flash por defecto
VERTEX_AI_MODEL_FLASH=gemini-2.5-flash  # Default
QUALITY_MODE=flash

# Solo usar Pro para:
# - Análisis extremadamente complejos
# - Razonamiento avanzado requerido
# - Contextos >200K tokens que necesitan máxima precisión
```

**Ahorro estimado**:
- Flash input: $0.15/1M tokens
- Pro input: $1.25/1M tokens
- **Ahorro: 88% usando Flash**

### 3. Optimizar Longitud de Respuestas

**Problema**: Output tokens son 4x más caros que input

**Solución**:
```python
generation_config = GenerationConfig(
    max_output_tokens=2048,  # ✅ Límite razonable
    temperature=0.1,  # Respuestas más directas
)

# ❌ MAL:
# max_output_tokens=8192  # Respuestas innecesariamente largas
```

**Ahorro estimado**: 50% en costos de output

### 4. Model Optimizer (Enrutamiento Dinámico)

**Implementar enrutamiento inteligente**:
```python
def select_optimal_model(query_complexity: str) -> str:
    """
    Seleccionar modelo óptimo basado en complejidad.

    - Simple: Gemini 2.0 Flash (más barato)
    - Moderate: Gemini 2.5 Flash (balance)
    - Complex: Gemini 2.5 Pro (máxima calidad)
    """
    if query_complexity == "simple":
        return "gemini-2.0-flash"
    elif query_complexity == "moderate":
        return "gemini-2.5-flash"
    else:
        return "gemini-2.5-pro"

# Ejemplo de uso
model_name = select_optimal_model(
    analyze_query_complexity(user_query)
)
```

**Ahorro estimado**: 30-50% promedio

---

## Optimización de Vector Search

### 1. Dimensionar Correctamente Tipos de Máquina

**Problema**: Usar máquinas muy grandes para cargas pequeñas

**Solución**:

| Embeddings | QPS requerido | Tipo máquina óptimo | Costo/mes |
|------------|---------------|---------------------|-----------|
| <10M | <200 | e2-standard-2 | $68 |
| 10-50M | 200-1,000 | e2-standard-16 | $547 |
| 50-200M | >1,000 | e2-highmem-16 | $1,477 |

**Monitorear QPS real**:
```bash
# Ver métricas de uso
gcloud monitoring time-series list \
  --filter='metric.type="aiplatform.googleapis.com/prediction/online/qps"'
```

### 2. Usar Batch Queries (30-40% reducción)

**Problema**: Queries individuales son ineficientes

**Solución**:
```python
# ❌ MAL: Queries individuales
for query in queries:
    results = endpoint.find_neighbors(query)

# ✅ BIEN: Batch queries
batch_results = endpoint.find_neighbors(
    deployed_index_id=deployed_index_id,
    queries=query_embeddings,  # Lista de queries
)
```

**Ahorro estimado**: 30-40% reducción en costos operacionales

### 3. Implementar Caché para Consultas Frecuentes

**Implementación**:
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def cached_vector_search(query_hash: str, top_k: int):
    """Cache de resultados de búsqueda para queries frecuentes."""
    return vector_search.search_similar(
        query_embedding,
        top_k=top_k
    )

# Usar hash de query como key
query_hash = hashlib.md5(query.encode()).hexdigest()
results = cached_vector_search(query_hash, top_k=10)
```

**Ahorro estimado**: 40-60% para queries repetidas

### 4. Usar Actualizaciones Streaming

**Para datos incrementales**:

- Actualizaciones batch: **$3.00/GiB**
- Actualizaciones streaming: **$0.45/GiB**
- **Ahorro: 85%**

```python
# Para updates frecuentes, usar streaming
index.upsert_datapoints(
    datapoints=new_datapoints,
    stream=True  # Usar streaming
)
```

---

## Optimización de Retrieval

### 1. Ajustar Parámetro top_k

**Problema**: Recuperar demasiados documentos

**Solución**:
```python
# ❌ MAL: top_k muy alto
retrieval_config = rag.RagRetrievalConfig(top_k=50)

# ✅ BIEN: top_k óptimo
retrieval_config = rag.RagRetrievalConfig(
    top_k=3  # 3-5 documentos típicamente suficientes
)
```

**Ejemplo**:
- top_k=50: 50 chunks × 512 tokens = 25,600 tokens input
- top_k=3: 3 chunks × 512 tokens = 1,536 tokens input
- **Ahorro: 94%**

### 2. Usar Umbrales de Distancia

**Filtrar resultados irrelevantes**:
```python
results = vector_search.search_similar(
    query_embedding,
    top_k=10,
    min_similarity=0.7  # Solo resultados con >70% similitud
)
```

**Ahorro estimado**: 20-30% al excluir chunks irrelevantes

### 3. Pre-filtrado de Metadatos

**Problema**: Buscar en todos los documentos

**Solución**:
```python
# ✅ BIEN: Filtrar antes de búsqueda vectorial
results = vector_search.search_similar(
    query_embedding,
    top_k=5,
    filter_metadata={
        "document_type": "manual",
        "year": 2024,
        "category": "molding_guidelines"
    }
)
```

**Ahorro estimado**: 40-50% al reducir espacio de búsqueda

---

## Estimador de Costos

### Ejemplo: Sistema con Carga Moderada

**Configuración**:
- 10M documentos indexados
- 10,000 consultas/día
- Análisis de 100 drawings/día

**Costos mensuales estimados**:

#### 1. Embeddings (One-time)
```
10M docs × 500 chars/doc = 5B caracteres
5B chars ÷ 1000 = 5M units
5M × $0.0001 = $500 (one-time)
```

#### 2. Vector Search
```
e2-standard-16 × 1 nodo = $547/mes
```

#### 3. Modelos (con optimizaciones)
```
# Consultas RAG
10,000 queries/día × 30 días = 300K queries/mes
Avg input: 2K tokens (con top_k=3)
Avg output: 500 tokens

Input: 300K × 2K = 600M tokens
  Con context caching (75% savings): 600M × 0.25 = 150M tokens
  Costo: 150M × $0.15 / 1M = $22.50

Output: 300K × 500 = 150M tokens
  Costo: 150M × $0.60 / 1M = $90

# Análisis de drawings
100 drawings/día × 30 = 3,000/mes
Avg: 5K tokens input, 2K output

Input: 3K × 5K = 15M tokens = $2.25
Output: 3K × 2K = 6M tokens = $3.60

Total modelos: $22.50 + $90 + $2.25 + $3.60 = $118.35
```

#### 4. Document AI (OCR fallback)
```
Asumiendo 10% de drawings necesitan OCR:
3,000 × 0.10 = 300 documentos
Avg 5 páginas/doc = 1,500 páginas
1,500 ÷ 1000 × $1.50 = $2.25
```

**TOTAL MENSUAL**: ~$668/mes

### Con Optimizaciones Adicionales

Implementando todas las optimizaciones de esta guía:

| Componente | Costo base | Optimizado | Ahorro |
|------------|------------|------------|--------|
| Vector Search | $547 | $547 | $0 (ya óptimo) |
| Modelos | $118.35 | $30 | **$88** (75% caching + Flash) |
| Document AI | $2.25 | $2.25 | $0 |
| **TOTAL** | **$668** | **$580** | **$88/mes** |

---

## Mejores Prácticas - Checklist

### Embeddings
- [ ] Usar chunk_size=512 con overlap=100
- [ ] Deduplicar documentos antes de embedding
- [ ] Usar text-embedding-005 para texto puro
- [ ] Procesar en batches

### Modelos
- [ ] Context caching habilitado (75% ahorro)
- [ ] Usar Gemini Flash por defecto
- [ ] Limitar max_output_tokens a 2048
- [ ] Implementar model router para queries complejas

### Vector Search
- [ ] Dimensionar máquinas según QPS real
- [ ] Usar batch queries
- [ ] Implementar cache para queries frecuentes
- [ ] Usar streaming updates para datos incrementales

### Retrieval
- [ ] top_k = 3-5 (no más)
- [ ] Usar umbrales de similitud (min_similarity=0.7)
- [ ] Pre-filtrar con metadatos
- [ ] Evitar búsquedas innecesarias

---

## Monitoreo de Costos

### Cloud Billing Dashboard

```bash
# Ver costos actuales
gcloud billing accounts list

# Configurar alertas de presupuesto
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="SME AI Monthly Budget" \
  --budget-amount=1000 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

### Métricas Clave a Trackear

1. **Token usage** (input/output por modelo)
2. **QPS de Vector Search** (dimensionar máquinas)
3. **Cache hit rate** (efectividad de caching)
4. **Embedding generation rate** (cuántos embeddings nuevos)

---

## Calculadora de Costos

Usar la calculadora oficial de Google Cloud:
https://cloud.google.com/products/calculator

**Servicios a incluir**:
- Vertex AI Prediction (Gemini models)
- Vertex AI Vector Search
- Cloud Storage
- Document AI

---

**Última actualización**: Noviembre 2025
**Versión**: 1.0
**Alineado con**: Guía Técnica Vertex AI RAG Multimodal Noviembre 2025

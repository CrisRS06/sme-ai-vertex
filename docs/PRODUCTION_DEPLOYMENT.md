# Checklist de Deployment a Producción

**Alineado con la Guía Técnica Vertex AI RAG Multimodal - Noviembre 2025**

Este checklist garantiza que todos los componentes críticos estén configurados antes del deployment a producción.

---

## Pre-Producción

### APIs y Servicios

- [ ] **Habilitar APIs requeridas**
  ```bash
  gcloud services enable aiplatform.googleapis.com \
    storage-api.googleapis.com \
    documentai.googleapis.com \
    discoveryengine.googleapis.com \
    cloudrun.googleapis.com \
    cloudbuild.googleapis.com \
    --project=PROJECT_ID
  ```

### IAM y Permisos

- [ ] **Crear service accounts con mínimo privilegio**
  ```bash
  # Ver docs/SECURITY.md para configuración detallada
  gcloud iam service-accounts create sme-ai-app \
    --display-name="SME AI Application" \
    --project=PROJECT_ID
  ```

- [ ] **Configurar roles IAM granulares**
  - `aiplatform.user` para Vertex AI
  - `storage.objectAdmin` para buckets específicos
  - `documentai.apiUser` para Document AI
  - `discoveryengine.admin` para RAG Engine

- [ ] **Rotar service account keys** (configurar rotación automática cada 90 días)

### VPC y Networking (Opcional pero Recomendado)

- [ ] **Configurar VPC Service Controls**
  ```bash
  # Ver docs/SECURITY.md sección VPC-SC
  ```

- [ ] **Configurar firewall rules**
  - Permitir solo tráfico HTTPS
  - Bloquear acceso directo a backends

### Cifrado

- [ ] **Crear CMEK keys**
  ```bash
  gcloud kms keyrings create sme-ai-keyring \
    --location=us-central1 \
    --project=PROJECT_ID

  gcloud kms keys create sme-ai-encryption-key \
    --location=us-central1 \
    --keyring=sme-ai-keyring \
    --purpose=encryption
  ```

- [ ] **Configurar buckets con CMEK**
  ```bash
  gsutil encryption set \
    -k projects/PROJECT_ID/locations/us-central1/keyRings/sme-ai-keyring/cryptoKeys/sme-ai-encryption-key \
    gs://PROJECT_ID-manuals
  ```

### Cloud Storage

- [ ] **Crear buckets con configuración de producción**
  ```bash
  # Manuals bucket
  gsutil mb -p PROJECT_ID -c STANDARD -l us-central1 gs://PROJECT_ID-manuals
  gsutil lifecycle set lifecycle-manuals.json gs://PROJECT_ID-manuals

  # Drawings bucket
  gsutil mb -p PROJECT_ID -c STANDARD -l us-central1 gs://PROJECT_ID-drawings
  gsutil lifecycle set lifecycle-drawings.json gs://PROJECT_ID-drawings

  # Reports bucket
  gsutil mb -p PROJECT_ID -c STANDARD -l us-central1 gs://PROJECT_ID-reports
  gsutil lifecycle set lifecycle-reports.json gs://PROJECT_ID-reports
  ```

- [ ] **Configurar lifecycle policies**
  ```json
  {
    "lifecycle": {
      "rule": [
        {
          "action": {"type": "Delete"},
          "condition": {"age": 365}
        }
      ]
    }
  }
  ```

- [ ] **Configurar CORS policies** (si aplicable)

### Environment Variables

- [ ] **Mover secrets a Secret Manager** (NO usar .env en producción)
  ```bash
  echo -n "secret-api-key" | gcloud secrets create api-key \
    --data-file=- \
    --replication-policy="automatic" \
    --project=PROJECT_ID
  ```

- [ ] **Configurar variables de entorno en Cloud Run**
  ```bash
  gcloud run services update sme-ai-vertex \
    --set-env-vars="GCP_PROJECT_ID=PROJECT_ID" \
    --set-secrets="API_KEY=api-key:latest" \
    --region=us-central1
  ```

---

## Preparación de Datos

### RAG Engine Setup

- [ ] **Crear RAG corpus**
  ```bash
  ./scripts/setup_rag_engine.sh PROJECT_ID us-central1
  ```

- [ ] **Verificar configuración de chunking**
  - chunk_size: 512 tokens
  - chunk_overlap: 100 tokens
  - Configurado en `src/services/knowledge_base.py:210`

- [ ] **Importar documentos iniciales**
  ```bash
  # Via API endpoint
  curl -X POST "https://API_URL/knowledgebase/upload" \
    -F "file=@molding_manual.pdf" \
    -F "document_type=manual"
  ```

### Vector Search Setup

- [ ] **Provisionar índice Vector Search**
  ```bash
  ./scripts/setup_vector_search.sh PROJECT_ID us-central1 sme-vector-index
  ```

- [ ] **Verificar configuración TreeAH**
  - leafNodeEmbeddingCount: 1000
  - leafNodesToSearchPercent: 10
  - Configurado en `scripts/setup_vector_search.sh:50-52`

- [ ] **Deploy índice a endpoint**
  - Machine type: e2-standard-16 (para 10-50M embeddings)
  - Ajustar según QPS esperado

- [ ] **Migrar embeddings existentes** (si aplica)
  ```bash
  python scripts/migrate_embeddings_to_vertex.py --batch-size 200
  ```

### Document AI Setup (OCR Fallback)

- [ ] **Crear Document AI processor**
  ```bash
  ./scripts/setup_document_ai_processor.sh PROJECT_ID us-central1
  ```

- [ ] **Configurar processor ID en environment**
  ```bash
  DOCUMENT_AI_PROCESSOR_ID=processor-id-here
  ```

---

## Testing

### Unit Tests

- [ ] **Ejecutar suite completa de tests**
  ```bash
  pytest tests/ -v --cov=src --cov-report=html
  ```

- [ ] **Cobertura mínima: 80%**

### Integration Tests

- [ ] **Test de pipeline completo**
  - Upload manual → Index → Search
  - Upload drawing → Analyze → Generate report
  - Chat con grounding

- [ ] **Test de RAG quality**
  ```python
  from src.services.rag_evaluation import get_rag_evaluation

  eval_service = get_rag_evaluation()
  scores = await eval_service.evaluate_response(
      query="¿Cuál es el espesor mínimo de pared?",
      response="...",
      retrieved_docs=[...]
  )

  assert scores["groundedness"] > 0.7
  assert scores["relevance"] > 0.7
  ```

### Load Testing

- [ ] **Simular carga de producción**
  ```bash
  # Usar herramienta como Locust o k6
  k6 run --vus 100 --duration 5m load_test.js
  ```

- [ ] **Verificar latencias**
  - p50 < 2s
  - p95 < 5s
  - p99 < 10s

### Evaluation Metrics

- [ ] **Evaluar calidad de retrieval**
  - Recall@5: >80%
  - MRR (Mean Reciprocal Rank): >0.7

- [ ] **Evaluar calidad de generación**
  ```python
  # Ver src/services/rag_evaluation.py
  from vertexai.evaluation import EvalTask

  metrics = ["groundedness", "relevance", "coherence", "fluency", "safety"]
  eval_task = EvalTask(dataset=test_dataset, metrics=metrics)
  results = eval_task.evaluate()
  ```

---

## Deployment

### Build y Deploy

- [ ] **Construir container image**
  ```bash
  gcloud builds submit --tag gcr.io/PROJECT_ID/sme-ai-vertex
  ```

- [ ] **Deploy a Cloud Run**
  ```bash
  gcloud run deploy sme-ai-vertex \
    --image gcr.io/PROJECT_ID/sme-ai-vertex \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 100 \
    --min-instances 1 \
    --concurrency 80 \
    --timeout 600s \
    --service-account sme-ai-app@PROJECT_ID.iam.gserviceaccount.com
  ```

### Configuración de Escalado

- [ ] **Auto-scaling configurado**
  - Min instances: 1 (evitar cold starts)
  - Max instances: 100
  - Target CPU: 70%
  - Target concurrency: 80

- [ ] **Circuit breakers habilitados**
  ```python
  # En main.py, configurar circuit breaker middleware
  ```

### Health Checks

- [ ] **Endpoint de health implementado**
  ```bash
  curl https://API_URL/health
  ```

- [ ] **Verificar servicios**
  - GCP: configured
  - Vertex AI: enabled
  - RAG grounding: configured
  - Document AI OCR: configured

### Monitoreo

- [ ] **Cloud Monitoring dashboards configurados**
  - Latencia de requests
  - Error rate
  - QPS
  - Token usage
  - Costos

- [ ] **Alertas configuradas**
  ```bash
  gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="SME AI Alerts" \
    --condition-display-name="High Error Rate" \
    --condition-threshold-value=0.05 \
    --condition-threshold-duration=300s
  ```

### Logging

- [ ] **Cloud Logging habilitado**
  ```bash
  # Structured logging con structlog ya configurado
  ```

- [ ] **Log retention configurado**
  - Retention: 30 días (ajustar según compliance)

- [ ] **Log-based metrics creados**
  ```bash
  gcloud logging metrics create rag_query_latency \
    --description="RAG query latency" \
    --log-filter='resource.type="cloud_run_revision"
      AND textPayload=~"rag_query_completed"'
  ```

---

## Post-Deployment

### Verificación

- [ ] **Smoke tests en producción**
  - Test de upload de documento
  - Test de análisis de drawing
  - Test de chat con grounding

- [ ] **Verificar métricas baseline**
  - Latencia promedio
  - Error rate inicial
  - QPS inicial

### Optimización

- [ ] **Context caching habilitado**
  - Verificado en logs: `chat_service_initialized_with_caching`
  - Cache TTL: 3600s (1 hora)

- [ ] **Monitorear cache hit rate**
  ```python
  # En Cloud Monitoring, crear métrica personalizada
  ```

### Seguridad

- [ ] **DLP scanning habilitado**
  - Escanear uploads para PII
  - Ver docs/SECURITY.md

- [ ] **Audit logs habilitados**
  - Admin Activity Logs: ✓ (default)
  - Data Access Logs: configurar manualmente

- [ ] **Security Command Center scan**
  ```bash
  gcloud scc findings list organizations/ORG_ID
  ```

### Costos

- [ ] **Budget alerts configurados**
  ```bash
  gcloud billing budgets create \
    --billing-account=ACCOUNT_ID \
    --display-name="SME AI Budget" \
    --budget-amount=1000 \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90
  ```

- [ ] **Cost breakdown dashboard**
  - Ver docs/COST_OPTIMIZATION.md

### Documentación

- [ ] **Runbook de operaciones documentado**
- [ ] **Incident response plan definido**
- [ ] **On-call schedule configurado**
- [ ] **Escalation paths definidos**

---

## Mantenimiento Continuo

### Weekly

- [ ] Revisar logs de error
- [ ] Verificar métricas de calidad RAG
- [ ] Revisar costos semanales

### Monthly

- [ ] Rotar service account keys (si no está automatizado)
- [ ] Actualizar dependencias (security patches)
- [ ] Review de performance y optimización
- [ ] Backup de configuraciones

### Quarterly

- [ ] Audit de seguridad completo
- [ ] Review de arquitectura
- [ ] Capacity planning
- [ ] Disaster recovery drill

---

## Rollback Plan

En caso de problemas críticos en producción:

### Rollback Rápido

```bash
# Revertir a versión anterior
gcloud run services update-traffic sme-ai-vertex \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=us-central1
```

### Rollback de Datos

- [ ] Backups de Cloud Storage configurados
- [ ] Point-in-time recovery para bases de datos
- [ ] Snapshots de Vector Search índices

---

## Checklist Final

### Crítico (Bloqueantes)

- [ ] Todas las APIs habilitadas
- [ ] Service accounts configuradas
- [ ] RAG corpus creado y documentos indexados
- [ ] Vector Search índice deployado
- [ ] Environment variables configuradas
- [ ] Health checks pasando
- [ ] Tests de integración pasando

### Importante (Alta Prioridad)

- [ ] Context caching habilitado
- [ ] Monitoreo y alertas configurados
- [ ] Logging habilitado
- [ ] Budget alerts configurados
- [ ] CMEK configurado
- [ ] DLP scanning habilitado

### Recomendado (Media Prioridad)

- [ ] VPC-SC configurado
- [ ] Load testing completado
- [ ] RAG evaluation metrics >0.7
- [ ] Documentation completa

---

## Recursos

- **Guía de Seguridad**: [docs/SECURITY.md](./SECURITY.md)
- **Optimización de Costos**: [docs/COST_OPTIMIZATION.md](./COST_OPTIMIZATION.md)
- **Vertex AI Documentation**: https://cloud.google.com/vertex-ai/docs
- **RAG Engine Guide**: https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine

---

**Última actualización**: Noviembre 2025
**Versión**: 1.0
**Alineado con**: Guía Técnica Vertex AI RAG Multimodal Noviembre 2025

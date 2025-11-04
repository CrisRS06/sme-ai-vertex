# Guía de Seguridad y Cumplimiento

**Alineada con la Guía Técnica Vertex AI RAG Multimodal - Noviembre 2025**

Esta guía detalla las mejores prácticas de seguridad y cumplimiento para el sistema SME AI Vertex en producción.

## Tabla de Contenidos

- [IAM y Permisos](#iam-y-permisos)
- [VPC Service Controls](#vpc-service-controls)
- [Cifrado de Datos](#cifrado-de-datos)
- [Data Loss Prevention (DLP)](#data-loss-prevention-dlp)
- [Cumplimiento Normativo](#cumplimiento-normativo)
- [Auditoría y Logging](#auditoría-y-logging)

---

## IAM y Permisos

### Principio de Mínimo Privilegio

Usar roles IAM granulares para permisos específicos:

#### Service Account para la Aplicación

```bash
# Crear service account
gcloud iam service-accounts create sme-ai-app \
  --display-name="SME AI Application Service Account" \
  --project=PROJECT_ID

# Roles necesarios (granulares)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:sme-ai-app@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:sme-ai-app@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:sme-ai-app@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/documentai.apiUser"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:sme-ai-app@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/discoveryengine.admin"
```

#### Service Account para Vector Search

```bash
# Service account separada para operaciones de Vector Search
gcloud iam service-accounts create sme-ai-vector-search \
  --display-name="SME AI Vector Search Service Account" \
  --project=PROJECT_ID

# Solo permisos para Vector Search
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:sme-ai-vector-search@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.indexUser"
```

### Roles Recomendados por Componente

| Componente | Rol IAM | Descripción |
|------------|---------|-------------|
| Aplicación principal | `aiplatform.user` | Usar Vertex AI models y endpoints |
| Cloud Storage | `storage.objectAdmin` | Leer/escribir en buckets específicos |
| Document AI | `documentai.apiUser` | Procesar documentos con OCR |
| RAG Engine | `discoveryengine.admin` | Gestionar corpus y buscar |
| Vector Search | `aiplatform.indexUser` | Consultar índices vectoriales |
| Cloud Run | `run.invoker` | Invocar servicios |

### Mejores Prácticas IAM

1. **Separación de Service Accounts**
   - Una service account por componente
   - Nunca usar service accounts con roles de Owner o Editor

2. **Rotación de Credenciales**
   - Rotar keys cada 90 días
   - Usar Workload Identity en GKE (no keys en archivos)

3. **Auditoría de Permisos**
   ```bash
   # Revisar permisos de service account
   gcloud projects get-iam-policy PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:sme-ai-app@PROJECT_ID.iam.gserviceaccount.com"
   ```

---

## VPC Service Controls

### ¿Qué es VPC-SC?

VPC Service Controls crea un perímetro de seguridad alrededor de recursos de GCP para:
- Prevenir exfiltración de datos
- Controlar acceso a APIs
- Aislar datos sensibles

### Configuración Básica

#### 1. Crear Access Policy

```bash
gcloud access-context-manager policies create \
  --title="SME AI Security Policy" \
  --organization=ORGANIZATION_ID
```

#### 2. Crear Perimeter

```bash
# Definir servicios protegidos
SERVICES="storage.googleapis.com,aiplatform.googleapis.com,documentai.googleapis.com"

# Crear perimeter
gcloud access-context-manager perimeters create sme_ai_perimeter \
  --title="SME AI Production Perimeter" \
  --resources=projects/PROJECT_ID \
  --restricted-services=$SERVICES \
  --access-levels=LEVEL_NAME \
  --policy=POLICY_ID
```

#### 3. Configurar Egress/Ingress

```yaml
# egress_policy.yaml
egressPolicies:
  - egressFrom:
      identityType: ANY_IDENTITY
    egressTo:
      resources:
        - "projects/PROJECT_ID"
      operations:
        - serviceName: "storage.googleapis.com"
          methodSelectors:
            - method: "*"
```

### Recursos a Proteger

- **Cloud Storage Buckets**: Drawings, reports, manuals
- **Vertex AI**: RAG Engine, Vector Search, Models
- **Document AI**: Processors
- **BigQuery**: Analytics data (si aplica)

---

## Cifrado de Datos

### Encryption at Rest (CMEK)

Customer-Managed Encryption Keys para control total del cifrado.

#### 1. Crear Key Ring y Key

```bash
# Crear key ring
gcloud kms keyrings create sme-ai-keyring \
  --location=us-central1 \
  --project=PROJECT_ID

# Crear encryption key
gcloud kms keys create sme-ai-encryption-key \
  --location=us-central1 \
  --keyring=sme-ai-keyring \
  --purpose=encryption \
  --project=PROJECT_ID

# Obtener key resource name
KEY_NAME="projects/PROJECT_ID/locations/us-central1/keyRings/sme-ai-keyring/cryptoKeys/sme-ai-encryption-key"
```

#### 2. Dar permisos a Service Accounts

```bash
# Permitir que Vertex AI use la key
gcloud kms keys add-iam-policy-binding sme-ai-encryption-key \
  --location=us-central1 \
  --keyring=sme-ai-keyring \
  --member="serviceAccount:service-PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com" \
  --role="roles/cloudkms.cryptoKeyEncrypterDecrypter" \
  --project=PROJECT_ID
```

#### 3. Usar CMEK en Cloud Storage

```bash
# Configurar bucket con CMEK
gsutil encryption set \
  -k $KEY_NAME \
  gs://PROJECT_ID-drawings
```

#### 4. Usar CMEK en Vertex AI

```python
from google.cloud import aiplatform

aiplatform.init(
    project=PROJECT_ID,
    location="us-central1",
    encryption_spec_key_name=KEY_NAME  # Usar CMEK
)
```

### Encryption in Transit

- **TLS 1.3**: Todas las comunicaciones usan TLS
- **Cloud Run**: HTTPS obligatorio
- **mTLS**: Considerar para APIs internas

---

## Data Loss Prevention (DLP)

### Escaneo de Datos Sensibles

Prevenir que PII (Personally Identifiable Information) entre al sistema.

#### 1. Crear DLP Template

```bash
# Crear inspection template para detectar PII
gcloud dlp inspect-templates create \
  --display-name="SME AI PII Detection" \
  --location=global \
  --min-likelihood=POSSIBLE \
  --max-findings-per-request=100 \
  --include-quote=true \
  --info-types=PERSON_NAME,EMAIL_ADDRESS,PHONE_NUMBER,CREDIT_CARD_NUMBER
```

#### 2. Escanear antes de Ingestión

```python
from google.cloud import dlp_v2

def scan_for_pii(content: str) -> bool:
    """
    Escanear contenido para detectar PII antes de procesamiento.

    Returns:
        True si se detecta PII (bloquear), False si está limpio
    """
    dlp_client = dlp_v2.DlpServiceClient()

    inspect_config = {
        "info_types": [
            {"name": "PERSON_NAME"},
            {"name": "EMAIL_ADDRESS"},
            {"name": "PHONE_NUMBER"},
            {"name": "CREDIT_CARD_NUMBER"},
        ],
        "min_likelihood": dlp_v2.Likelihood.POSSIBLE,
    }

    item = {"value": content}

    response = dlp_client.inspect_content(
        request={
            "parent": f"projects/{PROJECT_ID}/locations/global",
            "inspect_config": inspect_config,
            "item": item
        }
    )

    # Si hay findings, bloquear
    return len(response.result.findings) > 0
```

### Anonimización

```python
def anonymize_pii(content: str) -> str:
    """Reemplazar PII detectado con placeholders."""
    deidentify_config = {
        "info_type_transformations": {
            "transformations": [
                {
                    "primitive_transformation": {
                        "replace_config": {
                            "new_value": {"string_value": "[REDACTED]"}
                        }
                    }
                }
            ]
        }
    }

    response = dlp_client.deidentify_content(
        request={
            "parent": f"projects/{PROJECT_ID}/locations/global",
            "deidentify_config": deidentify_config,
            "item": {"value": content}
        }
    )

    return response.item.value
```

---

## Cumplimiento Normativo

### HIPAA (Health Insurance Portability and Accountability Act)

**Si procesas datos de salud:**

1. **Usar regiones compatibles con HIPAA**
   - `us-central1`, `us-east4`, `europe-west4`
   - No usar regiones multi-región

2. **Firmar BAA con Google**
   - Contactar Google Cloud compliance
   - Configurar HIPAA controls

3. **Auditoría completa**
   ```bash
   # Habilitar Cloud Audit Logs
   gcloud logging write --severity=NOTICE "HIPAA audit log enabled"
   ```

### GDPR (General Data Protection Regulation)

**Si procesas datos de ciudadanos EU:**

1. **Residencia de Datos**
   - Usar regiones EU: `europe-west1`, `europe-west4`
   - Configurar residencia en `.env`:
     ```bash
     GCP_REGION=europe-west1
     GCP_LOCATION=europe-west1
     ```

2. **Derecho al Olvido**
   ```python
   async def delete_user_data(user_id: str):
       """Eliminar todos los datos de un usuario (GDPR compliance)."""
       # Eliminar documentos
       await knowledge_base.delete_user_documents(user_id)

       # Eliminar análisis
       await analysis_service.delete_user_analyses(user_id)

       # Eliminar embeddings
       vector_search.delete_user_embeddings(user_id)

       # Log deletion
       logger.info("gdpr_user_data_deleted", user_id=user_id)
   ```

3. **Consentimiento de Datos**
   - Implementar checkbox de consentimiento en UI
   - Almacenar consentimiento en metadata

### SOC 2 / ISO 27001

1. **Controles de acceso** (ver IAM section)
2. **Logging completo** (ver Auditoría section)
3. **Incident response plan**
4. **Regular security assessments**

---

## Auditoría y Logging

### Cloud Audit Logs

#### Habilitar Todos los Tipos de Logs

```bash
# Admin Activity Logs (habilitados por defecto)
# Data Access Logs (habilitar manualmente)
gcloud logging sinks create sme-ai-audit-sink \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/audit_logs \
  --log-filter='protoPayload.serviceName=("aiplatform.googleapis.com" OR "storage.googleapis.com")'
```

#### Monitorear Accesos Sospechosos

```bash
# Query para accesos no autorizados
gcloud logging read 'protoPayload.status.code!=0' \
  --limit 50 \
  --format json
```

### Security Command Center

```bash
# Habilitar Security Command Center
gcloud services enable securitycenter.googleapis.com

# Ver findings de seguridad
gcloud scc findings list organizations/ORGANIZATION_ID \
  --filter="category='ANOMALOUS_ACTIVITY'"
```

### Structured Logging

El sistema ya usa `structlog` para logging estructurado:

```python
import structlog

logger = structlog.get_logger()

# Log con contexto
logger.info(
    "user_action",
    user_id=user_id,
    action="upload_document",
    document_type="manual",
    ip_address=request.client.host
)
```

### Métricas de Seguridad

Trackear en Cloud Monitoring:

- Intentos de autenticación fallidos
- Uploads rechazados (PII detectado)
- Accesos fuera de horario
- Patrones anómalos de uso

---

## Checklist de Seguridad en Producción

### Pre-Deployment

- [ ] Service accounts configuradas con mínimo privilegio
- [ ] CMEK configurado para todos los buckets
- [ ] VPC-SC perimeter creado (opcional pero recomendado)
- [ ] DLP templates configurados
- [ ] Audit logs habilitados
- [ ] Secrets en Secret Manager (no en .env)

### Post-Deployment

- [ ] Revisar logs de auditoría semanalmente
- [ ] Rotar service account keys cada 90 días
- [ ] Scan de vulnerabilidades mensual
- [ ] Incident response plan documentado
- [ ] Security training para equipo

### Continuous Monitoring

```bash
# Configurar alertas en Cloud Monitoring
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="SME AI Security Alerts" \
  --condition-display-name="Unauthorized Access" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=60s
```

---

## Soporte y Recursos

- **GCP Security Command Center**: https://cloud.google.com/security-command-center
- **VPC-SC Documentation**: https://cloud.google.com/vpc-service-controls/docs
- **CMEK Guide**: https://cloud.google.com/kms/docs/cmek
- **DLP Best Practices**: https://cloud.google.com/dlp/docs/best-practices
- **Compliance Resources**: https://cloud.google.com/security/compliance

---

**Última actualización**: Noviembre 2025
**Versión**: 1.0
**Alineado con**: Guía Técnica Vertex AI RAG Multimodal Noviembre 2025

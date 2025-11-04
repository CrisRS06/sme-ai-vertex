# Índice de Documentación - SME AI Vertex

**Versión**: 1.0.0 | **Status**: Production-Ready | **Última actualización**: 2025-11-04

---

## 🚀 Inicio Rápido

| Documento | Descripción | Tiempo |
|-----------|-------------|--------|
| [QUICKSTART.md](./QUICKSTART.md) | Setup rápido del sistema local o GCP | 5-30 min |
| [README.md](./README.md) | Documentación principal del proyecto | - |

---

## 🧪 Testing y Validación

| Documento | Descripción | Para quién |
|-----------|-------------|------------|
| [TESTING_GUIDE.md](./docs/TESTING_GUIDE.md) | Guía completa de testing con 4 opciones | Desarrolladores |
| [test_system.sh](./scripts/test_system.sh) | Script automatizado de testing | DevOps |

---

## 🎨 Experiencia de Usuario

| Documento | Descripción | Para quién |
|-----------|-------------|------------|
| [USER_EXPERIENCE.md](./docs/USER_EXPERIENCE.md) | Flujos end-to-end, 3 personas | Product, UX |
| [SYSTEM_FLOW_DIAGRAM.md](./docs/SYSTEM_FLOW_DIAGRAM.md) | Diagramas de arquitectura | Ingenieros |

---

## 🔌 Integración

| Documento | Descripción | Para quién |
|-----------|-------------|------------|
| [FRONTEND_API_GUIDE.md](./FRONTEND_API_GUIDE.md) | Guía de integración con API REST | Frontend devs |
| Swagger UI | Documentación interactiva | Todos |

**Acceso a Swagger**: http://localhost:8080/docs (cuando el servidor está corriendo)

---

## 🏭 Producción

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| [PRODUCTION_DEPLOYMENT.md](./docs/PRODUCTION_DEPLOYMENT.md) | Checklist completo de deployment | DevOps, SRE |
| [SECURITY.md](./docs/SECURITY.md) | IAM, VPC-SC, CMEK, DLP, compliance | Security, DevOps |
| [COST_OPTIMIZATION.md](./docs/COST_OPTIMIZATION.md) | Estrategias de optimización de costos | FinOps, Ingenieros |

---

## 📊 Alineación Técnica

| Documento | Descripción | Para quién |
|-----------|-------------|------------|
| [ALIGNMENT_SUMMARY.md](./ALIGNMENT_SUMMARY.md) | Resumen de alineación con guía Vertex AI | Arquitectos, PM |

---

## 📁 Estructura del Proyecto

```
SME AI Vertex/
├── 📖 Documentación Principal
│   ├── README.md                    ← Empieza aquí
│   ├── QUICKSTART.md               ← Setup en 5 minutos
│   ├── DOCUMENTATION_INDEX.md      ← Este archivo
│   ├── FRONTEND_API_GUIDE.md       ← Integración frontend
│   └── ALIGNMENT_SUMMARY.md        ← Alineación técnica
│
├── 📚 docs/                        ← Guías especializadas
│   ├── TESTING_GUIDE.md
│   ├── USER_EXPERIENCE.md
│   ├── SYSTEM_FLOW_DIAGRAM.md
│   ├── PRODUCTION_DEPLOYMENT.md
│   ├── SECURITY.md
│   └── COST_OPTIMIZATION.md
│
├── 🔧 src/                         ← Código fuente
│   ├── api/                        ← Endpoints REST
│   ├── services/                   ← Lógica de negocio
│   ├── models/                     ← Schemas Pydantic
│   └── config/                     ← Configuración
│
├── 🛠 scripts/                     ← Automatización
│   ├── setup_gcp.sh                ← Setup GCP
│   ├── setup_vector_search.sh      ← Provisionar Vector Search
│   ├── deploy_cloudrun.sh          ← Deploy a Cloud Run
│   └── test_system.sh              ← Testing automatizado
│
└── 🎨 frontend/                    ← Frontend Vercel (separado)
    └── README.md
```

---

## 🎯 Flujo de Lectura Recomendado

### Para Desarrolladores Nuevos
1. [README.md](./README.md) - Entender el proyecto
2. [QUICKSTART.md](./QUICKSTART.md) - Configurar ambiente local
3. [TESTING_GUIDE.md](./docs/TESTING_GUIDE.md) - Probar el sistema
4. [FRONTEND_API_GUIDE.md](./FRONTEND_API_GUIDE.md) - Integrar con frontend

### Para DevOps/SRE
1. [README.md](./README.md) - Overview del sistema
2. [PRODUCTION_DEPLOYMENT.md](./docs/PRODUCTION_DEPLOYMENT.md) - Deployment
3. [SECURITY.md](./docs/SECURITY.md) - Seguridad y compliance
4. [COST_OPTIMIZATION.md](./docs/COST_OPTIMIZATION.md) - Optimización de costos

### Para Arquitectos/PM
1. [README.md](./README.md) - Overview técnico
2. [ALIGNMENT_SUMMARY.md](./ALIGNMENT_SUMMARY.md) - Alineación con best practices
3. [SYSTEM_FLOW_DIAGRAM.md](./docs/SYSTEM_FLOW_DIAGRAM.md) - Arquitectura
4. [USER_EXPERIENCE.md](./docs/USER_EXPERIENCE.md) - Experiencia end-to-end

### Para Product/UX
1. [USER_EXPERIENCE.md](./docs/USER_EXPERIENCE.md) - Flujos de usuario
2. [SYSTEM_FLOW_DIAGRAM.md](./docs/SYSTEM_FLOW_DIAGRAM.md) - Arquitectura visual
3. [FRONTEND_API_GUIDE.md](./FRONTEND_API_GUIDE.md) - Capacidades de la API

---

## 🔍 Búsqueda Rápida

### ¿Cómo...?
- **...empezar rápido?** → [QUICKSTART.md](./QUICKSTART.md)
- **...probar el sistema?** → [TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)
- **...integrar frontend?** → [FRONTEND_API_GUIDE.md](./FRONTEND_API_GUIDE.md)
- **...deployar a producción?** → [PRODUCTION_DEPLOYMENT.md](./docs/PRODUCTION_DEPLOYMENT.md)
- **...optimizar costos?** → [COST_OPTIMIZATION.md](./docs/COST_OPTIMIZATION.md)
- **...configurar seguridad?** → [SECURITY.md](./docs/SECURITY.md)

### ¿Qué es...?
- **...la arquitectura del sistema?** → [SYSTEM_FLOW_DIAGRAM.md](./docs/SYSTEM_FLOW_DIAGRAM.md)
- **...la experiencia de usuario?** → [USER_EXPERIENCE.md](./docs/USER_EXPERIENCE.md)
- **...el nivel de alineación?** → [ALIGNMENT_SUMMARY.md](./ALIGNMENT_SUMMARY.md)

---

## 📞 Soporte

- **Swagger UI**: http://localhost:8080/docs
- **Testing rápido**: `./scripts/test_system.sh http://localhost:8080`
- **Troubleshooting**: [TESTING_GUIDE.md#troubleshooting](./docs/TESTING_GUIDE.md)
- **Issues**: GitHub Issues

---

**Status**: ✅ Production-Ready | **Version**: 1.0.0 | **Última actualización**: 2025-11-04

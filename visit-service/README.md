# Visit Service

Microservicio para gestión de visitas a clientes con soporte para evidencias multimedia.

## 🎯 Características

- ✅ Registro de visitas a clientes con información detallada
- ✅ Carga de evidencias multimedia (fotos y videos)
- ✅ URLs pre-firmadas de S3 para visualización segura (24h de validez)
- ✅ Almacenamiento flexible: S3 o local
- ✅ RBAC integrado con validación de permisos
- ✅ Validación de archivos (tipo, tamaño, formato)
- ✅ API RESTful con FastAPI

## 📋 Requisitos

- Python 3.12+
- PostgreSQL 14+
- Amazon S3 (opcional, para producción)
- Docker & Docker Compose (recomendado)

## 🚀 Inicio Rápido

### Con Docker (Recomendado)

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de S3

# 2. Iniciar servicios
docker-compose up -d

# 3. Verificar salud del servicio
curl http://localhost:8011/health
```

### Local (Desarrollo)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables de entorno
export FILES_BACKEND=s3
export S3_BUCKET=tu-bucket
export AWS_ACCESS_KEY_ID=tu-key
export AWS_SECRET_ACCESS_KEY=tu-secret

# 3. Ejecutar servicio
uvicorn main:app --reload --host 0.0.0.0 --port 8011

# 4. Ejecutar tests
pytest
```

## 📚 Documentación

- **[S3_CONFIGURATION.md](./S3_CONFIGURATION.md)** - Configuración completa de Amazon S3
- **[TESTING_EVIDENCE_DISPLAY.md](./TESTING_EVIDENCE_DISPLAY.md)** - Guía de testing de evidencias
- **[API Docs](http://localhost:8011/docs)** - Documentación interactiva (Swagger)
- **[Postman Collection](./postman_collection.json)** - Colección de requests de ejemplo

## 🔧 Configuración

### Variables de Entorno Principales

```bash
# Base de Datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=visit_db
DB_USER=visit_user
DB_PASSWORD=visit_password

# Almacenamiento
FILES_BACKEND=s3              # "s3" o "local"
MAX_UPLOAD_MB=15              # Tamaño máximo de archivo

# S3 (si FILES_BACKEND=s3)
S3_BUCKET=medisupply-visit-evidences
S3_PREFIX=visits
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# Autenticación
JWT_SECRET=tu-jwt-secret
```

## 🏗️ Arquitectura Backend-Managed

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  App Móvil  │────────>│visit-service │────────>│  Amazon S3  │
│             │  Upload │   (FastAPI)  │  Store  │   (Bucket)  │
└─────────────┘         └──────────────┘         └─────────────┘
       │                        │                        │
       │   Pre-signed URL       │   Generate URL         │
       │<───────────────────────│<───────────────────────│
       │                        │                        │
       │   View/Download        │                        │
       │───────────────────────────────────────────────>│
```

**Ventajas:**
- Control total de validaciones en el backend
- Seguridad: No se exponen credenciales AWS al cliente
- Auditoría completa de todos los uploads
- Simplicidad en la app móvil

## 📡 Endpoints Principales

### Visitas

- `POST /visits` - Crear nueva visita
- `GET /api/v1/visits/{visit_id}` - Obtener detalle de visita
- `GET /api/v1/visits/client/{client_id}` - Listar visitas por cliente

### Evidencias

- `POST /visits/{visit_id}/evidence` - Subir evidencia (imagen/video)
- `GET /api/v1/visits/{visit_id}/evidence/{evidence_id}/url` - Regenerar URL pre-firmada

## 🧪 Testing

```bash
# Tests unitarios
pytest tests/

# Tests con cobertura
pytest --cov=app tests/

# Test específico
pytest tests/test_visits.py -v
```

## 🔐 Seguridad

- ✅ Autenticación JWT requerida
- ✅ RBAC con roles (gerente_cuenta, admin)
- ✅ Bucket S3 privado (no acceso público)
- ✅ URLs pre-firmadas con expiración (24h)
- ✅ Validación de tipos de archivo
- ✅ Límite de tamaño de archivo (15MB)

## 📊 Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **SQLAlchemy** - ORM para PostgreSQL
- **boto3** - Cliente AWS SDK para Python
- **Pydantic** - Validación de datos
- **pytest** - Framework de testing

## 🔗 Enlaces Útiles

- [Documentación de Configuración S3](./S3_CONFIGURATION.md)
- [Guía de Testing](./TESTING_EVIDENCE_DISPLAY.md)
- [Postman Collection](./postman_collection.json)

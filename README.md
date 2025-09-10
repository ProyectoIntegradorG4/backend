# Backend Microservices

Este proyecto implementa una arquitectura de microservicios usando FastAPI y PostgreSQL, con Docker Compose para la orquestación.

## Estructura del Proyecto

```
backend/
├── user-service/           # Microservicio de gestión de usuarios
├── tax-service/            # Microservicio de cálculo de impuestos
├── audit-service/          # Microservicio de auditoría y logs
├── docker-compose.yml      # Orquestación de servicios
├── nginx.conf             # Configuración del API Gateway
├── .env                   # Variables de entorno
└── README.md              # Este archivo
```

## Microservicios

### 1. User Service (Puerto 8001)
- **Propósito**: Gestión de usuarios, autenticación y autorización
- **Base de datos**: PostgreSQL (puerto 5432)
- **Endpoints principales**:
  - `POST /api/v1/users/` - Crear usuario
  - `GET /api/v1/users/` - Listar usuarios
  - `GET /api/v1/users/{id}` - Obtener usuario
  - `PUT /api/v1/users/{id}` - Actualizar usuario
  - `DELETE /api/v1/users/{id}` - Eliminar usuario

### 2. Tax Service (Puerto 8002)
- **Propósito**: Cálculo y gestión de impuestos
- **Base de datos**: PostgreSQL (puerto 5433)
- **Endpoints principales**:
  - `POST /api/v1/taxes/` - Crear tipo de impuesto
  - `GET /api/v1/taxes/` - Listar impuestos
  - `POST /api/v1/taxes/calculate/` - Calcular impuesto
  - `GET /api/v1/taxes/calculations/{user_id}` - Historial de cálculos

### 3. Audit Service (Puerto 8003)
- **Propósito**: Auditoría, logs y trazabilidad del sistema
- **Base de datos**: PostgreSQL (puerto 5434)
- **Endpoints principales**:
  - `POST /api/v1/audits/` - Crear log de auditoría
  - `GET /api/v1/audits/` - Consultar logs (con filtros)
  - `GET /api/v1/audits/stats/summary` - Resumen estadístico

## Tecnologías Utilizadas

- **Framework**: FastAPI (Python 3.12)
- **Base de datos**: PostgreSQL 16
- **Driver de BD**: psycopg3 (última versión)
- **ORM**: SQLAlchemy 2.0
- **Contenedores**: Docker & Docker Compose
- **API Gateway**: Nginx
- **Validación**: Pydantic

## Inicio Rápido

### Prerrequisitos
- Docker
- Docker Compose

### Levantar los servicios

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd backend

# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar estado de servicios
docker-compose ps
```

### Acceso a los servicios

- **API Gateway**: http://localhost
- **User Service**: http://localhost:8001
- **Tax Service**: http://localhost:8002
- **Audit Service**: http://localhost:8003

### Documentación de APIs

Cada servicio tiene documentación automática de Swagger:

- User Service: http://localhost:8001/docs
- Tax Service: http://localhost:8002/docs
- Audit Service: http://localhost:8003/docs

## Desarrollo Local

### Configurar entorno de desarrollo

```bash
# Crear entorno virtual para cada servicio
cd user-service
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Repetir para tax-service y audit-service
```

### Variables de entorno

Copiar `.env` y ajustar las variables según tu entorno:

```bash
cp .env .env.local
# Editar .env.local con tus configuraciones
```

## Base de Datos

Los 3 microservicios comparten una sola instancia de PostgreSQL con bases de datos separadas:

- **PostgreSQL Server**: Puerto 5432
  - `user_db` - Base de datos del User Service
  - `tax_db` - Base de datos del Tax Service  
  - `audit_db` - Base de datos del Audit Service

### Conexiones de base de datos

```bash
# Conectar a la instancia principal
psql -h localhost -p 5432 -U postgres

# Conectar a bases de datos específicas
psql -h localhost -p 5432 -U user_service -d user_db
psql -h localhost -p 5432 -U tax_service -d tax_db
psql -h localhost -p 5432 -U audit_service -d audit_db
```

## Comandos Útiles

```bash
# Reconstruir servicios
docker-compose build

# Levantar servicios específicos
docker-compose up user-service tax-service

# Ver logs de un servicio específico
docker-compose logs -f user-service

# Ejecutar comando en contenedor
docker-compose exec user-service bash

# Parar todos los servicios
docker-compose down

# Parar y eliminar volúmenes
docker-compose down -v
```

## Arquitectura

```
┌─────────────────┐
│   API Gateway   │ (Puerto 80)
│     (Nginx)     │
└─────────┬───────┘
          │
    ┌─────┴─────┐
    │           │
┌───▼───┐   ┌───▼───┐   ┌────▼────┐
│ User  │   │ Tax   │   │ Audit   │
│Service│   │Service│   │ Service │
│:8001  │   │:8002  │   │ :8003   │
└───┬───┘   └───┬───┘   └────┬────┘
    │           │            │
    └─────┬─────┴─────┬──────┘
          │           │
      ┌───▼───────────▼───┐
      │   PostgreSQL DB   │
      │ user_db|tax_db|   │
      │     audit_db      │
      │      :5432        │
      └───────────────────┘
```

## Buenas Prácticas Implementadas

1. **Separación de responsabilidades**: Cada servicio tiene una responsabilidad específica
2. **Base de datos independientes**: Cada servicio maneja su propia base de datos
3. **Containerización**: Todos los servicios están dockerizados
4. **API Gateway**: Punto único de entrada para todas las APIs
5. **Health checks**: Verificación de salud de servicios y bases de datos
6. **Logs estructurados**: Sistema de auditoría centralizado
7. **Validación de datos**: Uso de Pydantic para validación
8. **Documentación automática**: Swagger/OpenAPI para cada servicio

## Próximos Pasos

- [ ] Implementar autenticación JWT
- [ ] Agregar tests unitarios e integración
- [ ] Configurar CI/CD
- [ ] Implementar rate limiting
- [ ] Agregar monitoreo (Prometheus/Grafana)
- [ ] Implementar circuit breaker
- [ ] Configurar logging centralizado (ELK Stack)

## Documentación Adicional

- [Migración a psycopg3](./PSYCOPG3_MIGRATION.md) - Detalles sobre el uso de psycopg3
Backend for 

# Cliente Service - HU-MOV-002

Microservicio de gestión de clientes institucionales para gerentes de cuenta de MediSupply.

## Descripción

Este servicio permite a los gerentes de cuenta consultar la lista de clientes institucionales (hospitales, clínicas, IPS, etc.) asignados a su territorio. Los gerentes solo pueden ver clientes del mismo país al que están asignados, garantizando la segregación de datos por región.

## Tecnologías

- **Framework**: FastAPI 0.104.1
- **ORM**: SQLAlchemy 2.0.23
- **Base de datos**: PostgreSQL 16
- **Driver DB**: psycopg 3.1.12
- **Autenticación**: JWT (python-jose, PyJWT)
- **Validación**: Pydantic 2.5.0
- **Caché**: Redis 5.0.1
- **Testing**: pytest 7.4.0, pytest-cov 4.1.0

## Modelo de Datos

### Tabla: clientes

Almacena información de clientes institucionales que MediSupply atiende.

```sql
CREATE TABLE clientes (
    cliente_id SERIAL PRIMARY KEY,
    nit VARCHAR(20) UNIQUE NOT NULL,
    nombre_comercial VARCHAR(255) NOT NULL,
    razon_social VARCHAR(255) NOT NULL,
    tipo_institucion VARCHAR(100) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    departamento VARCHAR(100),
    ciudad VARCHAR(100),
    direccion TEXT,
    telefono VARCHAR(50),
    email VARCHAR(255),
    contacto_principal VARCHAR(255),
    cargo_contacto VARCHAR(100),
    especialidad_medica VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pais_activo (pais, activo),
    INDEX idx_tipo_institucion (tipo_institucion),
    INDEX idx_nit (nit)
);
```

### Tabla: gerente_cuenta_clientes

Tabla de asignación de clientes a gerentes de cuenta.

```sql
CREATE TABLE gerente_cuenta_clientes (
    id SERIAL PRIMARY KEY,
    gerente_id INTEGER NOT NULL,
    cliente_id INTEGER NOT NULL,
    pais VARCHAR(100) NOT NULL,
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id) ON DELETE CASCADE,
    UNIQUE (gerente_id, cliente_id),
    INDEX idx_gerente_pais (gerente_id, pais, activo),
    INDEX idx_cliente (cliente_id)
);
```

## Endpoints API

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "cliente-service",
  "version": "1.0.0"
}
```

### Listar Clientes Asignados

```http
GET /api/v1/clientes/mis-clientes
```

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>` (requerido)

**Query Parameters:**
- `tipo_institucion` (opcional): Filtrar por tipo de institución
- `search` (opcional): Buscar por nombre o ubicación
- `page` (opcional, default: 1): Número de página
- `limit` (opcional, default: 50, max: 100): Elementos por página
- `activo` (opcional, default: true): Filtrar solo clientes activos

**Response 200:**
```json
{
  "total": 25,
  "page": 1,
  "limit": 50,
  "clientes": [
    {
      "cliente_id": 1,
      "nit": "800123456-1",
      "nombre_comercial": "Hospital San Juan",
      "razon_social": "Hospital San Juan de Dios SAS",
      "tipo_institucion": "Hospital",
      "pais": "Colombia",
      "ciudad": "Bogotá",
      "direccion": "Calle 10 # 20-30",
      "telefono": "+57 1 234 5678",
      "email": "contacto@hospitalsanjuan.com",
      "contacto_principal": "Dr. Carlos Pérez",
      "cargo_contacto": "Director de Compras",
      "activo": true
    }
  ]
}
```

**Errores:**
- `401 Unauthorized`: Token no proporcionado o inválido
- `403 Forbidden`: Usuario no tiene rol gerente_cuenta
- `500 Internal Server Error`: Error en el servidor

### Obtener Detalle de Cliente

```http
GET /api/v1/clientes/{cliente_id}
```

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>` (requerido)

**Response 200:**
```json
{
  "cliente_id": 1,
  "nit": "800123456-1",
  "nombre_comercial": "Hospital San Juan",
  "razon_social": "Hospital San Juan de Dios SAS",
  "tipo_institucion": "Hospital",
  "pais": "Colombia",
  "departamento": "Cundinamarca",
  "ciudad": "Bogotá",
  "direccion": "Calle 10 # 20-30",
  "telefono": "+57 1 234 5678",
  "email": "contacto@hospitalsanjuan.com",
  "contacto_principal": "Dr. Carlos Pérez",
  "cargo_contacto": "Director de Compras",
  "especialidad_medica": "General",
  "activo": true,
  "fecha_registro": "2024-01-15T10:30:00Z",
  "fecha_actualizacion": "2024-01-15T10:30:00Z"
}
```

**Errores:**
- `404 Not Found`: Cliente no encontrado o no tiene acceso

### Obtener Tipos de Institución

```http
GET /api/v1/clientes/tipos-institucion
```

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>` (requerido)

**Response 200:**
```json
{
  "tipos": [
    "Hospital",
    "Clínica",
    "IPS",
    "EPS",
    "Laboratorio Clínico",
    "Centro de Salud"
  ]
}
```

## Autenticación y Autorización

El servicio utiliza JWT (JSON Web Tokens) para autenticación. El token debe incluirse en el header `Authorization` con el formato:

```
Authorization: Bearer <token>
```

### Rol Requerido

Solo usuarios con el rol `gerente_cuenta` pueden acceder a los endpoints.

### Segregación por País

Los gerentes de cuenta solo pueden ver clientes del mismo país al que están asignados. El país del gerente se determina mediante su NIT asociado a MediSupply.

## Variables de Entorno

```env
# Base de datos
CLIENTE_DB_NAME=cliente_db
CLIENTE_DB_USER=cliente_service
CLIENTE_DB_PASSWORD=cliente_password
POSTGRES_HOST=postgres-db
POSTGRES_PORT=5432
CLIENTE_DATABASE_URL=postgresql+psycopg://cliente_service:cliente_password@postgres-db:5432/cliente_db

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-2024

# Redis
REDIS_URL=redis://redis-cache:6379

# Pool de conexiones
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=1800
DB_POOL_TIMEOUT=30
DB_CONNECT_TIMEOUT=10
SQL_ECHO=false
DB_SSL_MODE=disable
```

## Instalación y Ejecución

### Desarrollo Local

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Configurar variables de entorno (crear archivo `.env` basado en `example.env`)

3. Ejecutar el servicio:
```bash
uvicorn main:app --host 0.0.0.0 --port 8013 --reload
```

### Docker

1. Construir imagen:
```bash
docker build -t cliente-service .
```

2. Ejecutar contenedor:
```bash
docker run -p 8013:8013 --env-file .env cliente-service
```

### Docker Compose

Desde el directorio raíz del backend:

```bash
docker-compose up cliente-service
```

## Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con reporte de cobertura
pytest --cov=app --cov-report=term-missing

# Solo tests de integración
pytest tests/test_clientes.py

# Solo tests unitarios
pytest tests/test_cliente_service_unit.py
```

### Cobertura de Tests

El proyecto mantiene una cobertura de tests >= 80% según los criterios de aceptación de HU-MOV-002.

Casos de prueba incluyen:
- ✅ Autenticación y autorización
- ✅ Listado de clientes con filtros
- ✅ Búsqueda por nombre y ubicación
- ✅ Paginación
- ✅ Segregación por país
- ✅ Filtrado por tipo de institución
- ✅ Solo clientes activos
- ✅ Detalle de cliente
- ✅ Manejo de errores

## Arquitectura

El servicio sigue una arquitectura en capas siguiendo principios de Clean Code y Clean Architecture:

```
cliente-service/
├── app/
│   ├── models/          # Modelos SQLAlchemy y Pydantic
│   ├── services/        # Lógica de negocio
│   ├── routes/          # Endpoints REST
│   └── database/        # Conexión y configuración DB
├── tests/               # Tests unitarios e integración
└── main.py              # Punto de entrada de la aplicación
```

### Principios Aplicados

- **12 Factor App**: Configuración en variables de entorno, stateless, logs a stdout
- **Clean Code**: Separación de concerns, nombres descriptivos, funciones pequeñas
- **SOLID**: Dependency injection, single responsibility
- **DRY**: Código reutilizable y sin duplicación
- **Optimización**: Pool de conexiones, índices en BD, paginación

## Datos de Prueba

El servicio incluye un seed automático con ~30 clientes de prueba distribuidos en:
- Colombia: 10 clientes
- Perú: 8 clientes
- México: 7 clientes
- Ecuador: 5 clientes

Los datos de prueba cubren diferentes tipos de institución y ciudades.

## Monitoreo

### Health Checks

```bash
# Servicio directo
curl http://localhost:8013/health

# A través de API Gateway
curl http://localhost/health/cliente
```

### Logs

Los logs se emiten a stdout/stderr siguiendo el patrón 12 Factor App:

```
🚀 Iniciando Cliente Service...
🔍 Verificando existencia de base de datos...
✅ Base de datos cliente_db ya existe
✅ Conexión a base de datos establecida.
📋 Creando tablas...
✅ Tablas creadas exitosamente
🌱 Ejecutando seeds de datos de prueba...
✅ Se insertaron 30 clientes de prueba
✅ Cliente Service iniciado correctamente
```

## Integración con Otros Servicios

### Dependencies

- **auth-service**: Para generación y validación de tokens JWT
- **user-service**: Para información de usuarios/gerentes
- **nit-validation-service**: Para validar país del gerente según NIT
- **postgres-db**: Base de datos compartida
- **redis**: Caché compartido

## Roadmap

Futuras mejoras planificadas:
- [ ] Caché de consultas con Redis
- [ ] Exportación de lista de clientes (CSV, Excel)
- [ ] Filtros avanzados (por especialidad médica, departamento)
- [ ] Histórico de cambios en clientes
- [ ] Integración con servicio de geolocalización
- [ ] Métricas y analytics de consultas

## Contribuir

1. Seguir la estructura del proyecto existente
2. Mantener cobertura de tests >= 80%
3. Documentar nuevos endpoints en este README
4. Aplicar principios Clean Code y 12 Factor
5. Actualizar modelos Pydantic para validación

## Soporte

Para preguntas o reportar issues, contactar al equipo de desarrollo backend.

## Licencia

Propiedad de MediSupply - Uso interno únicamente


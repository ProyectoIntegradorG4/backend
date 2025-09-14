# NIT Validation Service

Microservicio para validación de NIT contra tabla de instituciones asociadas con soporte de caché Redis.

## Características

- ✅ Validación de formato de NIT
- ✅ Consulta contra base de datos PostgreSQL de instituciones asociadas
- ✅ Caché Redis para optimizar rendimiento
- ✅ API REST con endpoints tipificados
- ✅ Manejo de errores estructurado
- ✅ Métricas de latencia
- ✅ Health checks con verificación de dependencias

## Estructura del Proyecto

```
nit-validation-service/
├── app/
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py          # Configuración PostgreSQL y Redis
│   ├── models/
│   │   ├── __init__.py
│   │   └── institucion.py         # Modelos SQLAlchemy y Pydantic
│   ├── routes/
│   │   ├── __init__.py
│   │   └── nit_validation.py      # Endpoints API REST
│   ├── services/
│   │   ├── __init__.py
│   │   └── nit_validation_service.py  # Lógica de negocio
│   └── __init__.py
├── main.py                        # Aplicación FastAPI principal
├── requirements.txt               # Dependencias Python
├── Dockerfile                     # Contenedor Docker
├── NITValidationData.json         # Datos de prueba
├── load_sample_data.py           # Script para cargar datos
├── test_service.py               # Script de pruebas
└── README.md                     # Este archivo
```

## Modelo de Datos

### Tabla: InstitucionesAsociadas

```sql
CREATE TABLE InstitucionesAsociadas (
    nit VARCHAR(20) PRIMARY KEY,
    nombre_institucion VARCHAR(255) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);
```

## API Endpoints

### 🔍 Validación de NIT

#### POST `/api/v1/validate`
```json
{
  "nit": "4347402554",
  "pais": "Colombia"  // opcional
}
```

#### GET `/api/v1/validate/{nit}?pais=Colombia`

**Respuesta exitosa:**
```json
{
  "valid": true,
  "nit": "4347402554",
  "nombre_institucion": "Emmerich and Sons",
  "pais": "Colombia",
  "fecha_registro": "2024-12-27T00:00:00",
  "activo": true,
  "mensaje": "NIT válido encontrado"
}
```

**Respuesta de error:**
```json
{
  "valid": false,
  "mensaje": "NIT no encontrado en instituciones asociadas"
}
```

### 🏢 Detalles de Institución

#### GET `/api/v1/institution/{nit}`
Obtiene detalles completos de una institución por NIT.

### 🗄️ Gestión de Caché

#### DELETE `/api/v1/cache/{nit}?pais=Colombia`
Limpia caché para un NIT específico.

#### GET `/api/v1/cache/stats`
Obtiene estadísticas del caché Redis.

### ❤️ Health Check

#### GET `/api/v1/health`
```json
{
  "status": "healthy",
  "service": "nit-validation-service",
  "database": "connected",
  "redis": "connected",
  "timestamp": 1694684400.0
}
```

## Configuración

### Variables de Entorno

```bash
# Base de datos PostgreSQL
DATABASE_URL=postgresql+psycopg://nit_service:nit_password@localhost:5432/nit_db

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_TTL=3600  # TTL en segundos (1 hora por defecto)
```

## Instalación y Ejecución

### 1. Preparar entorno local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export DATABASE_URL="postgresql+psycopg://nit_service:nit_password@localhost:5432/nit_db"
export REDIS_URL="redis://localhost:6379/0"
```

### 2. Cargar datos de prueba

```bash
# Ejecutar script de carga de datos
python load_sample_data.py
```

### 3. Ejecutar servicio

```bash
# Modo desarrollo
python main.py

# O con uvicorn
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### 4. Ejecutar con Docker

```bash
# Construir imagen
docker build -t nit-validation-service .

# Ejecutar contenedor
docker run -p 8002:8002 \
  -e DATABASE_URL="postgresql+psycopg://user:pass@host:5432/db" \
  -e REDIS_URL="redis://host:6379/0" \
  nit-validation-service
```

## Pruebas

### Script de pruebas automatizadas

```bash
# Ejecutar suite completa de pruebas
python test_service.py
```

### Pruebas manuales con cURL

```bash
# Health check
curl http://localhost:8002/api/v1/health

# Validar NIT (POST)
curl -X POST http://localhost:8002/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{"nit": "4347402554", "pais": "Colombia"}'

# Validar NIT (GET)
curl http://localhost:8002/api/v1/validate/4347402554?pais=Colombia

# Detalles de institución
curl http://localhost:8002/api/v1/institution/4347402554

# Estadísticas del caché
curl http://localhost:8002/api/v1/cache/stats
```

## Rendimiento

### Objetivos de Latencia

- **P50**: < 50ms (con caché)
- **P95**: < 200ms
- **P99**: < 500ms

### Optimizaciones

1. **Caché Redis**: Resultados de validación con TTL configurable
2. **Índices de BD**: Optimización de consultas por NIT y país
3. **Pool de conexiones**: Configuración optimizada para PostgreSQL
4. **Validación temprana**: Formato de NIT antes de consultar BD

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| `NIT_FORMATO_INVALIDO` | Formato de NIT incorrecto |
| `NIT_NO_ENCONTRADO` | NIT no existe en instituciones asociadas |
| `INSTITUCION_INACTIVA` | Institución encontrada pero inactiva |
| `PAIS_NO_VALIDO` | País no válido o no soportado |
| `ERROR_INTERNO` | Error interno del servicio |
| `CACHE_ERROR` | Error en operaciones de caché |
| `DATABASE_ERROR` | Error de base de datos |

## Datos de Prueba

El archivo `NITValidationData.json` contiene 49 instituciones de prueba:

- **Colombia**: 16 instituciones (9 activas, 7 inactivas)
- **Peru**: 16 instituciones (9 activas, 7 inactivas)  
- **Mexico**: 15 instituciones (6 activas, 9 inactivas)
- **Ecuador**: 2 instituciones (1 activa, 1 inactiva)

### NITs de prueba recomendados:

- `4347402554` (Colombia, activa) ✅
- `1927250080` (Colombia, inactiva) ⚠️
- `7572516483` (Peru, activa) ✅
- `2034955153` (Ecuador, activa) ✅

## Monitoreo

El servicio expone métricas de rendimiento en los logs:

```
INFO: NIT validation completed in 45.23ms
INFO: Cache hit for key: nit_validation:4347402554:COLOMBIA
```

## Contribución

1. Seguir la estructura de microservicios existente
2. Mantener compatibilidad con la tabla `InstitucionesAsociadas`
3. Incluir pruebas para nuevas funcionalidades
4. Documentar cambios en API
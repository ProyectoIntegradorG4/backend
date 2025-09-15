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
CREATE TABLE instituciones_asociadas (
    nit VARCHAR(20) PRIMARY KEY,
    nombre_institucion VARCHAR(200) NOT NULL,
    pais VARCHAR(50) NOT NULL,
    fecha_registro DATE NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true
);
```

**Nota**: La tabla se crea automáticamente al inicializar el servicio, y se puebla con datos de prueba usando el script `load_test_data.py`.

## API Endpoints

### 🔍 Validación de NIT

#### POST `/api/v1/validate`
```json
{
  "nit": "17-767-0400",
  "pais": "Colombia"  // opcional
}
```

#### GET `/api/v1/validate/{nit}?pais=Colombia`

**Respuesta exitosa:**
```json
{
  "valid": true,
  "nit": "17-767-0400",
  "nombre_institucion": "Carter LLC",
  "pais": "Colombia",
  "fecha_registro": "2025-03-12T00:00:00",
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

#### GET `/health`
```json
{
  "status": "healthy",
  "service": "nit-validation-service"
}
```

**Nota**: El endpoint se encuentra en `/health` (no `/api/v1/health` como otros endpoints).

## Configuración

### Variables de Entorno

```bash
# Configuración de PostgreSQL (usando variables separadas)
POSTGRES_DB=nit_db
POSTGRES_USER=nit_service
POSTGRES_PASSWORD=nit_password

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_TTL=3600  # TTL en segundos (1 hora por defecto)
```

**Nota**: El servicio construye automáticamente la URL de conexión PostgreSQL usando las variables de entorno separadas.

## Instalación y Ejecución Completa

### 🚀 Guía Paso a Paso desde Cero

#### Paso 1: Preparar el entorno
```bash
# Clonar repositorio (si no está clonado)
cd c:\MISORepos\MediSupplyApp\backend

# Verificar estructura de archivos
ls -la
```

#### Paso 2: Inicializar servicios de infraestructura
```bash
# Detener y limpiar servicios existentes (si los hay)
docker-compose down -v

# Iniciar PostgreSQL y Redis primero
docker-compose up -d postgres-db redis

# Verificar que PostgreSQL se inicializó correctamente
docker-compose logs postgres-db

# Buscar estos mensajes en los logs:
# - "running /docker-entrypoint-initdb.d/001-init.sql"
# - "CREATE DATABASE" (3 veces)
# - "database system is ready to accept connections"
```

#### Paso 3: Iniciar el servicio NIT Validation
```bash
# Construir e iniciar el servicio
docker-compose up -d nit-validation-service

# Verificar logs del servicio
docker-compose logs nit-validation-service

# Buscar estos mensajes:
# - "Base de datos inicializada correctamente"
# - "Conexión a Redis establecida correctamente"
# - "Uvicorn running on http://0.0.0.0:8002"
```

#### Paso 4: Cargar datos de prueba
```bash
# Navegar al directorio del servicio
cd nit-validation-service

# Instalar psycopg2 para el script de carga (si no está instalado)
pip install psycopg2-binary

# Ejecutar script de carga de datos
python load_test_data.py

# Verificar que se cargaron 50 registros
# El script debe mostrar: "✅ Carga completada: - Registros insertados: 50"
```

#### Paso 5: Verificar funcionamiento

##### 5.1 Health Check
```bash
curl http://localhost:8002/health
# Respuesta esperada: {"status":"healthy","service":"nit-validation-service"}
```

##### 5.2 Validación de NIT activo
```bash
# Con PowerShell:
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/validate" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"nit": "17-767-0400"}'

# Con cURL (bash):
curl -X POST http://localhost:8002/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{"nit": "17-767-0400"}'

# Respuesta esperada:
# {"valid":true,"nit":"17-767-0400","nombre_institucion":"Carter LLC","pais":"Colombia",...}
```

##### 5.3 Validación endpoint GET
```bash
curl http://localhost:8002/api/v1/validate/68-286-6298
# Respuesta esperada: NIT válido de "Senger, Mraz and Conroy"
```

##### 5.4 Consulta de institución
```bash
curl http://localhost:8002/api/v1/institution/61-362-0843
# Respuesta esperada: Datos completos de "Balistreri-Walsh"
```

#### Paso 6: Probar casos de error

##### 6.1 NIT inexistente
```bash
curl -X POST http://localhost:8002/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{"nit": "99-999-9999"}'
# Respuesta esperada: {"valid":false,"mensaje":"NIT no encontrado..."}
```

##### 6.2 NIT inactivo
```bash
curl http://localhost:8002/api/v1/validate/77-285-9581
# Respuesta esperada: {"valid":true,"activo":false,...} (Quigley Inc inactiva)
```

### 🔧 Troubleshooting

#### Problema: Error de autenticación PostgreSQL
```bash
# Verificar que el script de inicialización se ejecutó
docker-compose logs postgres-db | grep "running /docker-entrypoint-initdb.d"

# Si no aparece, reiniciar con volumen limpio:
docker-compose down -v
docker-compose up -d postgres-db redis
```

#### Problema: Cache con datos incorrectos
```bash
# Limpiar cache específico
curl -X DELETE http://localhost:8002/api/v1/cache/177670400

# O reiniciar Redis
docker-compose restart redis
```

#### Problema: Puerto 8002 ocupado
```bash
# Verificar qué proceso usa el puerto
netstat -ano | findstr :8002
# Cambiar puerto en docker-compose.yml o detener proceso existente
```

### 🧪 Ejecución Local (Desarrollo)

#### 1. Configurar entorno Python local
```bash
# Crear ambiente virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export POSTGRES_DB="nit_db"
export POSTGRES_USER="nit_service"
export POSTGRES_PASSWORD="nit_password"
export REDIS_URL="redis://localhost:6379/0"
```

#### 2. Ejecutar servicio local
```bash
# Desde el directorio nit-validation-service
python main.py

# O con uvicorn para desarrollo
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## Pruebas

### Script de pruebas automatizadas

```bash
# Ejecutar suite completa de pruebas
python test_service.py
```

### Pruebas manuales desde PowerShell (Windows)

```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:8002/health"

# Validar NIT activo (POST)
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/validate" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"nit": "17-767-0400"}'

# Validar NIT con país específico
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/validate" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"nit": "61-362-0843", "pais": "Peru"}'

# Validar NIT (GET)
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/validate/68-286-6298"

# Detalles de institución
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/institution/17-767-0400"

# Limpiar cache específico
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/cache/177670400" -Method DELETE

# Estadísticas del caché (si implementado)
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/cache/stats"
```

### Pruebas manuales con cURL (Linux/Mac)

```bash
# Health check
curl http://localhost:8002/health

# Validar NIT (POST)
curl -X POST http://localhost:8002/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{"nit": "17-767-0400", "pais": "Colombia"}'

# Validar NIT (GET)
curl http://localhost:8002/api/v1/validate/68-286-6298?pais=Colombia

# Detalles de institución
curl http://localhost:8002/api/v1/institution/17-767-0400

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

El archivo `NITValidationData.json` contiene 50 instituciones de prueba distribuidas por países:

- **Colombia**: 17 instituciones (10 activas, 7 inactivas)
- **Peru**: 16 instituciones (9 activas, 7 inactivas)  
- **Mexico**: 15 instituciones (6 activas, 9 inactivas)
- **Ecuador**: 2 instituciones (2 activas, 0 inactivas)

### NITs de prueba validados y recomendados:

#### ✅ NITs Activos
- `17-767-0400` (Carter LLC, Colombia) 
- `61-362-0843` (Balistreri-Walsh, Peru)
- `68-286-6298` (Senger, Mraz and Conroy, Colombia)
- `89-078-5710` (Walker and Sons, Peru)
- `94-974-6914` (Pouros-Terry, Colombia)

#### ⚠️ NITs Inactivos  
- `77-285-9581` (Quigley Inc, Mexico)
- `48-036-6903` (Quigley, Raynor and Abernathy, Peru)
- `39-070-9206` (Daniel, Koepp and MacGyver, Colombia)
- `32-435-7287` (Robel-Gleason, Mexico)

#### ❌ NITs para pruebas de error
- `99-999-9999` (No existe)
- `12-345-6789` (No existe)

### Comando para cargar datos de prueba:
```bash
cd nit-validation-service
python load_test_data.py
```

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
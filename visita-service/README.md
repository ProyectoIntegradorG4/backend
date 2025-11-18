# Visita Service (HU-MOV-003)

Microservicio de gestión de visitas y rutas optimizadas para gerentes de cuenta.

## Características

- ✅ CRUD completo de visitas programadas
- ✅ Optimización automática de rutas usando algoritmo Nearest Neighbor
- ✅ Cálculo de distancias y tiempos estimados
- ✅ Integración con cliente-service para validación y geolocalización
- ✅ Tracking de versiones de rutas para cambios
- ✅ API REST con endpoints tipificados
- ✅ Manejo de prioridades de visitas
- ✅ Búsqueda de clientes disponibles en zona

## Estructura del Proyecto

```
visita-service/
├── app/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py          # Configuración PostgreSQL
│   │   └── seed.py                # Datos de prueba
│   ├── models/
│   │   ├── __init__.py
│   │   └── visita.py              # Modelos SQLAlchemy y Pydantic
│   ├── routes/
│   │   ├── __init__.py
│   │   └── visitas.py             # Endpoints API REST
│   ├── services/
│   │   ├── __init__.py
│   │   ├── visita_service.py      # Lógica de negocio
│   │   └── ruta_optimizer.py      # Algoritmo de optimización
│   └── __init__.py
├── main.py                        # Aplicación FastAPI principal
├── requirements.txt               # Dependencias Python
├── Dockerfile                     # Contenedor Docker
├── postman_collection.json        # Colección Postman
└── README.md                      # Este archivo
```

## Modelo de Datos

### Tabla: visitas

Almacena visitas programadas a clientes institucionales.

```sql
CREATE TABLE visitas (
    visita_id SERIAL PRIMARY KEY,
    gerente_id INTEGER NOT NULL,
    cliente_id INTEGER NOT NULL,
    ruta_id INTEGER,
    fecha_visita DATE NOT NULL,
    hora_inicio_sugerida TIME,
    hora_fin_sugerida TIME,
    duracion_estimada_minutos INTEGER DEFAULT 60,
    estado VARCHAR(20) NOT NULL,  -- programada, en_curso, completada, cancelada, reprogramada
    prioridad VARCHAR(10) NOT NULL,  -- alta, media, baja
    orden_en_ruta INTEGER,
    latitud DECIMAL(10,8),  -- Denormalizado del cliente
    longitud DECIMAL(11,8),  -- Denormalizado del cliente
    nombre_cliente VARCHAR(255),
    direccion_cliente TEXT,
    observaciones TEXT,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Tabla: rutas_visitas

Almacena rutas optimizadas calculadas.

```sql
CREATE TABLE rutas_visitas (
    ruta_id SERIAL PRIMARY KEY,
    gerente_id INTEGER NOT NULL,
    fecha_ruta DATE NOT NULL,
    version_ruta INTEGER DEFAULT 1,
    distancia_total_km DECIMAL(10,2),
    tiempo_total_minutos INTEGER,
    hora_inicio_sugerida TIME,
    hora_fin_sugerida TIME,
    origen_ruta VARCHAR(20) NOT NULL,  -- planificada, recalculada, manual
    fecha_calculo TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activa BOOLEAN DEFAULT TRUE
);
```

## Endpoints API

### Gestión de Visitas

#### `POST /api/v1/visitas`
Crear nueva visita programada.

**Request Body:**
```json
{
  "gerente_id": 1,
  "cliente_id": 5,
  "fecha_visita": "2025-11-20",
  "hora_inicio_sugerida": "09:00:00",
  "duracion_estimada_minutos": 60,
  "prioridad": "alta",
  "observaciones": "Primera visita del mes"
}
```

#### `GET /api/v1/visitas/{visita_id}`
Obtener detalle de visita específica.

**Query Params:** `gerente_id` (validación)

#### `PUT /api/v1/visitas/{visita_id}`
Actualizar visita existente.

**Query Params:** `gerente_id`

#### `DELETE /api/v1/visitas/{visita_id}`
Cancelar visita (soft delete).

**Query Params:** `gerente_id`

#### `GET /api/v1/visitas`
Listar visitas programadas para una fecha.

**Query Params:**
- `gerente_id` (requerido)
- `fecha` (requerido, formato: YYYY-MM-DD)
- `estado` (opcional: programada, en_curso, completada, cancelada)

### Rutas Optimizadas (HU-MOV-003)

#### `GET /api/v1/rutas-visitas`
**Obtener ruta optimizada de visitas para una fecha.**

**Query Params:**
- `gerente_id` (requerido)
- `fecha` (requerido, formato: YYYY-MM-DD)

**Response:**
```json
{
  "ruta_id": 1,
  "gerente_id": 1,
  "fecha_ruta": "2025-11-20",
  "version_ruta": 1,
  "distancia_total_km": 45.3,
  "tiempo_total_minutos": 270,
  "hora_inicio_sugerida": "08:00:00",
  "hora_fin_sugerida": "13:30:00",
  "origen_ruta": "planificada",
  "activa": true,
  "cantidad_visitas": 4,
  "visitas": [
    {
      "visita_id": 1,
      "cliente_id": 5,
      "nombre_cliente": "Hospital San José",
      "direccion_cliente": "Calle 10 #20-30",
      "latitud": 4.6533,
      "longitud": -74.0836,
      "hora_inicio_sugerida": "08:00:00",
      "hora_fin_sugerida": "09:00:00",
      "duracion_estimada_minutos": 60,
      "orden_en_ruta": 1,
      "prioridad": "alta",
      "distancia_desde_anterior_km": null,
      "tiempo_viaje_desde_anterior_min": null
    },
    {
      "visita_id": 2,
      "cliente_id": 7,
      "nombre_cliente": "Clínica Los Andes",
      "orden_en_ruta": 2,
      "distancia_desde_anterior_km": 12.5,
      "tiempo_viaje_desde_anterior_min": 25
    }
  ]
}
```

#### `POST /api/v1/rutas-visitas/recalcular`
Recalcular ruta optimizada (incrementa versión).

**Request Body:**
```json
{
  "fecha": "2025-11-20",
  "gerente_id": 1
}
```

#### `GET /api/v1/clientes-disponibles-zona`
Obtener clientes disponibles en zona geográfica.

**Query Params:**
- `gerente_id` (requerido)
- `fecha` (requerido)
- `lat` (requerido, latitud punto de referencia)
- `lng` (requerido, longitud punto de referencia)
- `radio_km` (opcional, default: 20, max: 100)

**Response:**
```json
{
  "fecha": "2025-11-20",
  "gerente_id": 1,
  "punto_referencia": {"lat": 4.6533, "lng": -74.0836},
  "radio_km": 20.0,
  "total": 5,
  "clientes": [
    {
      "cliente_id": 3,
      "nombre_comercial": "IPS Salud Total",
      "direccion": "Calle 50 #45-20",
      "latitud": 4.6697,
      "longitud": -74.0560,
      "distancia_km": 2.5,
      "tiene_visita_programada": false
    }
  ]
}
```

## Algoritmo de Optimización

**Nearest Neighbor (Vecino más Cercano)**

Algoritmo greedy que optimiza la ruta seleccionando siempre la siguiente visita más cercana.

### Características:
- ✅ Tiempo de cálculo: < 2 segundos para hasta 20 visitas
- ✅ Considera prioridades (alta prioridad = 30% menos "distancia efectiva")
- ✅ Calcula distancias usando fórmula de Haversine
- ✅ Estima tiempos de viaje basados en velocidad promedio (30 km/h urbano)
- ✅ Asigna horarios sugeridos automáticamente

### Simplificaciones MVP:
- ❌ No considera tráfico en tiempo real
- ❌ No considera ventanas horarias complejas
- ❌ No considera restricciones de vehículo

## Integración con Otros Servicios

### Cliente Service
- Valida que gerente tenga acceso a clientes
- Obtiene coordenadas (lat/long) de clientes
- Obtiene lista de clientes asignados a gerente

**Endpoints usados:**
- `GET /api/v1/clientes/{cliente_id}` - Obtener datos del cliente
- `GET /api/v1/clientes/mis-cliente-ids?gerente_id={id}` - Lista de cliente_ids del gerente
- `GET /api/v1/clientes/mis-clientes?gerente_id={id}` - Lista completa de clientes

## Tecnologías Utilizadas

- **Framework**: FastAPI 0.104.1
- **Base de datos**: PostgreSQL
- **Driver de BD**: psycopg3
- **ORM**: SQLAlchemy 2.0
- **Validación**: Pydantic 2.5
- **HTTP Client**: httpx (para integración con cliente-service)

## Inicio Rápido

### Prerrequisitos
- Docker & Docker Compose
- PostgreSQL 16
- Python 3.12+ (para desarrollo local)

### Iniciar con Docker Compose

```bash
cd backend
docker-compose up -d visita-service
```

El servicio estará disponible en `http://localhost:8015`

### Desarrollo Local

```bash
cd visita-service

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export DATABASE_URL="postgresql+psycopg://visita_service:visita_password@localhost:5432/visita_db"
export CLIENTE_SERVICE_URL="http://localhost:8013"

# Ejecutar servicio
python main.py
```

## Testing

Ver colección de Postman en `postman_collection.json` con ejemplos de todos los endpoints.

### Flujo de Prueba Básico

1. **Crear visitas** → `POST /api/v1/visitas`
2. **Obtener ruta optimizada** → `GET /api/v1/rutas-visitas?gerente_id=1&fecha=2025-11-20`
3. **Ver clientes cercanos** → `GET /api/v1/clientes-disponibles-zona`
4. **Recalcular ruta** → `POST /api/v1/rutas-visitas/recalcular`

## Health Check

```bash
curl http://localhost:8015/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "visita-service",
  "version": "1.0.0"
}
```

## Datos de Prueba

El servicio incluye seeds automáticos con visitas de ejemplo para:
- Gerente ID 1 (Colombia)
- Fechas: hoy y mañana
- 5 visitas distribuidas en Bogotá, Medellín y Cali

## Logs

El servicio genera logs estructurados con:
- ✅ Creación/actualización de visitas
- ✅ Cálculo y optimización de rutas
- ✅ Integraciones con cliente-service
- ❌ Errores y warnings

## Consideraciones de Performance

- **Pool de conexiones**: 20 base, 40 overflow
- **Timeout de queries**: 30s
- **Objetivo de latencia**: < 2s para consultas, < 5s para recálculos
- **Caché**: Considerar Redis para rutas calculadas (fase 2)

## Roadmap / Mejoras Futuras

- [ ] WebSocket para notificaciones en tiempo real
- [ ] Integración con Google Maps / Mapbox para distancias reales
- [ ] Considerar tráfico en tiempo real
- [ ] Algoritmo más avanzado (Genetic Algorithm, Ant Colony)
- [ ] Caché de rutas con Redis
- [ ] Soporte para múltiples puntos de inicio
- [ ] Restricciones de ventanas horarias


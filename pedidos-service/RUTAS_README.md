# Generación de Rutas de Entrega (HU-WEB-012)

## Descripción

Módulo de optimización de rutas para el microservicio de pedidos. Implementa un algoritmo VRP (Vehicle Routing Problem) simplificado con validaciones de capacidad, cadena de frío y ventanas de tiempo.

## Características Principales

### ✅ Algoritmo de Optimización
- **Nearest Neighbor**: Algoritmo greedy para asignación inicial de rutas
- **Objetivos soportados**:
  - `min_distancia`: Minimizar distancia total recorrida
  - `min_tiempo`: Minimizar tiempo total considerando ventanas

### ✅ Validaciones Implementadas

#### Hard Constraints (Bloquean operación)
- ✅ Capacidad de volumen y peso
- ✅ Cadena de frío (pedidos con frío solo en vehículos refrigerados)
- ✅ Ventanas de tiempo en recálculo manual
- ✅ Duración máxima de ruta

#### Soft Constraints (Generan warnings)
- ⚠️ Ventanas de tiempo en generación automática
- ⚠️ Duración excedida (informativa)
- ⚠️ Pedidos no asignados

### ✅ Performance (SLAs)
- **Generación**: ≤ 3 segundos para 10 vehículos + 100 pedidos
- **Recálculo**: ≤ 1 segundo
- **Límites MVP**: Máximo 10 vehículos y 100 pedidos por operación

## Arquitectura

```
pedidos-service/
├── app/
│   ├── models/
│   │   └── ruta.py          # Modelos SQLAlchemy (Vehiculo, Ruta, Parada)
│   ├── schemas/
│   │   └── ruta.py          # Schemas Pydantic con validación
│   ├── services/
│   │   └── rutas.py         # Lógica de negocio (OptimizadorRutas, RutasService)
│   └── routes/
│       └── rutas.py         # Endpoints FastAPI
└── test_rutas.py            # Script de pruebas
```

## Modelos de Datos

### Vehiculo
```python
{
  "vehiculo_id": "VEH-001",
  "nombre": "Camión Refrigerado Grande",
  "capacidad_volumen": 50.0,    # m³
  "capacidad_peso": 1000.0,     # kg
  "cadena_frio": true,
  "depot_latitud": 4.6097,
  "depot_longitud": -74.0817,
  "depot_direccion": "Calle 26 #68-90",
  "duracion_maxima_minutos": 480,
  "activo": true
}
```

### Ruta
```python
{
  "ruta_id": "uuid",
  "vehiculo_id": "VEH-001",
  "estado": "planificada",       # borrador|planificada|en_curso|completada|cancelada
  "distancia_total_km": 45.3,
  "duracion_total_minutos": 180,
  "volumen_utilizado": 25.5,
  "peso_utilizado": 450.0,
  "secuencia_pedidos": ["PED-1", "PED-2"],
  "etas": {"PED-1": "09:30", "PED-2": "10:15"},
  "advertencias": []
}
```

### Parada
```python
{
  "parada_id": "uuid",
  "ruta_id": "uuid",
  "pedido_id": "PED-001",
  "orden": 1,
  "latitud": 4.6351,
  "longitud": -74.0703,
  "ventana_inicio": "08:00",
  "ventana_fin": "12:00",
  "eta": "09:30",
  "tiempo_servicio_minutos": 15,
  "cumple_ventana": true
}
```

## Endpoints API

### 1. Generar Rutas
**POST** `/api/v1/logistica/rutas/generar`

Genera rutas optimizadas para un conjunto de pedidos y vehículos.

**Headers requeridos:**
```
usuario-id: 1
rol-usuario: Supervisor de Logística
nit-usuario: 1234567890
```

**Request body:**
```json
{
  "objetivo": "min_distancia",
  "vehiculos": [
    {
      "id": "VEH-001",
      "capacidad_volumen": 50.0,
      "capacidad_peso": 1000.0,
      "cadena_frio": true,
      "depot": {"lat": 4.6097, "lon": -74.0817},
      "duracion_maxima_minutos": 480
    }
  ],
  "pedidos": [
    {
      "id": "PED-001",
      "lat": 4.6351,
      "lon": -74.0703,
      "ventana_inicio": "08:00",
      "ventana_fin": "12:00",
      "tiempo_servicio_minutos": 15,
      "requiere_frio": true,
      "volumen": 5.0,
      "peso": 50.0
    }
  ],
  "limites": {
    "max_distancia_km": 100.0,
    "max_duracion_minutos": 480,
    "considerar_trafico": false
  }
}
```

**Response (200 OK):**
```json
{
  "rutas": [
    {
      "vehiculo_id": "VEH-001",
      "orden": ["DEPOT", "PED-001", "PED-002", "DEPOT"],
      "paradas": [
        {
          "pedido_id": "PED-001",
          "orden": 1,
          "eta": "09:30",
          "latitud": 4.6351,
          "longitud": -74.0703,
          "ventana_inicio": "08:00",
          "ventana_fin": "12:00",
          "cumple_ventana": true,
          "tiempo_servicio_minutos": 15
        }
      ],
      "distancia_km": 45.3,
      "duracion_minutos": 180,
      "uso_capacidad": {
        "volumen": 25.5,
        "peso": 450.0,
        "porcentaje": 75.5
      }
    }
  ],
  "warnings": [],
  "tiempo_calculo_ms": 1250
}
```

**Errores:**
- `400 Bad Request`: Validación fallida (más de 100 pedidos, más de 10 vehículos, pedido con frío en vehículo sin refrigeración, etc.)
- `403 Forbidden`: Usuario no tiene rol "Supervisor de Logística"
- `500 Internal Server Error`: Error del servidor

---

### 2. Recalcular Ruta
**POST** `/api/v1/logistica/rutas/recalcular`

Recalcula una ruta tras ajuste manual de la secuencia (drag-and-drop en UI).

**Headers requeridos:**
```
usuario-id: 1
rol-usuario: Supervisor de Logística
nit-usuario: 1234567890
```

**Request body:**
```json
{
  "ruta_id": "550e8400-e29b-41d4-a716-446655440000",
  "nueva_secuencia": ["PED-002", "PED-001", "PED-003"]
}
```

**Response (200 OK):**
```json
{
  "ruta": {
    "vehiculo_id": "VEH-001",
    "orden": ["DEPOT", "PED-002", "PED-001", "DEPOT"],
    "paradas": [...],
    "distancia_km": 48.1,
    "duracion_minutos": 190,
    "uso_capacidad": {...}
  },
  "warnings": [],
  "tiempo_calculo_ms": 450
}
```

**Errores:**
- `400 Bad Request`: Nueva secuencia viola ventanas de tiempo o duración máxima (hard constraints)
- `404 Not Found`: Ruta no encontrada

---

### 3. Crear Vehículo
**POST** `/api/v1/logistica/vehiculos`

Registra un nuevo vehículo en el sistema.

**Request body:**
```json
{
  "vehiculo_id": "VEH-TEST-001",
  "nombre": "Camión Refrigerado Grande",
  "capacidad_volumen": 60.0,
  "capacidad_peso": 1500.0,
  "cadena_frio": true,
  "depot_latitud": 4.6097,
  "depot_longitud": -74.0817,
  "depot_direccion": "Calle 26 #68-90, Bogotá",
  "duracion_maxima_minutos": 540
}
```

**Response (201 Created):**
```json
{
  "vehiculo_id": "VEH-TEST-001",
  "nombre": "Camión Refrigerado Grande",
  "capacidad_volumen": 60.0,
  "capacidad_peso": 1500.0,
  "cadena_frio": true,
  "depot_latitud": 4.6097,
  "depot_longitud": -74.0817,
  "depot_direccion": "Calle 26 #68-90, Bogotá",
  "duracion_maxima_minutos": 540,
  "activo": true
}
```

---

### 4. Listar Vehículos
**GET** `/api/v1/logistica/vehiculos?solo_activos=true`

Lista todos los vehículos registrados.

**Response (200 OK):**
```json
{
  "total": 2,
  "vehiculos": [
    {
      "vehiculo_id": "VEH-001",
      "nombre": "Camión Refrigerado Grande",
      ...
    }
  ]
}
```

## Algoritmo de Optimización

### Nearest Neighbor (Greedy)

1. **Asignación de pedidos a vehículos:**
   - Itera sobre vehículos disponibles
   - Para cada vehículo, asigna pedidos que cumplan:
     - Capacidad disponible (volumen y peso)
     - Cadena de frío compatible
   - Usa estrategia FIFO con validación

2. **Generación de secuencia:**
   - Inicia en DEPOT
   - Selecciona pedido más cercano no visitado
   - Si objetivo es `min_tiempo`, penaliza pedidos fuera de ventana
   - Calcula ETA sumando tiempo de viaje + tiempo de servicio
   - Valida ventana de tiempo (soft en generación, hard en recálculo)
   - Retorna a DEPOT

3. **Cálculo de distancias:**
   - Fórmula de Haversine para coordenadas geográficas
   - Velocidad promedio: 30 km/h (ajustable con factor de tráfico)

4. **Validaciones en cada paso:**
   - Capacidad acumulada vs. límite del vehículo
   - Requiere frío → vehículo debe tener cadena_frio=true
   - Duración total vs. duracion_maxima_minutos

## Pruebas

### Script de Prueba Manual
```bash
# Iniciar el servicio
python main.py

# En otra terminal, ejecutar pruebas
python test_rutas.py
```

El script `test_rutas.py` prueba:
- ✅ Health check del módulo
- ✅ Generación de rutas con 2 vehículos y 5 pedidos
- ✅ Validación de warnings (ventanas de tiempo)
- ✅ Cálculo de métricas (distancia, duración, uso de capacidad)

### Casos de Prueba Recomendados

1. **Happy Path:**
   - 2 vehículos, 5 pedidos compatibles
   - Todos con ventanas de tiempo amplias
   - Sin exceder capacidades

2. **Cadena de Frío:**
   - Pedido con `requiere_frio: true`
   - Vehículo 1: `cadena_frio: true` ✅
   - Vehículo 2: `cadena_frio: false` → warning

3. **Exceso de Capacidad:**
   - Pedidos totales superan capacidad de vehículos
   - Resultado: algunos pedidos quedan sin asignar → warning

4. **Ventanas de Tiempo:**
   - Pedido con ventana `08:00-09:00`
   - Secuencia genera ETA `10:30`
   - Resultado: `cumple_ventana: false` + warning

5. **Recálculo Inválido:**
   - Ruta existente con secuencia válida
   - Nueva secuencia viola ventana de tiempo
   - Resultado: `400 Bad Request` (hard constraint)

## Configuración

### Variables de Entorno
```bash
# Base de datos (hereda de pedidos-service)
PEDIDOS_DB_USER=pedidos_service
PEDIDOS_DB_PASSWORD=pedidos_password
POSTGRES_HOST=postgres-db
POSTGRES_PORT=5432
PEDIDOS_DB_NAME=pedidos_db

# Puerto del servicio
PEDIDOS_SERVICE_PORT=8007
```

### Tablas de Base de Datos

Al iniciar el servicio, se crean automáticamente:
- `vehiculos`: Datos maestros de vehículos
- `rutas`: Rutas generadas con métricas
- `paradas`: Detalle de cada parada en las rutas

## Limitaciones del MVP

### Funcionalidad No Implementada (Fuera de Scope)
- ❌ Algoritmos avanzados (Christofides, Simulated Annealing, Genetic Algorithms)
- ❌ Optimización global multi-vehículo
- ❌ Integración con APIs de mapas en tiempo real (Google Maps, Mapbox)
- ❌ Tracking en tiempo real de vehículos
- ❌ Notificaciones push a conductores
- ❌ Re-optimización automática por cambios de tráfico
- ❌ Multi-depot (todos los vehículos comparten depot)

### Limitaciones Técnicas
- **Tamaño del problema**: Máximo 10 vehículos y 100 pedidos
- **Algoritmo**: Greedy (no garantiza solución óptima global)
- **Distancias**: Haversine (línea recta, no vías reales)
- **Velocidad**: Constante 30 km/h (no considera tipo de vía)
- **Tráfico**: Factor simple (70% de velocidad), no datos reales

### Mejoras Futuras Sugeridas
1. **Fase 2 - Algoritmos Avanzados:**
   - OR-Tools de Google para VRP
   - Integración con APIs de ruteo (Mapbox Directions)
   - Optimización multi-criterio (distancia + tiempo + costo)

2. **Fase 3 - Tracking y Ajustes:**
   - GPS en tiempo real vía WebSockets
   - Re-optimización automática por retrasos
   - Notificaciones a clientes con ETA actualizado

3. **Fase 4 - Inteligencia:**
   - Machine Learning para predecir tiempos de servicio
   - Análisis histórico para mejorar rutas
   - A/B testing de algoritmos

## Monitoreo y Logs

### Logs Importantes
```python
logger.info("Rutas generadas en {tiempo_ms}ms: {n_rutas} rutas para {n_pedidos} pedidos")
logger.warning("Error de validación: {error}")
logger.error("Error inesperado: {error}", exc_info=True)
```

### Métricas Clave
- `tiempo_calculo_ms`: Debe estar bajo SLA (3000ms generación, 1000ms recálculo)
- `warnings`: Indica violaciones de soft constraints
- `uso_capacidad.porcentaje`: Optimización del uso de vehículos

## Soporte y Contacto

Para preguntas sobre la implementación:
- **Documentación técnica**: Ver `app/services/rutas.py` (comentarios inline)
- **API Docs**: http://localhost:8007/docs (Swagger UI)
- **Redoc**: http://localhost:8007/redoc

---

**Versión**: 1.0.0  
**Fecha**: Diciembre 2024  
**Historia de Usuario**: HU-WEB-012 - Generación de Rutas de Entrega

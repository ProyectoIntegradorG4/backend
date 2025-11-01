# 📦 Pedidos Service

Microservicio de gestión de pedidos con validación en tiempo real del inventario, soporte para múltiples usuarios y generación automática de números secuenciales.

## 📋 Descripción General

El servicio `pedidos-service` (puerto **8007**) gestiona la creación, consulta y administración de pedidos. Proporciona:

- ✅ **Validación en tiempo real** del inventario consultando `product-service`
- ✅ **Soporte para dos tipos de usuarios**: Cliente Institucional y Gerente/Admin
- ✅ **Gestión automática del NIT**: se recibe en el body del request y se asocia correctamente según el rol
- ✅ **Generación de números únicos**: PED-000001, PED-000002, etc.
- ✅ **Seguimiento de estado**: 7 estados posibles (pendiente, confirmado, enviado, entregado, etc.)
- ✅ **Snapshots de datos**: precios y disponibilidad se capturan al momento del pedido

---

## 🔧 Requisitos Técnicos

| Componente | Versión |
|-----------|---------|
| Python | 3.11+ |
| PostgreSQL | 16 |
| FastAPI | 0.104.1 |
| SQLAlchemy | 2.0.23 |
| Pydantic | 2.5.0 |
| pytest | 7.4.0 |

---

## ⚙️ Instalación y Ejecución

### 🐳 Con Docker Compose (Recomendado)

```bash
# Desde la carpeta raíz del backend
docker-compose up -d pedidos-service

# Ver logs
docker-compose logs pedidos-service -f

# Verificar salud del servicio
curl http://localhost:8007/health
```

### 🏠 Localmente

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export PEDIDOS_DATABASE_URL="postgresql+psycopg://pedidos_service:pedidos_password@localhost:5432/pedidos_db"

# Ejecutar servidor
python main.py
```

### 📦 Con Docker

```bash
docker build -t pedidos-service .
docker run -p 8007:8007 \
  -e PEDIDOS_DATABASE_URL="postgresql+psycopg://..." \
  pedidos-service
```

---

## 🌍 Variables de Entorno

```env
# Base de datos
PEDIDOS_DB_NAME=pedidos_db
PEDIDOS_DB_USER=pedidos_service
PEDIDOS_DB_PASSWORD=pedidos_password
PEDIDOS_DATABASE_URL=postgresql+psycopg://pedidos_service:pedidos_password@postgres-db:5432/pedidos_db

# Puerto del servicio
PEDIDOS_SERVICE_PORT=8007

# URLs de servicios dependientes
PRODUCT_SERVICE_URL=http://product-service:8005
NIT_VALIDATION_SERVICE_URL=http://nit-validation-service:8002
```

---

## 📡 Endpoints Disponibles

### 1. ✅ POST `/api/v1/pedidos/` - Crear Pedido

Crea un nuevo pedido con validación de inventario en tiempo real.

**Headers Requeridos:**
```http
usuario-id: <integer>           # ID del usuario
rol-usuario: <string>           # "usuario_institucional" o "admin"
Content-Type: application/json
```

**Body Requerido:**
```json
{
  "nit": "901234567",
  "productos": [
    {
      "producto_id": "550e8400-e29b-41d4-a716-446655440000",
      "cantidad_solicitada": 10
    }
  ],
  "observaciones": "Campo opcional"
}
```

**Response (200 - Éxito):**
```json
{
  "exito": true,
  "numero_pedido": "PED-000001",
  "mensaje": "Pedido creado exitosamente",
  "pedido": {
    "pedido_id": "abc123...",
    "numero_pedido": "PED-000001",
    "nit": "901234567",
    "usuario_id": 1,
    "rol_usuario": "usuario_institucional",
    "estado": "pendiente",
    "monto_total": 500000.0,
    "detalles": [...]
  }
}
```

**Response (400 - Inventario Insuficiente):**
```json
{
  "error": "INVENTARIO_INSUFICIENTE",
  "mensaje": "Inventario insuficiente para uno o más productos",
  "sugerencias": [
    {
      "producto_id": "...",
      "cantidad_maxima": 5,
      "cantidad_solicitada": 10
    }
  ]
}
```

---

### 2. ✅ GET `/api/v1/pedidos/` - Listar Pedidos

Lista pedidos con filtros opcionales y paginación.

**Query Parameters:**
```
pagina=1              # Número de página (default: 1)
por_pagina=10         # Resultados por página (default: 10)
nit=900123456         # (Opcional) Filtrar por NIT
usuario_id=1          # (Opcional) Filtrar por usuario
estado=pendiente      # (Opcional) Filtrar por estado
```

**Ejemplos:**
```
GET /api/v1/pedidos/?pagina=1&por_pagina=10
GET /api/v1/pedidos/?nit=900123456
GET /api/v1/pedidos/?usuario_id=1&estado=confirmado
```

**Response (200):**
```json
{
  "pedidos": [
    {
      "pedido_id": "abc123...",
      "numero_pedido": "PED-000001",
      "nit": "900123456",
      "usuario_id": 1,
      "estado": "pendiente",
      "monto_total": 500000.0,
      "detalles": [...]
    }
  ],
  "total": 1,
  "pagina": 1,
  "por_pagina": 10
}
```

---

### 3. ✅ GET `/api/v1/pedidos/{pedido_id}` - Obtener Pedido

Retorna los detalles completos de un pedido específico.

**Response (200):**
```json
{
  "pedido_id": "550e8400-e29b-41d4-a716-446655440000",
  "numero_pedido": "PED-000001",
  "nit": "900123456",
  "usuario_id": 1,
  "rol_usuario": "usuario_institucional",
  "estado": "pendiente",
  "monto_total": 500000.0,
  "detalles": [...]
}
```

---

### 4. ✅ POST `/api/v1/pedidos/validar-inventario` - Validar Inventario

Valida el inventario **sin crear** el pedido. Útil para verificar disponibilidad antes de confirmar.

**Body:**
```json
{
  "nit": "900123456",
  "productos": [
    {"producto_id": "...", "cantidad_solicitada": 5}
  ]
}
```

**Response (200):**
```json
{
  "valido": true,
  "validaciones": [
    {
      "producto_id": "550e8400-...",
      "disponible": true,
      "cantidad_disponible": 100,
      "cantidad_solicitada": 5,
      "mensaje": "Inventario disponible"
    }
  ]
}
```

---

### 5. ✅ PUT `/api/v1/pedidos/{pedido_id}/estado` - Actualizar Estado

Actualiza el estado de un pedido (solo admin).

**Headers:**
```
rol-usuario: admin              # Solo admins pueden actualizar
```

**Body:**
```json
{
  "nuevo_estado": "confirmado",
  "observaciones": "Pedido confirmado por gerente"
}
```

**Estados Válidos:**
```
pendiente    → confirmado      (Admin confirma)
confirmado   → en_proceso      (Sistema/Admin)
en_proceso   → enviado         (Logística)
enviado      → entregado       (Cliente/Sistema)
*            → cancelado       (Cualquier estado)
*            → rechazado       (Cualquier estado)
```

---

### 6. ✅ GET `/health` - Health Check

Verifica que el servicio esté saludable.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "pedidos-service"
}
```

---

## 🔑 Gestión del NIT

### Características Clave

El NIT se **recibe en el body del request** (no en headers) y se asocia automáticamente según el rol del usuario:

### Caso 1: Usuario Institucional

```http
POST /api/v1/pedidos/

Headers:
  usuario-id: 1
  rol-usuario: usuario_institucional

Body:
{
  "nit": "901234567",         ← Su propio NIT
  "productos": [...]
}

Resultado en BD:
  usuario_id: 1
  nit: "901234567"            ← Guardado correctamente
  rol_usuario: "usuario_institucional"
```

**Significado:** El usuario crea un pedido para su institución.

### Caso 2: Gerente/Admin

```http
POST /api/v1/pedidos/

Headers:
  usuario-id: 2
  rol-usuario: admin

Body:
{
  "nit": "800123456",         ← NIT del cliente
  "productos": [...]
}

Resultado en BD:
  usuario_id: 2               ← ID del gerente
  nit: "800123456"            ← NIT del cliente
  rol_usuario: "admin"
```

**Significado:** El gerente crea un pedido para un cliente específico.

---

## 📊 Estructura de la Base de Datos

### Tabla: `pedidos`

```sql
pedido_id (UUID)              PRIMARY KEY
usuario_id (INTEGER)          Quién creó el pedido
nit (VARCHAR 20)              Para quién es el pedido
rol_usuario (VARCHAR 50)      Rol del usuario
numero_pedido (VARCHAR 50)    UNIQUE - PED-000001
estado (ENUM)                 pendiente, confirmado, etc.
monto_total (FLOAT)           Suma de detalles
fecha_creacion (TIMESTAMP)    Creado
fecha_actualizacion (TIMESTAMP) Actualizado
observaciones (TEXT)          Notas opcionales
```

### Tabla: `detalles_pedido`

```sql
detalle_id (UUID)                 PRIMARY KEY
pedido_id (UUID)                  FK → pedidos
producto_id (UUID)                ID del producto
nombre_producto (VARCHAR 255)     Snapshot del nombre
cantidad_solicitada (INTEGER)     Cantidad pedida
cantidad_disponible_al_momento (INTEGER)  Disponibilidad en ese momento
precio_unitario (FLOAT)           Snapshot del precio
subtotal (FLOAT)                  precio * cantidad
fecha_agregado (TIMESTAMP)        Cuándo se agregó
```

---

## 🧪 Pruebas

### Ejecutar Tests de Integración

```bash
# Todos los tests
docker exec pedidos-service python -m pytest tests/test_integracion_completa.py -v

# Con salida detallada
docker exec pedidos-service python -m pytest tests/test_integracion_completa.py -v -s

# Test específico
docker exec pedidos-service python -m pytest \
  tests/test_integracion_completa.py::TestIntegracionCompleta::test_crear_usuario_y_pedido_con_3_productos \
  -v -s
```

### Resultado Esperado

```
test_crear_usuario_y_pedido_con_3_productos PASSED
test_crear_pedido_gerente_con_3_productos PASSED
test_listar_pedidos_del_usuario PASSED

======================== 3 passed in 0.23s =========================
```

### Ejecutar con Cobertura

```bash
docker exec pedidos-service python -m pytest tests/ --cov=app --cov-report=html
```

---

## 📦 Postman Collection

**Archivo:** `pedidos-service/postman_collection.json`

**8 Requests Pre-configurados:**

| # | Nombre | Método | Descripción |
|---|--------|--------|-------------|
| 1 | Crear Pedido - Gerente | POST | Test como admin |
| 2 | Crear Pedido - Cliente | POST | Test como usuario institucional |
| 3 | Obtener Pedido | GET | Recuperar pedido específico |
| 4 | Listar Pedidos | GET | Listar todos con paginación |
| 5 | Listar por NIT | GET | Filtrar por NIT |
| 6 | Validar Inventario | POST | Validar sin crear |
| 7 | Actualizar Estado | PUT | Cambiar estado |
| 8 | Health Check | GET | Verificar servicio |

### Importar en Postman

1. Abrir Postman
2. Click en **Import**
3. Seleccionar `pedidos-service/postman_collection.json`
4. Click en **Import**
5. Los 8 requests aparecerán en la colección

---

## 🔄 Integración con Otros Servicios

### Product Service (8005)

- **GET** `/api/productos/{producto_id}/inventario` → Obtiene `{cantidad_disponible, precio}`
- **GET** `/api/productos/{producto_id}` → Obtiene información completa

**Uso:** El pedidos-service consulta en tiempo real antes de crear pedido.

### User Service (8001)

- `usuario_id` y `rol_usuario` se obtienen del header
- Futuro: incluir NIT en JWT token para validación adicional

### NIT Validation Service (8002)

- Futuro: Validar que el NIT exista en `nit_db`

---

## 📊 Datos de Prueba

### NITs Válidos (en BD)

```
901234567   Clínica Central (Colombia)
800123456   Hospital Universitario (Colombia)
900987654   Centro Médico Los Andes (Colombia)
```

### Productos de Ejemplo

| Producto | Precio | Stock | Categoría |
|----------|--------|-------|-----------|
| Vacuna COVID-19 | $50,000 | 100 | Vacunas |
| Ibuprofeno 400mg | $5,000 | 500 | Analgésicos |
| Jeringa estéril 10ml | $2,000 | 1,000 | Dispositivos |
| Guantes de látex | $15,000 | 300 | Dispositivos |

---

## 🎯 Casos de Uso Completamente Implementados

### ✅ Gerente de Cuenta - Crear Pedido
- Crear pedido con productos en inventario
- Validar inventario en tiempo real
- Mostrar error si inventario insuficiente
- Sugerir cantidades máximas disponibles

### ✅ Cliente Institucional - Crear Pedido
- Crear pedido asociado a su NIT
- Validar disponibilidad antes de confirmar
- Mostrar error si producto sin disponibilidad
- Mostrar cantidades máximas disponibles

### ✅ Listar Pedidos
- Filtrar por NIT, usuario_id, estado
- Paginación automática
- Snapshots de datos históricos

### ✅ Validar Inventario
- Validar sin crear pedido
- Útil para frontend: verificar disponibilidad

---

## 🚀 Próximas Mejoras Recomendadas

### 1. Validación de NIT (Prioridad: Media)

```python
# Verificar que el NIT existe antes de crear pedido
if not await validar_nit_existe(request.nit):
    raise HTTPException("NIT no registrado")
```

### 2. Caché de Productos (Prioridad: Baja)

```python
# Cachear lista de productos para reducir llamadas
# Redis cache con TTL de 5 minutos
```

### 3. Notificaciones (Prioridad: Media)

```python
# Enviar email cuando pedido es confirmado/entregado
# Integrar con email-service
```

### 4. Reporte de Ventas (Prioridad: Media)

```python
# Endpoint para reportes de ventas por período
# GET /api/v1/pedidos/reportes/ventas?desde=...&hasta=...
```

---

## 🔍 Troubleshooting

### Problema: "pedidos-service is unhealthy"

```bash
# Ver logs del servicio
docker-compose logs pedidos-service

# Probar health check
curl http://localhost:8007/health
```

### Problema: "INVENTARIO_INSUFICIENTE"

```bash
# Revisar si product-service está disponible
curl http://localhost:8005/health

# Verificar datos de inventario
curl http://localhost:8005/api/productos/{id}/inventario
```

### Problema: Error de BD (pedidos_db)

```bash
# Ver estado de postgres
docker-compose ps postgres-db

# Reiniciar BD y servicio
docker-compose down -v
docker-compose up -d
```

---

## 📝 Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `app/models/pedido.py` | Modelos SQLAlchemy (Pedido, DetallePedido) |
| `app/routes/pedidos.py` | Endpoints FastAPI (6 endpoints) |
| `app/services/pedidos.py` | Lógica de negocio (400+ líneas) |
| `app/schemas/` | Validación Pydantic (13 schemas) |
| `tests/test_integracion_completa.py` | Tests de integración (3 casos) |
| `conftest.py` | Configuración pytest y fixtures |
| `requirements.txt` | Dependencias Python |
| `Dockerfile` | Imagen Docker |
| `postman_collection.json` | 8 requests de prueba |

---

## ✅ Checklist - Estado Actual

- ✅ 6 endpoints implementados y funcionales
- ✅ NIT se recibe en body y se asocia correctamente
- ✅ Usuario Institucional: su propio NIT
- ✅ Admin/Gerente: NIT del cliente
- ✅ Validación de inventario en tiempo real
- ✅ Generación automática de números (PED-000001)
- ✅ 3 tests de integración PASANDO
- ✅ 8 requests en Postman collection
- ✅ Todos los servicios HEALTHY
- ✅ Base de datos correctamente inicializada
- ✅ UUID compatible con SQLite + PostgreSQL

---

## 📞 Referencias Rápidas

### Ejecutar Servidor
```bash
docker-compose up -d pedidos-service
```

### Ver Logs
```bash
docker-compose logs pedidos-service -f
```

### Probar Servicio
```bash
curl http://localhost:8007/health
```

### Ejecutar Tests
```bash
docker exec pedidos-service python -m pytest tests/test_integracion_completa.py -v
```

### Importar en Postman
```
Archivo: pedidos-service/postman_collection.json
8 requests pre-configurados listos para usar
```

---

## 📄 Licencia

Mismo que el proyecto principal.

---

**Última actualización:** 26 de octubre de 2025
**Estado:** ✅ COMPLETAMENTE FUNCIONAL
**Rama:** feature/sprint2

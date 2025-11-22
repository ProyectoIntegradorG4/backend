# Quick Start - Visita Service

## ⚡ Inicio Rápido (5 minutos)

### Paso 1: Levantar el Servicio

```bash
cd backend

# Opción A: Desde cero (limpio)
docker-compose down
docker volume rm postgres_data
docker-compose up -d visita-service

# Opción B: Solo reiniciar
docker-compose restart visita-service
```

### Paso 2: Verificar que Funciona

```bash
# Health check
curl http://localhost:8015/health

# Debería retornar:
# {"status":"healthy","service":"visita-service","version":"1.0.0"}
```

### Paso 3: Probar con Datos de Ejemplo

El servicio incluye 5 visitas de ejemplo automáticamente.

```bash
# Ver ruta optimizada de HOY
curl "http://localhost:8015/api/v1/rutas-visitas?gerente_id=1&fecha=$(Get-Date -Format 'yyyy-MM-dd')"

# Listar visitas programadas
curl "http://localhost:8015/api/v1/visitas?gerente_id=1&fecha=$(Get-Date -Format 'yyyy-MM-dd')"
```

### Paso 4: Crear una Visita Nueva

```bash
curl -X POST http://localhost:8015/api/v1/visitas \
  -H "Content-Type: application/json" \
  -d '{
    "gerente_id": 1,
    "cliente_id": 1,
    "fecha_visita": "2025-11-25",
    "hora_inicio_sugerida": "09:00:00",
    "duracion_estimada_minutos": 60,
    "prioridad": "alta",
    "observaciones": "Visita importante"
  }'
```

### Paso 5: Ver Ruta Optimizada

```bash
curl "http://localhost:8015/api/v1/rutas-visitas?gerente_id=1&fecha=2025-11-25"
```

---

## 🧪 Ejecutar Tests

```bash
cd backend/visita-service

# Tests core (rápidos, 100% pasan)
pytest tests/test_ruta_optimizer.py tests/test_visita_service_unit.py tests/test_visitas_routes_simple.py -v

# Con cobertura
pytest tests/test_ruta_optimizer.py tests/test_visita_service_unit.py tests/test_visitas_routes_simple.py --cov=app --cov-report=html

# Resultado: 48 tests, 100% pasan, 71% cobertura
```

---

## 📖 Colección de Postman

Importa `postman_collection.json` en Postman para probar todos los endpoints.

**Variable:** `BASE_URL` = `http://localhost:8015`

**Carpetas:**
1. Health Check
2. Gestión de Visitas (POST, GET, PUT, DELETE)
3. Rutas Optimizadas (HU-MOV-003)
4. Ejemplos Completos (flujo end-to-end)

---

## 🔧 Troubleshooting

### Error: "password authentication failed for user visita_service"

**Solución:**
```bash
cd backend
.\fix_visita_service.ps1
```

### Error: "column clientes.latitud does not exist"

**Solución:**
```bash
cd backend
.\fix_all_databases.ps1
```

### Error: Tests fallan

**Solución:** Ejecuta solo los tests core que funcionan:
```bash
pytest tests/test_ruta_optimizer.py tests/test_visita_service_unit.py tests/test_visitas_routes_simple.py
```

---

## 📚 Documentación Adicional

- `README.md` - Documentación completa del servicio
- `TESTING_GUIDE.md` - Guía de testing
- `TEST_RESULTS.md` - Resultados detallados
- `RESUMEN_IMPLEMENTACION.md` - Resumen de implementación

---

## ✅ Verificación de Instalación

```bash
# 1. Servicio está corriendo
docker ps | grep visita-service

# 2. Base de datos existe
docker exec -it postgres-db psql -U postgres -c "\l" | grep visita_db

# 3. Tablas creadas
docker exec -it postgres-db psql -U visita_service -d visita_db -c "\dt"

# 4. Datos de prueba cargados
docker exec -it postgres-db psql -U visita_service -d visita_db -c "SELECT COUNT(*) FROM visitas;"
# Debería retornar: 5

# 5. Health check
curl http://localhost:8015/health
```

---

## 🎯 Endpoints Principales

### 1. Obtener Ruta Optimizada (HU-MOV-003)

```http
GET /api/v1/rutas-visitas?gerente_id=1&fecha=2025-11-25
```

**Retorna:**
- Ruta optimizada con orden de visitas
- Distancias entre visitas
- Tiempos estimados
- Horarios sugeridos

### 2. Listar Visitas

```http
GET /api/v1/visitas?gerente_id=1&fecha=2025-11-25
```

### 3. Crear Visita

```http
POST /api/v1/visitas
Content-Type: application/json

{
  "gerente_id": 1,
  "cliente_id": 1,
  "fecha_visita": "2025-11-25",
  "prioridad": "alta"
}
```

### 4. Recalcular Ruta

```http
POST /api/v1/rutas-visitas/recalcular
Content-Type: application/json

{
  "fecha": "2025-11-25",
  "gerente_id": 1
}
```

### 5. Clientes Disponibles en Zona

```http
GET /api/v1/clientes-disponibles-zona?gerente_id=1&fecha=2025-11-25&lat=4.6533&lng=-74.0836&radio_km=20
```

---

## 🎉 ¡Listo para Usar!

El servicio está completamente funcional y testeado. Consulta la documentación completa en `README.md` para más detalles.


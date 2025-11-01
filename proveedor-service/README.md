# Proveedor Service

Microservicio de gestión de proveedores médicos para el sistema de registro de productos médicos.

## Descripción

Este servicio gestiona el registro y administración de proveedores de productos médicos, incluyendo laboratorios, distribuidores e importadores de diferentes países latinoamericanos.

## Características

- ✅ CRUD completo de proveedores
- ✅ Validación de NIT único
- ✅ Validación de email único
- ✅ Filtrado y búsqueda avanzada
- ✅ Control de versiones de registros
- ✅ Auditoría de cambios (created_at, updated_at)
- ✅ Soporte para múltiples países
- ✅ Gestión de certificaciones
- ✅ Calificación y tiempo de entrega promedio

## Especificación de Base de Datos

### Tabla: `proveedores`

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `proveedor_id` | UUID | PK | Identificador único (generado por backend) |
| `razon_social` | VARCHAR(255) | NOT NULL | Nombre legal del proveedor |
| `nit` | VARCHAR(50) | NOT NULL, UK | Número de identificación tributaria |
| `tipo_proveedor` | ENUM | NOT NULL | laboratorio, distribuidor, importador |
| `email` | VARCHAR(255) | NOT NULL, UK | Correo electrónico único |
| `telefono` | VARCHAR(20) | NOT NULL | Número de contacto |
| `direccion` | TEXT | NOT NULL | Dirección física |
| `ciudad` | VARCHAR(100) | NOT NULL | Ciudad |
| `pais` | ENUM | NOT NULL | colombia, peru, ecuador, mexico |
| `certificaciones` | TEXT[] | | Array de certificaciones (ej: ISO 9001, GMP) |
| `estado` | ENUM | NOT NULL | activo, inactivo, suspendido |
| `calificacion` | DECIMAL(3,2) | NULLABLE | Rango 0-5 |
| `tiempo_entrega_promedio` | INTEGER | NULLABLE | Días promedio de entrega |
| `created_at` | DATETIME | NOT NULL | Fecha de creación con timezone |
| `updated_at` | DATETIME | NOT NULL | Fecha de última actualización |
| `version` | INTEGER | NOT NULL | Control de versión optimista |

## Endpoints API

### Base URL
```
http://localhost:8005/api/v1/proveedores
```

### 1. Crear Proveedor
```http
POST /api/v1/proveedores
Content-Type: application/json

{
  "razon_social": "Farmacéutica Colombiana S.A.",
  "nit": "800123456-1",
  "tipo_proveedor": "laboratorio",
  "email": "info@farmacolombiana.com",
  "telefono": "+57-1-2345678",
  "direccion": "Cra. 7 # 32-15, Bogotá",
  "ciudad": "Bogotá",
  "pais": "colombia",
  "certificaciones": ["ISO 9001:2015", "ISO 13485:2016", "GMP"],
  "estado": "activo",
  "calificacion": 4.5,
  "tiempo_entrega_promedio": 3
}
```

**Respuesta (201 Created):**
```json
{
  "proveedor_id": "550e8400-e29b-41d4-a716-446655440000",
  "razon_social": "Farmacéutica Colombiana S.A.",
  "nit": "800123456-1",
  "tipo_proveedor": "laboratorio",
  "email": "info@farmacolombiana.com",
  "telefono": "+57-1-2345678",
  "direccion": "Cra. 7 # 32-15, Bogotá",
  "ciudad": "Bogotá",
  "pais": "colombia",
  "certificaciones": ["ISO 9001:2015", "ISO 13485:2016", "GMP"],
  "estado": "activo",
  "calificacion": 4.5,
  "tiempo_entrega_promedio": 3,
  "created_at": "2025-10-23T15:30:00+00:00",
  "updated_at": "2025-10-23T15:30:00+00:00",
  "version": 0
}
```

### 2. Obtener Proveedor por ID
```http
GET /api/v1/proveedores/{proveedor_id}
```

**Respuesta (200 OK):**
```json
{
  "proveedor_id": "550e8400-e29b-41d4-a716-446655440000",
  "razon_social": "Farmacéutica Colombiana S.A.",
  ...
}
```

### 3. Listar Proveedores (Paginado)
```http
GET /api/v1/proveedores?skip=0&limit=10
```

**Respuesta (200 OK):**
```json
{
  "total": 15,
  "skip": 0,
  "limit": 10,
  "data": [
    {
      "proveedor_id": "550e8400-e29b-41d4-a716-446655440000",
      ...
    }
  ]
}
```

### 4. Buscar Proveedores (Con Filtros)
```http
GET /api/v1/proveedores/search/?tipo_proveedor=laboratorio&pais=colombia&skip=0&limit=10
```

**Parámetros de Query:**
- `razon_social`: Búsqueda parcial (LIKE)
- `nit`: Búsqueda parcial
- `tipo_proveedor`: laboratorio, distribuidor, importador
- `estado`: activo, inactivo, suspendido
- `pais`: colombia, peru, ecuador, mexico
- `skip`: Offset para paginación (default: 0)
- `limit`: Límite de resultados (default: 10, máximo: 100)

### 5. Actualizar Proveedor
```http
PUT /api/v1/proveedores/{proveedor_id}
Content-Type: application/json

{
  "calificacion": 4.8,
  "tiempo_entrega_promedio": 2,
  "estado": "activo"
}
```

**Respuesta (200 OK):** Proveedor actualizado con versión incrementada

### 6. Eliminar Proveedor
```http
DELETE /api/v1/proveedores/{proveedor_id}
```

**Respuesta (204 No Content)**

### 7. Health Check
```http
GET /health
```

**Respuesta (200 OK):**
```json
{
  "status": "healthy",
  "service": "proveedor-service"
}
```

## Códigos de Estado HTTP

| Código | Significado |
|--------|-------------|
| 201 | Proveedor creado exitosamente |
| 204 | Proveedor eliminado exitosamente |
| 400 | Datos de entrada inválidos |
| 404 | Proveedor no encontrado |
| 409 | Conflicto (NIT o email duplicado) |
| 422 | Error en validación de negocio |
| 500 | Error interno del servidor |

## Errores Comunes

### NIT Duplicado
```json
{
  "error": "NIT duplicado",
  "detalles": {
    "nit": "El NIT 800123456-1 ya existe en el sistema"
  }
}
```

### Email Duplicado
```json
{
  "error": "Email duplicado",
  "detalles": {
    "email": "El email info@farmacolombiana.com ya está registrado"
  }
}
```

### Proveedor No Encontrado
```json
{
  "error": "No encontrado",
  "detalles": {
    "proveedor_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## Configuración de Variables de Entorno

```env
# Base de datos
DATABASE_URL=postgresql+psycopg://proveedor_service:proveedor_password@postgres-db:5432/proveedor_db

# Redis (opcional para caché)
REDIS_URL=redis://redis-cache:6379

# Puerto
PORT=8005
```

## Inicialización de Datos

Al iniciar el contenedor, se ejecuta automáticamente `load_sample_data.py` que:
1. Crea las tablas si no existen
2. Carga 5 proveedores de ejemplo (si la BD está vacía)

## Desarrollo Local

### Requisitos
- Python 3.12+
- PostgreSQL 16+
- pip

### Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp example.env .env
# Editar .env con tus valores

# 4. Ejecutar migraciones
python -c "from app.database.connection import init_db; init_db()"

# 5. Cargar datos de ejemplo
python load_sample_data.py

# 6. Iniciar servicio
python main.py
```

### Pruebas

```bash
# Ejecutar pruebas completas
pytest tests/

# Ejecutar pruebas con cobertura
pytest tests/ --cov=app

# Prueba interactiva simple
python test_service.py
```

## Arquitectura

```
proveedor-service/
├── app/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py        # Configuración de BD
│   ├── models/
│   │   ├── __init__.py
│   │   └── proveedor.py         # Modelos ORM y Pydantic
│   ├── routes/
│   │   ├── __init__.py
│   │   └── proveedores.py       # Endpoints API
│   └── services/
│       ├── __init__.py
│       └── proveedor_service.py # Lógica de negocio
├── tests/
│   └── ...
├── main.py                      # Punto de entrada
├── requirements.txt             # Dependencias
├── Dockerfile                   # Configuración Docker
└── load_sample_data.py         # Script de inicialización
```

## Performance

- Pool de conexiones configurado: 20 conexiones
- Máximo overflow: 40 conexiones
- Índices en campos: `nit`, `email`
- Paginación implementada por defecto
- Validaciones optimizadas en DB (constrainsts)

## Seguridad

- ✅ Validación de email con Pydantic
- ✅ Constraints de BD (UNIQUE, NOT NULL)
- ✅ CORS configurado
- ✅ Validación de tipos de datos
- ✅ Manejo seguro de excepciones

## Próximas Mejoras

- [ ] Implementar caché Redis para búsquedas
- [ ] Agregar auditoría de cambios (audit-service)
- [ ] Endpoints de importación masiva (CSV)
- [ ] Validación con servicio de NIT
- [ ] Rate limiting
- [ ] Autenticación con JWT
- [ ] Historial de cambios

## Soporte

Para reportar problemas o sugerencias, contacta al equipo de desarrollo.

---

**Versión:** 1.0.0  
**Última actualización:** 2025-10-23

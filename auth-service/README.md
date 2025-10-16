# Auth Service - MediSupply

Microservicio de autenticación con JWT para el sistema MediSupply.

## Descripción

Este servicio maneja la autenticación de usuarios utilizando JWT (JSON Web Tokens). Proporciona endpoints para:

- **Login**: Autenticación de usuarios con email y contraseña
- **Verificación de Token**: Validación de tokens JWT

## Características

- ✅ Autenticación con JWT
- ✅ Validación de contraseñas con bcrypt
- ✅ Integración con base de datos PostgreSQL
- ✅ Manejo de roles de usuario
- ✅ Configuración de CORS
- ✅ Health checks
- ✅ Logging estructurado

## Estructura del Proyecto

```
auth-service/
├── app/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── auth.py
│   └── services/
│       ├── __init__.py
│       └── auth_service.py
├── tests/
├── main.py
├── requirements.txt
├── Dockerfile
├── test_auth.py
└── README.md
```

## Endpoints

### POST /api/v1/auth/login

Autentica un usuario y devuelve un token JWT.

**Request Body:**
```json
{
  "email": "test1@google.com",
  "password": "Abc123"
}
```

**Response (200):**
```json
{
  "id": "73715499-2c0b-4f05-8e86-7cf99d04cdf4",
  "email": "test1@google.com",
  "fullName": "Juan Carlos",
  "isActive": true,
  "roles": ["admin"],
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (401):**
```json
{
  "detail": "Credenciales inválidas"
}
```

### GET /api/v1/auth/verify-token

Verifica si un token JWT es válido.

**Query Parameters:**
- `token`: Token JWT a verificar

**Response (200):**
```json
{
  "valid": true,
  "user_id": 1,
  "email": "test1@google.com",
  "roles": ["admin"]
}
```

**Response (401):**
```json
{
  "detail": "Token inválido o expirado"
}
```

### GET /health

Health check del servicio.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "auth-service"
}
```

## Configuración

### Variables de Entorno

- `DATABASE_URL`: URL de conexión a la base de datos PostgreSQL
- `JWT_SECRET_KEY`: Clave secreta para firmar tokens JWT
- `JWT_EXPIRE_MINUTES`: Tiempo de expiración del token en minutos (default: 60)

### Ejemplo de configuración

```bash
DATABASE_URL=postgresql+psycopg://user_service:user_password@postgres-db:5432/user_db
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-2024
JWT_EXPIRE_MINUTES=60
```

## Instalación y Ejecución

### Con Docker

```bash
# Construir la imagen
docker build -t auth-service .

# Ejecutar el contenedor
docker run -p 8004:8004 \
  -e DATABASE_URL="postgresql+psycopg://user_service:user_password@postgres-db:5432/user_db" \
  -e JWT_SECRET_KEY="your-secret-key" \
  auth-service
```

### Con Docker Compose

```bash
# Desde el directorio backend
docker-compose up auth-service
```

### Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servicio
python main.py
```

## Pruebas

### Ejecutar pruebas manuales

```bash
python test_auth.py
```

### Pruebas con curl

```bash
# Health check
curl http://localhost:8004/health

# Login
curl -X POST http://localhost:8004/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test1@google.com", "password": "Abc123"}'

# Verificar token
curl "http://localhost:8004/api/v1/auth/verify-token?token=YOUR_TOKEN_HERE"
```

## Base de Datos

El servicio utiliza la tabla `usuarios` existente con la siguiente estructura:

```sql
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    correo_electronico VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nit VARCHAR(20) NOT NULL,
    rol VARCHAR(50) DEFAULT 'usuario_institucional',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);
```

## Seguridad

- Las contraseñas se almacenan con hash bcrypt
- Los tokens JWT tienen tiempo de expiración configurable
- Se valida que el usuario esté activo antes de autenticar
- Se utiliza una clave secreta para firmar los tokens

## Logs

El servicio genera logs estructurados para:
- Intentos de login exitosos y fallidos
- Errores de autenticación
- Errores de verificación de tokens
- Errores de base de datos

## Integración

Este servicio se integra con:
- **User Service**: Para obtener datos de usuarios
- **Nginx Gateway**: Para enrutamiento de requests
- **PostgreSQL**: Para persistencia de datos
- **Redis**: Para caché (opcional)

## Monitoreo

- Health check endpoint: `/health`
- Logs estructurados para monitoreo
- Métricas de rendimiento integradas

# API Documentation - Auth Service

## Overview

El Auth Service es un microservicio que maneja la autenticación de usuarios utilizando JWT (JSON Web Tokens) para el sistema MediSupply.

**Base URL:** `http://localhost:8004`  
**API Version:** v1  
**Content-Type:** `application/json`

## Authentication

El servicio utiliza JWT para la autenticación. Los tokens se obtienen mediante el endpoint de login y deben incluirse en el header `Authorization` como `Bearer <token>`.

## Endpoints

### 1. Health Check

Verifica el estado del servicio.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "auth-service"
}
```

**Status Codes:**
- `200 OK`: Servicio funcionando correctamente

---

### 2. User Login

Autentica un usuario y devuelve un token JWT.

**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email": "test1@google.com",
  "password": "Abc123"
}
```

**Response (Success - 200):**
```json
{
  "id": "73715499-2c0b-4f05-8e86-7cf99d04cdf4",
  "email": "test1@google.com",
  "fullName": "Juan Carlos",
  "isActive": true,
  "roles": ["admin"],
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjczNzE1NDk5LTJjMGItNGYwNS04ZTg2LTdjZjk5ZDA0Y2RmNCIsImlhdCI6MTc2MDU2MTMxNCwiZXhwIjoxNzYwNTY4NTE0fQ.pn_RuxpFsv74iSuunj6Kt3apD23DNJ6Ga8MRVinXcHw"
}
```

**Response (Error - 401):**
```json
{
  "detail": "Credenciales inválidas"
}
```

**Status Codes:**
- `200 OK`: Login exitoso
- `401 Unauthorized`: Credenciales inválidas
- `422 Unprocessable Entity`: Datos de entrada inválidos
- `500 Internal Server Error`: Error interno del servidor

**Validation Rules:**
- `email`: Debe ser un email válido
- `password`: Campo requerido

---

### 3. Token Verification

Verifica si un token JWT es válido y devuelve información del usuario.

**Endpoint:** `GET /api/v1/auth/verify-token`

**Query Parameters:**
- `token` (required): Token JWT a verificar

**Response (Success - 200):**
```json
{
  "valid": true,
  "user_id": 1,
  "email": "test1@google.com",
  "roles": ["admin"]
}
```

**Response (Error - 401):**
```json
{
  "detail": "Token inválido o expirado"
}
```

**Status Codes:**
- `200 OK`: Token válido
- `401 Unauthorized`: Token inválido o expirado
- `500 Internal Server Error`: Error interno del servidor

---

## Data Models

### LoginRequest

```json
{
  "email": "string (email format)",
  "password": "string"
}
```

### LoginResponse

```json
{
  "id": "string (UUID)",
  "email": "string",
  "fullName": "string",
  "isActive": "boolean",
  "roles": ["string"],
  "token": "string (JWT)"
}
```

### TokenVerificationResponse

```json
{
  "valid": "boolean",
  "user_id": "integer",
  "email": "string",
  "roles": ["string"]
}
```

---

## Error Handling

El servicio utiliza códigos de estado HTTP estándar y devuelve mensajes de error en formato JSON:

```json
{
  "detail": "Mensaje de error descriptivo"
}
```

### Common Error Codes

- `400 Bad Request`: Datos de entrada malformados
- `401 Unauthorized`: Credenciales inválidas o token expirado
- `422 Unprocessable Entity`: Datos de entrada inválidos
- `500 Internal Server Error`: Error interno del servidor

---

## Security

### Password Hashing
- Las contraseñas se almacenan usando bcrypt con salt
- No se almacenan contraseñas en texto plano

### JWT Tokens
- Algoritmo: HS256
- Tiempo de expiración configurable (default: 60 minutos)
- Clave secreta configurable via variable de entorno

### User Validation
- Solo usuarios activos pueden autenticarse
- Validación de email y contraseña requerida

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://user_service:user_password@postgres-db:5432/user_db` |
| `JWT_SECRET_KEY` | Secret key for JWT signing | `your-secret-key` |
| `JWT_EXPIRE_MINUTES` | Token expiration time in minutes | `60` |

### Database Schema

El servicio utiliza la tabla `usuarios` existente:

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

---

## Examples

### cURL Examples

#### Health Check
```bash
curl -X GET http://localhost:8004/health
```

#### Login
```bash
curl -X POST http://localhost:8004/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test1@google.com",
    "password": "Abc123"
  }'
```

#### Verify Token
```bash
curl -X GET "http://localhost:8004/api/v1/auth/verify-token?token=YOUR_JWT_TOKEN_HERE"
```

### JavaScript Examples

#### Login
```javascript
const response = await fetch('http://localhost:8004/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'test1@google.com',
    password: 'Abc123'
  })
});

const data = await response.json();
console.log(data.token); // JWT token
```

#### Verify Token
```javascript
const token = 'your-jwt-token-here';
const response = await fetch(`http://localhost:8004/api/v1/auth/verify-token?token=${token}`);
const data = await response.json();
console.log(data.valid); // true/false
```

---

## Rate Limiting

Actualmente no hay rate limiting implementado, pero se recomienda implementar en producción.

## Monitoring

- Health check endpoint disponible en `/health`
- Logs estructurados para monitoreo
- Métricas de rendimiento integradas

## Support

Para soporte técnico o reportar problemas, contactar al equipo de desarrollo de MediSupply.

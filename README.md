# Backend Microservices

Este proyecto implementa una arquitectura de microservicios usando FastAPI y PostgreSQL, con Docker Compose para la orquestación.

## Estructura del Proyecto

```
backend/
├── user-service/              # Microservicio de gestión de usuarios
├── nit-validation-service/    # Microservicio de validación de NIT
├── audit-service/             # Microservicio de auditoría y logs
├── docker-compose.yml         # Orquestación de servicios
├── nginx.conf                # Configuración del API Gateway
├── .env                      # Variables de entorno
└── README.md                 # Este archivo
```

## Microservicios

### 1. User Service (Puerto 8001)
- **Propósito**: Gestión de usuarios institucionales con orquestador de registro
- **Base de datos**: PostgreSQL (user_db)
- **Funcionalidades**:
  - Registro de usuarios institucionales con validación de NIT
  - Validación de políticas de contraseña (complejidad)
  - Integración con servicio de validación de NIT
  - Auditoría automática de eventos de registro
  - Generación de tokens JWT para autenticación
- **Endpoints principales**:
  - `POST /register` - Registrar usuario institucional (orquestador)
  - `GET /health` - Health check del servicio
- **Modelo de datos**: Campo NIT como string (VARCHAR(20)) para mayor flexibilidad

### 2. NIT Validation Service (Puerto 8002)
- **Propósito**: Validación de NIT contra instituciones asociadas
- **Base de datos**: PostgreSQL (nit_db) + Redis para caché
- **Funcionalidades**:
  - Validación de NITs de instituciones autorizadas
  - Caché de consultas con Redis para optimización
  - Soporte para NITs como strings (mayor flexibilidad)
  - Validación de estado activo de instituciones
- **Endpoints principales**:
  - `GET /api/v1/validate/{nit}` - Validar NIT (string)
  - `GET /health` - Health check del servicio
- **Datos de prueba**: 10 instituciones precargadas con NITs de diferentes países

### 3. Audit Service (Puerto 8003)
- **Propósito**: Auditoría, logs y trazabilidad del sistema
- **Base de datos**: PostgreSQL (audit_db)
- **Funcionalidades**:
  - Registro de eventos de auditoría (success/fail)
  - Tracking de acciones de usuario (registro, validación, etc.)
  - Almacenamiento de requests y outcomes
  - Generación de IDs únicos de auditoría
- **Endpoints principales**:
  - `POST /audit/register` - Registrar evento de auditoría
  - `GET /health` - Health check del servicio
- **Modelo de datos**: Eventos con JSONB para requests flexibles

## Funcionalidades Implementadas

### User Management Orquestador
El **User Service** implementa un patrón orquestador para el registro de usuarios que coordina múltiples validaciones:

1. **Validación de complejidad de contraseña**:
   - Mínimo 8 caracteres
   - Al menos una mayúscula, minúscula, número y carácter especial
   
2. **Validación de NIT**: Consulta al NIT Validation Service para verificar instituciones autorizadas

3. **Validación de duplicados**: Verificación de email único en el sistema

4. **Auditoría automática**: Registro de todos los eventos (éxito y fallo) en Audit Service

5. **Respuestas estandarizadas**: Códigos HTTP específicos para cada tipo de error:
   - `200` - Registro exitoso con JWT token
   - `400` - Datos inválidos (formato)
   - `404` - NIT no autorizado
   - `409` - Usuario ya existe
   - `422` - Reglas de negocio fallidas (password débil)
   - `500` - Error interno

### Arquitectura de Microservicios
- **Comunicación HTTP REST** entre servicios
- **Base de datos independientes** por servicio
- **Manejo de timeouts** y errores de red
- **Logs estructurados** para debugging

## Tecnologías Utilizadas
- **Base de datos**: PostgreSQL 16
- **Driver de BD**: psycopg3 (última versión)
- **ORM**: SQLAlchemy 2.0
- **Contenedores**: Docker & Docker Compose
- **API Gateway**: Nginx
- **Validación**: Pydantic

## Inicio Rápido

### Prerrequisitos
- Docker
- Docker Compose

### Levantar los servicios

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd backend

# (Opcional pero recomendado) Configurar variables de entorno
# Copiar archivo de ejemplo y ajustar si el puerto 5432 está ocupado
# Windows PowerShell:
Copy-Item -Path .env.example -Destination .env -Force
# macOS/Linux:
cp .env.example .env

# Si tienes PostgreSQL local u otro servicio usando 5432,
# edita el archivo `.env` y cambia `POSTGRES_PORT` (por ejemplo 5440).

# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar estado de servicios
docker-compose ps
```

### Acceso a los servicios

- **API Gateway**: http://localhost
- **User Service**: http://localhost:8001
- **NIT Validation Service**: http://localhost:8002
- **Audit Service**: http://localhost:8003

### Documentación de APIs

Cada servicio tiene documentación automática de Swagger:

- User Service: http://localhost:8001/docs
- NIT Validation Service: http://localhost:8002/docs  
- Audit Service: http://localhost:8003/docs

### Colección de Postman

El proyecto incluye una colección completa de Postman para testing manual y automatizado:

**Archivos incluidos**:
- `postman_collection.json` - Colección principal con todas las pruebas
- `postman_environment.json` - Variables de entorno configurables
- `POSTMAN_README.md` - Documentación detallada

**Variables de entorno disponibles**:
```json
{
  "base_url": "http://localhost:8001",
  "audit_url": "http://localhost:8003", 
  "nit_url": "http://localhost:8002",
  "nit_valido": "901234567",
  "nit_invalido": "999999999",
  "password_valido": "S3gura!2025",
  "password_debil": "123"
}
```

**Casos de prueba incluidos**:
- ✅ Registro exitoso con JWT token (200)
- ✅ Validación de NIT inválido (404)
- ✅ Email duplicado (409)
- ✅ Password débil (422)
- ✅ Datos inválidos (400)
- ✅ Health checks de todos los servicios
- ✅ Tests de auditoría y NIT validation
- ✅ Tests automáticos con verificación de tiempo de respuesta

**Importar en Postman**:
1. Abrir Postman
2. Hacer clic en "Import"
3. Seleccionar y arrastrar ambos archivos JSON
4. Configurar el environment "Backend Microservices Environment"

## Desarrollo Local

### Configurar entorno de desarrollo

```bash
# Crear entorno virtual para cada servicio
cd user-service
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Repetir para nit-validation-service y audit-service
```

### Variables de entorno

Copiar `.env` y ajustar las variables según tu entorno:

```bash
# Crear desde el ejemplo y editar según tu entorno
# Windows PowerShell:
Copy-Item -Path .env.example -Destination .env -Force
# macOS/Linux:
cp .env.example .env
# Editar .env con tus configuraciones (p. ej. POSTGRES_PORT)
```

## Base de Datos

Los 3 microservicios comparten una sola instancia de PostgreSQL con bases de datos separadas:

- **PostgreSQL Server**: Puerto 5432
  - `user_db` - Base de datos del User Service
  - `nit_db` - Base de datos del NIT Validation Service  
  - `audit_db` - Base de datos del Audit Service
- **Redis Server**: Puerto 6379 (usado por NIT Validation Service para caché)

### Conexiones de base de datos

```bash
# Conectar a la instancia principal
psql -h localhost -p 5432 -U postgres

# Conectar a bases de datos específicas
psql -h localhost -p 5432 -U user_service -d user_db
psql -h localhost -p 5432 -U nit_service -d nit_db
psql -h localhost -p 5432 -U audit_service -d audit_db
```

## Testing

### Tests de Integración

Los servicios incluyen tests de integración que se ejecutan con los servicios reales en contenedores Docker, proporcionando mayor confiabilidad que los tests unitarios con mocks.

#### Características de los Tests de Integración:
- **Servicios reales**: Tests contra APIs funcionando con base de datos
- **Entorno consistente**: Misma configuración que producción
- **Comunicación entre servicios**: Verificación de integración completa
- **Dependencias preinstaladas**: pytest, pytest-asyncio, httpx incluidos en requirements.txt

#### Ejecución de Tests

**User Service (8 tests de integración)**:
```bash
# Ejecutar tests desde contenedor
docker-compose exec user-service pytest tests/ -v

# Con coverage
docker-compose exec user-service pytest tests/ --cov=app --cov-report=term
```

**Audit Service (7 tests de integración)**:
```bash
# Ejecutar tests desde contenedor
docker-compose exec audit-service pytest tests/ -v

# Con coverage
docker-compose exec audit-service pytest tests/ --cov=app --cov-report=term
```

#### Cobertura de Tests de Integración

**User Service Tests**:
- ✅ Validación de reglas de contraseña con API real
- ✅ Hashing de contraseñas con bcrypt
- ✅ Generación de tokens JWT
- ✅ Validación de NIT con servicio real
- ✅ Health checks de endpoints
- ✅ Registro completo de usuarios (exitoso)
- ✅ Registro con fallos (NIT inválido, contraseña débil)
- ✅ Prevención de usuarios duplicados

**Audit Service Tests**:
- ✅ Health check del servicio
- ✅ Registro de logs de auditoría (exitoso y fallido)
- ✅ Validación de errores de entrada
- ✅ Múltiples logs de auditoría
- ✅ Datos complejos de request
- ✅ Requests concurrentes

#### Configuración de Testing

Cada servicio incluye:
- `tests/test_integration.py` - Tests de integración
- `pytest.ini` - Configuración de pytest con asyncio
- Dependencies en `requirements.txt`:
  ```txt
  pytest==7.4.0
  pytest-asyncio==0.21.1
  pytest-cov==4.1.0
  httpx==0.25.2
  ```

#### Métricas de Calidad
- **Tiempo de ejecución**: <3 segundos por servicio
- **Cobertura objetivo**: >90% para funcionalidades críticas
- **Todos los tests deben pasar** antes de merge a develop
- **Tests automáticos en CI/CD** (próximamente)

#### Testing Guide Completo
Para información detallada sobre testing unitario y configuración avanzada, consultar: `TESTING_GUIDE.md`

## Comandos Útiles

```bash
# Reconstruir servicios
docker-compose build

# Levantar servicios específicos
docker-compose up user-service nit-validation-service

# Ver logs de un servicio específico
docker-compose logs -f user-service

# Ejecutar comando en contenedor
docker-compose exec user-service bash

# Parar todos los servicios
docker-compose down

# Parar y eliminar volúmenes
docker-compose down -v
```

## Arquitectura

```
┌─────────────────┐
│   API Gateway   │ (Puerto 80)
│     (Nginx)     │
└─────────┬───────┘
          │
    ┌─────┴─────┐
    │           │
┌───▼───┐   ┌───▼───┐   ┌────▼────┐
│ User  │   │nit-val│   │ Audit   │
│Service│   │Service│   │ Service │
│:8001  │   │:8002  │   │ :8003   │
└───┬───┘   └───┬───┘   └────┬────┘
    │           │            │
    └─────┬─────┴─────┬──────┘
          │           │
      ┌───▼───────────▼───┐
      │   PostgreSQL DB   │
      │ user_db|tax_db|   │
      │     audit_db      │
      │      :5432        │
      └───────────────────┘
```

## Buenas Prácticas Implementadas

1. **Separación de responsabilidades**: Cada servicio tiene una responsabilidad específica
2. **Base de datos independientes**: Cada servicio maneja su propia base de datos
3. **Containerización**: Todos los servicios están dockerizados
4. **API Gateway**: Punto único de entrada para todas las APIs
5. **Health checks**: Verificación de salud de servicios y bases de datos
6. **Logs estructurados**: Sistema de auditoría centralizado
7. **Validación de datos**: Uso de Pydantic para validación
8. **Documentación automática**: Swagger/OpenAPI para cada servicio

## Próximos Pasos

- [x] Implementar orquestador de registro de usuarios
- [x] Validación de complejidad de contraseña
- [x] Integración con servicio de validación de NIT
- [x] Sistema de auditoría automatizado
- [x] Generación de tokens JWT
- [x] Tests unitarios completos
- [x] Colección de Postman con variables
- [ ] Tests de integración end-to-end
- [ ] Configurar CI/CD con GitHub Actions
- [ ] Implementar rate limiting
- [ ] Agregar monitoreo (Prometheus/Grafana)
- [ ] Implementar circuit breaker
- [ ] Configurar logging centralizado (ELK Stack)
- [ ] Documentación de APIs con OpenAPI 3.0

## Documentación Adicional

- **[Flujo de Trabajo del Equipo](./FLUJO_EQUIPO.md)** - ⭐ Guía rápida para el equipo sobre despliegues monorepo
- **[Guía de Despliegue](./GUIA_DESPLIEGUE.md)** - Documentación completa del sistema de despliegue
- **[Testing Guide](./TESTING_GUIDE.md)** - Guía completa de testing unitario y configuración avanzada
- **[Postman Collection](./POSTMAN_README.md)** - Documentación detallada de la colección de Postman

### Archivos de Configuración
- `postman_collection.json` - Colección de Postman con todos los tests
- `postman_environment.json` - Variables de entorno para Postman
- `docker-compose.yml` - Orquestación de todos los servicios
- `.env` - Variables de entorno del proyecto

---

## Metodología de Desarrollo - Git Flow

### Estrategia de Ramas

Este proyecto utiliza una estrategia de ramas Git Flow simplificada:

- **`main`**: Rama de producción - contiene código estable y releases
- **`develop`**: Rama de desarrollo - integración de features antes de release
- **`feature/*`**: Ramas de funcionalidades - se crean desde `develop` y se mergean de vuelta

### Crear una Nueva Feature

Sigue estos pasos para desarrollar una nueva funcionalidad siguiendo las mejores prácticas de Git Flow:

#### 1. Sincronizar la rama de desarrollo
```bash
# Cambiar a la rama develop
git checkout develop

# Si no tienes develop local, créala desde la remota
git checkout -b develop origin/develop

# Obtener los últimos cambios del repositorio remoto
git pull origin develop
```

#### 2. Crear una nueva rama para la feature
```bash
# Crear y cambiar a una nueva rama desde develop
git checkout -b feature/nombre-de-la-feature

# Ejemplo: git checkout -b feature/add-user-authentication
```

#### 3. Desarrollar la funcionalidad
- Implementa los cambios necesarios
- Asegúrate de seguir las convenciones de código del proyecto
- Realiza commits frecuentes con mensajes descriptivos

#### 4. Realizar commits
```bash
# Agregar archivos modificados
git add .

# Realizar commit con mensaje descriptivo
git commit -m "feat: descripción clara de lo implementado"

# Ejemplos de buenos mensajes:
# git commit -m "feat: add user authentication endpoint"
# git commit -m "fix: resolve database connection timeout"
# git commit -m "docs: update API documentation"
```

#### 5. Subir la rama al repositorio remoto
```bash
# Primera vez - crear rama remota
git push -u origin feature/nombre-de-la-feature

# Siguientes commits
git push origin feature/nombre-de-la-feature
```

#### 6. Crear Pull Request
1. Ve a GitHub y navega al repositorio
2. Haz clic en "Compare & pull request" o "New pull request"
3. Selecciona la rama base (**develop**) y tu rama feature
4. Completa el título y descripción del PR:
   - **Título**: Resumen conciso de la funcionalidad
   - **Descripción**: Detalla qué se implementó, por qué y cómo probarlo

#### 7. Revisión y Merge
- Espera la revisión del código por parte del equipo
- Realiza los cambios solicitados si es necesario
- Una vez aprobado, el PR será mergeado a develop

#### 8. Limpiar rama local
```bash
# Cambiar a develop y actualizar
git checkout develop
git pull origin develop

# Eliminar rama local (opcional)
git branch -d feature/nombre-de-la-feature
```

### Convenciones de Nombres de Ramas
- `feature/descripcion-funcionalidad` - Para nuevas funcionalidades
- `fix/descripcion-problema` - Para corrección de bugs
- `hotfix/descripcion-urgente` - Para fixes críticos en producción
- `docs/descripcion-documentacion` - Para cambios en documentación

### Tipos de Commits (Conventional Commits)
- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de bug
- `docs:` - Cambios en documentación
- `style:` - Cambios de formato (sin afectar funcionalidad)
- `refactor:` - Refactorización de código
- `test:` - Agregar o modificar tests
- `chore:` - Tareas de mantenimiento

---

# Documentación Migroservicio de cargar Masiva
Este proyecto implementa un pipeline de microservicios en Python para la carga, validación y consolidación de productos médicos, con ejecución local en Docker

## Estructura 

```
carga_masiva/                     
│
├── ingestion-service/             # Microservicio de carga de archivos CSV
│   ├── app/
│   │   ├── main.py                # Punto de entrada (FastAPI + handler Lambda)
│   │   ├── routes/                # Endpoints de ingesta
│   │   └── utils/                 # Funciones auxiliares (ej. safe_float)
│   ├── requirements.txt           # Dependencias específicas
│   └── Dockerfile                 # Imagen Docker + Lambda (ECR)
│
├── validator-service/             # Microservicio de validación de productos
│   ├── app/
│   │   ├── main.py                # Validaciones de campos críticos
│   │   ├── validators/            # Reglas de negocio
│   │   └── errors/                # Manejo de errores
│   ├── requirements.txt
│   └── Dockerfile
│
├── upserter-service/              # Microservicio de inserción en tabla final
│   ├── app/
│   │   ├── main.py                # Inserción en tabla final products
│   │   └── db/                    # Conexión a Aurora PostgreSQL
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml             # Orquestación local con Docker
```

# Instalación y ejecución
## Clonar repositorios
git clone https://github.com/ProyectoIntegradorG4/backend
cd carga_masiva

## Configuración variables de entorno

DATABASE_URL=postgresql+psycopg2://postgres:grupo4@postgres-db:5432/postgres


## Teniendo instalado Docker Composse se levanta con:
docker compose up --build


# Endpoints locales
Ingesta    → http://localhost:8010/upload-csv
Validator  → http://localhost:8011/validate
Upserter   → http://localhost:8012/upsert


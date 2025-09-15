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
- **Propósito**: Gestión de usuarios, autenticación y autorización
- **Base de datos**: PostgreSQL (puerto 5432)
- **Endpoints principales**:
  - `POST /api/v1/users/` - Crear usuario
  - `GET /api/v1/users/` - Listar usuarios
  - `GET /api/v1/users/{id}` - Obtener usuario
  - `PUT /api/v1/users/{id}` - Actualizar usuario
  - `DELETE /api/v1/users/{id}` - Eliminar usuario

### 2. NIT Validation Service (Puerto 8002)
- **Propósito**: Validación de NIT contra instituciones asociadas
- **Base de datos**: PostgreSQL + Redis para caché
- **Endpoints principales**:
  - `POST /api/v1/validate` - Validar NIT
  - `GET /api/v1/validate/{nit}` - Validar NIT (GET)
  - `GET /api/v1/institution/{nit}` - Detalles de institución
  - `GET /api/v1/cache/stats` - Estadísticas de caché
  - `DELETE /api/v1/cache/{nit}` - Limpiar caché

### 3. Audit Service (Puerto 8003)
- **Propósito**: Auditoría, logs y trazabilidad del sistema
- **Base de datos**: PostgreSQL (puerto 5434)
- **Endpoints principales**:
  - `POST /api/v1/audits/` - Crear log de auditoría
  - `GET /api/v1/audits/` - Consultar logs (con filtros)
  - `GET /api/v1/audits/stats/summary` - Resumen estadístico

## Tecnologías Utilizadas

- **Framework**: FastAPI (Python 3.12)
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
│ User  │   │ Tax   │   │ Audit   │
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

- [ ] Implementar autenticación JWT
- [ ] Agregar tests unitarios e integración
- [ ] Configurar CI/CD
- [ ] Implementar rate limiting
- [ ] Agregar monitoreo (Prometheus/Grafana)
- [ ] Implementar circuit breaker
- [ ] Configurar logging centralizado (ELK Stack)

## Documentación Adicional

- [Migración a psycopg3](./PSYCOPG3_MIGRATION.md) - Detalles sobre el uso de psycopg3

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


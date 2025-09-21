# Testing Guide - Backend Microservices

Este documento describe cómo ejecutar y trabajar con los tests unitarios de los microservicios.

## 📋 Descripción General

Los tests unitarios están diseñados para ejecutarse **sin necesidad de levantar las APIs** ni conectarse a bases de datos reales. Utilizan:

- **SQLite en memoria** para simulación de base de datos
- **Mocks** para servicios externos (HTTP, audit client)
- **Fixtures** para datos de prueba consistentes
- **pytest** como framework principal
- **Coverage** para reportes de cobertura

## 🏗️ Estructura de Testing

### User Service Tests
```
user-service/
├── tests/
│   ├── test_user_service.py    # Tests del servicio principal
│   └── test_models.py          # Tests de modelos Pydantic
├── conftest.py                 # Configuración y fixtures
├── pytest.ini                 # Configuración de pytest
├── requirements-test.txt       # Dependencias de testing
├── run_tests.ps1              # Script PowerShell
└── run_tests.sh               # Script Bash
```

### Audit Service Tests
```
audit-service/
├── tests/
│   ├── test_audit_service.py   # Tests del servicio principal
│   └── test_audit_models.py    # Tests de modelos Pydantic
├── conftest.py                 # Configuración y fixtures
├── pytest.ini                 # Configuración de pytest
├── requirements-test.txt       # Dependencias de testing
└── run_tests.ps1              # Script PowerShell
```

## 🚀 Ejecución de Tests

### Opción 1: Scripts Automáticos (Recomendado)

#### Windows PowerShell:
```powershell
# User Service
cd user-service
.\run_tests.ps1

# Audit Service  
cd audit-service
.\run_tests.ps1
```

#### Linux/Mac:
```bash
# User Service
cd user-service
chmod +x run_tests.sh
./run_tests.sh

# Audit Service
cd audit-service
chmod +x run_tests.sh  
./run_tests.sh
```

### Opción 2: Comandos Manuales

```bash
# 1. Instalar dependencias
pip install -r requirements-test.txt

# 2. Ejecutar todos los tests
pytest tests/ -v

# 3. Ejecutar tests específicos
pytest tests/test_user_service.py::TestUserServicePasswordValidation -v

# 4. Ejecutar con coverage
pip install pytest-cov
pytest tests/ --cov=app --cov-report=html --cov-report=term

# 5. Ejecutar solo tests marcados
pytest tests/ -m "unit" -v
```

## 📊 Cobertura de Tests

### User Service (24 tests)

#### `TestUserServicePasswordValidation` (5 tests)
- ✅ Contraseñas válidas con todos los requisitos
- ✅ Rechazo de contraseñas muy cortas
- ✅ Rechazo sin mayúsculas/minúsculas/números/especiales

#### `TestUserServiceNITValidation` (4 tests)  
- ✅ Validación exitosa de NIT existente
- ✅ Manejo de NIT no encontrado (404)
- ✅ Rechazo de instituciones inactivas
- ✅ Manejo de errores de red

#### `TestUserServiceJWTGeneration` (2 tests)
- ✅ Generación de tokens válidos
- ✅ Inclusión de datos de usuario en token

#### `TestUserServiceUserCreation` (4 tests)
- ✅ Creación exitosa completa con auditoría
- ✅ Rechazo de contraseñas débiles (422)
- ✅ Rechazo de NITs no autorizados (404)
- ✅ Rechazo de emails duplicados (409)

#### `TestUserServiceHashingUtilities` (2 tests)
- ✅ Generación de hashes bcrypt válidos
- ✅ Hashes únicos por llamada (sales)

#### `TestUserRegisterModel` (4 tests)
- ✅ Validación de modelos Pydantic
- ✅ Rechazo de emails inválidos
- ✅ Validación de campos obligatorios

### Audit Service (20 tests)

#### `TestAuditServiceCreate` (5 tests)
- ✅ Creación exitosa de logs de auditoría
- ✅ Generación de IDs únicos automáticos
- ✅ Logs para eventos fallidos
- ✅ Preservación de timestamps
- ✅ Creación de múltiples logs

#### `TestAuditServiceRetrieval` (3 tests)
- ✅ Recuperación de logs existentes
- ✅ Manejo de logs inexistentes
- ✅ Recuperación post-creación

#### `TestAuditServiceDataIntegrity` (2 tests)
- ✅ Preservación de estructura de requests
- ✅ Almacenamiento correcto de enums

#### `TestAuditServiceErrorHandling` (2 tests)
- ✅ Manejo de sesión de base de datos
- ✅ Creación con datos mínimos

#### `TestModelos y Enums` (8 tests)
- ✅ Validación de RequestData, AuditLogCreate, AuditLogResponse
- ✅ Validación de enums OutcomeType y ActionType
- ✅ Tests de integración entre modelos

## 🔧 Configuración Avanzada

### Ejecutar Tests con Filtros
```bash
# Solo tests de validación de password
pytest -k "password" -v

# Solo tests que no requieren red
pytest -k "not network" -v

# Tests rápidos solamente
pytest -m "not slow" -v
```

### Coverage Detallado
```bash
# Coverage con exclusión de líneas
pytest --cov=app --cov-report=html --cov-fail-under=90

# Coverage solo para archivos modificados
pytest --cov=app --cov-report=term-missing
```

### Debug de Tests
```bash
# Parar en primer fallo
pytest -x

# Verbose con stdout
pytest -v -s

# Debugger en fallos
pytest --pdb
```

## 🐛 Solución de Problemas

### Error: "No module named 'pytest'"
```bash
pip install -r requirements-test.txt
```

### Error: "cannot import name 'app'"
```bash
# Asegúrate de estar en el directorio correcto
cd user-service  # o audit-service
export PYTHONPATH=$PWD:$PYTHONPATH
```

### Tests Muy Lentos
```bash
# Ejecutar en paralelo
pip install pytest-xdist
pytest -n 4 tests/
```

### Error de Base de Datos
Los tests usan SQLite en memoria, no requieren PostgreSQL. Si hay errores:
```bash
# Limpiar cache de pytest
pytest --cache-clear
```

## 📈 Métricas de Calidad

### Objetivos de Coverage
- **User Service**: >90% cobertura
- **Audit Service**: >95% cobertura
- **Modelos**: 100% cobertura

### Tiempo de Ejecución Objetivo
- **Tests unitarios**: <30 segundos por servicio
- **Tests completos**: <1 minuto total

### Estándares de Código
- Todos los tests deben pasar en CI/CD
- No warnings de deprecación
- Documentación en docstrings
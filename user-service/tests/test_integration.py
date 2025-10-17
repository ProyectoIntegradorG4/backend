"""
Tests de integración para User Service usando servicios reales
Estos tests se ejecutan en contenedores Docker con servicios activos
"""
import pytest
import asyncio
import httpx
from app.models.user import UserRegister
from app.services.user_service import UserService
from app.database.connection import get_db
from sqlalchemy.orm import Session


class TestUserServiceIntegration:
    """Tests de integración con servicios reales."""

    def test_password_validation_rules(self):
        """Test que valida las reglas de contraseña sin servicios externos."""
        from app.services.user_service import UserService
        
        # Crear una instancia temporal sin base de datos para test de validación
        service = UserService(None)
        
        # Contraseñas válidas
        assert service.validate_password_complexity("S3gura!2025") is True
        assert service.validate_password_complexity("Admin@123") is True
        
        # Contraseñas inválidas
        assert service.validate_password_complexity("123") is False  # Muy corta
        assert service.validate_password_complexity("password") is False  # Sin mayúsculas/números/especiales
        assert service.validate_password_complexity("PASSWORD123") is False  # Sin minúsculas/especiales
        assert service.validate_password_complexity("Password") is False  # Sin números/especiales

    def test_password_hashing(self):
        """Test que valida el hashing de contraseñas."""
        from app.services.user_service import UserService
        
        service = UserService(None)
        password = "TestPassword123!"
        
        hash1 = service.get_password_hash(password)
        hash2 = service.get_password_hash(password)
        
        # Los hashes deben ser diferentes (sal única)
        assert hash1 != hash2
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")

    def test_jwt_token_generation(self):
        """Test que valida la generación de tokens JWT."""
        from app.services.user_service import UserService

        service = UserService(None)
        user_id = 123
        email = "test@example.com"

        # Usar el método correcto
        token = service.create_access_token({"sub": str(user_id), "email": email})

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens son largos

    @pytest.mark.asyncio
    async def test_nit_validation_with_real_service(self):
        """Test que valida NIT usando el servicio real de validación."""
        from app.services.user_service import UserService
        
        service = UserService(None)
        
        # Test con NIT válido (debe existir en los datos de prueba)
        exists, institution_id = await service.validate_nit_exists("901234567")
        assert exists is True
        assert institution_id is not None
        
        # Test con NIT inválido
        exists, institution_id = await service.validate_nit_exists("999999999")
        assert exists is False
        assert institution_id is None

    @pytest.mark.asyncio
    async def test_health_check_endpoints(self):
        """Test que verifica que todos los servicios estén respondiendo."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # User Service
            response = await client.get("http://user-service:8001/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "user-service"
            
            # NIT Validation Service
            response = await client.get("http://nit-validation-service:8002/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            
            # Audit Service
            response = await client.get("http://audit-service:8003/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_user_registration_integration(self):
        """Test completo de registro de usuario usando servicios reales."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Datos de usuario para registro
            user_data = {
                "nombre": "Hospital Test Integration",
                "email": f"integration_test_{asyncio.get_event_loop().time()}@test.com",  # Email único
                "nit": "901234567",  # NIT válido
                "password": "S3gura!2025"
            }
            
            # Realizar registro
            response = await client.post(
                "http://user-service:8001/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Verificar respuesta exitosa
            assert response.status_code == 200
            data = response.json()
            
            assert "userId" in data
            assert "institucionId" in data
            assert "token" in data
            assert data["rol"] == "usuario_institucional"
            assert data["mensaje"] == "Registro exitoso"

    @pytest.mark.asyncio
    async def test_user_registration_failures(self):
        """Test de casos de fallo en registro de usuario."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            
            # Test 1: NIT inválido
            user_data = {
                "nombre": "Hospital Test",
                "email": "test_invalid_nit@test.com",
                "nit": "999999999",  # NIT que no existe
                "password": "S3gura!2025"
            }
            
            response = await client.post(
                "http://user-service:8001/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert "NIT no autorizado" in data["detail"]["error"]
            
            # Test 2: Contraseña débil
            user_data = {
                "nombre": "Hospital Test",
                "email": "test_weak_password@test.com",
                "nit": "901234567",
                "password": "123"  # Contraseña muy débil
            }
            
            response = await client.post(
                "http://user-service:8001/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert "Reglas de negocio fallidas" in data["detail"]["error"]

    @pytest.mark.asyncio 
    async def test_duplicate_user_registration(self):
        """Test que verifica que no se pueden registrar usuarios duplicados."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            
            # Registrar usuario por primera vez
            user_data = {
                "nombre": "Hospital Duplicate Test",
                "email": "duplicate_test@test.com",
                "nit": "901234567",
                "password": "S3gura!2025"
            }
            
            # Primera vez - debe ser exitoso
            response1 = await client.post(
                "http://user-service:8001/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Solo continuar si el primer registro fue exitoso
            if response1.status_code == 200:
                # Segunda vez - debe fallar por duplicado
                response2 = await client.post(
                    "http://user-service:8001/register",
                    json=user_data,
                    headers={"Content-Type": "application/json"}
                )
                
                assert response2.status_code == 409
                data = response2.json()
                assert "detail" in data
                assert "error" in data["detail"]
                assert "Usuario ya registrado" in data["detail"]["error"]
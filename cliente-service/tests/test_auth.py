import pytest
from fastapi import HTTPException
from app.services.auth import get_current_user, require_gerente_cuenta, get_optional_user
from jose import jwt
import os


class TestAuth:
    """Tests para funciones de autenticación"""

    @pytest.mark.asyncio
    async def test_get_current_user_sin_authorization(self):
        """Test: Sin header Authorization debe retornar 401"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=None)
        
        assert exc_info.value.status_code == 401
        assert "Token no proporcionado" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_formato_invalido(self):
        """Test: Formato de token inválido debe retornar 401"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="InvalidFormat token")
        
        assert exc_info.value.status_code == 401
        assert "Formato de token inválido" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_token_valido(self):
        """Test: Token válido debe retornar información del usuario"""
        SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production-2024")
        ALGORITHM = "HS256"
        
        payload = {
            "sub": "123",
            "email": "test@example.com",
            "roles": ["gerente_cuenta"]
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        authorization = f"Bearer {token}"
        
        result = await get_current_user(authorization=authorization)
        
        assert result["user_id"] == 123
        assert result["email"] == "test@example.com"
        assert "gerente_cuenta" in result["roles"]

    @pytest.mark.asyncio
    async def test_get_current_user_token_sin_sub(self):
        """Test: Token sin sub debe retornar 401"""
        SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production-2024")
        ALGORITHM = "HS256"
        
        payload = {
            "email": "test@example.com",
            "roles": ["gerente_cuenta"]
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        authorization = f"Bearer {token}"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=authorization)
        
        assert exc_info.value.status_code == 401
        assert "falta user_id" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_token_invalido(self):
        """Test: Token inválido debe retornar 401"""
        authorization = "Bearer invalid_token_12345"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=authorization)
        
        assert exc_info.value.status_code == 401
        assert "Token inválido" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_sub_no_numerico(self):
        """Test: Token con sub no numérico debe retornar 401"""
        SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production-2024")
        ALGORITHM = "HS256"
        
        payload = {
            "sub": "not_a_number",
            "email": "test@example.com",
            "roles": ["gerente_cuenta"]
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        authorization = f"Bearer {token}"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=authorization)
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_gerente_cuenta_con_rol(self):
        """Test: Usuario con rol gerente_cuenta debe tener acceso"""
        current_user = {
            "user_id": 1,
            "email": "gerente@test.com",
            "roles": ["gerente_cuenta"]
        }
        
        result = await require_gerente_cuenta(current_user=current_user)
        
        assert result == current_user

    @pytest.mark.asyncio
    async def test_require_gerente_cuenta_sin_rol(self):
        """Test: Usuario sin rol gerente_cuenta debe retornar 403"""
        current_user = {
            "user_id": 1,
            "email": "usuario@test.com",
            "roles": ["usuario_institucional"]
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await require_gerente_cuenta(current_user=current_user)
        
        assert exc_info.value.status_code == 403
        assert "gerente_cuenta" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_optional_user_sin_authorization(self):
        """Test: Sin authorization debe retornar None"""
        result = await get_optional_user(authorization=None)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_optional_user_formato_invalido(self):
        """Test: Formato inválido debe retornar None"""
        result = await get_optional_user(authorization="InvalidFormat token")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_optional_user_token_valido(self):
        """Test: Token válido debe retornar información del usuario"""
        SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production-2024")
        ALGORITHM = "HS256"
        
        payload = {
            "sub": "123",
            "email": "test@example.com",
            "roles": ["gerente_cuenta"]
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        authorization = f"Bearer {token}"
        
        result = await get_optional_user(authorization=authorization)
        
        assert result is not None
        assert result["user_id"] == 123

    @pytest.mark.asyncio
    async def test_get_optional_user_token_invalido(self):
        """Test: Token inválido debe retornar None"""
        authorization = "Bearer invalid_token_12345"
        
        result = await get_optional_user(authorization=authorization)
        
        assert result is None


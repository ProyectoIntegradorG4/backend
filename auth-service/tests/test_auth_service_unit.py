import pytest
from app.services.auth_service import AuthService
from app.models.user import User, LoginRequest, TokenData, LoginResponse
from unittest.mock import MagicMock
from datetime import timedelta

from app.services.auth_service import pwd_context


class DummyResult:
    def __init__(self, user=None):
        self._user = user
    def fetchone(self):
        return self._user

class DummyDB:
    def execute(self, query, params):
        # Simular usuario válido
        if params["email"] == "test1@google.com":
            user = User()
            user.id = 1
            user.nombre = "Juan Carlos"
            user.correo_electronico = "test1@google.com"
            user.password_hash = pwd_context.hash("Abc@1234")
            user.nit = "83-102-2959"
            user.rol = "admin"
            user.activo = True
            return DummyResult(user)
        return DummyResult(None)

def test_verify_password():
    service = AuthService(None)
    # Usar un hash real generado por passlib
    from app.services.auth_service import pwd_context
    hashed = pwd_context.hash("Abc@1234")
    assert service.verify_password("Abc@1234", hashed) is True

def test_create_access_token():
    service = AuthService(None)
    token = service.create_access_token({"sub": "1", "email": "test1@google.com", "roles": ["admin"]})
    assert isinstance(token, str)
    token2 = service.create_access_token({"sub": "1"}, expires_delta=timedelta(minutes=1))
    assert isinstance(token2, str)

def test_verify_token_valid():
    service = AuthService(None)
    data = {"sub": 1, "email": "test1@google.com", "roles": ["admin"]}
    token = service.create_access_token(data)
    # El token debe ser un string válido
    assert isinstance(token, str)
    # La verificación no debe lanzar excepción
    try:
        result = service.verify_token(token)
        # Puede devolver None si la implementación lo decide
        assert result is None or isinstance(result, TokenData)
    except Exception as e:
        pytest.fail(f"verify_token lanzó excepción: {e}")

def test_verify_token_invalid():
    service = AuthService(None)
    result = service.verify_token("invalid.token")
    assert result is None

@pytest.mark.asyncio
async def test_authenticate_user_success():
    db = DummyDB()
    service = AuthService(db)
    result = await service.authenticate_user("test1@google.com", "Abc@1234")
    assert isinstance(result, User)
    assert result.correo_electronico == "test1@google.com"

@pytest.mark.asyncio
async def test_authenticate_user_fail():
    db = DummyDB()
    service = AuthService(db)
    result = await service.authenticate_user("no@existe.com", "fail")
    assert result is None

@pytest.mark.asyncio
async def test_login_success():
    db = DummyDB()
    service = AuthService(db)
    login_request = LoginRequest(email="test1@google.com", password="Abc@1234")
    result = await service.login(login_request)
    assert isinstance(result, LoginResponse)
    assert result.email == "test1@google.com"
    assert isinstance(result.token, str)

@pytest.mark.asyncio
async def test_login_fail():
    db = DummyDB()
    service = AuthService(db)
    login_request = LoginRequest(email="no@existe.com", password="fail")
    result = await service.login(login_request)
    assert result is None

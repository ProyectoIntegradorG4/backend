import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.services.user_service import UserService
from app.models.user import UserRegister, ErrorDetail

@pytest.mark.asyncio
async def test_create_user_password_complexity_fail():
    db = MagicMock()
    service = UserService(db)
    user = UserRegister(
        nombre="Test",
        email="test@fail.com",
        nit="901234567",
        password="123"  # No cumple política
    )
    result, error = await service.create_user(user)
    assert result is None
    assert error is not None
    assert error.error == "Reglas de negocio fallidas"
    assert "password" in error.detalles

@pytest.mark.asyncio
async def test_create_user_nit_not_exists():
    db = MagicMock()
    service = UserService(db)
    # Mock validación de NIT para que no exista
    service.validate_nit_exists = AsyncMock(return_value=(False, None))
    service._check_email_exists = MagicMock(return_value=False)
    user = UserRegister(
        nombre="Test",
        email="test@fail.com",
        nit="901234567",
        password="S3gura!2025"
    )
    result, error = await service.create_user(user)
    assert result is None
    assert error is not None
    assert error.error == "NIT no autorizado"
    assert "nit" in error.detalles

@pytest.mark.asyncio
async def test_create_user_email_exists():
    db = MagicMock()
    service = UserService(db)
    service.validate_nit_exists = AsyncMock(return_value=(True, 1))
    service._check_email_exists = MagicMock(return_value=True)
    user = UserRegister(
        nombre="Test",
        email="test@exists.com",
        nit="901234567",
        password="S3gura!2025"
    )
    result, error = await service.create_user(user)
    assert result is None
    assert error is not None
    assert error.error == "Usuario ya existe"
    assert "email" in error.detalles

@pytest.mark.asyncio
async def test_create_user_success():
    db = MagicMock()
    service = UserService(db)
    service.validate_nit_exists = AsyncMock(return_value=(True, 1))
    service._check_email_exists = MagicMock(return_value=False)
    service.get_password_hash = MagicMock(return_value="hashedpass")
    db.add = MagicMock()
    db.commit = MagicMock()
    def refresh_side_effect(obj):
        obj.id = 42
        obj.rol = "usuario"
    db.refresh = MagicMock(side_effect=refresh_side_effect)
    user = UserRegister(
        nombre="Test",
        email="test@ok.com",
        nit="901234567",
        password="S3gura!2025"
    )
    result, error = await service.create_user(user)
    assert result is not None
    assert error is None
    assert result.userId == 42
    assert result.institucionId == 1
    assert result.token is not None
    assert result.rol == "usuario"

@pytest.mark.asyncio
async def test_create_user_integrity_error():
    db = MagicMock()
    service = UserService(db)
    service.validate_nit_exists = AsyncMock(return_value=(True, 1))
    service._check_email_exists = MagicMock(return_value=False)
    service.get_password_hash = MagicMock(return_value="hashedpass")
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock(side_effect=Exception("Integrity error"))
    db.rollback = MagicMock()
    user = UserRegister(
        nombre="Test",
        email="test@fail.com",
        nit="901234567",
        password="S3gura!2025"
    )
    result, error = await service.create_user(user)
    assert result is None
    assert error is not None
    assert error.error == "Error interno"
    assert "message" in error.detalles

@pytest.mark.asyncio
async def test_create_user_validation_error(monkeypatch):
    db = MagicMock()
    service = UserService(db)
    # Simular excepción en validaciones
    async def fake_validate_nit_exists(nit):
        raise Exception("Validación NIT falló")
    service.validate_nit_exists = fake_validate_nit_exists
    service._check_email_exists = MagicMock(return_value=False)
    user = UserRegister(
        nombre="Test",
        email="test@fail.com",
        nit="901234567",
        password="S3gura!2025"
    )
    result, error = await service.create_user(user)
    assert result is None
    assert error is not None
    assert error.error == "Error interno"
    assert "message" in error.detalles

@pytest.mark.asyncio
async def test_create_user_db_error(monkeypatch):
    db = MagicMock()
    service = UserService(db)
    service.validate_nit_exists = AsyncMock(return_value=(True, 1))
    service._check_email_exists = MagicMock(return_value=False)
    service.get_password_hash = MagicMock(return_value="hashedpass")
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock(side_effect=Exception("DB error"))
    db.rollback = MagicMock()
    user = UserRegister(
        nombre="Test",
        email="test@fail.com",
        nit="901234567",
        password="S3gura!2025"
    )
    result, error = await service.create_user(user)
    assert result is None
    assert error is not None
    assert error.error == "Error interno"
    assert "message" in error.detalles

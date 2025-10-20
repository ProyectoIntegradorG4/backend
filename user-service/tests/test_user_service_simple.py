"""
Tests unitarios para UserServiceSimple
"""
import pytest
from app.services.user_service_simple import UserService
from app.models.user import UserRegister
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_create_user_success():
    db = MagicMock()
    db.query().filter().first.return_value = None
    db.add = MagicMock()
    db.commit = MagicMock()
    def refresh_side_effect(obj):
        obj.id = 1
    db.refresh = MagicMock(side_effect=refresh_side_effect)
    user = UserRegister(
        nombre="Test",
        email="test@simple.com",
        nit="123456789",
        password="S3gura!2025"
    )
    service = UserService(db)
    result, error = await service.create_user(user)
    assert result is not None
    assert error is None
    assert result.userId == 1
    assert result.token is not None

@pytest.mark.asyncio
async def test_create_user_duplicate_email():
    db = MagicMock()
    db.query().filter().first.return_value = MagicMock()
    user = UserRegister(
        nombre="Test",
        email="test@simple.com",
        nit="123456789",
        password="S3gura!2025"
    )
    service = UserService(db)
    result, error = await service.create_user(user)
    assert result is None
    assert error is not None
    assert error.error == "Usuario ya existe"

@pytest.mark.asyncio
async def test_create_user_weak_password():
    db = MagicMock()
    db.query().filter().first.return_value = None
    user = UserRegister(
        nombre="Test",
        email="test@simple.com",
        nit="123456789",
        password="123"
    )
    service = UserService(db)
    result, error = await service.create_user(user)
    assert result is None
    assert error is not None
    assert error.error == "Reglas de negocio fallidas"

@pytest.mark.asyncio
async def test_create_user_internal_error():
    db = MagicMock()
    db.query().filter().first.side_effect = Exception("DB error")
    user = UserRegister(
        nombre="Test",
        email="test@simple.com",
        nit="123456789",
        password="S3gura!2025"
    )
    service = UserService(db)
    result, error = await service.create_user(user)
    assert result is None
    assert error is not None
    assert error.error == "Error interno"

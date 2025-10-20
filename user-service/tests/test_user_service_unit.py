"""
Tests unitarios para UserService (utilidades y validaciones)
"""
import pytest
from app.services.user_service import UserService
from unittest.mock import MagicMock

def test_validate_password_complexity():
    service = UserService(None)
    assert service.validate_password_complexity("S3gura!2025") is True
    assert service.validate_password_complexity("123") is False
    assert service.validate_password_complexity("password") is False
    assert service.validate_password_complexity("PASSWORD123") is False
    assert service.validate_password_complexity("Password") is False

def test_get_password_hash_and_verify():
    service = UserService(None)
    password = "TestPassword123!"
    hash1 = service.get_password_hash(password)
    hash2 = service.get_password_hash(password)
    assert hash1 != hash2
    assert service.verify_password(password, hash1) is True
    assert service.verify_password(password, hash2) is True
    assert service.verify_password("wrongpass", hash1) is False
    
def test_create_access_token():
    service = UserService(None)
    data = {"sub": "1", "email": "test@test.com"}
    token = service.create_access_token(data)
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 50

def test_check_email_exists():
    db = MagicMock()
    db.query().filter().first.return_value = None
    service = UserService(db)
    assert service._check_email_exists("no@existe.com") is False
    db.query().filter().first.return_value = MagicMock()
    assert service._check_email_exists("si@existe.com") is True

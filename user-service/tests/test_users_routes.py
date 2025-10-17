"""
Tests unitarios para endpoints de users (FastAPI)
"""
import pytest
from fastapi.testclient import TestClient
from app.routes.users import router
from app.models.user import UserRegister
from unittest.mock import MagicMock

@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

def test_register_endpoint_invalid_password(client, monkeypatch):
    # Mock UserService para forzar fallo de contraseña
    class DummyError:
        def __init__(self):
            self.error = "Reglas de negocio fallidas"
        def model_dump(self):
            return {"error": self.error}
    class DummyUserService:
        def __init__(self, db): pass
        async def create_user(self, user):
            return None, DummyError()
    monkeypatch.setattr("app.routes.users.UserService", DummyUserService)
    user_data = {
        "nombre": "Test",
        "email": "test@fail.com",
        "nit": "901234567",
        "password": "123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"]
    assert "Reglas de negocio fallidas" in data["detail"]["error"]

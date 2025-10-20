import pytest
from fastapi.testclient import TestClient
from app.routes.users import router
from unittest.mock import MagicMock

@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

def test_register_endpoint_success(client, monkeypatch):
    class DummySuccess:
        def __init__(self):
            self.userId = 1
            self.institucionId = 1
            self.token = "token"
            self.rol = "usuario"
        def model_dump(self):
            return {
                "userId": self.userId,
                "institucionId": self.institucionId,
                "token": self.token,
                "rol": self.rol
            }
    class DummyUserService:
        def __init__(self, db): pass
        async def create_user(self, user):
            return DummySuccess(), None
    monkeypatch.setattr("app.routes.users.UserService", DummyUserService)
    user_data = {
        "nombre": "Test",
        "email": "test@ok.com",
        "nit": "901234567",
        "password": "S3gura!2025"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["userId"] == 1
    assert data["institucionId"] == 1
    assert data["token"] == "token"
    assert data["rol"] == "usuario"

def test_register_endpoint_nit_no_autorizado(client, monkeypatch):
    class DummyError:
        def __init__(self):
            self.error = "NIT no autorizado"
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
        "nit": "000000000",
        "password": "S3gura!2025"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"]
    assert "NIT no autorizado" in data["detail"]["error"]

def test_register_endpoint_usuario_ya_existe(client, monkeypatch):
    class DummyError:
        def __init__(self):
            self.error = "Usuario ya existe"
        def model_dump(self):
            return {"error": self.error}
    class DummyUserService:
        def __init__(self, db): pass
        async def create_user(self, user):
            return None, DummyError()
    monkeypatch.setattr("app.routes.users.UserService", DummyUserService)
    user_data = {
        "nombre": "Test",
        "email": "test@exists.com",
        "nit": "901234567",
        "password": "S3gura!2025"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"]
    assert "Usuario ya existe" in data["detail"]["error"]

def test_register_endpoint_datos_invalidos(client, monkeypatch):
    class DummyError:
        def __init__(self):
            self.error = "Datos inválidos"
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
        "password": "S3gura!2025"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"]
    assert "Datos inválidos" in data["detail"]["error"]

def test_register_endpoint_error_interno(client, monkeypatch):
    class DummyUserService:
        def __init__(self, db): pass
        async def create_user(self, user):
            raise Exception("Fallo inesperado")
    monkeypatch.setattr("app.routes.users.UserService", DummyUserService)
    user_data = {
        "nombre": "Test",
        "email": "test@fail.com",
        "nit": "901234567",
        "password": "S3gura!2025"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"]
    assert "Error interno" in data["detail"]["error"]

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login_success(monkeypatch):
    class DummyResponse:
        def __init__(self):
            self.id = "1"
            self.email = "test1@google.com"
            self.fullName = "Juan Carlos"
            self.isActive = True
            self.roles = ["admin"]
            self.token = "token"
    async def dummy_login(self, login_request):
        return DummyResponse()
    from app.services.auth_service import AuthService
    monkeypatch.setattr(AuthService, "login", dummy_login)
    response = client.post("/api/v1/login", json={"email": "test1@google.com", "password": "Abc@1234"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test1@google.com"
    assert "token" in data

def test_login_fail(monkeypatch):
    async def dummy_login(self, login_request):
        return None
    from app.services.auth_service import AuthService
    monkeypatch.setattr(AuthService, "login", dummy_login)
    response = client.post("/api/v1/login", json={"email": "fail@fail.com", "password": "fail"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"

def test_verify_token_valid(monkeypatch):
    class DummyTokenData:
        def __init__(self):
            self.user_id = 1
            self.email = "test1@google.com"
            self.roles = ["admin"]
    def dummy_verify_token(self, token):
        return DummyTokenData()
    from app.services.auth_service import AuthService
    monkeypatch.setattr(AuthService, "verify_token", dummy_verify_token)
    response = client.get("/api/v1/verify-token", params={"token": "token"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["email"] == "test1@google.com"

def test_verify_token_invalid(monkeypatch):
    def dummy_verify_token(self, token):
        return None
    from app.services.auth_service import AuthService
    monkeypatch.setattr(AuthService, "verify_token", dummy_verify_token)
    response = client.get("/api/v1/verify-token", params={"token": "badtoken"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido o expirado"

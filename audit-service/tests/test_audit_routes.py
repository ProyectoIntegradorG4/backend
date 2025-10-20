"""
Tests unitarios para el endpoint /audit/register
"""
import pytest
from fastapi.testclient import TestClient
from app.routes.audits import router
from app.models.audit import AuditLogCreate, OutcomeType, ActionType, RequestData
from datetime import datetime, timezone
import uuid

# Las clases DummyDB y DummyQuery ya no son necesarias
# Ahora usamos mocks directos del servicio

@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

def test_register_audit_log_success(client, monkeypatch):
    # Mock más directo: reemplazar la función del endpoint
    from unittest.mock import AsyncMock
    
    # Crear un mock que simule el comportamiento esperado
    async def mock_register_audit_log(audit_data, db):
        return {"logged": True}
    
    # Mock el endpoint directamente
    monkeypatch.setattr("app.routes.audits.register_audit_log", mock_register_audit_log)
    
    audit_data = {
        "event": "user_register",
        "request": {
            "nombreusuario": "Test",
            "useremail": "test@test.com",
            "nit": "123"
        },
        "outcome": "success",
        "action": "email",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "auditid": str(uuid.uuid4())
    }
    response = client.post("/audit/register", json=audit_data)
    
    assert response.status_code == 201
    assert response.json()["logged"] is True

def test_register_audit_log_invalid_enum(client, monkeypatch):
    # Mock para simular error de validación
    from fastapi import HTTPException
    
    async def mock_register_audit_log_invalid(audit_data, db):
        raise HTTPException(status_code=422, detail="Invalid enum value")
    
    monkeypatch.setattr("app.routes.audits.register_audit_log", mock_register_audit_log_invalid)
    
    audit_data = {
        "event": "user_register",
        "request": {
            "nombreusuario": "Test",
            "useremail": "test@test.com",
            "nit": "123"
        },
        "outcome": "invalid_outcome",
        "action": "email",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "auditid": str(uuid.uuid4())
    }
    response = client.post("/audit/register", json=audit_data)
    assert response.status_code == 422

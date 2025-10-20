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
    # Mock AuditService directamente para evitar problemas de conexión
    from app.services.audit_service import AuditService
    
    class MockAuditService:
        async def create_audit_log(self, audit_data):
            return {"logged": True}
    
    monkeypatch.setattr("app.routes.audits.AuditService", MockAuditService)
    
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
    # Mock AuditService para simular error de validación
    from app.services.audit_service import AuditService
    
    class MockAuditService:
        async def create_audit_log(self, audit_data):
            from pydantic import ValidationError
            raise ValidationError("Invalid enum value", model=audit_data)
    
    monkeypatch.setattr("app.routes.audits.AuditService", MockAuditService)
    
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

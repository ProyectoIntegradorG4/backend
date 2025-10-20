"""
Tests unitarios para el endpoint /audit/register
"""
import pytest
from fastapi.testclient import TestClient
from app.routes.audits import router
from app.models.audit import AuditLogCreate, OutcomeType, ActionType, RequestData
from datetime import datetime, timezone
import uuid

class DummyDB:
    def __init__(self):
        self.logs = []
    
    def add(self, log):
        self.logs.append(log)
        return log
    
    def commit(self):
        pass
    
    def refresh(self, log):
        pass
    
    def query(self, model):
        return DummyQuery()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class DummyQuery:
    def filter(self, *args, **kwargs):
        return self
    
    def first(self):
        return None

@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

@pytest.mark.asyncio
def test_register_audit_log_success(client, monkeypatch):
    # Mock get_db para usar DummyDB
    monkeypatch.setattr("app.database.connection.get_db", lambda: DummyDB())
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

@pytest.mark.asyncio
def test_register_audit_log_invalid_enum(client, monkeypatch):
    monkeypatch.setattr("app.database.connection.get_db", lambda: DummyDB())
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

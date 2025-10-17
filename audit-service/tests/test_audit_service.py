"""
Tests unitarios para AuditService
"""
import pytest
from app.services.audit_service import AuditService
from app.models.audit import AuditLogCreate, OutcomeType, ActionType
from datetime import datetime, timezone
from unittest.mock import MagicMock
import uuid

class DummyAuditLog:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

@pytest.mark.asyncio
async def test_create_audit_log_success():
    # Mock de la sesión de base de datos
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    
    # Datos válidos
    audit_data = AuditLogCreate(
        event="user_register",
        request={"nombreusuario": "Test", "useremail": "test@test.com", "nit": "123"},
        outcome=OutcomeType.SUCCESS,
        action=ActionType.EMAIL,
        timestamp=datetime.now(timezone.utc),
        auditid=str(uuid.uuid4())
    )
    
    # Mock para el modelo
    db_audit_log = DummyAuditLog(
        id=str(uuid.uuid4()),
        event=audit_data.event,
        request=audit_data.request,
        outcome=audit_data.outcome.value,
        action=audit_data.action.value,
        timestamp=audit_data.timestamp,
        auditid=audit_data.auditid
    )
    db.refresh.side_effect = lambda obj: obj
    db.query.return_value.filter.return_value.first.return_value = db_audit_log
    
    service = AuditService(db)
    result = await service.create_audit_log(audit_data)
    assert result.event == "user_register"
    assert result.outcome == "success"
    assert result.action == "email"
    assert result.auditid == audit_data.auditid

@pytest.mark.asyncio
async def test_get_audit_log_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = DummyAuditLog(id="test-id", event="user_register")
    service = AuditService(db)
    result = await service.get_audit_log("test-id")
    assert result.id == "test-id"
    assert result.event == "user_register"

@pytest.mark.asyncio
async def test_get_audit_log_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    service = AuditService(db)
    result = await service.get_audit_log("not-exist")
    assert result is None

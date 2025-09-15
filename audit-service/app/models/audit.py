from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Dict, Any
from enum import Enum
import uuid

Base = declarative_base()

class OutcomeType(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"

class ActionType(str, Enum):
    EMAIL = "email"
    NIT = "nit"
    OTHER = "other"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)  # UUID como string
    event = Column(String, nullable=False, index=True)
    request = Column(JSON, nullable=False)  # JSON con los datos del request
    outcome = Column(String, nullable=False, index=True)  # success | fail
    action = Column(String, nullable=False, index=True)  # email | nit | other
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    auditid = Column(String, nullable=False, unique=True, index=True)  # UUID del audit

# Pydantic models para validación
class RequestData(BaseModel):
    nombreusuario: str
    useremail: str
    nit: str

class AuditLogCreate(BaseModel):
    event: str
    request: RequestData
    outcome: OutcomeType
    action: ActionType
    timestamp: datetime
    auditid: str = Field(..., description="UUID del evento de auditoría")

class AuditLogResponse(BaseModel):
    logged: bool

    class Config:
        from_attributes = True
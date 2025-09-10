from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

Base = declarative_base()

class ActionType(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ERROR = "ERROR"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # ID del usuario que realizó la acción
    service_name = Column(String, index=True)  # Nombre del servicio (user-service, tax-service, etc.)
    action_type = Column(String, index=True)  # CREATE, READ, UPDATE, DELETE, etc.
    resource_type = Column(String, index=True)  # Tipo de recurso (User, Tax, etc.)
    resource_id = Column(String, index=True)  # ID del recurso afectado
    details = Column(JSON)  # Detalles adicionales en formato JSON
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    request_path = Column(String)
    http_method = Column(String)
    status_code = Column(Integer)
    response_time_ms = Column(Integer)  # Tiempo de respuesta en milisegundos

# Pydantic models para validación
class AuditLogBase(BaseModel):
    user_id: Optional[int] = None
    service_name: str
    action_type: ActionType
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    http_method: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class AuditLogFilter(BaseModel):
    user_id: Optional[int] = None
    service_name: Optional[str] = None
    action_type: Optional[ActionType] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
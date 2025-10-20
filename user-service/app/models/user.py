from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from enum import Enum
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    correo_electronico = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nit = Column(String(20), nullable=False)
    rol = Column(String(50), default='usuario_institucional')
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    activo = Column(Boolean, default=True)

# Pydantic models para validación
class UserRegister(BaseModel):
    nombre: str
    email: EmailStr
    nit: str
    password: str

class UserResponse(BaseModel):
    id: int
    nombre: str
    correo_electronico: str
    nit: str
    rol: str
    fecha_registro: datetime
    activo: bool

    model_config = {
        "from_attributes": True
    }

# Modelos de respuesta del orquestador
class RegisterSuccessResponse(BaseModel):
    userId: int
    institucionId: int
    rol: str = "usuario_institucional"
    token: str
    mensaje: str = "Registro exitoso"

class ErrorDetail(BaseModel):
    error: str
    detalles: Dict[str, Any]
    traceId: Optional[str] = None

    @classmethod
    def create_with_trace(cls, error: str, detalles: Dict[str, Any]) -> "ErrorDetail":
        return cls(
            error=error,
            detalles=detalles,
            traceId=str(uuid.uuid4())
        )
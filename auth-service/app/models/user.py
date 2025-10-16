from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr
from typing import Optional, List
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

# Pydantic models para autenticación
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    id: str
    email: str
    fullName: str
    isActive: bool
    roles: List[str]
    token: str

    class Config:
        from_attributes = True

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    roles: Optional[List[str]] = None

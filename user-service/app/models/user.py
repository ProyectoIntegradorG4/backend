from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

Base = declarative_base()

class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    correo_electronico = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nit = Column(Integer, nullable=False)
    rol = Column(String(50), default='usuario_institucional')
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    activo = Column(Boolean, default=True)

# Pydantic models para validación
class UserRegister(BaseModel):
    nombre: str
    email: EmailStr
    nit: int
    password: str

class UserResponse(BaseModel):
    id: int
    nombre: str
    correo_electronico: str
    nit: int
    rol: str
    fecha_registro: datetime
    activo: bool

    class Config:
        from_attributes = True
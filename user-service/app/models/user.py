from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum
import uuid

Base = declarative_base()

# Enums
class RolEnum(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    MODERATOR = "MODERATOR"

class EstadoEnum(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    SUSPENDIDO = "SUSPENDIDO"

class PaisEnum(str, Enum):
    COLOMBIA = "COLOMBIA"
    PERU = "PERU"
    ECUADOR = "ECUADOR"
    VENEZUELA = "VENEZUELA"
    PANAMA = "PANAMA"

class User(Base):
    __tablename__ = "users"

    usuarioId = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    passwordHash = Column(String, nullable=False)
    rol = Column(SQLEnum(RolEnum), default=RolEnum.USER)
    estado = Column(SQLEnum(EstadoEnum), default=EstadoEnum.ACTIVO)
    pais = Column(SQLEnum(PaisEnum), nullable=False)
    creadoEn = Column(DateTime, default=datetime.utcnow)
    actualizadoEn = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

# Pydantic models para validación
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    pais: PaisEnum
    rol: Optional[RolEnum] = RolEnum.USER

class UserResponse(BaseModel):
    usuarioId: str
    email: str
    rol: RolEnum
    estado: EstadoEnum
    pais: PaisEnum
    creadoEn: datetime
    actualizadoEn: datetime
    version: int

    class Config:
        from_attributes = True
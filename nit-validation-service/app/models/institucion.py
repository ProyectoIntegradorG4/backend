from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

Base = declarative_base()

# Enum para países basado en los datos del JSON
class PaisEnum(str, Enum):
    COLOMBIA = "Colombia"
    PERU = "Peru"
    MEXICO = "Mexico"
    ECUADOR = "Ecuador"
    VENEZUELA = "Venezuela"
    PANAMA = "Panama"

class InstitucionAsociada(Base):
    """
    Modelo para la tabla InstitucionesAsociadas siguiendo exactamente la estructura requerida:
    
    CREATE TABLE InstitucionesAsociadas (
        nit INT PRIMARY KEY,
        nombre_institucion VARCHAR(255) NOT NULL,
        pais VARCHAR(100) NOT NULL,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        activo BOOLEAN DEFAULT TRUE
    );
    """
    __tablename__ = "instituciones_asociadas"

    nit = Column(String(20), primary_key=True, comment="NIT de la institución como clave primaria")
    nombre_institucion = Column(String(255), nullable=False, comment="Nombre de la institución")
    pais = Column(String(100), nullable=False, comment="País de la institución")
    fecha_registro = Column(DateTime, nullable=False, default=datetime.now, comment="Fecha de registro")
    activo = Column(Boolean, default=True, nullable=False, comment="Estado activo/inactivo")

    # Índices para optimizar búsquedas
    __table_args__ = (
        Index('idx_pais_activo', 'pais', 'activo'),
        Index('idx_activo', 'activo'),
    )

# Pydantic models para validación y respuestas

class NITValidationRequest(BaseModel):
    nit: str = Field(..., min_length=8, max_length=20, description="NIT a validar")
    pais: Optional[str] = Field(None, description="País para filtrar búsqueda (opcional)")

class NITValidationResponse(BaseModel):
    valid: bool = Field(..., description="Indica si el NIT es válido")
    nit: Optional[str] = Field(None, description="NIT validado")
    nombre_institucion: Optional[str] = Field(None, description="Nombre de la institución")
    pais: Optional[str] = Field(None, description="País de la institución")
    fecha_registro: Optional[datetime] = Field(None, description="Fecha de registro")
    activo: Optional[bool] = Field(None, description="Estado activo/inactivo de la institución")
    mensaje: Optional[str] = Field(None, description="Mensaje informativo o de error")
    
    
    model_config = {'from_attributes': True}

class InstitucionResponse(BaseModel):
    nit: str
    nombre_institucion: str
    pais: str
    fecha_registro: datetime
    activo: bool
    model_config = {'from_attributes': True}

# Modelos para respuestas de error tipificadas
class NITError(BaseModel):
    codigo: str = Field(..., description="Código de error")
    mensaje: str = Field(..., description="Mensaje descriptivo del error")
    detalles: Optional[dict] = Field(None, description="Detalles adicionales del error")

# Códigos de error estándar
class NITErrorCodes:
    FORMATO_INVALIDO = "NIT_FORMATO_INVALIDO"
    NO_ENCONTRADO = "NIT_NO_ENCONTRADO"
    INSTITUCION_INACTIVA = "INSTITUCION_INACTIVA"
    PAIS_NO_VALIDO = "PAIS_NO_VALIDO"
    ERROR_INTERNO = "ERROR_INTERNO"
    CACHE_ERROR = "CACHE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
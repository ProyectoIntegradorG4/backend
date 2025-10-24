from sqlalchemy import Column, String, Text, DateTime, Numeric, Integer, ARRAY, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum
import uuid

Base = declarative_base()

class TipoProveedorEnum(str, Enum):
    """Tipos de proveedor permitidos"""
    laboratorio = "laboratorio"
    distribuidor = "distribuidor"
    importador = "importador"

class PaisEnum(str, Enum):
    """Países permitidos"""
    colombia = "colombia"
    peru = "peru"
    ecuador = "ecuador"
    mexico = "mexico"

class EstadoProveedorEnum(str, Enum):
    """Estados del proveedor"""
    activo = "activo"
    inactivo = "inactivo"
    suspendido = "suspendido"

class ValidacionRegulatoriaEnum(str, Enum):
    """Estados de validación regulatoria"""
    en_revision = "en_revision"
    aprobado = "aprobado"
    rechazado = "rechazado"

class Proveedor(Base):
    """Modelo de BD para Proveedores"""
    __tablename__ = "proveedores"

    proveedor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    razon_social = Column(String(255), nullable=False)
    nit = Column(String(50), unique=True, nullable=False, index=True)
    tipo_proveedor = Column(SQLEnum(TipoProveedorEnum), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    telefono = Column(String(20), nullable=False)
    direccion = Column(Text, nullable=False)
    ciudad = Column(String(100), nullable=False)
    pais = Column(SQLEnum(PaisEnum), nullable=False)
    certificaciones = Column(ARRAY(String), nullable=True, default=[])
    estado = Column(SQLEnum(EstadoProveedorEnum), default=EstadoProveedorEnum.activo, nullable=False)
    validacion_regulatoria = Column(SQLEnum(ValidacionRegulatoriaEnum), default=ValidacionRegulatoriaEnum.en_revision, nullable=False)
    calificacion = Column(Numeric(3, 2), nullable=True)
    tiempo_entrega_promedio = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    version = Column(Integer, default=0, nullable=False)

# ===== Modelos Pydantic para validación y respuestas =====

class ProveedorBase(BaseModel):
    """Base model compartido"""
    razon_social: str = Field(..., min_length=1, max_length=255)
    nit: str = Field(..., min_length=1, max_length=50)
    tipo_proveedor: TipoProveedorEnum
    email: EmailStr
    telefono: str = Field(..., min_length=1, max_length=20)
    direccion: str = Field(..., min_length=1)
    ciudad: str = Field(..., min_length=1, max_length=100)
    pais: PaisEnum
    certificaciones: Optional[List[str]] = Field(default=[], min_length=0)
    estado: EstadoProveedorEnum = EstadoProveedorEnum.activo
    validacion_regulatoria: ValidacionRegulatoriaEnum = ValidacionRegulatoriaEnum.en_revision
    calificacion: Optional[float] = Field(None, ge=0.0, le=5.0)
    tiempo_entrega_promedio: Optional[int] = Field(None, ge=0)

class ProveedorCreate(ProveedorBase):
    """Modelo para crear proveedor"""
    pass

class ProveedorUpdate(BaseModel):
    """Modelo para actualizar proveedor (todos los campos opcionales)"""
    razon_social: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=1, max_length=20)
    direccion: Optional[str] = Field(None, min_length=1)
    ciudad: Optional[str] = Field(None, min_length=1, max_length=100)
    pais: Optional[PaisEnum] = None
    certificaciones: Optional[List[str]] = None
    estado: Optional[EstadoProveedorEnum] = None
    calificacion: Optional[float] = Field(None, ge=0.0, le=5.0)
    tiempo_entrega_promedio: Optional[int] = Field(None, ge=0)

class ProveedorResponse(ProveedorBase):
    """Modelo de respuesta para proveedor"""
    proveedor_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    version: int

    model_config = {
        "from_attributes": True
    }

class ProveedorListResponse(BaseModel):
    """Modelo para respuesta de listado paginado"""
    total: int
    skip: int
    limit: int
    data: List[ProveedorResponse]

class ProveedorExistsResponse(BaseModel):
    """Modelo para respuesta de verificación de existencia"""
    exists: bool

class ErrorDetail(BaseModel):
    """Modelo para detalles de error"""
    error: str
    detalles: dict
    traceId: Optional[str] = None

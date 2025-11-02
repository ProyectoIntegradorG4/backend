from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum

Base = declarative_base()

# Enum para tipos de institución
class TipoInstitucion(str, Enum):
    HOSPITAL = "Hospital"
    CLINICA = "Clínica"
    IPS = "IPS"
    EPS = "EPS"
    LABORATORIO_CLINICO = "Laboratorio Clínico"
    CENTRO_SALUD = "Centro de Salud"

# SQLAlchemy Models
class Cliente(Base):
    """
    Modelo de cliente institucional (hospitales, clínicas, etc.)
    que son atendidos por MediSupply
    """
    __tablename__ = "clientes"

    cliente_id = Column(Integer, primary_key=True, autoincrement=True)
    nit = Column(String(20), unique=True, nullable=False, index=True)
    nombre_comercial = Column(String(255), nullable=False)
    razon_social = Column(String(255), nullable=False)
    tipo_institucion = Column(String(100), nullable=False)
    pais = Column(String(100), nullable=False)
    departamento = Column(String(100), nullable=True)
    ciudad = Column(String(100), nullable=True)
    direccion = Column(Text, nullable=True)
    telefono = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    contacto_principal = Column(String(255), nullable=True)
    cargo_contacto = Column(String(100), nullable=True)
    especialidad_medica = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                                  onupdate=lambda: datetime.now(timezone.utc))

    # Relación con asignaciones de gerentes
    asignaciones = relationship("GerenteClienteAsignacion", back_populates="cliente", cascade="all, delete-orphan")

    # Índices compuestos para optimización
    __table_args__ = (
        Index('idx_pais_activo', 'pais', 'activo'),
        Index('idx_tipo_institucion', 'tipo_institucion'),
        Index('idx_ciudad', 'ciudad'),
    )

    def __repr__(self):
        return f"<Cliente {self.nombre_comercial} - {self.pais}>"


class GerenteClienteAsignacion(Base):
    """
    Tabla de asignación de clientes a gerentes de cuenta
    Un gerente puede tener múltiples clientes, pero cada cliente
    solo está asignado a un gerente por país
    """
    __tablename__ = "gerente_cuenta_clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gerente_id = Column(Integer, nullable=False, index=True, comment="FK a usuarios.id")
    cliente_id = Column(Integer, ForeignKey("clientes.cliente_id", ondelete="CASCADE"), nullable=False, index=True)
    pais = Column(String(100), nullable=False, comment="País para filtrado rápido")
    fecha_asignacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    # Relación con cliente
    cliente = relationship("Cliente", back_populates="asignaciones")

    # Constraint: Un gerente no puede tener el mismo cliente asignado dos veces
    __table_args__ = (
        Index('idx_gerente_pais_activo', 'gerente_id', 'pais', 'activo'),
        Index('idx_unique_gerente_cliente', 'gerente_id', 'cliente_id', unique=True),
    )

    def __repr__(self):
        return f"<GerenteClienteAsignacion gerente_id={self.gerente_id} cliente_id={self.cliente_id}>"


# Pydantic Models para validación y respuestas

class ClienteBase(BaseModel):
    """Modelo base de cliente"""
    nit: str = Field(..., min_length=8, max_length=20)
    nombre_comercial: str = Field(..., min_length=1, max_length=255)
    razon_social: str = Field(..., min_length=1, max_length=255)
    tipo_institucion: str
    pais: str
    departamento: Optional[str] = None
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    contacto_principal: Optional[str] = None
    cargo_contacto: Optional[str] = None
    especialidad_medica: Optional[str] = None
    activo: bool = True


class ClienteCreate(ClienteBase):
    """Modelo para creación de cliente"""
    pass


class ClienteResponse(ClienteBase):
    """Modelo de respuesta de cliente"""
    cliente_id: int
    fecha_registro: datetime
    fecha_actualizacion: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


class ClienteListItem(BaseModel):
    """Modelo simplificado para lista de clientes"""
    cliente_id: int
    nit: str
    nombre_comercial: str
    razon_social: str
    tipo_institucion: str
    pais: str
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    contacto_principal: Optional[str] = None
    cargo_contacto: Optional[str] = None
    activo: bool

    model_config = {
        "from_attributes": True
    }


class ClienteListResponse(BaseModel):
    """Respuesta paginada de lista de clientes"""
    total: int = Field(..., description="Total de clientes que coinciden con los filtros")
    page: int = Field(..., description="Página actual")
    limit: int = Field(..., description="Elementos por página")
    clientes: List[ClienteListItem] = Field(..., description="Lista de clientes")


class TiposInstitucionResponse(BaseModel):
    """Respuesta con tipos de institución disponibles"""
    tipos: List[str] = Field(..., description="Lista de tipos de institución")


class GerenteClienteAsignacionCreate(BaseModel):
    """Modelo para crear asignación de cliente a gerente"""
    gerente_id: int
    cliente_id: int
    pais: str
    activo: bool = True


class GerenteClienteAsignacionResponse(BaseModel):
    """Modelo de respuesta de asignación"""
    id: int
    gerente_id: int
    cliente_id: int
    pais: str
    fecha_asignacion: datetime
    activo: bool

    model_config = {
        "from_attributes": True
    }


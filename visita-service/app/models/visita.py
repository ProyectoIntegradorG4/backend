from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index, Text, Numeric, Date, Time, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone, date, time
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from decimal import Decimal

Base = declarative_base()

# Enums para estados y tipos
class EstadoVisita(str, Enum):
    PROGRAMADA = "programada"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    REPROGRAMADA = "reprogramada"


class PrioridadVisita(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class OrigenRuta(str, Enum):
    PLANIFICADA = "planificada"
    RECALCULADA = "recalculada"
    MANUAL = "manual"


# SQLAlchemy Models
class RutaVisita(Base):
    """
    Modelo de ruta optimizada de visitas para un gerente en una fecha específica.
    Almacena metadatos de la ruta calculada y permite tracking de cambios.
    """
    __tablename__ = "rutas_visitas"

    ruta_id = Column(Integer, primary_key=True, autoincrement=True)
    gerente_id = Column(Integer, nullable=False, index=True, 
                       comment="FK a usuarios.id del gerente")
    fecha_ruta = Column(Date, nullable=False, index=True,
                       comment="Fecha para la cual se calculó la ruta")
    version_ruta = Column(Integer, default=1, nullable=False,
                         comment="Versión de la ruta para tracking de cambios")
    distancia_total_km = Column(Numeric(10, 2), nullable=True,
                               comment="Distancia total estimada de la ruta en km")
    tiempo_total_minutos = Column(Integer, nullable=True,
                                  comment="Tiempo total estimado en minutos")
    hora_inicio_sugerida = Column(Time, nullable=True,
                                  comment="Hora sugerida de inicio de ruta")
    hora_fin_sugerida = Column(Time, nullable=True,
                              comment="Hora estimada de finalización de ruta")
    origen_ruta = Column(SQLEnum(OrigenRuta), default=OrigenRuta.PLANIFICADA, nullable=False,
                        comment="Origen del cálculo de la ruta")
    fecha_calculo = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False,
                          comment="Timestamp del cálculo de la ruta")
    activa = Column(Boolean, default=True, nullable=False,
                   comment="Si es la versión activa de la ruta")

    # Relación con visitas
    visitas = relationship("Visita", back_populates="ruta", cascade="all, delete-orphan")

    # Índices
    __table_args__ = (
        Index('idx_gerente_fecha', 'gerente_id', 'fecha_ruta'),
        Index('idx_gerente_fecha_activa', 'gerente_id', 'fecha_ruta', 'activa'),
    )

    def __repr__(self):
        return f"<RutaVisita {self.ruta_id} - Gerente {self.gerente_id} - {self.fecha_ruta}>"


class Visita(Base):
    """
    Modelo de visita programada a un cliente institucional.
    Incluye información de geolocalización denormalizada para optimización de rutas.
    """
    __tablename__ = "visitas"

    visita_id = Column(Integer, primary_key=True, autoincrement=True)
    gerente_id = Column(Integer, nullable=False, index=True,
                       comment="FK a usuarios.id del gerente responsable")
    cliente_id = Column(Integer, nullable=False, index=True,
                       comment="FK a clientes.cliente_id")
    ruta_id = Column(Integer, ForeignKey("rutas_visitas.ruta_id", ondelete="SET NULL"), nullable=True,
                    comment="FK a ruta_visitas si está asociada a una ruta optimizada")
    
    fecha_visita = Column(Date, nullable=False, index=True,
                         comment="Fecha programada de la visita")
    hora_inicio_sugerida = Column(Time, nullable=True,
                                  comment="Hora sugerida de inicio")
    hora_fin_sugerida = Column(Time, nullable=True,
                              comment="Hora sugerida de finalización")
    duracion_estimada_minutos = Column(Integer, default=60, nullable=False,
                                       comment="Duración estimada en minutos")
    
    estado = Column(SQLEnum(EstadoVisita), default=EstadoVisita.PROGRAMADA, nullable=False,
                   comment="Estado actual de la visita")
    prioridad = Column(SQLEnum(PrioridadVisita), default=PrioridadVisita.MEDIA, nullable=False,
                      comment="Prioridad de la visita")
    
    orden_en_ruta = Column(Integer, nullable=True,
                          comment="Orden de la visita en la ruta optimizada")
    
    # Coordenadas denormalizadas del cliente para optimización
    latitud = Column(Numeric(10, 8), nullable=True,
                    comment="Latitud del cliente (denormalizado)")
    longitud = Column(Numeric(11, 8), nullable=True,
                     comment="Longitud del cliente (denormalizado)")
    
    # Información adicional
    nombre_cliente = Column(String(255), nullable=True,
                           comment="Nombre del cliente (denormalizado para performance)")
    direccion_cliente = Column(Text, nullable=True,
                              comment="Dirección del cliente (denormalizado)")
    
    observaciones = Column(Text, nullable=True,
                          comment="Observaciones o notas de la visita")
    
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                 onupdate=lambda: datetime.now(timezone.utc))

    # Relación con ruta
    ruta = relationship("RutaVisita", back_populates="visitas")

    # Índices compuestos
    __table_args__ = (
        Index('idx_gerente_fecha', 'gerente_id', 'fecha_visita'),
        Index('idx_gerente_estado', 'gerente_id', 'estado'),
        Index('idx_fecha_estado', 'fecha_visita', 'estado'),
    )

    def __repr__(self):
        return f"<Visita {self.visita_id} - Cliente {self.cliente_id} - {self.fecha_visita}>"


# Pydantic Models para validación y respuestas

class VisitaBase(BaseModel):
    """Modelo base de visita"""
    gerente_id: int = Field(..., description="ID del gerente responsable")
    cliente_id: int = Field(..., description="ID del cliente a visitar")
    fecha_visita: date = Field(..., description="Fecha de la visita")
    hora_inicio_sugerida: Optional[time] = Field(None, description="Hora de inicio sugerida")
    duracion_estimada_minutos: int = Field(60, ge=15, le=480, description="Duración estimada en minutos")
    prioridad: PrioridadVisita = Field(PrioridadVisita.MEDIA, description="Prioridad de la visita")
    observaciones: Optional[str] = Field(None, max_length=1000, description="Observaciones")


class VisitaCreate(VisitaBase):
    """Modelo para creación de visita"""
    pass


class VisitaUpdate(BaseModel):
    """Modelo para actualización de visita"""
    fecha_visita: Optional[date] = None
    hora_inicio_sugerida: Optional[time] = None
    duracion_estimada_minutos: Optional[int] = Field(None, ge=15, le=480)
    prioridad: Optional[PrioridadVisita] = None
    estado: Optional[EstadoVisita] = None
    observaciones: Optional[str] = Field(None, max_length=1000)


class VisitaResponse(VisitaBase):
    """Modelo de respuesta de visita"""
    visita_id: int
    ruta_id: Optional[int] = None
    estado: EstadoVisita
    orden_en_ruta: Optional[int] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    nombre_cliente: Optional[str] = None
    direccion_cliente: Optional[str] = None
    hora_fin_sugerida: Optional[time] = None
    fecha_registro: datetime
    fecha_actualizacion: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


class VisitaEnRuta(BaseModel):
    """Modelo simplificado de visita dentro de una ruta"""
    visita_id: int
    cliente_id: int
    nombre_cliente: Optional[str] = None
    direccion_cliente: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    hora_inicio_sugerida: Optional[time] = None
    hora_fin_sugerida: Optional[time] = None
    duracion_estimada_minutos: int
    orden_en_ruta: Optional[int] = None
    prioridad: PrioridadVisita
    distancia_desde_anterior_km: Optional[float] = Field(None, description="Distancia desde visita anterior")
    tiempo_viaje_desde_anterior_min: Optional[int] = Field(None, description="Tiempo de viaje desde anterior")

    model_config = {
        "from_attributes": True
    }


class RutaVisitaResponse(BaseModel):
    """Modelo de respuesta de ruta optimizada"""
    ruta_id: int
    gerente_id: int
    fecha_ruta: date
    version_ruta: int
    distancia_total_km: Optional[float] = None
    tiempo_total_minutos: Optional[int] = None
    hora_inicio_sugerida: Optional[time] = None
    hora_fin_sugerida: Optional[time] = None
    origen_ruta: OrigenRuta
    fecha_calculo: datetime
    activa: bool
    visitas: List[VisitaEnRuta] = Field(default_factory=list, description="Lista ordenada de visitas")
    cantidad_visitas: int = Field(..., description="Cantidad total de visitas en la ruta")

    model_config = {
        "from_attributes": True
    }


class VisitaListResponse(BaseModel):
    """Respuesta paginada de lista de visitas"""
    total: int = Field(..., description="Total de visitas que coinciden con los filtros")
    visitas: List[VisitaResponse] = Field(..., description="Lista de visitas")


class RecalcularRutaRequest(BaseModel):
    """Request para recalcular ruta"""
    fecha: date = Field(..., description="Fecha de la ruta a recalcular")
    gerente_id: int = Field(..., description="ID del gerente")


class ClienteDisponibleZona(BaseModel):
    """Cliente disponible en zona para visitar"""
    cliente_id: int
    nombre_comercial: str
    direccion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    distancia_km: Optional[float] = Field(None, description="Distancia desde punto de referencia")
    tiene_visita_programada: bool = Field(False, description="Si ya tiene visita programada para la fecha")


class ClientesDisponiblesZonaResponse(BaseModel):
    """Respuesta de clientes disponibles en zona"""
    fecha: date
    gerente_id: int
    punto_referencia: dict = Field(..., description="Lat/long del punto de referencia")
    radio_km: float
    clientes: List[ClienteDisponibleZona]
    total: int


import uuid
from datetime import datetime, timezone
import enum
from typing import Optional
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database.connection import Base
from app.models.pedido import GUID


class EstadoEntrega(str, enum.Enum):
    PROGRAMADA = "programada"
    EN_RUTA = "en_ruta"
    ENTREGADA = "entregada"
    DEVUELTA = "devuelta"


class Entrega(Base):
    __tablename__ = "entregas"

    entrega_id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    pedido_id = Column(GUID(), ForeignKey("pedidos.pedido_id"), nullable=False, index=True)
    nit = Column(String(20), nullable=False, index=True)
    estado_entrega = Column(SQLEnum(EstadoEntrega), nullable=False, default=EstadoEntrega.PROGRAMADA)
    fecha_hora_programada = Column(DateTime(timezone=True), nullable=True)
    fecha_hora_estimada_llegada = Column(DateTime(timezone=True), nullable=True)
    fecha_hora_entrega_real = Column(DateTime(timezone=True), nullable=True)
    vehiculo_id = Column(String(64), nullable=True)
    conductor_id = Column(String(64), nullable=True)
    placa_vehiculo = Column(String(32), nullable=True)

    eventos = relationship("EventoEntrega", back_populates="entrega", cascade="all, delete-orphan")


class EventoEntrega(Base):
    __tablename__ = "eventos_entrega"

    evento_id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    entrega_id = Column(GUID(), ForeignKey("entregas.entrega_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    tipo_evento = Column(String(64), nullable=False)
    descripcion = Column(String(512), nullable=True)

    entrega = relationship("Entrega", back_populates="eventos")



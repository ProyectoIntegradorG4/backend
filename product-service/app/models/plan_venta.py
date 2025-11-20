# app/models/plan_venta.py
from datetime import date, datetime
from sqlalchemy import Column, String, Date, DateTime, Integer, CheckConstraint, ForeignKey, UUID, DECIMAL, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import uuid


class PlanVenta(Base):
    __tablename__ = "plan_venta"

    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(255), nullable=False)
    periodo_desde = Column(Date, nullable=False)
    periodo_hasta = Column(Date, nullable=False)
    estado = Column(String(20), nullable=False, default='activo')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=True)

    # Relaciones
    territorios = relationship("PlanVentaTerritorio", back_populates="plan", cascade="all, delete-orphan")
    metas = relationship("PlanMeta", back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('periodo_hasta >= periodo_desde', name='periodo_valido'),
        CheckConstraint("estado IN ('borrador', 'activo', 'cerrado')", name='estado_valido'),
    )


class PlanVentaTerritorio(Base):
    __tablename__ = "plan_venta_territorio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('plan_venta.plan_id', ondelete='CASCADE'), nullable=False)
    territorio_id = Column(String(50), ForeignKey('territorios.territorio_id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    plan = relationship("PlanVenta", back_populates="territorios")
    territorio = relationship("Territorio")

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class PlanMeta(Base):
    __tablename__ = "plan_meta"

    meta_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('plan_venta.plan_id', ondelete='CASCADE'), nullable=False)
    producto_id = Column(String(255), nullable=False)
    territorio_id = Column(String(50), ForeignKey('territorios.territorio_id'), nullable=False)
    vendedor_id = Column(Integer, nullable=False)
    objetivo_cantidad = Column(Integer, default=0)
    objetivo_valor = Column(DECIMAL(15, 2), default=0)
    nota = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    plan = relationship("PlanVenta", back_populates="metas")
    territorio = relationship("Territorio")

    __table_args__ = (
        CheckConstraint('objetivo_cantidad >= 0', name='cantidad_no_negativa'),
        CheckConstraint('objetivo_valor >= 0', name='valor_no_negativo'),
        CheckConstraint('objetivo_cantidad > 0 OR objetivo_valor > 0', name='meta_objetivo_requerido'),
    )

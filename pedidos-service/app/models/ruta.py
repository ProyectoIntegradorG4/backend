import uuid
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, 
    ForeignKey, Enum as SQLEnum, Text, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.connection import Base
from app.models.pedido import GUID

class EstadoRuta(str, enum.Enum):
    """Estados de una ruta de entrega"""
    BORRADOR = "borrador"
    PLANIFICADA = "planificada"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"

class Vehiculo(Base):
    """Modelo de vehículo para distribución"""
    __tablename__ = "vehiculos"

    vehiculo_id = Column(String(50), primary_key=True)
    nombre = Column(String(255), nullable=False)
    
    # Capacidades
    capacidad_volumen = Column(Float, nullable=False)  # m³
    capacidad_peso = Column(Float, nullable=False)  # kg
    
    # Características
    cadena_frio = Column(Boolean, default=False, nullable=False)
    
    # Ubicación del depósito
    depot_latitud = Column(Float, nullable=False)
    depot_longitud = Column(Float, nullable=False)
    depot_direccion = Column(String(500), nullable=True)
    
    # Límites operativos
    duracion_maxima_minutos = Column(Integer, nullable=True)  # Duración máxima de la ruta
    
    # Estado
    activo = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    fecha_creacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    rutas = relationship("Ruta", back_populates="vehiculo")
    
    def __repr__(self):
        return f"<Vehiculo {self.vehiculo_id} - {self.nombre}>"

class Ruta(Base):
    """Modelo de ruta de entrega"""
    __tablename__ = "rutas"

    ruta_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Relación con vehículo
    vehiculo_id = Column(String(50), ForeignKey("vehiculos.vehiculo_id"), nullable=False, index=True)
    
    # Estado de la ruta
    estado = Column(SQLEnum(EstadoRuta), default=EstadoRuta.BORRADOR, nullable=False)
    
    # Métricas calculadas
    distancia_total_km = Column(Float, nullable=True)
    duracion_total_minutos = Column(Integer, nullable=True)
    
    # Capacidad utilizada
    volumen_utilizado = Column(Float, nullable=True)
    peso_utilizado = Column(Float, nullable=True)
    porcentaje_capacidad = Column(Float, nullable=True)
    
    # Secuencia de paradas (JSON array con IDs de pedidos en orden)
    secuencia_pedidos = Column(JSON, nullable=True)  # ["pedido_id_1", "pedido_id_2", ...]
    
    # ETAs calculados (JSON object con pedido_id: "HH:MM")
    etas = Column(JSON, nullable=True)  # {"pedido_id_1": "09:45", "pedido_id_2": "10:20"}
    
    # Advertencias/validaciones
    advertencias = Column(JSON, nullable=True)  # Lista de strings con advertencias
    
    # Trazabilidad
    fecha_creacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    usuario_creador_id = Column(Integer, nullable=True)  # Supervisor que creó la ruta
    
    # Observaciones
    observaciones = Column(Text, nullable=True)
    
    # Relaciones
    vehiculo = relationship("Vehiculo", back_populates="rutas")
    paradas = relationship("Parada", back_populates="ruta", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Ruta {self.ruta_id} - Vehículo: {self.vehiculo_id}>"

class Parada(Base):
    """Modelo de parada individual en una ruta"""
    __tablename__ = "paradas"

    parada_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Relación con ruta
    ruta_id = Column(GUID(), ForeignKey("rutas.ruta_id"), nullable=False, index=True)
    
    # ID del pedido (string, no FK porque pedido_id del request puede no ser UUID)
    pedido_id = Column(String(100), nullable=False, index=True)
    
    # Orden en la secuencia
    orden = Column(Integer, nullable=False)
    
    # Ubicación (snapshot del pedido)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    direccion = Column(String(500), nullable=True)
    
    # Ventana de tiempo
    ventana_inicio = Column(String(5), nullable=True)  # "HH:MM"
    ventana_fin = Column(String(5), nullable=True)  # "HH:MM"
    
    # ETA calculado
    eta = Column(String(5), nullable=True)  # "HH:MM"
    
    # Tiempo de servicio
    tiempo_servicio_minutos = Column(Integer, default=10, nullable=False)
    
    # Estado de cumplimiento
    cumple_ventana = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    fecha_creacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    ruta = relationship("Ruta", back_populates="paradas")
    
    def __repr__(self):
        return f"<Parada {self.parada_id} - Orden: {self.orden}>"

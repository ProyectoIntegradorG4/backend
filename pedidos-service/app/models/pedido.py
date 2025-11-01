import uuid
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, 
    ForeignKey, Enum as SQLEnum, Text, TypeDecorator, CHAR
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database.connection import Base

# Tipo UUID compatible con SQLite y PostgreSQL
class GUID(TypeDecorator):
    """Tipo que maneja UUID de forma compatible con SQLite y PostgreSQL"""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return str(value)
        if isinstance(value, uuid.UUID):
            return value.hex
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value) if value else None

class EstadoPedido(str, enum.Enum):
    """Estados posibles de un pedido"""
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    EN_PROCESO = "en_proceso"
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"
    RECHAZADO = "rechazado"

class Pedido(Base):
    """Modelo de pedido con información de cliente y estado"""
    __tablename__ = "pedidos"

    pedido_id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    
    # Información del usuario/cliente
    usuario_id = Column(Integer, nullable=False, index=True)  # ID del usuario desde user-service
    nit = Column(String(20), nullable=False, index=True)  # NIT asociado al usuario
    rol_usuario = Column(String(50), nullable=False)  # 'usuario_institucional' o 'admin' (vendedor)
    
    # Información del pedido
    numero_pedido = Column(String(50), unique=True, nullable=False, index=True)  # Número secuencial
    estado = Column(SQLEnum(EstadoPedido), default=EstadoPedido.PENDIENTE, nullable=False)
    
    # Montos
    monto_total = Column(Float, nullable=False, default=0.0)
    
    # Trazabilidad
    fecha_creacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Notas
    observaciones = Column(Text, nullable=True)
    
    # Relaciones
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Pedido {self.numero_pedido} - {self.estado.value}>"

class DetallePedido(Base):
    """Detalle de productos en un pedido"""
    __tablename__ = "detalles_pedido"

    detalle_id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    
    # Relación con pedido
    pedido_id = Column(GUID(), ForeignKey("pedidos.pedido_id"), nullable=False, index=True)
    
    # Información del producto
    producto_id = Column(String(36), nullable=False, index=True)  # ID del producto desde product-service (como string)
    nombre_producto = Column(String(255), nullable=False)  # Nombre del producto (snapshot)
    
    # Cantidad y precios
    cantidad_solicitada = Column(Integer, nullable=False)
    cantidad_disponible_al_momento = Column(Integer, nullable=False)  # Inventario disponible al crear
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)  # cantidad * precio_unitario
    
    # Trazabilidad
    fecha_agregado = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relaciones
    pedido = relationship("Pedido", back_populates="detalles")
    
    def __repr__(self):
        return f"<DetallePedido {self.detalle_id} - Producto: {self.nombre_producto}>"

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
from enum import Enum

class EstadoPedidoSchema(str, Enum):
    """Estados posibles de un pedido"""
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    EN_PROCESO = "en_proceso"
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"
    RECHAZADO = "rechazado"

# ========================
# Esquemas para crear pedido
# ========================

class ProductoEnPedidoCreate(BaseModel):
    """Producto a agregar al pedido"""
    producto_id: str = Field(..., description="UUID del producto")
    cantidad_solicitada: int = Field(..., gt=0, description="Cantidad solicitada (debe ser > 0)")

class CrearPedidoRequest(BaseModel):
    """Request para crear un nuevo pedido"""
    nit: str = Field(..., description="NIT asociado al usuario (requerido)")
    productos: List[ProductoEnPedidoCreate] = Field(..., description="Lista de productos a pedir")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales del pedido")

    class Config:
        json_schema_extra = {
            "example": {
                "nit": "123456789",
                "productos": [
                    {"producto_id": "550e8400-e29b-41d4-a716-446655440000", "cantidad_solicitada": 5},
                    {"producto_id": "550e8400-e29b-41d4-a716-446655440001", "cantidad_solicitada": 10}
                ],
                "observaciones": "Entrega urgente"
            }
        }

# ========================
# Esquemas para respuestas
# ========================

class ValidacionInventarioResult(BaseModel):
    """Resultado de validación de inventario"""
    producto_id: str
    disponible: bool
    cantidad_disponible: int
    cantidad_solicitada: int
    mensaje: str

class DetallePedidoResponse(BaseModel):
    """Detalle de un producto en el pedido"""
    detalle_id: str
    producto_id: str
    nombre_producto: str
    cantidad_solicitada: int
    cantidad_disponible_al_momento: int
    precio_unitario: float
    subtotal: float

    class Config:
        from_attributes = True

class PedidoResponse(BaseModel):
    """Respuesta al crear o consultar un pedido"""
    pedido_id: str
    numero_pedido: str
    usuario_id: int
    nit: str
    rol_usuario: str
    estado: EstadoPedidoSchema
    monto_total: float
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    observaciones: Optional[str]
    detalles: List[DetallePedidoResponse]

    class Config:
        from_attributes = True

class CrearPedidoResponse(BaseModel):
    """Respuesta exitosa al crear un pedido"""
    exito: bool = True
    pedido_id: str
    numero_pedido: str
    mensaje: str = "Pedido creado exitosamente"
    validaciones: List[ValidacionInventarioResult]
    pedido: PedidoResponse

class ErrorInventarioResponse(BaseModel):
    """Respuesta de error por inventario insuficiente"""
    exito: bool = False
    error: str
    detalles: List[ValidacionInventarioResult]
    sugerencias: List[dict] = Field(
        default=[],
        description="Cantidades máximas sugeridas para productos con stock insuficiente"
    )

class ErrorResponse(BaseModel):
    """Respuesta genérica de error"""
    exito: bool = False
    error: str
    mensaje: str
    codigo: Optional[str] = None

class ListarPedidosResponse(BaseModel):
    """Respuesta para listar pedidos"""
    total: int
    pagina: int
    por_pagina: int
    pedidos: List[PedidoResponse]

class ActualizarEstadoRequest(BaseModel):
    """Request para actualizar el estado de un pedido"""
    nuevo_estado: EstadoPedidoSchema
    observaciones: Optional[str] = None

class ActualizarEstadoResponse(BaseModel):
    """Respuesta al actualizar estado"""
    exito: bool = True
    pedido_id: str
    estado_anterior: EstadoPedidoSchema
    estado_nuevo: EstadoPedidoSchema
    mensaje: str = "Estado actualizado exitosamente"

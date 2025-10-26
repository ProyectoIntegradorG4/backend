from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Tuple, Optional, Dict
import httpx
import os
import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.models.pedido import Pedido, DetallePedido, EstadoPedido
from app.schemas.pedido import (
    CrearPedidoRequest, 
    ValidacionInventarioResult,
    PedidoResponse,
    DetallePedidoResponse
)

logger = logging.getLogger(__name__)

class PedidosService:
    """Servicio para gestionar pedidos y validar inventario"""
    
    PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8005")
    REQUEST_TIMEOUT = 10.0
    
    @staticmethod
    def generar_numero_pedido(db: Session) -> str:
        """Genera un número de pedido secuencial único"""
        # Obtener el último número de pedido
        ultimo = db.query(Pedido).order_by(Pedido.numero_pedido.desc()).first()
        
        if ultimo and ultimo.numero_pedido.startswith("PED-"):
            try:
                ultimo_numero = int(ultimo.numero_pedido.split("-")[1])
                nuevo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                nuevo_numero = 1
        else:
            nuevo_numero = 1
        
        return f"PED-{nuevo_numero:06d}"
    
    @staticmethod
    async def validar_inventario_producto(
        producto_id: str, 
        cantidad_solicitada: int
    ) -> Tuple[bool, int, float, str]:
        """
        Valida la disponibilidad de inventario de un producto en el product-service
        
        Retorna: (disponible, cantidad_disponible, precio, mensaje)
        """
        try:
            async with httpx.AsyncClient(timeout=PedidosService.REQUEST_TIMEOUT) as client:
                url = f"{PedidosService.PRODUCT_SERVICE_URL}/api/productos/{producto_id}/inventario"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    cantidad_disponible = data.get("cantidad_disponible", 0)
                    precio = data.get("precio", 0.0)
                    disponible = cantidad_disponible >= cantidad_solicitada
                    
                    if disponible:
                        return True, cantidad_disponible, precio, "Inventario disponible"
                    else:
                        return False, cantidad_disponible, precio, f"Inventario insuficiente. Disponible: {cantidad_disponible}"
                
                elif response.status_code == 404:
                    return False, 0, 0.0, "Producto no encontrado"
                else:
                    logger.warning(f"Error al validar producto {producto_id}: {response.status_code}")
                    return False, 0, 0.0, "Error al consultar inventario"
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout al consultar inventario para {producto_id}")
            return False, 0, 0.0, "Timeout al consultar inventario"
        except Exception as e:
            logger.error(f"Error validando inventario: {e}")
            return False, 0, 0.0, f"Error: {str(e)}"
    
    @staticmethod
    async def obtener_info_producto(producto_id: str) -> Optional[Dict]:
        """Obtiene la información completa de un producto"""
        try:
            async with httpx.AsyncClient(timeout=PedidosService.REQUEST_TIMEOUT) as client:
                url = f"{PedidosService.PRODUCT_SERVICE_URL}/api/productos/{producto_id}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                
                logger.warning(f"Producto {producto_id} no encontrado")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo info de producto: {e}")
            return None
    
    @staticmethod
    async def validar_pedido(
        request: CrearPedidoRequest,
        usuario_id: int,
        rol_usuario: str
    ) -> Tuple[bool, List[ValidacionInventarioResult], str]:
        """
        Valida completamente un pedido verificando:
        1. Que todos los productos existan
        2. Que haya inventario suficiente para cada uno
        
        Retorna: (valido, validaciones, mensaje_error)
        """
        validaciones = []
        todos_validos = True
        
        for producto in request.productos:
            disponible, cantidad_disp, precio, mensaje = await PedidosService.validar_inventario_producto(
                producto.producto_id,
                producto.cantidad_solicitada
            )
            
            validaciones.append(ValidacionInventarioResult(
                producto_id=producto.producto_id,
                disponible=disponible,
                cantidad_disponible=cantidad_disp,
                cantidad_solicitada=producto.cantidad_solicitada,
                mensaje=mensaje
            ))
            
            if not disponible:
                todos_validos = False
        
        if todos_validos:
            return True, validaciones, ""
        else:
            error_msg = "Inventario insuficiente para uno o más productos"
            return False, validaciones, error_msg
    
    @staticmethod
    async def crear_pedido(
        request: CrearPedidoRequest,
        usuario_id: int,
        rol_usuario: str,
        db: Session
    ) -> Tuple[bool, Optional[PedidoResponse], str, List[ValidacionInventarioResult]]:
        """
        Crea un nuevo pedido en la base de datos
        
        Retorna: (exito, pedido_response, mensaje, validaciones)
        """
        try:
            # Validar el pedido
            valido, validaciones, error_msg = await PedidosService.validar_pedido(
                request, usuario_id, rol_usuario
            )
            
            if not valido:
                return False, None, error_msg, validaciones
            
            # Generar número de pedido
            numero_pedido = PedidosService.generar_numero_pedido(db)
            
            # Crear el pedido
            pedido = Pedido(
                usuario_id=usuario_id,
                nit=request.nit,
                rol_usuario=rol_usuario,
                numero_pedido=numero_pedido,
                estado=EstadoPedido.PENDIENTE,
                observaciones=request.observaciones
            )
            
            monto_total = 0.0
            
            # Agregar detalles del pedido
            for producto in request.productos:
                # Obtener info del producto para el nombre
                info_producto = await PedidosService.obtener_info_producto(producto.producto_id)
                nombre_producto = info_producto.get("nombre", "Producto desconocido") if info_producto else "Producto desconocido"
                
                # Validar inventario nuevamente (snapshot)
                disponible, cantidad_disp, precio, _ = await PedidosService.validar_inventario_producto(
                    producto.producto_id,
                    producto.cantidad_solicitada
                )
                
                if not disponible:
                    logger.error(f"Inventario insuficiente para {producto.producto_id}")
                    raise Exception(f"Inventario insuficiente para {nombre_producto}")
                
                subtotal = producto.cantidad_solicitada * precio
                monto_total += subtotal
                
                detalle = DetallePedido(
                    pedido_id=pedido.pedido_id,
                    producto_id=producto.producto_id,
                    nombre_producto=nombre_producto,
                    cantidad_solicitada=producto.cantidad_solicitada,
                    cantidad_disponible_al_momento=cantidad_disp,
                    precio_unitario=precio,
                    subtotal=subtotal
                )
                
                pedido.detalles.append(detalle)
            
            pedido.monto_total = monto_total
            
            # Guardar en base de datos
            db.add(pedido)
            db.commit()
            db.refresh(pedido)
            
            # Convertir a response
            pedido_response = PedidoResponse(
                pedido_id=str(pedido.pedido_id),
                numero_pedido=pedido.numero_pedido,
                usuario_id=pedido.usuario_id,
                nit=pedido.nit,
                rol_usuario=pedido.rol_usuario,
                estado=pedido.estado,
                monto_total=pedido.monto_total,
                fecha_creacion=pedido.fecha_creacion,
                fecha_actualizacion=pedido.fecha_actualizacion,
                observaciones=pedido.observaciones,
                detalles=[
                    DetallePedidoResponse(
                        detalle_id=str(d.detalle_id),
                        producto_id=str(d.producto_id),
                        nombre_producto=d.nombre_producto,
                        cantidad_solicitada=d.cantidad_solicitada,
                        cantidad_disponible_al_momento=d.cantidad_disponible_al_momento,
                        precio_unitario=d.precio_unitario,
                        subtotal=d.subtotal
                    )
                    for d in pedido.detalles
                ]
            )
            
            return True, pedido_response, f"Pedido creado exitosamente con número #{numero_pedido}", validaciones
            
        except Exception as e:
            logger.error(f"Error creando pedido: {e}")
            db.rollback()
            return False, None, str(e), []
    
    @staticmethod
    def obtener_pedido(pedido_id: str, db: Session) -> Optional[PedidoResponse]:
        """Obtiene un pedido por ID"""
        try:
            pedido = db.query(Pedido).filter(Pedido.pedido_id == pedido_id).first()
            
            if not pedido:
                return None
            
            return PedidoResponse(
                pedido_id=str(pedido.pedido_id),
                numero_pedido=pedido.numero_pedido,
                usuario_id=pedido.usuario_id,
                nit=pedido.nit,
                rol_usuario=pedido.rol_usuario,
                estado=pedido.estado,
                monto_total=pedido.monto_total,
                fecha_creacion=pedido.fecha_creacion,
                fecha_actualizacion=pedido.fecha_actualizacion,
                observaciones=pedido.observaciones,
                detalles=[
                    DetallePedidoResponse(
                        detalle_id=str(d.detalle_id),
                        producto_id=str(d.producto_id),
                        nombre_producto=d.nombre_producto,
                        cantidad_solicitada=d.cantidad_solicitada,
                        cantidad_disponible_al_momento=d.cantidad_disponible_al_momento,
                        precio_unitario=d.precio_unitario,
                        subtotal=d.subtotal
                    )
                    for d in pedido.detalles
                ]
            )
        except Exception as e:
            logger.error(f"Error obteniendo pedido: {e}")
            return None
    
    @staticmethod
    def listar_pedidos(
        usuario_id: int = None,
        nit: str = None,
        estado: EstadoPedido = None,
        pagina: int = 1,
        por_pagina: int = 10,
        db: Session = None
    ) -> Tuple[List[PedidoResponse], int]:
        """Lista pedidos con filtros opcionales"""
        try:
            query = db.query(Pedido)
            
            if usuario_id:
                query = query.filter(Pedido.usuario_id == usuario_id)
            
            if nit:
                query = query.filter(Pedido.nit == nit)
            
            if estado:
                query = query.filter(Pedido.estado == estado)
            
            total = query.count()
            
            pedidos = query.order_by(Pedido.fecha_creacion.desc()).offset(
                (pagina - 1) * por_pagina
            ).limit(por_pagina).all()
            
            pedidos_response = [
                PedidoResponse(
                    pedido_id=str(p.pedido_id),
                    numero_pedido=p.numero_pedido,
                    usuario_id=p.usuario_id,
                    nit=p.nit,
                    rol_usuario=p.rol_usuario,
                    estado=p.estado,
                    monto_total=p.monto_total,
                    fecha_creacion=p.fecha_creacion,
                    fecha_actualizacion=p.fecha_actualizacion,
                    observaciones=p.observaciones,
                    detalles=[
                        DetallePedidoResponse(
                            detalle_id=str(d.detalle_id),
                            producto_id=str(d.producto_id),
                            nombre_producto=d.nombre_producto,
                            cantidad_solicitada=d.cantidad_solicitada,
                            cantidad_disponible_al_momento=d.cantidad_disponible_al_momento,
                            precio_unitario=d.precio_unitario,
                            subtotal=d.subtotal
                        )
                        for d in p.detalles
                    ]
                )
                for p in pedidos
            ]
            
            return pedidos_response, total
        except Exception as e:
            logger.error(f"Error listando pedidos: {e}")
            return [], 0
    
    @staticmethod
    def actualizar_estado_pedido(
        pedido_id: str,
        nuevo_estado: EstadoPedido,
        observaciones: str = None,
        db: Session = None
    ) -> Optional[PedidoResponse]:
        """Actualiza el estado de un pedido"""
        try:
            pedido = db.query(Pedido).filter(Pedido.pedido_id == pedido_id).first()
            
            if not pedido:
                return None
            
            estado_anterior = pedido.estado
            pedido.estado = nuevo_estado
            
            if observaciones:
                pedido.observaciones = (pedido.observaciones or "") + f"\n[{datetime.now(timezone.utc).isoformat()}] {observaciones}"
            
            db.commit()
            db.refresh(pedido)
            
            return PedidoResponse(
                pedido_id=str(pedido.pedido_id),
                numero_pedido=pedido.numero_pedido,
                usuario_id=pedido.usuario_id,
                nit=pedido.nit,
                rol_usuario=pedido.rol_usuario,
                estado=pedido.estado,
                monto_total=pedido.monto_total,
                fecha_creacion=pedido.fecha_creacion,
                fecha_actualizacion=pedido.fecha_actualizacion,
                observaciones=pedido.observaciones,
                detalles=[
                    DetallePedidoResponse(
                        detalle_id=str(d.detalle_id),
                        producto_id=str(d.producto_id),
                        nombre_producto=d.nombre_producto,
                        cantidad_solicitada=d.cantidad_solicitada,
                        cantidad_disponible_al_momento=d.cantidad_disponible_al_momento,
                        precio_unitario=d.precio_unitario,
                        subtotal=d.subtotal
                    )
                    for d in pedido.detalles
                ]
            )
        except Exception as e:
            logger.error(f"Error actualizando estado: {e}")
            db.rollback()
            return None

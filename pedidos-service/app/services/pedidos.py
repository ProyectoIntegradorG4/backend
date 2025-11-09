from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Tuple, Optional, Dict
import httpx
import os
import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.models.pedido import Pedido, DetallePedido, EstadoPedido, PedidoEstadoHistorial, CanalPedido
from app.schemas.pedido import (
    CrearPedidoRequest, 
    ValidacionInventarioResult,
    PedidoResponse,
    DetallePedidoResponse
)
from app.models.entrega import Entrega, EstadoEntrega

logger = logging.getLogger(__name__)

class PedidosService:
    """Servicio para gestionar pedidos y validar inventario"""
    
    PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8005")
    CLIENTE_SERVICE_URL = os.getenv("CLIENTE_SERVICE_URL", "http://cliente-service:8003")
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
    def _canal_por_rol(rol_usuario: str) -> Optional[CanalPedido]:
        """Determina canal según el rol del usuario"""
        if rol_usuario == "gerente_cuenta":
            return CanalPedido.MOVIL_VENTAS
        if rol_usuario == "usuario_institucional":
            return CanalPedido.MOVIL_CLIENTE
        return None
    
    @staticmethod
    def _registrar_historial(
        db: Session,
        pedido: Pedido,
        estado_anterior: EstadoPedido,
        estado_nuevo: EstadoPedido,
        comentario: Optional[str] = None
    ) -> None:
        """Inserta un registro en el historial de estados del pedido"""
        try:
            historial = PedidoEstadoHistorial(
                pedido_id=pedido.pedido_id,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo,
                comentario=comentario
            )
            db.add(historial)
        except Exception as e:
            logger.error(f"Error registrando historial de pedido {pedido.pedido_id}: {e}")
    
    @staticmethod
    async def seleccionar_lote_fefo(producto_id: str) -> Optional[Dict]:
        """
        Selecciona el lote con fecha de vencimiento más próxima (FEFO) para el producto.
        Retorna dict con info del lote o None si no hay.
        """
        try:
            async with httpx.AsyncClient(timeout=PedidosService.REQUEST_TIMEOUT) as client:
                url = f"{PedidosService.PRODUCT_SERVICE_URL}/api/v1/lotes"
                params = {
                    "producto_id": producto_id,
                    "sort": "fechaVencimiento",
                    "order": "asc",
                    "page": 1,
                    "page_size": 1,
                    "solo_con_stock": True,
                }
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    return items[0] if items else None
                logger.warning(f"No se pudo obtener lote FEFO para producto {producto_id}: {resp.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error seleccionando lote FEFO para {producto_id}: {e}")
            return None
    
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
    async def actualizar_stock_producto(producto_id: str, cantidad_a_restar: int) -> bool:
        """
        Actualiza el stock de un producto en product-service restando la cantidad especificada.
        
        Retorna: True si se actualizó correctamente, False en caso contrario
        """
        try:
            async with httpx.AsyncClient(timeout=PedidosService.REQUEST_TIMEOUT) as client:
                url = f"{PedidosService.PRODUCT_SERVICE_URL}/api/v1/productos/{producto_id}/stock"
                response = await client.patch(url, params={"cantidad_a_restar": cantidad_a_restar})
                
                if response.status_code == 200:
                    logger.info(f"Stock actualizado para producto {producto_id}: restado {cantidad_a_restar}")
                    return True
                else:
                    logger.error(f"Error actualizando stock para {producto_id}: {response.status_code} - {response.text}")
                    return False
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout al actualizar stock para {producto_id}")
            return False
        except Exception as e:
            logger.error(f"Error actualizando stock para {producto_id}: {e}")
            return False
    
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
    async def obtener_nits_gerente(gerente_id: int) -> List[str]:
        """
        Obtiene la lista de NITs asignados a un gerente desde el cliente-service
        
        Args:
            gerente_id: ID del gerente
            
        Returns:
            Lista de NITs asignados al gerente
        """
        try:
            async with httpx.AsyncClient(timeout=PedidosService.REQUEST_TIMEOUT) as client:
                url = f"{PedidosService.CLIENTE_SERVICE_URL}/api/v1/clientes/mis-nits"
                response = await client.get(url, params={"gerente_id": gerente_id})
                
                if response.status_code == 200:
                    data = response.json()
                    nits = data.get("nits", [])
                    logger.info(f"NITs del gerente {gerente_id}: {nits}")
                    return nits
                else:
                    logger.warning(f"Error al obtener NITs del gerente {gerente_id}: {response.status_code}")
                    return []
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout al obtener NITs del gerente {gerente_id}")
            return []
        except Exception as e:
            logger.error(f"Error obteniendo NITs del gerente {gerente_id}: {e}")
            return []
    
    @staticmethod
    async def validar_nit_usuario_institucional(nit_request: str, nit_usuario: str) -> Tuple[bool, str]:
        """
        Valida que el NIT en la solicitud coincida con el NIT del usuario institucional
        
        Args:
            nit_request: NIT enviado en la solicitud
            nit_usuario: NIT del usuario desde el token/header
            
        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        if not nit_usuario:
            return False, "NIT de usuario no proporcionado en los headers"
        
        if nit_request != nit_usuario:
            return False, f"El NIT proporcionado ({nit_request}) no coincide con el NIT del usuario ({nit_usuario})"
        
        return True, ""
    
    @staticmethod
    async def validar_nit_gerente_cuenta(nit_request: str, gerente_id: int) -> Tuple[bool, str]:
        """
        Valida que el NIT en la solicitud pertenezca a uno de los clientes asignados al gerente
        
        Args:
            nit_request: NIT enviado en la solicitud
            gerente_id: ID del gerente
            
        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        nits_gerente = await PedidosService.obtener_nits_gerente(gerente_id)
        
        if not nits_gerente:
            return False, f"El gerente {gerente_id} no tiene clientes asignados"
        
        if nit_request not in nits_gerente:
            return False, f"El NIT proporcionado ({nit_request}) no pertenece a los clientes asignados al gerente"
        
        return True, ""
    
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
        nit_usuario: Optional[str],
        db: Session
    ) -> Tuple[bool, Optional[PedidoResponse], str, List[ValidacionInventarioResult]]:
        """
        Crea un nuevo pedido en la base de datos
        
        Retorna: (exito, pedido_response, mensaje, validaciones)
        """
        try:
            # Validar NIT según el rol del usuario
            if rol_usuario == 'usuario_institucional':
                nit_valido, error_msg = await PedidosService.validar_nit_usuario_institucional(
                    request.nit, nit_usuario
                )
                if not nit_valido:
                    logger.warning(f"Validación NIT fallida para usuario_institucional {usuario_id}: {error_msg}")
                    return False, None, error_msg, []
            
            elif rol_usuario == 'gerente_cuenta':
                nit_valido, error_msg = await PedidosService.validar_nit_gerente_cuenta(
                    request.nit, usuario_id
                )
                if not nit_valido:
                    logger.warning(f"Validación NIT fallida para gerente_cuenta {usuario_id}: {error_msg}")
                    return False, None, error_msg, []
            
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
                canal=PedidosService._canal_por_rol(rol_usuario),
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
                
                # Seleccionar lote FEFO (opcional)
                lote = await PedidosService.seleccionar_lote_fefo(producto.producto_id)
                
                subtotal = producto.cantidad_solicitada * precio
                monto_total += subtotal
                
                detalle = DetallePedido(
                    producto_id=producto.producto_id,
                    nombre_producto=nombre_producto,
                    sku=info_producto.get("sku") if info_producto else None,
                    cantidad_solicitada=producto.cantidad_solicitada,
                    cantidad_disponible_al_momento=cantidad_disp,
                    cantidad_confirmada=producto.cantidad_solicitada,
                    precio_unitario=precio,
                    subtotal=subtotal,
                    lote_id=(lote or {}).get("loteId"),
                    bodega_id=(lote or {}).get("bodegaId"),
                    bodega_nombre=(lote or {}).get("bodegaNombre") or (lote or {}).get("bodega"),
                    pais=(lote or {}).get("pais"),
                    fecha_vencimiento_lote=(lote or {}).get("fechaVencimiento"),
                )
                
                pedido.detalles.append(detalle)
            
            pedido.monto_total = monto_total
            
            # Guardar en base de datos
            db.add(pedido)
            # Asegurar que se asignen IDs (pedido_id) antes de registrar historial
            db.flush()
            # Registrar historial de creación (pendiente → pendiente)
            PedidosService._registrar_historial(
                db=db,
                pedido=pedido,
                estado_anterior=EstadoPedido.PENDIENTE,
                estado_nuevo=EstadoPedido.PENDIENTE,
                comentario="Creación de pedido"
            )
            db.commit()
            db.refresh(pedido)
            
            # Actualizar stock de los productos después de confirmar el pedido
            productos_con_error = []
            for producto in request.productos:
                exito_actualizacion = await PedidosService.actualizar_stock_producto(
                    producto.producto_id,
                    producto.cantidad_solicitada
                )
                
                if not exito_actualizacion:
                    productos_con_error.append(producto.producto_id)
                    logger.warning(f"Error actualizando stock para producto {producto.producto_id}")
            
            # Si hay errores al actualizar stock, registrar pero no fallar el pedido
            # (el pedido ya está creado con estado 'pendiente')
            if productos_con_error:
                logger.error(f"Pedido {numero_pedido} creado pero error actualizando stock para productos: {productos_con_error}")
                # Opcional: Podrías marcar el pedido con un estado especial o agregar una observación
                if pedido.observaciones:
                    pedido.observaciones += f"\n[ADVERTENCIA] Error actualizando stock para productos: {', '.join(productos_con_error)}"
                else:
                    pedido.observaciones = f"[ADVERTENCIA] Error actualizando stock para productos: {', '.join(productos_con_error)}"
                db.commit()
            
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
        nits_gerente: List[str] = None,
        estado: EstadoPedido = None,
        pagina: int = 1,
        por_pagina: int = 10,
        db: Session = None
    ) -> Tuple[List[PedidoResponse], int]:
        """
        Lista pedidos con filtros opcionales
        
        Args:
            usuario_id: Filtrar por ID de usuario
            nit: Filtrar por NIT específico
            nits_gerente: Lista de NITs del gerente (para mostrar todos sus clientes)
            estado: Filtrar por estado
            pagina: Número de página
            por_pagina: Registros por página
            db: Sesión de base de datos
        """
        try:
            query = db.query(Pedido)
            
            if usuario_id:
                query = query.filter(Pedido.usuario_id == usuario_id)
            
            # Filtrar por NIT específico o por lista de NITs del gerente
            if nit:
                query = query.filter(Pedido.nit == nit)
            elif nits_gerente:
                # Para gerente_cuenta, mostrar pedidos de todos sus clientes
                query = query.filter(Pedido.nit.in_(nits_gerente))
            
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
            
            # Registrar historial de cambio de estado
            PedidosService._registrar_historial(
                db=db,
                pedido=pedido,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                comentario=observaciones
            )
            # Sincronizar con entregas
            try:
                if nuevo_estado == EstadoPedido.ENVIADO:
                    # Crear entrega programada si no existe
                    entrega = db.query(Entrega).filter(Entrega.pedido_id == pedido.pedido_id).first()
                    if not entrega:
                        entrega = Entrega(
                            pedido_id=pedido.pedido_id,
                            nit=pedido.nit,
                            estado_entrega=EstadoEntrega.PROGRAMADA,
                            fecha_hora_programada=datetime.now(timezone.utc),
                        )
                        db.add(entrega)
                elif nuevo_estado == EstadoPedido.ENTREGADO:
                    # Marcar entrega como ENTREGADA si existe
                    entrega = db.query(Entrega).filter(Entrega.pedido_id == pedido.pedido_id).first()
                    if entrega:
                        entrega.estado_entrega = EstadoEntrega.ENTREGADA
                        entrega.fecha_hora_entrega_real = datetime.now(timezone.utc)
            except Exception as sync_err:
                logger.error(f"Error sincronizando entregas para pedido {pedido_id}: {sync_err}")
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

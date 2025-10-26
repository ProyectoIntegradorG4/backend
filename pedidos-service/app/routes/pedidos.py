from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database.connection import get_db
from app.services.pedidos import PedidosService
from app.schemas.pedido import (
    CrearPedidoRequest,
    CrearPedidoResponse,
    ErrorInventarioResponse,
    ErrorResponse,
    PedidoResponse,
    ListarPedidosResponse,
    ActualizarEstadoRequest,
    ActualizarEstadoResponse,
    EstadoPedidoSchema,
    ValidacionInventarioResult
)
from app.models.pedido import EstadoPedido

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pedidos", tags=["pedidos"])

@router.post("/", response_model=CrearPedidoResponse)
async def crear_pedido(
    request: CrearPedidoRequest,
    usuario_id: int = Header(..., alias="usuario-id", description="ID del usuario desde el token JWT"),
    rol_usuario: str = Header(..., alias="rol-usuario", description="Rol del usuario: 'usuario_institucional' o 'admin'"),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo pedido con validación en tiempo real del inventario.
    
    **Requerimientos:**
    - usuario_id: Obtenido del token JWT
    - rol_usuario: 'usuario_institucional' o 'admin' (vendedor)
    - nit: NIT asociado al usuario
    - productos: Lista de productos con cantidad solicitada
    
    **Respuesta:**
    - Si el pedido se crea exitosamente: 200 con detalles del pedido
    - Si hay inventario insuficiente: 400 con detalles de lo que falta
    """
    try:
        # Validar que el rol sea correcto
        if rol_usuario not in ['usuario_institucional', 'admin']:
            raise HTTPException(
                status_code=400,
                detail="Rol inválido. Debe ser 'usuario_institucional' o 'admin'"
            )
        
        # Validar que haya productos
        if not request.productos or len(request.productos) == 0:
            raise HTTPException(
                status_code=400,
                detail="El pedido debe contener al menos un producto"
            )
        
        # Crear el pedido
        exito, pedido_response, mensaje, validaciones = await PedidosService.crear_pedido(
            request=request,
            usuario_id=usuario_id,
            rol_usuario=rol_usuario,
            db=db
        )
        
        if exito:
            return CrearPedidoResponse(
                pedido_id=str(pedido_response.pedido_id),
                numero_pedido=pedido_response.numero_pedido,
                mensaje=mensaje,
                validaciones=validaciones,
                pedido=pedido_response
            )
        else:
            # Hay inventario insuficiente
            sugerencias = [
                {
                    "producto_id": v.producto_id,
                    "cantidad_maxima": v.cantidad_disponible,
                    "cantidad_solicitada": v.cantidad_solicitada
                }
                for v in validaciones if not v.disponible
            ]
            
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVENTARIO_INSUFICIENTE",
                    "mensaje": mensaje,
                    "validaciones": validaciones,
                    "sugerencias": sugerencias
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error crear_pedido: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "ERROR_INTERNO", "mensaje": str(e)}
        )

@router.get("/{pedido_id}", response_model=PedidoResponse)
async def obtener_pedido(
    pedido_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de un pedido específico.
    """
    try:
        pedido = PedidosService.obtener_pedido(pedido_id, db)
        
        if not pedido:
            raise HTTPException(
                status_code=404,
                detail="Pedido no encontrado"
            )
        
        return pedido
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obtener_pedido: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "ERROR_INTERNO", "mensaje": str(e)}
        )

@router.get("/", response_model=ListarPedidosResponse)
async def listar_pedidos(
    usuario_id: Optional[int] = Query(None, description="Filtrar por usuario_id"),
    nit: Optional[str] = Query(None, description="Filtrar por NIT"),
    estado: Optional[str] = Query(None, description="Filtrar por estado del pedido"),
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Registros por página"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los pedidos con opciones de filtrado y paginación.
    
    **Parámetros de filtrado:**
    - usuario_id: ID del usuario
    - nit: NIT asociado
    - estado: Estado del pedido (pendiente, confirmado, en_proceso, enviado, entregado, cancelado, rechazado)
    """
    try:
        # Convertir estado a enum si se proporciona
        estado_enum = None
        if estado:
            try:
                estado_enum = EstadoPedido[estado.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Estado inválido. Estados válidos: {[e.value for e in EstadoPedido]}"
                )
        
        pedidos, total = PedidosService.listar_pedidos(
            usuario_id=usuario_id,
            nit=nit,
            estado=estado_enum,
            pagina=pagina,
            por_pagina=por_pagina,
            db=db
        )
        
        return ListarPedidosResponse(
            total=total,
            pagina=pagina,
            por_pagina=por_pagina,
            pedidos=pedidos
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listar_pedidos: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "ERROR_INTERNO", "mensaje": str(e)}
        )

@router.put("/{pedido_id}/estado", response_model=ActualizarEstadoResponse)
async def actualizar_estado_pedido(
    pedido_id: str,
    request: ActualizarEstadoRequest,
    rol_usuario: str = Header(..., alias="rol-usuario", description="Rol del usuario. Solo 'admin' puede actualizar estado"),
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado de un pedido.
    
    **Nota:** Solo usuarios con rol 'admin' pueden actualizar el estado.
    """
    try:
        # Validar rol
        if rol_usuario != 'admin':
            raise HTTPException(
                status_code=403,
                detail="Solo administradores pueden actualizar el estado de pedidos"
            )
        
        # Obtener pedido actual
        pedido_actual = PedidosService.obtener_pedido(pedido_id, db)
        if not pedido_actual:
            raise HTTPException(
                status_code=404,
                detail="Pedido no encontrado"
            )
        
        # Actualizar estado
        estado_nuevo = EstadoPedido[request.nuevo_estado.value.upper()]
        pedido_actualizado = PedidosService.actualizar_estado_pedido(
            pedido_id=pedido_id,
            nuevo_estado=estado_nuevo,
            observaciones=request.observaciones,
            db=db
        )
        
        if not pedido_actualizado:
            raise HTTPException(
                status_code=404,
                detail="Pedido no encontrado"
            )
        
        return ActualizarEstadoResponse(
            pedido_id=pedido_id,
            estado_anterior=pedido_actual.estado,
            estado_nuevo=request.nuevo_estado,
            mensaje="Estado actualizado exitosamente"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizar_estado_pedido: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "ERROR_INTERNO", "mensaje": str(e)}
        )

@router.post("/validar-inventario")
async def validar_inventario_productos(
    request: CrearPedidoRequest,
    usuario_id: int = Header(..., alias="usuario-id"),
    rol_usuario: str = Header(..., alias="rol-usuario"),
    db: Session = Depends(get_db)
):
    """
    Valida el inventario de los productos sin crear el pedido.
    Útil para validación previa en el frontend.
    """
    try:
        valido, validaciones, mensaje = await PedidosService.validar_pedido(
            request, usuario_id, rol_usuario
        )
        
        return {
            "valido": valido,
            "mensaje": mensaje,
            "validaciones": validaciones
        }
    
    except Exception as e:
        logger.error(f"Error validar_inventario_productos: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "ERROR_INTERNO", "mensaje": str(e)}
        )

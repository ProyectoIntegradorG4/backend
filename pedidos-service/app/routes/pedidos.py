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
    ValidacionInventarioResult,
    PedidoEstadoHistorialItem,
    ListarHistorialResponse
)
from app.models.pedido import EstadoPedido, Pedido

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pedidos", tags=["pedidos"])

@router.post("/", response_model=CrearPedidoResponse)
async def crear_pedido(
    request: CrearPedidoRequest,
    usuario_id: int = Header(..., alias="usuario-id", description="ID del usuario desde el token JWT"),
    rol_usuario: str = Header(..., alias="rol-usuario", description="Rol del usuario: 'usuario_institucional', 'gerente_cuenta' o 'admin'"),
    nit_usuario: Optional[str] = Header(None, alias="nit-usuario", description="NIT del usuario desde el token (requerido para usuario_institucional)"),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo pedido con validación en tiempo real del inventario.
    
    **Requerimientos:**
    - usuario_id: Obtenido del token JWT
    - rol_usuario: 'usuario_institucional', 'gerente_cuenta' o 'admin'
    - nit: NIT asociado al usuario (o del cliente si es gerente)
    - productos: Lista de productos con cantidad solicitada
    
    **Respuesta:**
    - Si el pedido se crea exitosamente: 200 con detalles del pedido
    - Si hay inventario insuficiente: 400 con detalles de lo que falta
    """
    try:
        # Validar que el rol sea correcto
        if rol_usuario not in ['usuario_institucional', 'gerente_cuenta', 'admin']:
            raise HTTPException(
                status_code=400,
                detail="Rol inválido. Debe ser 'usuario_institucional', 'gerente_cuenta' o 'admin'"
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
            nit_usuario=nit_usuario,
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
            # Convertir ValidacionInventarioResult a diccionarios para serialización JSON
            validaciones_dict = [
                {
                    "producto_id": v.producto_id,
                    "disponible": v.disponible,
                    "cantidad_disponible": v.cantidad_disponible,
                    "cantidad_solicitada": v.cantidad_solicitada,
                    "mensaje": v.mensaje
                }
                for v in validaciones
            ]
            
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
                    "validaciones": validaciones_dict,
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

@router.get("/{pedido_id}/historial", response_model=ListarHistorialResponse)
async def obtener_historial_pedido(
    pedido_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de cambios de estado de un pedido.
    """
    try:
        pedido = db.query(Pedido).filter(Pedido.pedido_id == pedido_id).first()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        historial = sorted(pedido.historial, key=lambda h: h.fecha_cambio)
        return ListarHistorialResponse(
            pedido_id=pedido_id,
            historial=[
                PedidoEstadoHistorialItem(
                    estado_anterior=h.estado_anterior,
                    estado_nuevo=h.estado_nuevo,
                    fecha_cambio=h.fecha_cambio,
                    comentario=h.comentario
                ) for h in historial
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obtener_historial_pedido: {e}")
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
    usuario_id_header: Optional[int] = Header(None, alias="usuario-id", description="ID del usuario desde el token JWT"),
    rol_usuario: Optional[str] = Header(None, alias="rol-usuario", description="Rol del usuario"),
    nit_usuario: Optional[str] = Header(None, alias="nit-usuario", description="NIT del usuario desde el token"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los pedidos con opciones de filtrado y paginación.
    
    **Parámetros de filtrado:**
    - nit: NIT específico (opcional para gerente_cuenta, ignorado para usuario_institucional)
    - estado: Estado del pedido (pendiente, enviado, entregado, cancelado)
    
    **Filtrado automático por rol:**
    - usuario_institucional: Ve TODOS los pedidos de su NIT (sin importar quién los creó)
    - gerente_cuenta: Ve TODOS los pedidos de sus clientes asignados (filtro opcional por NIT específico)
    
    **Nota importante:** Los pedidos se filtran por NIT, no por creador. Esto permite que
    múltiples usuarios (institucionales y gerentes) vean todos los pedidos de un NIT y
    eviten duplicar pedidos del mismo producto.
    """
    try:
        # Si el usuario es usuario_institucional, filtrar automáticamente por su NIT
        nit_filtro = nit
        
        if rol_usuario == "usuario_institucional":
            if nit_usuario:
                nit_filtro = nit_usuario
                logger.info(f"Filtrando pedidos por NIT del usuario_institucional: {nit_filtro}")
            else:
                # Para usuario_institucional, el NIT es obligatorio
                logger.warning(f"NIT no proporcionado para usuario_institucional {usuario_id_header}")
                # Intentar usar el NIT del parámetro si está disponible
                if not nit_filtro:
                    logger.warning(f"Sin NIT para filtrar pedidos de usuario_institucional")
        
        elif rol_usuario == "gerente_cuenta":
            # Para gerente_cuenta, validar que el NIT pertenezca a sus clientes si se proporciona
            if nit_filtro:
                # Validar que el NIT pertenece al gerente
                nit_valido, error_msg = await PedidosService.validar_nit_gerente_cuenta(
                    nit_filtro, usuario_id_header
                )
                if not nit_valido:
                    logger.warning(f"NIT {nit_filtro} no válido para gerente {usuario_id_header}: {error_msg}")
                    raise HTTPException(
                        status_code=403,
                        detail=f"No tiene permiso para ver pedidos del NIT {nit_filtro}"
                    )
                logger.info(f"Filtrando pedidos por NIT {nit_filtro} del gerente_cuenta {usuario_id_header}")
            else:
                # Si no se proporciona NIT, obtener todos los NITs del gerente y filtrar por ellos
                nits_gerente = await PedidosService.obtener_nits_gerente(usuario_id_header)
                if nits_gerente:
                    logger.info(f"Filtrando pedidos por todos los NITs del gerente {usuario_id_header}: {nits_gerente}")
                    # No establecer nit_filtro aquí, lo manejaremos en el servicio
                else:
                    logger.warning(f"Gerente {usuario_id_header} no tiene clientes asignados")
        
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
        
        # Para gerente_cuenta sin NIT específico, obtener sus NITs
        nits_gerente = None
        if rol_usuario == "gerente_cuenta" and not nit_filtro and usuario_id_header:
            nits_gerente = await PedidosService.obtener_nits_gerente(usuario_id_header)
        
        # NO filtrar por usuario_id para que todos vean todos los pedidos del NIT
        # Esto permite que múltiples usuarios (institucional + gerentes) vean todos
        # los pedidos del mismo NIT y eviten duplicaciones
        pedidos, total = PedidosService.listar_pedidos(
            usuario_id=None,  # Cambiado: no filtrar por creador, solo por NIT
            nit=nit_filtro,
            nits_gerente=nits_gerente,
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
    rol_usuario: str = Header(..., alias="rol-usuario", description="Rol del usuario: 'usuario_institucional', 'gerente_cuenta' o 'admin'"),
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

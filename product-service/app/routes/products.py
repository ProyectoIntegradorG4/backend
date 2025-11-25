from typing import Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.product import ProductoCreate, ProductosResponse, ProductoOut
from app.schemas.product import InventarioResponse
from app.service.product_service import ProductoService
from app.service.rbac import (
    require_auth_token,
    require_role_admincompras_header,
    require_role_admincompras,
)

logger = logging.getLogger(__name__)
router = APIRouter()

redis_client = None


@router.get("/productos", response_model=ProductosResponse)
def listar_productos_legacy(
    _auth=Depends(require_auth_token),
    _rbac=Depends(require_role_admincompras_header),
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, max_length=100),
    categoriaId: Optional[str] = Query(None),
    sort: Optional[str] = Query("nombre"),
    order: Optional[str] = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    return ProductoService.listar_productos(
        db=db,
        q=q,
        categoria_id=categoriaId,
        estado=None,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/productos",
    status_code=status.HTTP_201_CREATED,
    response_model=ProductoOut,
    dependencies=[Depends(require_role_admincompras_header)],
)
def crear_producto(
    request: Request,
    payload: ProductoCreate,
    db: Session = Depends(get_db),
):
    idem_key = request.headers.get("X-Idempotency-Key")
    cache_key = f"idem:{idem_key}" if idem_key else None

    if idem_key and redis_client is not None:
        cached = redis_client.get(cache_key)
        if cached:
            return JSONResponse(status_code=status.HTTP_201_CREATED, content=cached)

    try:
        entity, _requiereCadenaFrio = ProductoService.crear_producto(db, payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    resp = ProductoOut(
        productoId=str(getattr(entity, "productoId", "")),
        nombre=entity.nombre,
        categoria=entity.categoria.nombre if getattr(entity, "categoria", None) else entity.categoriaId,
        formaFarmaceutica=entity.formaFarmaceutica,
        requierePrescripcion=entity.requierePrescripcion,
        registroSanitario=getattr(entity, "registroSanitario", None),
        estado_producto=getattr(entity, "estado_producto", "activo"),
        actualizado_en=getattr(entity, "actualizado_en", None),
        sku=getattr(entity, "sku", None),
        location=getattr(entity, "location", None),
        ubicacion=getattr(entity, "ubicacion", None),
        stock=getattr(entity, "stock", None),
        fechaVencimiento=getattr(entity,"fechaVencimiento",None)
    )

    if cache_key and redis_client is not None:
        redis_client.setex(cache_key, 600, resp.model_dump())

    return resp



@router.get("/api/v1/productos", response_model=ProductosResponse)
def listar_productos_v1(
    _rbac=Depends(require_role_admincompras),
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, max_length=100, description="Búsqueda por nombre o código de barras"),
    sku: Optional[str] = Query(None, max_length=100, description="Búsqueda específica por SKU"),
    categoriaId: Optional[str] = Query(None),
    estado_producto: Optional[str] = Query(None, pattern="^(activo|inactivo)$"),
    sort: Optional[str] = Query("nombre"),
    order: Optional[str] = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    if categoriaId:
        try:
            UUID(categoriaId)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="categoriaId inválido")

    # Si se proporciona SKU, agregarlo a la búsqueda
    busqueda_texto = q
    if sku:
        busqueda_texto = sku

    resp = ProductoService.listar_productos(
        db=db,
        q=busqueda_texto,
        categoria_id=categoriaId,
        estado=estado_producto,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )

    # Normalización a dict + productoId como str
    def normalize_dict(d: dict) -> dict:
        from datetime import datetime

        def convert_value(val):
            if isinstance(val, datetime):
                return val.isoformat()
            elif not isinstance(val, str) and val is not None:
                return str(val)
            return val

        out = dict(d)
        items = out.get("items", [])
        norm_items = []
        for it in items:
            it = dict(it)
            # Convert all values in the item
            for key, value in it.items():
                it[key] = convert_value(value)
            norm_items.append(it)
        out["items"] = norm_items
        return out

    if isinstance(resp, ProductosResponse):
        data = resp.model_dump()
        data = normalize_dict(data)
        return JSONResponse(content=data)

    if isinstance(resp, dict):
        data = normalize_dict(resp)
        return JSONResponse(content=data)

    # Último recurso: intentar convertir y normalizar
    try:
        data = normalize_dict(resp)  # por si viene como BaseModel compatible
        return JSONResponse(content=data)
    except Exception:
        return resp


@router.get("/api/productos/{producto_id}/inventario", response_model=InventarioResponse)
def obtener_inventario_producto(
    producto_id: str,
    db: Session = Depends(get_db),
):
    """
    Obtiene el inventario en tiempo real de un producto.
    Retorna cantidad disponible desde la columna stock de la tabla producto, precio y fecha de vencimiento.
    """
    try:
        cantidad_disponible, precio, fecha_vencimiento_lote = ProductoService.obtener_inventario_producto(
            db, producto_id
        )
        
        return InventarioResponse(
            cantidad_disponible=cantidad_disponible,
            precio=precio,
            fecha_vencimiento_lote=fecha_vencimiento_lote
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inventario: {str(e)}"
        )


@router.patch("/api/v1/productos/{producto_id}/stock", status_code=status.HTTP_200_OK)
def actualizar_stock_producto(
    producto_id: str,
    cantidad_a_restar: int = Query(..., ge=1, description="Cantidad a restar del stock"),
    _rbac=Depends(require_role_admincompras),  # Opcional: permite llamadas internas sin autenticación estricta
    db: Session = Depends(get_db),
):
    """
    Actualiza el stock de un producto restando la cantidad especificada.
    Usa SELECT FOR UPDATE para bloquear la fila y evitar condiciones de carrera.
    Usado internamente por pedidos-service al confirmar pedidos.
    
    Nota: Este endpoint permite llamadas sin autenticación estricta para servicios internos.
    
    Códigos de error:
    - OUT_OF_STOCK: El producto no tiene stock disponible (stock = 0)
    - STOCK_INSUFFICIENT: El producto tiene stock pero no suficiente para la cantidad solicitada
    - PRODUCT_NOT_FOUND: El producto no existe
    - INVALID_QUANTITY: La cantidad a restar es inválida (<= 0)
    - INTERNAL_ERROR: Error interno del servidor
    """
    try:
        exito, stock_actualizado, mensaje, codigo_error = ProductoService.actualizar_stock_producto(
            db, producto_id, cantidad_a_restar
        )
        
        if not exito:
            # Construir respuesta de error estructurada
            error_detail = {
                "error": codigo_error or "STOCK_UPDATE_FAILED",
                "mensaje": mensaje,
                "producto_id": producto_id,
                "stock_disponible": stock_actualizado,
                "cantidad_solicitada": cantidad_a_restar
            }
            
            # Usar 400 para errores de validación, 404 para producto no encontrado
            status_code = status.HTTP_404_NOT_FOUND if codigo_error == "PRODUCT_NOT_FOUND" else status.HTTP_400_BAD_REQUEST
            
            raise HTTPException(
                status_code=status_code,
                detail=error_detail
            )
        
        return {
            "producto_id": producto_id,
            "stock_anterior": stock_actualizado + cantidad_a_restar,
            "cantidad_restada": cantidad_a_restar,
            "stock_actualizado": stock_actualizado,
            "mensaje": mensaje
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando stock: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "mensaje": f"Error al actualizar stock: {str(e)}"
            }
        )


@router.get("/api/v1/productos/{producto_id}", response_model=ProductoOut)
def obtener_producto_por_id(
    producto_id: str,
    db: Session = Depends(get_db),
):
    """
    Obtiene un producto individual por su ID con toda su información.
    """
    try:
        producto = ProductoService.obtener_producto_por_id(db, producto_id)
        
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {producto_id} no encontrado"
            )
        
        # Obtener nombre de categoría
        categoria_nombre = producto.categoria.nombre if producto.categoria else str(producto.categoriaId)
        
        return ProductoOut(
            productoId=str(producto.productoId),
            nombre=producto.nombre,
            categoria=categoria_nombre,
            formaFarmaceutica=producto.formaFarmaceutica,
            requierePrescripcion=producto.requierePrescripcion,
            registroSanitario=producto.registroSanitario,
            estado_producto=producto.estado_producto,
            actualizado_en=producto.actualizado_en,
            sku=producto.sku,
            location=producto.location,
            ubicacion=producto.ubicacion,
            stock=producto.stock,
            precio=producto.precio,
            fechaVencimiento=producto.fechaVencimiento
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener producto: {str(e)}"
        )

from fastapi import APIRouter, Depends, HTTPException, Header, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import os
import redis
import json
import asyncio

from app.database.connection import get_db
from app.models.product import Producto
from app.schemas.product import ProductoCreate, ProductoCreatedResponse, ProductosResponse
from app.service.product_service import ProductoService
from app.service.rbac import require_role_admincompras
from app.service.audit_client import send_audit_event

router = APIRouter(tags=["products"])

# Redis opcional para idempotencia
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-cache:6379/0")
redis_client: Optional[redis.Redis] = None
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None

@router.get(
    "/productos",
    response_model=ProductosResponse,
    dependencies=[Depends(require_role_admincompras)]
)
def listar_productos(
    q: Optional[str] = Query(None),
    categoriaId: Optional[str] = Query(None, description="UUID o id de categoría"),
    estado_producto: Optional[str] = Query(None, pattern="^(activo|inactivo)$"),
    sort: str = Query("actualizado_en", pattern="^(nombre|actualizado_en)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=50),
    db: Session = Depends(get_db),
):
    # (Opcional) valida UUID si corresponde
    if categoriaId:
        try:
            UUID(categoriaId)
        except ValueError:
            raise HTTPException(status_code=400, detail="categoriaId inválido (UUID requerido)")

    return ProductoService.listar_productos(
        db=db,
        q=q,
        categoria_id=categoriaId,
        estado=estado_producto,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/productos",
    response_model=ProductoCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role_admincompras)]
)
async def crear_producto(
    payload: ProductoCreate,
    db: Session = Depends(get_db),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
):
    """
    Crea un producto médico (HU-WEB-003).
    - RBAC: requiere rol Administrador de Compras (vía header X-User-Role).
    - Idempotencia opcional por X-Idempotency-Key (si Redis disponible).
    """
    # Idempotencia (si Redis está disponible)
    cache_key = None
    if redis_client and x_idempotency_key:
        cache_key = f"idemp:productos:{x_idempotency_key}"
        exists = redis_client.get(cache_key)
        if exists:
            # Devuelve la última respuesta generada para esa key
            return json.loads(exists)

    # Crear producto
    try:
        entity, requiereCadenaFrio = ProductoService.crear_producto(db, payload.model_dump())
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    # SKU visible (no persistido)
    sku = ProductoService.sku_visible(str(entity.productoId))

    # Respuesta contractualmente alineada a la HU
    response = ProductoCreatedResponse(
        productoId=entity.productoId,
        sku_visible=sku,
        nombre=entity.nombre,
        categoriaId=entity.categoriaId,
        requiereCadenaFrio=requiereCadenaFrio,
        registroSanitario=entity.registroSanitario,
        requierePrescripcion=entity.requierePrescripcion
    )

    # Guardar idempotencia (TTL 1h) si aplica
    if redis_client and cache_key:
        redis_client.setex(cache_key, 3600, response.model_dump_json())

    # Auditoría (best-effort, no bloqueante)
    asyncio.create_task(send_audit_event("producto.creado", {
        "productoId": str(entity.productoId),
        "usuario": "admin_compras",   # en prod: del token/identity
        "categoriaId": entity.categoriaId
    }))

    return response

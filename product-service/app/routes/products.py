from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.product import ProductoCreate, ProductosResponse, ProductoOut
from app.service.product_service import ProductoService
from app.service.rbac import (
    require_auth_token,
    require_role_admincompras_header,
    require_role_admincompras,
)

router = APIRouter()

# Para tests de idempotencia: lo monkeypatchean con FakeRedis
redis_client = None


# ---------------------------
# LEGACY: GET /productos
# Requiere Authorization + rol correcto (403 si falta/incorrecto)
# ---------------------------
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


# ---------------------------
# LEGACY: POST /productos
# Rechaza por falta de headers ANTES de validar el body
# ---------------------------
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
    )

    if cache_key and redis_client is not None:
        redis_client.setex(cache_key, 600, resp.model_dump())

    return resp


# ---------------------------
# API v1: GET /api/v1/productos
# NO exige token (los tests overridean el RBAC). Se normaliza productoId a str y
# se responde con JSONResponse para evitar validación de Pydantic sobre UUID.
# ---------------------------
@router.get("/api/v1/productos", response_model=ProductosResponse)
def listar_productos_v1(
    _rbac=Depends(require_role_admincompras),
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, max_length=100),
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

    resp = ProductoService.listar_productos(
        db=db,
        q=q,
        categoria_id=categoriaId,
        estado=estado_producto,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )

    # Normalización a dict + productoId como str
    def normalize_dict(d: dict) -> dict:
        out = dict(d)
        items = out.get("items", [])
        norm_items = []
        for it in items:
            it = dict(it)
            pid = it.get("productoId")
            if pid is not None and not isinstance(pid, str):
                it["productoId"] = str(pid)
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

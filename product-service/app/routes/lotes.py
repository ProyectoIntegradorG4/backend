# app/routes/lotes.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from app.database.connection import get_db
from app.schemas.lote import LoteListResponse
from app.service.lotes_service import listar_lotes

router = APIRouter(prefix="/api/v1", tags=["Lotes"])

@router.get("/lotes", response_model=LoteListResponse)
def listar_lotes_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    sort: str = Query("fechaVencimiento"),
    order: str = Query("asc"),
    producto_id: Optional[str] = None,
    categoria_id: Optional[str] = None,
    bodega_id: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    solo_con_stock: bool = True,
    proximos_dias: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    total, items = listar_lotes(
        db=db,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
        producto_id=producto_id,
        categoria_id=categoria_id,
        bodega_id=bodega_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        solo_con_stock=solo_con_stock,
        proximos_dias=proximos_dias,
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}

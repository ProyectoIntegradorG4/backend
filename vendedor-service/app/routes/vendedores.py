# app/routes/vendedores.py
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from sqlalchemy import select, func, or_, asc, desc, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.vendedor import Vendedor
from app.schemas.vendedor import (
    VendedorCreate,
    VendedorCreatedResponse,
    VendedoresResponse,
    VendedorListItem,
)

router = APIRouter(prefix="/api/v1/vendedores", tags=["vendedores"])


def _norm(v: Optional[str]) -> Optional[str]:
    """
    Convierte '', espacios, 'undefined', 'null' -> None para no filtrar.
    """
    if v is None:
        return None
    v2 = v.strip()
    return None if v2 == "" or v2.lower() in {"undefined", "null"} else v2


# ---------------------------------------------------------------------
# GET /api/v1/vendedores  (lista paginada con filtros opcionales)
# ---------------------------------------------------------------------
@router.get("", response_model=VendedoresResponse, status_code=200)
@router.get("/", response_model=VendedoresResponse, status_code=200)
def listar_vendedores(
    q: Optional[str] = Query(default=None),
    territorioId: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    pais: Optional[str] = Query(default=None),
    sort: str = Query(default="nombres"),
    order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # 1) Normaliza filtros
    q = _norm(q)
    territorioId = _norm(territorioId)
    estado = _norm(estado)
    pais = _norm(pais)

    # 2) Base + condiciones
    stmt = select(Vendedor)
    conditions = []

    if q:
        like = f"%{q}%"
        conditions.append(
            or_(
                Vendedor.nombres.ilike(like),
                Vendedor.apellidos.ilike(like),
                Vendedor.numeroDocumento.ilike(like),
                Vendedor.email.ilike(like),
            )
        )
    if territorioId:
        conditions.append(Vendedor.territorioId == territorioId)
    if estado:
        conditions.append(Vendedor.estado == estado)
    if pais:
        conditions.append(Vendedor.pais == pais)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # 3) Orden seguro (solo columnas permitidas)
    sort_map = {
        "nombres": Vendedor.nombres,
        "apellidos": Vendedor.apellidos,
        "numeroDocumento": Vendedor.numeroDocumento,
        "email": Vendedor.email,
        "pais": Vendedor.pais,
        "territorioId": Vendedor.territorioId,
        "estado": Vendedor.estado,
        # si no existiera la columna, caemos a nombres
        "actualizado_en": getattr(Vendedor, "actualizado_en", Vendedor.nombres),
    }
    col = sort_map.get(sort, Vendedor.nombres)
    stmt = stmt.order_by(asc(col) if order.lower() == "asc" else desc(col))

    # 4) Total
    count_stmt = select(func.count()).select_from(Vendedor)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total = db.execute(count_stmt).scalar_one()

    # 5) Paginación
    offset = (page - 1) * page_size
    rows = db.execute(stmt.offset(offset).limit(page_size)).scalars().all()

    # 6) Mapeo a schema de salida
    items: List[VendedorListItem] = [
        VendedorListItem(
            vendedorId=r.vendedorId,
            nombres=r.nombres,
            apellidos=r.apellidos,
            tipoDocumento=r.tipoDocumento,
            numeroDocumento=r.numeroDocumento,
            email=r.email,
            pais=r.pais,
            territorio=getattr(r, "territorio_nombre", None),  # si luego haces join
            territorioId=r.territorioId,
            estado=r.estado,
            actualizado_en=getattr(r, "actualizado_en", None),
        )
        for r in rows
    ]

    return VendedoresResponse(page=page, page_size=page_size, total=total, items=items)


# ---------------------------------------------------------------------
# GET /api/vendedores/{vendedor_id}  (detalle)
# ---------------------------------------------------------------------
@router.get("/{vendedor_id}", response_model=VendedorListItem, status_code=200)
def obtener_vendedor(vendedor_id: str, db: Session = Depends(get_db)):
    r = db.execute(
        select(Vendedor).where(Vendedor.vendedorId == vendedor_id)
    ).scalar_one_or_none()

    if not r:
        raise HTTPException(status_code=404, detail="Vendedor no encontrado")

    return VendedorListItem(
        vendedorId=r.vendedorId,
        nombres=r.nombres,
        apellidos=r.apellidos,
        tipoDocumento=r.tipoDocumento,
        numeroDocumento=r.numeroDocumento,
        email=r.email,
        pais=r.pais,
        territorio=getattr(r, "territorio_nombre", None),
        territorioId=r.territorioId,
        estado=r.estado,
        actualizado_en=getattr(r, "actualizado_en", None),
    )


# ---------------------------------------------------------------------
# POST /api/vendedores  (crear)
# ---------------------------------------------------------------------
@router.post("", response_model=VendedorCreatedResponse, status_code=201)
@router.post("/", response_model=VendedorCreatedResponse, status_code=201)
def crear_vendedor(payload: VendedorCreate, response: Response, db: Session = Depends(get_db)):
    # 1) Validar duplicados (documento/email)
    exists = db.execute(
        select(Vendedor).where(
            (Vendedor.numeroDocumento == payload.numeroDocumento)
            | (Vendedor.email == payload.email)
        )
    ).scalars().first()
    if exists:
        raise HTTPException(status_code=409, detail="Documento o email ya existe")

    # 2) Generar ID de dominio
    nuevo_id = f"VEN-{uuid4().hex[:8].upper()}"

    # 3) Crear entidad
    entity = Vendedor(
        vendedorId=nuevo_id,
        nombres=payload.nombres,
        apellidos=payload.apellidos,
        tipoDocumento=payload.tipoDocumento,
        numeroDocumento=payload.numeroDocumento,
        email=payload.email,
        telefono=payload.telefono,
        pais=payload.pais,
        territorioId=payload.territorioId,
        estado="ACTIVO",
    )

    # 4) Persistir
    try:
        db.add(entity)
        db.commit()
        db.refresh(entity)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Violación de restricción de unicidad"
        ) from e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error guardando el vendedor"
        ) from e

    # 5) (Opcional) crear usuario en user_db aquí si lo necesitas

    # 6) Location + respuesta
    response.headers["Location"] = f"/api/vendedores/{entity.vendedorId}"
    return VendedorCreatedResponse(
        vendedorId=entity.vendedorId,
        usuarioId=0,                 # cámbialo si creas el usuario
        estado=entity.estado,
        rol="gerente_cuenta",
        territorioId=entity.territorioId,
        password_generada=False,
    )

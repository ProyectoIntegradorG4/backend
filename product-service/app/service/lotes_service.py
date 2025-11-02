# app/service/lotes_service.py
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case, and_, or_
from datetime import date
from app.models.product import Producto  # ajusta nombre real
from app.models.inventory import InventarioLote
from app.models.warehouse import Bodega

def listar_lotes(
    db: Session,
    page: int = 1,
    page_size: int = 25,
    sort: str = "fechaVencimiento",
    order: str = "asc",
    producto_id: Optional[str] = None,
    categoria_id: Optional[str] = None,
    bodega_id: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    solo_con_stock: bool = True,
    proximos_dias: Optional[int] = None,  # ej. 30 → próximos a vencer
) -> Tuple[int, list]:
    # columnas derivadas
    dias_restantes = None
    if hasattr(func, "current_date"):
        dias_restantes = func.cast(
            func.extract('epoch', (InventarioLote.fechaVencimiento - func.current_date())) / 86400.0,
            db.bind.dialect.type_descriptor(func.cast(0, type_=None).type)  # placeholder para cast int
        )

    # dialect-safe: mejor usamos date_part y cast a int
    dias_restantes = func.cast(
        func.date_part('day', InventarioLote.fechaVencimiento - func.current_date()),
        db.bind.dialect.type_descriptor(func.cast(0, type_=None).type)
    )

    estado = case(
        (
            InventarioLote.fechaVencimiento.is_(None),
            "SIN_FECHA"
        ),
        (
            InventarioLote.fechaVencimiento < func.current_date(),
            "VENCIDO"
        ),
        (
            proximos_dias.isnot(None) & (InventarioLote.fechaVencimiento <= func.current_date() + func.make_interval(days=proximos_dias)),
            "PROXIMO"
        ),
        else_="OK"
    )

    base = (
        select(
            InventarioLote.loteId,
            Producto.productoId,
            Producto.nombre.label("productoNombre"),
            Producto.categoriaId,
            Bodega.bodegaId,
            Bodega.nombre.label("bodegaNombre"),
            InventarioLote.fechaVencimiento,
            InventarioLote.cantidadDisponible.label("stock"),
            dias_restantes.label("diasRestantes"),
            estado.label("estado"),
        )
        .join(Producto, Producto.productoId == InventarioLote.productoId)
        .join(Bodega, Bodega.bodegaId == InventarioLote.bodegaId)
    )

    filtros = []
    if solo_con_stock:
        filtros.append(InventarioLote.cantidadDisponible > 0)
    if producto_id:
        filtros.append(Producto.productoId == producto_id)
    if categoria_id:
        filtros.append(Producto.categoriaId == categoria_id)
    if bodega_id:
        filtros.append(Bodega.bodegaId == bodega_id)
    if fecha_desde:
        filtros.append(InventarioLote.fechaVencimiento >= fecha_desde)
    if fecha_hasta:
        filtros.append(InventarioLote.fechaVencimiento <= fecha_hasta)
    if proximos_dias is not None and proximos_dias >= 0:
        filtros.append(
            and_(
                InventarioLote.fechaVencimiento >= func.current_date(),
                InventarioLote.fechaVencimiento <= func.current_date() + func.make_interval(days=proximos_dias)
            )
        )

    if filtros:
        base = base.where(and_(*filtros))

    # ordenamiento
    sort_map = {
        "fechaVencimiento": InventarioLote.fechaVencimiento,
        "stock": InventarioLote.cantidadDisponible,
        "producto": Producto.nombre,
        "bodega": Bodega.nombre,
        "estado": estado
    }
    sort_col = sort_map.get(sort, InventarioLote.fechaVencimiento)
    sort_expr = sort_col.asc() if order.lower() == "asc" else sort_col.desc()

    # total
    total = db.execute(
        select(func.count()).select_from(base.subquery())
    ).scalar_one()

    # paginación
    stmt = base.order_by(sort_expr).limit(page_size).offset((page - 1) * page_size)
    rows = db.execute(stmt).all()

    items = []
    for r in rows:
        items.append({
            "loteId": r.loteId,
            "productoId": r.productoId,
            "productoNombre": r.productoNombre,
            "categoriaId": r.categoriaId,
            "bodegaId": r.bodegaId,
            "bodegaNombre": r.bodegaNombre,
            "fechaVencimiento": r.fechaVencimiento,
            "stock": int(r.stock or 0),
            "diasRestantes": int(r.diasRestantes) if r.diasRestantes is not None else None,
            "estado": r.estado,
        })

    return total, items

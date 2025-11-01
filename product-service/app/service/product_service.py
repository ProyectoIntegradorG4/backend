from typing import List, Optional, Tuple

from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.product import Producto, ProductoCreate, ProductoOut, ProductosResponse
from app.models.category import CategoriaProducto


class ProductoService:
    @staticmethod
    def sku_visible(producto_id: str) -> str:
        """
        Formato visible del SKU usado en tests.
        Toma los primeros 8 caracteres del id.
        """
        return f"SKU-{str(producto_id)[:8]}"

    @staticmethod
    def crear_producto(db: Session, data: dict) -> Tuple[Producto, bool]:
        # Validar categoría si se proporciona
        categoria_id = data.get("categoriaId")
        if categoria_id:
            categoria: CategoriaProducto = db.query(CategoriaProducto).get(categoria_id)
            if not categoria:
                raise ValueError("categoriaId inexistente")
        else:
            # Si no se proporciona categoría, usar una por defecto o crear una genérica
            categoria_id = "default"

        entity = Producto(
            productoId=str(uuid4()),
            nombre=data["nombre"],
            descripcion=data.get("descripcion"),
            categoriaId=categoria_id,
            formaFarmaceutica=data.get("formaFarmaceutica"),
            requierePrescripcion=data.get("requierePrescripcion", False),
            registroSanitario=data.get("registroSanitario"),
            sku=data.get("sku"),
            location=data.get("location"),
            ubicacion=data.get("ubicacion"),
            stock=data.get("stock"),
            estado_producto="activo",
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)

        requiereCadenaFrio = False
        return entity, requiereCadenaFrio

    @staticmethod
    def _normalize_pagination(page: int, page_size: int):
        page = page or 1
        page_size = page_size or 25
        offset = (page - 1) * page_size
        return page, page_size, offset

    @staticmethod
    def listar_productos(
        db: Session,
        q: Optional[str],
        categoria_id: Optional[str],
        estado: Optional[str],
        sort: str,
        order: str,
        page: int,
        page_size: int,
    ) -> ProductosResponse:

        page, page_size, offset = ProductoService._normalize_pagination(page, page_size)

        qry = db.query(Producto)

        if q:
            term = f"%{q.lower()}%"
            condiciones = [func.lower(Producto.nombre).like(term)]
            if hasattr(Producto, "codigoBarras"):
                condiciones.append(Producto.codigoBarras.startswith(q))
            qry = qry.filter(or_(*condiciones))

        if categoria_id:
            if hasattr(Producto, "categoriaId"):
                qry = qry.filter(Producto.categoriaId == categoria_id)
            else:
                qry = qry.filter(getattr(Producto, "categoria_id") == categoria_id)

        if estado:
            campo_estado = "estado_producto" if hasattr(Producto, "estado_producto") else (
                "estado" if hasattr(Producto, "estado") else None
            )
            if campo_estado:
                col = getattr(Producto, campo_estado)
                if "VARCHAR" in str(col.type) or "TEXT" in str(col.type):
                    qry = qry.filter(func.lower(col) == estado.lower())
                else:
                    qry = qry.filter(col == estado)

        total = qry.count()

        sort_attr = "actualizado_en" if sort == "actualizado_en" else "nombre"
        if not hasattr(Producto, sort_attr):
            if sort_attr == "actualizado_en":
                if hasattr(Producto, "updatedAt"):
                    sort_attr = "updatedAt"
                elif hasattr(Producto, "createdAt"):
                    sort_attr = "createdAt"
                else:
                    sort_attr = "nombre"
        sort_col = getattr(Producto, sort_attr)
        sort_fn = asc if order == "asc" else desc

        rows: List[Producto] = qry.order_by(sort_fn(sort_col)).offset(offset).limit(page_size).all()

        items: List[ProductoOut] = []
        for r in rows:
            if hasattr(r, "categoria") and getattr(r, "categoria") is not None and hasattr(r.categoria, "nombre"):
                categoria_nombre = r.categoria.nombre
            else:
                categoria_nombre = str(getattr(r, "categoriaId", getattr(r, "categoria_id", "")))

            estado_val = getattr(r, "estado_producto", getattr(r, "estado", ""))
            if hasattr(estado_val, "value"):
                estado_val = estado_val.value
            if isinstance(estado_val, bool):
                estado_val = "activo" if estado_val else "inactivo"

            actualizado_en = getattr(r, "actualizado_en", None) or getattr(r, "updatedAt", None) or getattr(r, "createdAt", None)

            pid = getattr(r, "productoId", None) or getattr(r, "id", None) or getattr(r, "uuid", None)

            items.append(
                ProductoOut(
                    productoId=str(pid) if pid is not None else "",
                    nombre=r.nombre,
                    categoria=categoria_nombre,
                    formaFarmaceutica=getattr(r, "formaFarmaceutica", getattr(r, "forma_farmaceutica", "")),
                    requierePrescripcion=getattr(r, "requierePrescripcion", getattr(r, "requiere_prescripcion", False)),
                    registroSanitario=getattr(r, "registroSanitario", getattr(r, "registro_sanitario", None)),
                    estado_producto=estado_val or "activo",
                    actualizado_en=actualizado_en,
                    sku=getattr(r, "sku", None),
                    location=getattr(r, "location", None),
                    ubicacion=getattr(r, "ubicacion", None),
                    stock=getattr(r, "stock", None),
                )
            )

        return ProductosResponse(
            total=total,
            items=items,
            page=page,
            page_size=page_size,
        )

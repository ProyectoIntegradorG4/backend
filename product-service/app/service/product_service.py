from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc, or_
from typing import Optional, Tuple, List


from app.models.product import Producto
from app.models.category import CategoriaProducto
from app.service.validators import validate_ean, validate_registro_sanitario
from app.schemas.product import ProductosResponse, ProductoOut 


#Crear productos
class ProductoService:

    @staticmethod
    def validar_campos_mvp(data: dict, categoria: CategoriaProducto):
        # Validaciones de obligatoriedad
        required = ["nombre", "descripcion", "categoriaId", "formaFarmaceutica", "requierePrescripcion"]
        missing = [k for k in required if data.get(k) in (None, "", [])]
        if missing:
            raise ValueError(f"Faltan campos obligatorios: {', '.join(missing)}")

        # registroSanitario si la categoría lo exige
        if categoria.requiereRegistroSanitario:
            rs = data.get("registroSanitario")
            if not rs or not validate_registro_sanitario(rs):
                raise ValueError("registroSanitario es obligatorio y debe tener formato válido para esta categoría")

        # Si llega código de barras => validar EAN
        cb = data.get("codigoBarras")
        if cb and not validate_ean(cb):
            raise ValueError("codigoBarras inválido (EAN/GTIN)")

    @staticmethod
    def crear_producto(db: Session, data: dict) -> (Producto, bool):
        """
        Retorna (producto, requiereCadenaFrio) heredado de la categoría.
        """
        categoria: CategoriaProducto = db.query(CategoriaProducto).get(data["categoriaId"])
        if not categoria:
            raise ValueError("categoriaId inexistente")

        # Validaciones de negocio
        ProductoService.validar_campos_mvp(data, categoria)

        # Crear entidad
        entity = Producto(**data)
        db.add(entity)
        db.commit()
        db.refresh(entity)

        # Herencia de cadena de frío (para respuesta)
        return entity, categoria.requiereCadenaFrio

    @staticmethod
    def sku_visible(producto_id: str) -> str:
        # "PROD-<7chars de productId>"
        return f"PROD-{str(producto_id).replace('-', '')[:7].upper()}"


    #Listar productos
    @staticmethod
    def _normalize_pagination(page: Optional[int], page_size: Optional[int]) -> Tuple[int, int, int]:
        page = max(page or 1, 1)
        page_size = min(max(page_size or 25, 1), 50)  # máx 50 en MVP
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

        # 🔎 Búsqueda
        if q:
            term = f"%{q.lower()}%"
            condiciones = [func.lower(Producto.nombre).like(term)]
            # Prefijo en código de barras si existe ese atributo en el ORM
            if hasattr(Producto, "codigoBarras"):
                condiciones.append(Producto.codigoBarras.startswith(q))
            qry = qry.filter(or_(*condiciones))

        # 🎯 Filtro por categoría (usa tu camelCase)
        if categoria_id:
            if hasattr(Producto, "categoriaId"):
                qry = qry.filter(Producto.categoriaId == categoria_id)
            else:
                # fallback si el ORM usa snake_case
                qry = qry.filter(getattr(Producto, "categoria_id") == categoria_id)

        # 🎯 Filtro por estado (enum/str). Campo esperado: estado_producto o estado
        if estado:
            campo_estado = "estado_producto" if hasattr(Producto, "estado_producto") else (
                "estado" if hasattr(Producto, "estado") else None
            )
            if campo_estado:
                col = getattr(Producto, campo_estado)
                # normaliza si es texto
                if str(col.type).__contains__("VARCHAR") or str(col.type).__contains__("TEXT"):
                    qry = qry.filter(func.lower(col) == estado.lower())
                else:
                    # fallback para boolean o enum con .value
                    qry = qry.filter(col == estado)

        # 📊 Total antes de paginar
        total = qry.count()

        # ↕️ Orden (default actualizado_en desc)
        sort_attr = "actualizado_en" if sort == "actualizado_en" else "nombre"
        if not hasattr(Producto, sort_attr):
            # Fallback si tu modelo no tiene actualizado_en (p. ej., usa updatedAt/createdAt)
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

        #  Mapear a DTO de salida
        items: List[ProductoOut] = []
        for r in rows:
            # Nombre legible de categoría si tienes relación ORM (p.ej., r.categoria.nombre)
            if hasattr(r, "categoria") and getattr(r, "categoria") is not None and hasattr(r.categoria, "nombre"):
                categoria_nombre = r.categoria.nombre
            else:
                # Fallback: devuelve el ID
                categoria_nombre = str(getattr(r, "categoriaId", getattr(r, "categoria_id", "")))

            # Estado (enum/str/bool)
            estado_val = getattr(r, "estado_producto", getattr(r, "estado", ""))
            if hasattr(estado_val, "value"):
                estado_val = estado_val.value
            if isinstance(estado_val, bool):
                estado_val = "activo" if estado_val else "inactivo"

            # Timestamp de actualización (elige el que exista)
            actualizado_en = getattr(r, "actualizado_en", None) or getattr(r, "updatedAt", None) or getattr(r, "createdAt", None)

            items.append(
                ProductoOut(
                    productoId=getattr(r, "productoId", getattr(r, "id")),
                    nombre=r.nombre,
                    categoria=categoria_nombre,
                    formaFarmaceutica=getattr(r, "formaFarmaceutica", getattr(r, "forma_farmaceutica", "")),
                    requierePrescripcion=getattr(r, "requierePrescripcion", getattr(r, "requiere_prescripcion", False)),
                    registroSanitario=getattr(r, "registroSanitario", getattr(r, "registro_sanitario", None)),
                    estado_producto=estado_val or "activo",
                    actualizado_en=actualizado_en,
                )
            )

        return ProductosResponse(page=page, page_size=page_size, total=total, items=items)


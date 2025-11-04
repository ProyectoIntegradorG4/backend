# app/service/product_service.py
from typing import List, Optional, Tuple
import logging

from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload
from uuid import uuid4

from app.models.product import Producto, ProductoCreate, ProductoOut, ProductosResponse
from app.models.category import CategoriaProducto
from app.models.inventory import InventarioLote
from app.models.warehouse import Bodega  

from datetime import date, datetime

logger = logging.getLogger(__name__)

class ProductoService:
    @staticmethod
    def sku_visible(producto_id: str) -> str:
        return f"SKU-{str(producto_id)[:8]}"

    @staticmethod
    def crear_producto(db: Session, data: dict) -> Tuple[Producto, bool]:
        # Validar categoría si se proporciona
        categoria_id = data.get("categoriaId")
        if not categoria_id:
            categoria_id = "CAT-OTR-001"  # Usar categoría por defecto si no se proporciona
        
        if categoria_id:
            categoria: CategoriaProducto = db.get(CategoriaProducto, categoria_id)
            if not categoria:
                raise ValueError("categoriaId inexistente")
        else:
            # Si no se proporciona categoría, usar una por defecto o crear una genérica
            categoria_id = "default"

        fv = data.get("fechaVencimiento")
        if isinstance(fv, str):
          fv = date.fromisoformat(fv)  # 'YYYY-MM-DD'    
          
        entity = Producto(
            productoId=str(uuid4()),
            nombre=data["nombre"],
            descripcion=data.get("descripcion"),
            categoriaId=categoria_id,
            formaFarmaceutica=data.get("formaFarmaceutica"),
            requierePrescripcion=data.get("requierePrescripcion", False),
            registroSanitario=data.get("registroSanitario"),
            sku=data.get("sku"),
            # Semántica acordada: location = bodega (legacy), ubicacion = estante (legacy)
            location=data.get("location"),
            ubicacion=data.get("ubicacion"),
            stock=data.get("stock"),
            precio=data.get("precio", 0.0),
            estado_producto="activo",
            fechaVencimiento=fv,

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
    ):

        page, page_size, offset = ProductoService._normalize_pagination(page, page_size)

        # Cargar categoría y lotes + bodega (evitar N+1)
        qry = db.query(Producto).options(
            joinedload(Producto.categoria),
            joinedload(Producto.lotes).joinedload(InventarioLote.bodega),
        )

        if q:
            term = f"%{q.lower()}%"
            condiciones = [func.lower(Producto.nombre).like(term)]
            if hasattr(Producto, "codigoBarras"):
                condiciones.append(Producto.codigoBarras.startswith(q))
            # Búsqueda por SKU (búsqueda exacta o parcial)
            if hasattr(Producto, "sku"):
                condiciones.append(Producto.sku.ilike(term))
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

        items: List[dict] = []
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

            # Convertir datetime/date a string ISO para serialización JSON
            actualizado_en_str = None
            if actualizado_en:
                if isinstance(actualizado_en, datetime):
                    actualizado_en_str = actualizado_en.isoformat()
                elif isinstance(actualizado_en, date):
                    actualizado_en_str = actualizado_en.isoformat()
                else:
                    actualizado_en_str = str(actualizado_en)
            
            fecha_vencimiento_obj = getattr(r, "fechaVencimiento", None)
            fecha_vencimiento_str = None
            if fecha_vencimiento_obj:
                if isinstance(fecha_vencimiento_obj, date):
                    fecha_vencimiento_str = fecha_vencimiento_obj.isoformat()
                elif isinstance(fecha_vencimiento_obj, datetime):
                    fecha_vencimiento_str = fecha_vencimiento_obj.date().isoformat()
                else:
                    fecha_vencimiento_str = str(fecha_vencimiento_obj)

            lotes_out: List[dict] = []
            for lote in getattr(r, "lotes", []) or []:
                bod = getattr(lote, "bodega", None)
                fecha_venc_lote = getattr(lote, "fechaVencimiento", None)
                fecha_venc_lote_str = None
                if fecha_venc_lote:
                    if isinstance(fecha_venc_lote, date):
                        fecha_venc_lote_str = fecha_venc_lote.isoformat()
                    elif isinstance(fecha_venc_lote, datetime):
                        fecha_venc_lote_str = fecha_venc_lote.date().isoformat()
                    else:
                        fecha_venc_lote_str = str(fecha_venc_lote)
                
                lotes_out.append(
                    {
                        "loteId": str(lote.loteId),
                        "bodegaId": str(lote.bodegaId),
                        "bodega": (bod.nombre if bod else ""), 
                        "pais": str(lote.pais),
                        "stock": int(lote.stock or 0),
                        "fechaVencimiento": fecha_venc_lote_str,
                    }
                )

            items.append(
                {
                    "productoId": str(pid) if pid is not None else "",
                    "nombre": r.nombre,  # Visibilidad explícita del nombre
                    "categoria": categoria_nombre,
                    "formaFarmaceutica": getattr(r, "formaFarmaceutica", getattr(r, "forma_farmaceutica", "")),
                    "requierePrescripcion": getattr(r, "requierePrescripcion", getattr(r, "requiere_prescripcion", False)),
                    "registroSanitario": getattr(r, "registroSanitario", getattr(r, "registro_sanitario", None)),
                    "estado_producto": estado_val or "activo",
                    "actualizado_en": actualizado_en_str,
                    "fechaVencimiento": fecha_vencimiento_str,
                    "sku": getattr(r, "sku", None),
                    "location": getattr(r, "location", None),
                    "ubicacion": getattr(r, "ubicacion", None),
                    "stock": getattr(r, "stock", None),
                    "precio": getattr(r, "precio", 0.0),
                    **({"lotes": lotes_out} if lotes_out else {}),
                }
            )

        result = {
            "total": total,
            "items": items,
            "page": page,
            "page_size": page_size,
        }

        return result

    @staticmethod
    def obtener_producto_por_id(db: Session, producto_id: str) -> Optional[Producto]:
        """
        Obtiene un producto por su ID con todos sus lotes cargados
        """
        try:
            producto = db.query(Producto).options(
                joinedload(Producto.categoria),
                joinedload(Producto.lotes).joinedload(InventarioLote.bodega),
            ).filter(Producto.productoId == producto_id).first()
            return producto
        except Exception as e:
            logger.error(f"Error obteniendo producto {producto_id}: {e}")
            return None

    @staticmethod
    def actualizar_stock_producto(db: Session, producto_id: str, cantidad_a_restar: int) -> Tuple[bool, int, str]:
        """
        Actualiza el stock de un producto restando la cantidad especificada.
        
        Args:
            db: Sesión de base de datos
            producto_id: ID del producto
            cantidad_a_restar: Cantidad a restar del stock (debe ser positiva)
        
        Retorna: (exito, stock_actualizado, mensaje)
        - exito: True si se actualizó correctamente
        - stock_actualizado: Nuevo valor de stock después de la resta
        - mensaje: Mensaje descriptivo del resultado
        """
        try:
            if cantidad_a_restar <= 0:
                return False, 0, "La cantidad a restar debe ser mayor que cero"
            
            # Obtener el producto
            producto = db.query(Producto).filter(Producto.productoId == producto_id).first()
            
            if not producto:
                return False, 0, "Producto no encontrado"
            
            # Obtener stock actual
            stock_actual = producto.stock if producto.stock is not None else 0
            
            # Validar que haya suficiente stock
            if stock_actual < cantidad_a_restar:
                return False, stock_actual, f"Stock insuficiente. Disponible: {stock_actual}, Solicitado: {cantidad_a_restar}"
            
            # Actualizar stock
            nuevo_stock = stock_actual - cantidad_a_restar
            producto.stock = nuevo_stock
            
            # Guardar cambios
            db.commit()
            db.refresh(producto)
            
            logger.info(f"Stock actualizado para producto {producto_id}: {stock_actual} -> {nuevo_stock} (restado {cantidad_a_restar})")
            
            return True, nuevo_stock, f"Stock actualizado: {nuevo_stock}"
            
        except Exception as e:
            logger.error(f"Error actualizando stock para producto {producto_id}: {e}")
            db.rollback()
            return False, 0, f"Error al actualizar stock: {str(e)}"
    
    @staticmethod
    def obtener_inventario_producto(db: Session, producto_id: str) -> Tuple[int, float, Optional[date]]:
        """
        Obtiene el inventario de un producto desde la columna stock de la tabla producto.
        
        Retorna: (cantidad_disponible, precio, fecha_vencimiento)
        - cantidad_disponible: Valor del campo stock de la tabla producto
        - precio: Precio del producto (del campo precio del modelo Producto)
        - fecha_vencimiento: Fecha de vencimiento del producto (del campo fechaVencimiento)
        """
        try:
            # Obtener el producto directamente
            producto = db.query(Producto).filter(Producto.productoId == producto_id).first()
            
            if not producto:
                return 0, 0.0, None
            
            # Obtener stock directamente de la columna stock del producto
            cantidad_disponible = producto.stock if producto.stock is not None else 0
            
            # Obtener precio del producto
            precio = producto.precio if producto.precio is not None else 0.0
            
            # Obtener fecha de vencimiento del producto (si existe)
            fecha_vencimiento = producto.fechaVencimiento if hasattr(producto, 'fechaVencimiento') else None
            
            return cantidad_disponible, precio, fecha_vencimiento
            
        except Exception as e:
            logger.error(f"Error obteniendo inventario para producto {producto_id}: {e}")
            return 0, 0.0, None

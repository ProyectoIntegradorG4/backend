from sqlalchemy.orm import Session
from app.models.product import Producto
from app.models.category import CategoriaProducto
from app.service.validators import validate_ean, validate_registro_sanitario

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

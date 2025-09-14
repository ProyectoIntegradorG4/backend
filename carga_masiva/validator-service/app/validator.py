from datetime import datetime
from sqlalchemy.orm import Session
from .models import ProductStaging, ProductStagingErrors
from typing import List

def process_pending_products(db: Session):
    total_validados = 0
    total_invalidos = 0
    total_errores = 0

    # Traer todos los productos pendientes
    pending_products: List[ProductStaging] = db.query(ProductStaging).filter(
        ProductStaging.validation_status == "PENDING"
    ).all()

    errores_bulk: List[ProductStagingErrors] = []

    for product in pending_products:
        errores_producto = []

        # 1. Campos obligatorios
        for campo in ["sku", "name", "category", "import_id"]:
            if not getattr(product, campo):
                errores_producto.append(f"Campo {campo} obligatorio")

        # 2. Fecha de expiración
        if product.expiration_date and product.expiration_date < datetime.utcnow().date():
            errores_producto.append("Producto expirado")

        # 3. Vida útil mínima según categoría
        if product.min_shelf_life_months is not None:
            if product.category.lower() == "categoria_a" and product.min_shelf_life_months < 24:
                errores_producto.append("Producto no cumple mínimo de vida útil (24 meses)")
            elif product.category.lower() != "categoria_a" and product.min_shelf_life_months < 6:
                errores_producto.append("Producto no cumple mínimo de vida útil (6 meses)")

        # 4. Cadena de frío
        if getattr(product, "cold_chain_required", False):
            if getattr(product, "storage_type", "").lower() not in ["cold", "refrigerated"]:
                errores_producto.append(
                    "Producto requiere cadena de frío pero almacenamiento no cumple"
                )

        # 5. Precio unitario
        if product.unit_price is None or product.unit_price < 0:
            errores_producto.append("Precio unitario inválido")

        if errores_producto:
            product.validation_status = "INVALID"
            total_invalidos += 1

            for error_msg in errores_producto:
                error = ProductStagingErrors(
                    sku=product.sku,
                    import_id=product.import_id,
                    error_message=error_msg,
                    created_at=datetime.utcnow(),
                )
                errores_bulk.append(error)
                total_errores += 1
        else:
            product.validation_status = "VALID"
            total_validados += 1

    # Hacer un solo commit para todos los productos y errores
    if pending_products:
        db.bulk_save_objects(pending_products)
    if errores_bulk:
        db.bulk_save_objects(errores_bulk)
    db.commit()

    return total_validados, total_invalidos, total_errores

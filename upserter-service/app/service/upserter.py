from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from app.models import ProductsStg, Products

def upsert_valid_products(db: Session, processed_by="upserter_service"):

    products_to_insert = db.query(ProductsStg).filter(
        ProductsStg.validation_status == "VALID",
        ProductsStg.processed_at.is_(None)
    ).all()

    if not products_to_insert:
        return {"message": "No hay productos nuevos para insertar."}

    for prod_stg in products_to_insert:
        stmt = insert(Products).values(
            sku=prod_stg.sku,
            name=prod_stg.name,
            description=prod_stg.description,
            category=prod_stg.category,
            manufacturer=prod_stg.manufacturer,
            storage_type=prod_stg.storage_type,
            expiration_date=prod_stg.expiration_date,
            batch_number=prod_stg.batch_number,
            unit_price=prod_stg.unit_price,
            created_at=datetime.utcnow()
        ).on_conflict_do_nothing(
            index_elements=['sku']  # evita duplicados
        )
        db.execute(stmt)

        # Marcamos staging como procesado
        prod_stg.processed_at = datetime.utcnow()
        prod_stg.processed_by = processed_by

    db.commit()
    return {"message": f"UPSERT completado: {len(products_to_insert)} productos procesados."}


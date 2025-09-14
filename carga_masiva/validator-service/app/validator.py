from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .models import ProductStaging, ProductStagingErrors
from datetime import datetime

CHUNK_SIZE = 5000  # ajustar según necesidad

def validate_row(row: dict) -> list:

    errors = []

    if not row.get("sku"):
        errors.append("SKU missing")
    if not row.get("name"):
        errors.append("Name missing")

    exp_date = row.get("expiration_date")
    if exp_date:
        if isinstance(exp_date, str):
            try:
                exp_date = datetime.strptime(exp_date, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Expiration date invalid format")
        if isinstance(exp_date, datetime):
            exp_date = exp_date.date()
        if exp_date and exp_date < datetime.utcnow().date():
            errors.append("Product expired")

    unit_price = row.get("unit_price")
    if unit_price is not None:
        try:
            if float(unit_price) <= 0:
                errors.append("Unit price invalid")
        except ValueError:
            errors.append("Unit price not numeric")

    return errors

def process_pending_products(import_id: str, db: Session):
    
    pending_products = db.query(ProductStaging)\
        .filter(ProductStaging.import_id == import_id)\
        .filter(ProductStaging.validation_status == 'PENDING')\
        .all()

    for idx, product in enumerate(pending_products, start=1):
        row = {c.name: getattr(product, c.name) for c in product.__table__.columns}
        errors = validate_row(row)

        if errors:
            # Marcar como inválido
            product.validation_status = "INVALID"
            for error in errors:
                error_record = ProductStagingErrors(
                    sku=product.sku,
                    import_id=product.import_id,
                    error_message=error
                )
                db.add(error_record)
        else:
            # Marcar como válido
            product.validation_status = "VALID"

        # Commit por chunks
        if idx % CHUNK_SIZE == 0:
            try:
                db.commit()
            except SQLAlchemyError as e:
                db.rollback()
                print(f"Error en commit chunk: {e}")

    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error final en commit: {e}")

    print(f"Validación completa para import_id={import_id}")



from sqlalchemy.orm import Session
from .models import Product
from sqlalchemy.exc import IntegrityError

def upsert_products(db: Session, products: list):
    inserted, updated = 0, 0
    for p in products:
        existing = db.query(Product).filter(Product.sku == p["sku"]).first()
        if existing:
            existing.name = p["name"]
            existing.description = p.get("description")
            existing.category = p.get("category")
            existing.manufacturer = p.get("manufacturer")
            existing.storage_type = p.get("storage_type")
            existing.expiration_date = p.get("expiration_date")
            existing.batch_number = p.get("batch_number")
            existing.unit_price = p.get("unit_price")
            updated += 1
        else:
            new_product = Product(**p)
            db.add(new_product)
            inserted += 1
    db.commit()
    return {"inserted": inserted, "updated": updated}

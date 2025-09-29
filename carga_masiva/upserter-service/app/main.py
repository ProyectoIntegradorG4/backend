from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import SessionLocal, engine
from .models import Base, ProductStaging, Products
from typing import List
from pydantic import BaseModel
from datetime import datetime
import os


# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Products Upserter Service")

# Dependencia de sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schemas Pydantic
class ProductOut(BaseModel):
    product_id: int
    sku: str
    name: str
    description: str | None = None
    category: str | None = None
    manufacturer: str | None = None
    storage_type: str | None = None
    expiration_date: datetime | None = None
    batch_number: str | None = None
    unit_price: float | None = None
    created_at: datetime

    class Config:
        orm_mode = True


# Healthcheck
@app.get("/health")
def health():
    return {"status": "UP", "timestamp": datetime.utcnow()}

# Listar productos finales
@app.get("/products", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    products = db.execute(select(Products)).scalars().all()
    return products

# Upserter: inserta productos validados en tabla final
@app.post("/products/upsert")
def upsert_products(db: Session = Depends(get_db)):
    # Buscar registros validados y no procesados
    stg_products = db.execute(
        select(ProductStaging).where(
            ProductStaging.validation_status == "VALID",
            ProductStaging.processed == False
        )
    ).scalars().all()

    if not stg_products:
        return {"message": "No hay productos para insertar"}

    inserted_count = 0
    for p in stg_products:
        # Insertar en tabla final
        new_product = Products(
            sku=p.sku,
            name=p.name,
            description=p.description,
            category=p.category,
            manufacturer=p.manufacturer,
            storage_type=p.storage_type,
            expiration_date=p.expiration_date,
            batch_number=p.batch_number,
            unit_price=float(p.unit_price) if p.unit_price is not None else None
        )
        db.add(new_product)

        # Marcar como procesado en staging
        p.processed = True
        p.updated_at = datetime.utcnow()

        inserted_count += 1

    db.commit()
    return {"message": f"{inserted_count} productos insertados correctamente"}

# Handler para Lambda con Mangum
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None

# Variable opcional para distinguir entornos
IS_LAMBDA = os.environ.get("AWS_EXECUTION_ENV") is not None
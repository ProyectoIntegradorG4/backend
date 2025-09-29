from decimal import Decimal
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from tempfile import NamedTemporaryFile
from .database import SessionLocal, engine
from .models import Base, ProductStaging
from .utils import read_csv
import uuid
import os


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ingestion Service")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


import math

def safe_float(value):
    if value is None:
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None

def safe_int(value):
    if value is None:
        return None
    try:
        i = int(float(value))
        return i
    except (ValueError, TypeError):
        return None

def safe_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes']
    return bool(value)


@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), created_by: str = "system", db: Session = Depends(get_db)):
    try:
        # Guardar archivo temporal con nombre único
        with NamedTemporaryFile(delete=False, suffix=f"_{uuid.uuid4()}.csv") as tmp_file:
            tmp_file.write(await file.read())
            tmp_file_path = tmp_file.name

        # Leer CSV
        df = read_csv(tmp_file_path)

        # Validar columnas requeridas
        required_columns = [
            "sku", "name", "description", "category", "manufacturer",
            "storage_type", "min_shelf_life_months", "expiration_date",
            "batch_number", "cold_chain_required", "certifications",
            "commercialization_auth", "country_regulations", "unit_price",
            "purchase_conditions", "delivery_time_hours", "external_code",
            "import_id"
        ]
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"Faltan columnas en el CSV: {missing_cols}")

        # Convertir cold_chain_required a boolean
        if "cold_chain_required" in df.columns:
            df["cold_chain_required"] = df["cold_chain_required"].apply(safe_bool)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el CSV: {str(e)}")

    # Insertar en la base de datos
    try:
        for _, row in df.iterrows():
            product = ProductStaging(
                sku=row.get("sku"),
                name=row.get("name"),
                description=row.get("description"),
                category=row.get("category"),
                manufacturer=row.get("manufacturer"),
                storage_type=row.get("storage_type"),
                min_shelf_life_months=safe_int(row.get("min_shelf_life_months")),
                expiration_date=row.get("expiration_date"),
                batch_number=row.get("batch_number"),
                cold_chain_required=row.get("cold_chain_required"),
                certifications=row.get("certifications"),
                commercialization_auth=row.get("commercialization_auth"),
                country_regulations=row.get("country_regulations"),
                unit_price=safe_float(row.get("unit_price")),
                purchase_conditions=row.get("purchase_conditions"),
                delivery_time_hours=safe_int(row.get("delivery_time_hours")),
                external_code=row.get("external_code"),
                import_id=row.get("import_id"),
                created_by=created_by
            )
            db.add(product)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al insertar los datos: {str(e)}")

    total_products = len(df)
    categories_count = df['category'].value_counts().to_dict()
    cold_chain_count = int(df['cold_chain_required'].sum())
    avg_unit_price = round(float(df['unit_price'].mean()) if not df['unit_price'].isna().all() else 0, 2)

    return {
        "message": f"{total_products} productos ingresados",
        "summary": {
            "total_products": total_products,
            "categories_count": categories_count,
            "cold_chain_required_count": cold_chain_count,
            "avg_unit_price": avg_unit_price
        }
    }

@app.get("/staging-products")
def list_staging_products(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    products = db.query(ProductStaging).offset(offset).limit(limit).all()
    return [
        {
            "product_id": p.product_id,
            "sku": p.sku,
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "manufacturer": p.manufacturer,
            "storage_type": p.storage_type,
            "min_shelf_life_months": safe_int(p.min_shelf_life_months),
            "expiration_date": p.expiration_date,
            "batch_number": p.batch_number,
            "cold_chain_required": p.cold_chain_required,
            "certifications": p.certifications,
            "commercialization_auth": p.commercialization_auth,
            "country_regulations": p.country_regulations,
            "unit_price": safe_float(p.unit_price),
            "purchase_conditions": p.purchase_conditions,
            "delivery_time_hours": safe_int(p.delivery_time_hours),
            "external_code": p.external_code,
            "import_id": str(p.import_id),
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "created_by": p.created_by,
            "validation_status": p.validation_status,
            "validation_errors": p.validation_errors,
            "validated_at": p.validated_at,
            "processed": p.processed              
        } for p in products
    ]

@app.get("/health")
def health():
    return {"status": "ok"}


# Handler para Lambda con Mangum
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None

# Variable opcional para distinguir entornos
IS_LAMBDA = os.environ.get("AWS_EXECUTION_ENV") is not None




from fastapi import FastAPI, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, ProductStaging
from .utils import read_csv
import uuid

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ingestion Service")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), created_by: str = "system"):
    try:
        # Guardar temporalmente el archivo
        tmp_file_path = f"/tmp/{file.filename}"
        content = await file.read()
        with open(tmp_file_path, "wb") as f:
            f.write(content)

        # Leer CSV
        df = read_csv(tmp_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el CSV: {str(e)}")

    # Insertar en la base de datos
    db: Session = next(get_db())
    try:
        for _, row in df.iterrows():
            product = ProductStaging(
                sku=row.get("sku"),
                name=row.get("name"),
                description=row.get("description"),
                category=row.get("category"),
                manufacturer=row.get("manufacturer"),
                storage_type=row.get("storage_type"),
                min_shelf_life_months=row.get("min_shelf_life_months"),
                expiration_date=row.get("expiration_date"),
                batch_number=row.get("batch_number"),
                cold_chain_required=row.get("cold_chain_required"),
                certifications=row.get("certifications"),
                commercialization_auth=row.get("commercialization_auth"),
                country_regulations=row.get("country_regulations"),
                unit_price=row.get("unit_price"),
                purchase_conditions=row.get("purchase_conditions"),
                delivery_time_hours=row.get("delivery_time_hours"),
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
    cold_chain_count = df['cold_chain_required'].sum()  
    avg_unit_price = df['unit_price'].mean()  

    return {
        "message": f"{total_products} productor ingresados",
        "summary": {
            "total productos": total_products,
            "cantidad de categorias": categories_count,
            "Cantidad que requieren cadena de frio": int(cold_chain_count),
            "Precio promedio": round(float(avg_unit_price), 2)
        }
    }

@app.get("/staging-products")
def list_staging_products(limit: int = 100, offset: int = 0):
    db: Session = next(get_db())
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
            "min_shelf_life_months": p.min_shelf_life_months,
            "expiration_date": p.expiration_date,
            "batch_number": p.batch_number,
            "cold_chain_required": p.cold_chain_required,
            "certifications": p.certifications,
            "commercialization_auth": p.commercialization_auth,
            "country_regulations": p.country_regulations,
            "unit_price": p.unit_price,
            "purchase_conditions": p.purchase_conditions,
            "delivery_time_hours": p.delivery_time_hours,
            "external_code": p.external_code,
            "import_id": str(p.import_id),
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "created_by": p.created_by,
            "validation_status": p.validation_status,
            "validation_errors": p.validation_errors,
            "validated_at": p.validated_at
        } for p in products
    ]


@app.get("/health")
def health():
    return {"status": "ok"}




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
                import_id=row.get("import_id"),  # ya es UUID real
                created_by=created_by
            )
            db.add(product)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al insertar los datos: {str(e)}")

    return {"message": f"{len(df)} products ingested", "import_id": str(df["import_id"].iloc[0])}

@app.get("/health")
def health():
    return {"status": "ok"}




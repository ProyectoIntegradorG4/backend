from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .models import ProductStaging, ProductStagingErrors
from .validator import process_pending_products
from .database import SessionLocal, engine

# Crear tablas si no existen
from .models import Base
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Validator Definitivo")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/validate")
def validate_all(db: Session = Depends(get_db)):
    pending_products = db.query(ProductStaging).filter(
        ProductStaging.validation_status == 'PENDING'
    ).all()
    total_pendientes = len(pending_products)

    total_validados, total_invalidos, total_errores = process_pending_products(db)

    return {
        "estado": "validación completada",
        "resumen": {
            "total_pendientes": total_pendientes,
            "total_validados": total_validados,
            "total_invalidos": total_invalidos,
            "total_errores": total_errores
        }
    }


@app.get("/errors")
def list_errors(db: Session = Depends(get_db)):
    errores = db.query(ProductStagingErrors).all()
    return {
        "total": len(errores),
        "errores": [
            {
                "sku": e.sku,
                "import_id": str(e.import_id),  # convertimos UUID a string
                "error_message": e.error_message,
                "created_at": e.created_at
            } for e in errores
        ]
    }


@app.get("/health")
def health():
    return {"status": "ok"}

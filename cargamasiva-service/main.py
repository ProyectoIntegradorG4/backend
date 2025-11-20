# app/main.py
from fastapi import FastAPI
from app.routes.import_products import router as import_router

from app.database.session import SessionLocal, Base, engine
from app.models import category, product

from app.startup_seed import seed_default_categories

app = FastAPI(
    title="MediSupply Loader (Single Endpoint)",
    description="Microservicio de carga masiva unificado (ingestion + validation + upsert)",
    version="1.0.2"
)

@app.on_event("startup")
def _startup():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_default_categories(db)  
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

app.include_router(import_router, prefix="/api/v1/cargamasiva")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "cargamasiva-service",
        "version": "1.0.0"
    }

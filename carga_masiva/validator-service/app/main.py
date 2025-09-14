from fastapi import FastAPI
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base
from .validator import process_pending_products
from fastapi.responses import JSONResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Validator Service")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/validate/{import_id}")
def validate(import_id: str):
    db: Session = next(get_db())
    process_pending_products(import_id, db)
    return JSONResponse(content={"import_id": import_id, "status": "validation completed"})

@app.get("/health")
def health():
    return {"status": "ok"}


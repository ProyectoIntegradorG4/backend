from fastapi import FastAPI, Body
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, Product
from .upserter import upsert_products

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Upserter Service")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/upsert")
def upsert(products: list = Body(...)):
    db: Session = next(get_db())
    result = upsert_products(db, products)
    return result

@app.get("/health")
def health():
    return {"status": "ok"}

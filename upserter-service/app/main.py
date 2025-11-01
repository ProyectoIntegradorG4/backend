from fastapi import FastAPI, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import SessionLocal, engine
from .models import Base, ProductStaging, Products
from typing import List, Optional
from pydantic import BaseModel
from pydantic import ConfigDict
from datetime import datetime
import os

# =========================
#  Auth mínima por header
# =========================


SKIP_AUTH = os.environ.get("SKIP_AUTH", "true").lower() in ("1", "true", "yes")

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret-key")
JWT_ALG = "HS256"

def _decode_jwt(token: str):
    """
    Valida el JWT con HS256 usando JWT_SECRET_KEY.
    Si SKIP_AUTH está activo, devuelve un payload mínimo.
    """
    if SKIP_AUTH:
        return {"sub": "test-user", "roles": ["Administrador de Compras"]}

    if not JWT_SECRET_KEY:
        raise HTTPException(status_code=500, detail="JWT_SECRET_KEY faltante en configuración")

    try:
        import jwt  # PyJWT
    except Exception:
        raise HTTPException(status_code=500, detail="PyJWT no instalado")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALG])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def require_token(request: Request):
    """
    Lee Authorization: Bearer <token> y valida el JWT.
    """
    if SKIP_AUTH:
        return {"sub": "test-user"}

    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Token requerido")

    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de autorización inválido")

    token = auth.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")

    return _decode_jwt(token)

# =========================
#  FastAPI app
# =========================

app = FastAPI(
    title="Upserter Service",
    description="Microservicio de upsert de productos validados",
    version="1.0.0"
)

# Crear tablas en startup (evita efectos al importar el módulo)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

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
    description: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    storage_type: Optional[str] = None
    # En el modelo es Date; Pydantic lo serializa sin problema
    expiration_date: Optional[datetime] = None
    batch_number: Optional[str] = None
    unit_price: Optional[float] = None
    created_at: datetime

    # Pydantic v2
    model_config = ConfigDict(from_attributes=True)

# Healthcheck
@app.get("/health")
def health():
    return {"status": "UP", "timestamp": datetime.utcnow()}

# Listar productos finales
@app.get("/products", response_model=List[ProductOut])
def list_products(
    db: Session = Depends(get_db),
    _user=Depends(require_token),  # exige Bearer token
):
    products = db.execute(select(Products)).scalars().all()
    return products

# Upserter: inserta productos validados en tabla final
@app.post("/products/upsert")
def upsert_products(
    db: Session = Depends(get_db),
    _user=Depends(require_token),  # exige Bearer token
):
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

# Handler para Lambda con Mangum (opcional)
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None

# Variable opcional para distinguir entornos
IS_LAMBDA = os.environ.get("AWS_EXECUTION_ENV") is not None

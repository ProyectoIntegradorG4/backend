from fastapi import FastAPI, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from .models import Base, ProductStaging, ProductStagingErrors
from .validator import process_pending_products
from .database import SessionLocal, engine
import os
from datetime import datetime

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

app = FastAPI(title="Validator Definitivo")

# Crear tablas en startup (evita efectos secundarios al importar)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/validate")
def validate_all(
    db: Session = Depends(get_db),
    _user=Depends(require_token),
):
    pending_products = (
        db.query(ProductStaging)
        .filter(ProductStaging.validation_status == "PENDING")
        .all()
    )
    total_pendientes = len(pending_products)

    total_validados, total_invalidos, total_errores = process_pending_products(db)

    return {
        "estado": "validación completada",
        "resumen": {
            "total_pendientes": total_pendientes,
            "total_validados": total_validados,
            "total_invalidos": total_invalidos,
            "total_errores": total_errores,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }

@app.get("/errors")
def list_errors(
    db: Session = Depends(get_db),
    _user=Depends(require_token),
):
    errores = db.query(ProductStagingErrors).all()
    return {
        "total": len(errores),
        "errores": [
            {
                "sku": e.sku,
                "import_id": str(e.import_id),
                "error_message": e.error_message,
                "created_at": e.created_at,
            }
            for e in errores
        ],
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# Handler para Lambda con Mangum (opcional)
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None

# Variable opcional para distinguir entornos
IS_LAMBDA = os.environ.get("AWS_EXECUTION_ENV") is not None

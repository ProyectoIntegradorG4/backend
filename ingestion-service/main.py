
from decimal import Decimal, InvalidOperation
from datetime import date
import math
import os
import uuid
import pandas as pd

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, Request
from sqlalchemy.orm import Session
from tempfile import NamedTemporaryFile

from .database import SessionLocal, engine
from .models import Base, ProductStaging
from .utils import read_csv

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
        import jwt  # pyjwt
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
    Sin roles obligatorios aquí; si lo necesitas, léelos del payload.
    """
    if SKIP_AUTH:
        return {"sub": "test-user"}

    auth = request.headers.get("Authorization")
    if not auth:
        # Mantengo este mensaje para ser consistente con product-service
        raise HTTPException(status_code=401, detail="Token requerido")

    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de autorización inválido")

    token = auth.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")

    return _decode_jwt(token)


# =========================
#   FastAPI app
# =========================

app = FastAPI(
    title="Ingestion Service",
    description="Microservicio de ingesta masiva de productos vía CSV",
    version="1.0.1"
)

# Crear tablas en startup (evita efectos al importar el módulo)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
        return value.lower() in ["true", "1", "yes"]
    return bool(value)


@app.post("/upload-csv", status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: UploadFile = File(...),
    created_by: str = "system",
    db: Session = Depends(get_db),
    _user=Depends(require_token),  # <- exige Bearer token
):
    tmp_file_path = None
    try:
        # Guardar archivo temporal con nombre único
        content = await file.read()
        with NamedTemporaryFile(delete=False, suffix=f"_{uuid.uuid4()}.csv") as tmp_file:
            tmp_file.write(content)
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

        # Normalizaciones seguras
        # Booleanos
        if "cold_chain_required" in df.columns:
            df["cold_chain_required"] = df["cold_chain_required"].apply(safe_bool).fillna(False)

        # Fechas -> date
        if "expiration_date" in df.columns:
            dt = pd.to_datetime(df["expiration_date"], errors="coerce", utc=False)
            df["expiration_date"] = dt.dt.date  # datetime.date o NaN -> None después

        # Enteros (permitir NaN -> None)
        for col in ("min_shelf_life_months", "delivery_time_hours"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

        # Dinero -> Decimal (para DECIMAL(12,2))
        if "unit_price" in df.columns:
            def to_decimal(x):
                if pd.isna(x) or x == "":
                    return None
                try:
                    return Decimal(str(x))
                except (InvalidOperation, ValueError, TypeError):
                    return None
            df["unit_price"] = df["unit_price"].apply(to_decimal)

    except HTTPException:
        # No enmascarar 4xx como 500
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el CSV: {str(e)}")
    finally:
        # Limpieza del archivo temporal
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
            except OSError:
                pass

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
                min_shelf_life_months=int(row["min_shelf_life_months"]) if pd.notna(row.get("min_shelf_life_months")) else None,
                expiration_date=row.get("expiration_date") if isinstance(row.get("expiration_date"), date) else None,
                batch_number=row.get("batch_number"),
                cold_chain_required=bool(row.get("cold_chain_required")),
                certifications=row.get("certifications"),
                commercialization_auth=row.get("commercialization_auth"),
                country_regulations=row.get("country_regulations"),
                unit_price=row.get("unit_price"),  # Decimal o None
                purchase_conditions=row.get("purchase_conditions"),
                delivery_time_hours=int(row["delivery_time_hours"]) if pd.notna(row.get("delivery_time_hours")) else None,
                external_code=row.get("external_code"),
                import_id=row.get("import_id"),  # utils.read_csv asigna UUID válido
                created_by=created_by,
            )
            db.add(product)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al insertar los datos: {str(e)}")

    total_products = len(df)
    categories_count = df["category"].value_counts(dropna=False).to_dict()
    cold_chain_count = int(df["cold_chain_required"].sum()) if "cold_chain_required" in df.columns else 0

    # Promedio de unit_price con Decimal
    decimals = df["unit_price"].dropna() if "unit_price" in df.columns else pd.Series([], dtype="object")
    if len(decimals) > 0:
        avg = float(sum(decimals, start=Decimal("0")) / Decimal(len(decimals)))
        avg_unit_price = round(avg, 2)
    else:
        avg_unit_price = 0.0

    return {
        "message": f"{total_products} productos ingresados",
        "summary": {
            "total_products": total_products,
            "categories_count": categories_count,
            "cold_chain_required_count": cold_chain_count,
            "avg_unit_price": avg_unit_price,
        },
    }


@app.get("/staging-products")
def list_staging_products(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user=Depends(require_token),  # <- exige Bearer token también
):
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
            "processed": p.processed,
        }
        for p in products
    ]


@app.get("/health")
def health():
    return {"status": "ok"}


# Handler para Lambda con Mangum (opcional)
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None

IS_LAMBDA = os.environ.get("AWS_EXECUTION_ENV") is not None

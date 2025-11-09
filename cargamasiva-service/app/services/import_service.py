# app/services/import_service.py
from typing import List, Dict
import csv, io, os

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.product import Producto, ProductoCSVIn
from app.models.category import CategoriaProducto  # <-- NUEVO

from dateutil.parser import parse as parse_dt


def safe_int(v):
    if v in (None, "", "null", "NULL"): return None
    try: return int(float(str(v).replace(",", ".")))
    except: return None

def safe_float(v):
    if v in (None, "", "null", "NULL"): return None
    try: return float(str(v).replace(",", "."))
    except: return None

def safe_bool(v):
    if v is None: return None
    s = str(v).strip().lower()
    if s in ("true","1","yes","y","si","sí"): return True
    if s in ("false","0","no","n"): return False
    return None

def safe_date(v):
    if v in (None, "", "null", "NULL"): return None
    try: return parse_dt(v, dayfirst=False).date()
    except: return None

def safe_datetime(v):
    if v in (None, "", "null", "NULL"): return None
    try: return parse_dt(v)
    except: return None


# Encabezados EXACTOS esperados en el CSV (tal cual tu tabla)
CSV_FIELDS = [
    "productoId","nombre","descripcion","categoriaId","formaFarmaceutica",
    "requierePrescripcion","registroSanitario","sku","location","ubicacion",
    "stock","precio","estado_producto","actualizado_en","fechaVencimiento"
]


def _get_csv_headers(csv_bytes: bytes):
    text = csv_bytes.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    return reader.fieldnames or []


def _read_csv_rows(csv_bytes: bytes):
    text = csv_bytes.decode("utf-8", errors="ignore")
    yield from csv.DictReader(io.StringIO(text))


def _row_to_pydantic(raw: Dict) -> ProductoCSVIn:
    data = {
        "productoId":           (raw.get("productoId") or "").strip(),
        "nombre":               raw.get("nombre"),
        "descripcion":          raw.get("descripcion"),
        "categoriaId":          raw.get("categoriaId"),
        "formaFarmaceutica":    raw.get("formaFarmaceutica"),
        "requierePrescripcion": safe_bool(raw.get("requierePrescripcion")) if raw.get("requierePrescripcion") is not None else False,
        "registroSanitario":    raw.get("registroSanitario"),
        "sku":                  raw.get("sku"),
        "location":             raw.get("location"),
        "ubicacion":            raw.get("ubicacion"),
        "stock":                safe_int(raw.get("stock")),
        "precio":               safe_float(raw.get("precio")),
        "estado_producto":      raw.get("estado_producto"),
        "actualizado_en":       safe_datetime(raw.get("actualizado_en")),
        "fechaVencimiento":     safe_date(raw.get("fechaVencimiento")),
    }
    return ProductoCSVIn.model_validate(data)


def _pyd_to_db_row(p: ProductoCSVIn) -> Dict:
    return {
        "productoId":            p.productoId,
        "nombre":                p.nombre,
        "descripcion":           p.descripcion,
        "categoriaId":           p.categoriaId,
        "formaFarmaceutica":     p.formaFarmaceutica,
        "requierePrescripcion":  p.requierePrescripcion,
        "registroSanitario":     p.registroSanitario,
        "sku":                   p.sku,
        "location":              p.location,
        "ubicacion":             p.ubicacion,
        "stock":                 p.stock,
        "precio":                p.precio,
        "estado_producto":       p.estado_producto,
        "actualizado_en":        p.actualizado_en,
        "fechaVencimiento":      p.fechaVencimiento,
    }


def _load_existing_categories(db: Session) -> set:
    # Carga todas las categorias existentes a memoria
    return {row.categoriaId for row in db.query(CategoriaProducto.categoriaId).all()}


def _auto_create_missing_categories(db: Session, missing: set) -> int:
    if not missing:
        return 0
    # Inserta categorías faltantes con valores por defecto
    to_add = [
        CategoriaProducto(
            categoriaId=cid,
            nombre=f"Auto-{cid}",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False,
        )
        for cid in missing
    ]
    db.add_all(to_add)
    # commit lo hace el caller
    return len(to_add)


def bulk_upsert_products(db: Session, rows: List[Dict]) -> int:
    if not rows:
        return 0

    table = Producto.__table__
    stmt = pg_insert(table).values(rows)

    # Update todas menos la PK
    update_cols = {c.name: getattr(stmt.excluded, c.name) for c in table.columns if c.name != "productoId"}

    stmt = stmt.on_conflict_do_update(
        index_elements=[table.c["productoId"]],
        set_=update_cols
    )

    res = db.execute(stmt)
    return res.rowcount or 0


def process_import(db: Session, csv_bytes: bytes):
    # 1) Validación de encabezados
    headers = _get_csv_headers(csv_bytes)
    present = set(headers or [])
    expected = set(CSV_FIELDS)
    missing = sorted(expected - present)

    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "Faltan encabezados requeridos EXACTOS (CSV)",
                "faltantes": missing,
                "presentes": headers,
            },
        )

    # 2) Recorrer/validar filas
    total, invalid = 0, 0
    bad_examples: List[Dict] = []
    batch_all: List[Dict] = []

    for i, raw in enumerate(_read_csv_rows(csv_bytes), start=1):
        total += 1
        try:
            p = _row_to_pydantic(raw)
        except Exception as e:
            invalid += 1
            if len(bad_examples) < 10:
                bad_examples.append({
                    "row": raw.get("productoId") or f"line_{i}",
                    "errors": [str(e)]
                })
            continue

        batch_all.append(_pyd_to_db_row(p))

    # 3) Manejo de FK categoriaId
    #    3.1 Cargar categorías existentes
    existing = _load_existing_categories(db)

    #    3.2 Detectar faltantes en el batch
    incoming_cats = {row["categoriaId"] for row in batch_all if row.get("categoriaId")}
    missing_cats = sorted(incoming_cats - existing)

    #    3.3 Si habilitado por env, auto-crear; si no, filtrar filas inválidas
    auto_create = os.getenv("AUTO_CREATE_CATEGORIES", "false").lower() in ("1", "true", "yes")

    if missing_cats:
        if auto_create:
            _auto_create_missing_categories(db, set(missing_cats))
            db.flush()  # asegurar visibilidad antes del upsert
            existing = _load_existing_categories(db)
        else:
            # filtrar filas con categoriaId inexistente
            filtered_batch = []
            for row in batch_all:
                cid = row.get("categoriaId")
                if cid and cid not in existing:
                    invalid += 1
                    if len(bad_examples) < 10:
                        bad_examples.append({
                            "row": row.get("productoId"),
                            "errors": [f"categoriaId inexistente: {cid} (FK)"]
                        })
                    continue
                filtered_batch.append(row)
            batch_all = filtered_batch

    # 4) Eliminar duplicados de productoId dentro del mismo archivo, conservando el **último**
    seen = set()
    dedup_batch = []
    # Recorremos al revés para conservar el último; luego invertimos para mantener orden estable
    for row in reversed(batch_all):
        pid = row["productoId"]
        if pid in seen:
            continue
        seen.add(pid)
        dedup_batch.append(row)
    dedup_batch.reverse()

    # 5) Upsert
    upserted = bulk_upsert_products(db, dedup_batch)

    return {
        "message": "Importación completada",
        "summary": {
            "total_rows": total,
            "valid_rows_upserted": upserted,
            "invalid_rows": invalid
        },
        "invalid_samples": bad_examples
    }

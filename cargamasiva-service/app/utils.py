# app/utils.py  (CAMBIOS MÍNIMOS)
import csv, io
from dateutil.parser import parse as parse_dt

# CAMBIO: usar categoriaId en lugar de 'categoria'
REQUIRED = ["productoId", "nombre", "categoriaId", "requierePrescripcion",
            "estado_producto", "location", "ubicacion", "stock", "precio", "fechaVencimiento"]


def get_csv_headers(csv_bytes: bytes) -> list[str]:
    text = csv_bytes.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    return [h.strip() if isinstance(h, str) else h for h in headers]


def read_csv_bytes(csv_bytes: bytes):
    text = csv_bytes.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames:
        reader.fieldnames = [h.strip() if isinstance(h, str) else h for h in reader.fieldnames]
    yield from reader


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
    if s in ("true", "1", "yes", "y", "si", "sí"): return True
    if s in ("false", "0", "no", "n"): return False
    return None


def safe_date(v):
    if v in (None, "", "null", "NULL"): return None
    try: return parse_dt(v, dayfirst=False).date()
    except: return None


def safe_datetime(v):
    if v in (None, "", "null", "NULL"): return None
    try: return parse_dt(v)
    except: return None


def validate_row(r: dict) -> list[str]:
    errs = []
    # requeridos presentes
    for k in REQUIRED:
        if not str(r.get(k, "")).strip():
            errs.append(f"{k} requerido")

    # tipos
    if r.get("requierePrescripcion") not in (None, "") and safe_bool(r.get("requierePrescripcion")) is None:
        errs.append("requierePrescripcion inválido (true/false)")

    if r.get("stock") not in (None, "") and safe_int(r.get("stock")) is None:
        errs.append("stock inválido (entero)")

    if r.get("precio") not in (None, "") and safe_float(r.get("precio")) is None:
        errs.append("precio inválido (numérico)")

    if r.get("fechaVencimiento") not in (None, "") and safe_date(r.get("fechaVencimiento")) is None:
        errs.append("fechaVencimiento inválida (fecha)")

    if r.get("actualizado_en") not in (None, "") and safe_datetime(r.get("actualizado_en")) is None:
        errs.append("actualizado_en inválido (datetime)")

    return errs

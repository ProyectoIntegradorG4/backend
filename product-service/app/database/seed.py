# app/database/seed.py
from sqlalchemy.orm import Session
from app.models.category import CategoriaProducto
from app.models.warehouse import Bodega  # NUEVO: modelo de bodegas
import logging
import os
import json

logger = logging.getLogger("uvicorn")

# -------------------------------
# Seed de CATEGORÍAS (existente)
# -------------------------------
SEED_CATEGORIES = [
    {
        "categoriaId": "CAT-ANL-001",
        "nombre": "Analgésicos",
        "requiereCadenaFrio": False,
        "requiereRegistroSanitario": True,
    },
    {
        "categoriaId": "CAT-VAC-001",
        "nombre": "Vacunas",
        "requiereCadenaFrio": True,
        "requiereRegistroSanitario": True,
    },
    {
        "categoriaId": "CAT-OTR-001",
        "nombre": "Otros",
        "requiereCadenaFrio": False,
        "requiereRegistroSanitario": False,
    },
]

def seed_categories(db: Session) -> None:
    try:
        inserted = 0
        for item in SEED_CATEGORIES:
            if db.get(CategoriaProducto, item["categoriaId"]):
                continue
            db.add(CategoriaProducto(**item))
            inserted += 1
        db.commit()
        if inserted:
            logger.info(f"Seed de categorías: {inserted} nuevas registradas")
        else:
            logger.info("Seed de categorías: ya estaban registradas (sin cambios)")
    except Exception as e:
        db.rollback()
        logger.error(f"Error en seed de categorías: {e}")
        raise

# -------------------------------
# Seed de BODEGAS (nuevo)
# -------------------------------
# Valor por defecto si no se define WAREHOUSES_JSON
DEFAULT_WAREHOUSES = [
    {"bodegaId": "BOD-001", "nombre": "Bodega Principal", "pais": "CO"},
]

def _warehouses_from_env() -> list:
    raw = os.getenv("WAREHOUSES_JSON", "").strip()
    if not raw:
        return DEFAULT_WAREHOUSES
    try:
        data = json.loads(raw)
        if isinstance(data, list) and all(isinstance(x, dict) for x in data):
            return data
        logger.warning("WAREHOUSES_JSON no es una lista de objetos; usando DEFAULT_WAREHOUSES")
        return DEFAULT_WAREHOUSES
    except Exception as e:
        logger.warning(f"WAREHOUSES_JSON inválido ({e}); usando DEFAULT_WAREHOUSES")
        return DEFAULT_WAREHOUSES

def seed_warehouses(db: Session) -> None:
    try:
        payload = _warehouses_from_env()
        inserted = 0
        for w in payload:
            # Validación mínima de campos requeridos
            if not w.get("bodegaId") or not w.get("nombre") or not w.get("pais"):
                logger.warning(f"Seed bodega omitida por datos incompletos: {w}")
                continue
            if db.get(Bodega, w["bodegaId"]):
                continue
            db.add(Bodega(**w))
            inserted += 1
        db.commit()
        if inserted:
            logger.info(f"Seed de bodegas: {inserted} nuevas registradas")
        else:
            logger.info(" Seed de bodegas: ya estaban registradas (sin cambios)")
    except Exception as e:
        db.rollback()
        logger.error(f"Error en seed de bodegas: {e}")
        raise

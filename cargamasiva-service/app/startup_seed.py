# app/startup_seed.py
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.category import CategoriaProducto

DEFAULT_CATEGORIES: List[Dict] = [
    {"categoriaId": "CAT001", "nombre": "Analgésicos",        "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT002", "nombre": "Antiinflamatorios",  "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT003", "nombre": "Antibióticos",       "requiereCadenaFrio": False, "requiereRegistroSanitario": True},
    {"categoriaId": "CAT004", "nombre": "Antialérgicos",      "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT005", "nombre": "IBP (Gástricos)",    "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT006", "nombre": "Antidiabéticos",     "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT007", "nombre": "Cardiovasculares",   "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT008", "nombre": "Suplementos",        "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT009", "nombre": "Antivirales",        "requiereCadenaFrio": False, "requiereRegistroSanitario": True},
    {"categoriaId": "CAT010", "nombre": "Respiratorio",       "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT011", "nombre": "Corticoides",        "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT012", "nombre": "Antiagregantes",     "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT013", "nombre": "Endocrino",          "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT014", "nombre": "Hidratación Oral",   "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT015", "nombre": "Antiarrítmicos",     "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT016", "nombre": "Antipsicóticos",     "requiereCadenaFrio": False, "requiereRegistroSanitario": True},
    {"categoriaId": "CAT017", "nombre": "Antidepresivos",     "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT018", "nombre": "Diuréticos",         "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT019", "nombre": "Anticoagulantes",    "requiereCadenaFrio": False, "requiereRegistroSanitario": True},
    {"categoriaId": "CAT020", "nombre": "Antieméticos",       "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT021", "nombre": "Ansiolíticos",       "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    {"categoriaId": "CAT022", "nombre": "Inmunosupresores",   "requiereCadenaFrio": False, "requiereRegistroSanitario": True},
]

def seed_default_categories(db: Session) -> int:
    table = CategoriaProducto.__table__
    insert_stmt = pg_insert(table).values(DEFAULT_CATEGORIES)

    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=[table.c.categoriaId],
        set_={
            "nombre": insert_stmt.excluded.nombre,
            "requiereCadenaFrio": insert_stmt.excluded.requiereCadenaFrio,
            "requiereRegistroSanitario": insert_stmt.excluded.requiereRegistroSanitario,
        },
    )

    res = db.execute(upsert_stmt)
    return res.rowcount or 0

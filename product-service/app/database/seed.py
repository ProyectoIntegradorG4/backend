from sqlalchemy.orm import Session
from app.models.category import CategoriaProducto

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
    for item in SEED_CATEGORIES:
        exists = db.get(CategoriaProducto, item["categoriaId"])
        if exists:
            continue
        db.add(CategoriaProducto(**item))
    db.commit()

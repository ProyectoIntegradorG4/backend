from sqlalchemy.orm import Session
from app.models.category import CategoriaProducto

def seed_categories(db: Session):
    """
    Carga categorías mínimas para pruebas locales.
    """
    initial = [
        # Inmunizaciones (requiere cadena de frío y registro sanitario)
        {"categoriaId": "CAT-IMM-001", "nombre": "Vacunas", "requiereCadenaFrio": True, "requiereRegistroSanitario": True},
        # Analgésicos (no requiere cadena de frío, sí registro sanitario)
        {"categoriaId": "CAT-ANL-001", "nombre": "Analgésicos", "requiereCadenaFrio": False, "requiereRegistroSanitario": True},
        # Dispositivos (no requiere registro sanitario en este MVP)
        {"categoriaId": "CAT-DSP-001", "nombre": "Dispositivos médicos", "requiereCadenaFrio": False, "requiereRegistroSanitario": False},
    ]

    for item in initial:
        if not db.query(CategoriaProducto).get(item["categoriaId"]):
            db.add(CategoriaProducto(**item))
    db.commit()

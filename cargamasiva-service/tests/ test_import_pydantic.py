# tests/test_import_pydantic.py
from datetime import date, datetime
import pytest

from app.models.product import ProductoCSVIn

def test_producto_csv_in_ok():
    p = ProductoCSVIn.model_validate({
        "productoId": "P100",
        "nombre": "Producto X",
        "descripcion": "Desc",
        "categoriaId": "CAT001",
        "formaFarmaceutica": "Tableta",
        "requierePrescripcion": True,
        "registroSanitario": "RS-100",
        "sku": "SKU-100",
        "location": "B1",
        "ubicacion": "U1",
        "stock": 10,
        "precio": 99.5,
        "estado_producto": "activo",
        "actualizado_en": "2025-01-01T10:00:00",
        "fechaVencimiento": "2026-12-31",
    })
    assert p.estado_producto == "ACTIVO"
    assert isinstance(p.fechaVencimiento, date)
    assert isinstance(p.actualizado_en, datetime)

def test_producto_csv_in_estado_invalido():
    with pytest.raises(Exception):
        ProductoCSVIn.model_validate({
            "productoId":"P1","nombre":"X","categoriaId":"CAT001","estado_producto":"DESCONOCIDO"
        })

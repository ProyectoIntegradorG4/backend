# tests/test_utils.py
import pytest
from app.utils import (
    get_csv_headers, read_csv_bytes, safe_int, safe_float,
    safe_bool, safe_date, safe_datetime, validate_row
)


# -----------------------------
# Tests de parsing básico
# -----------------------------
def test_get_csv_headers():
    data = b"productoId,nombre,categoriaId\nP1,Prod1,CAT001"
    headers = get_csv_headers(data)
    assert headers == ["productoId", "nombre", "categoriaId"]


def test_read_csv_bytes():
    data = b"productoId,nombre,categoriaId\nP1,Prod1,CAT001"
    rows = list(read_csv_bytes(data))
    assert len(rows) == 1
    assert rows[0]["productoId"] == "P1"


# -----------------------------
# Tests de normalizadores
# -----------------------------
@pytest.mark.parametrize("value,expected", [
    ("10", 10),
    ("10.0", 10),
    ("", None),
    (None, None),
])
def test_safe_int(value, expected):
    assert safe_int(value) == expected


@pytest.mark.parametrize("value,expected", [
    ("10.5", 10.5),
    ("1000", 1000.0),
    ("", None),
    (None, None),
])
def test_safe_float(value, expected):
    assert safe_float(value) == expected


@pytest.mark.parametrize("value,expected", [
    ("true", True),
    ("1", True),
    ("sí", True),
    ("false", False),
    ("0", False),
    ("no", False),
    ("", None),
    (None, None),
])
def test_safe_bool(value, expected):
    assert safe_bool(value) == expected


def test_safe_date():
    assert str(safe_date("2026-01-01")) == "2026-01-01"
    assert safe_date("") is None


def test_safe_datetime():
    assert safe_datetime("2025-01-01T10:00:00").year == 2025
    assert safe_datetime("") is None


# -----------------------------
# Tests de validate_row
# -----------------------------
def test_validate_row_happy_path():
    row = {
        "productoId": "P1",
        "nombre": "X",
        "categoriaId": "CAT001",  
        "requierePrescripcion": "true",
        "estado_producto": "ACTIVO",
        "location": "B1",
        "ubicacion": "U1",
        "stock": "10",
        "precio": "1000",
        "fechaVencimiento": "2026-01-01"
    }
    assert validate_row(row) == []


def test_validate_row_missings():
    row = {}
    errors = validate_row(row)
    # Debe reportar todos los requeridos
    assert "productoId requerido" in errors
    assert "categoriaId requerido" in errors
    assert "precio requerido" in errors


def test_validate_row_bad_types():
    row = {
        "productoId": "P1",
        "nombre": "X",
        "categoriaId": "CAT001",
        "requierePrescripcion": "maybe",
        "estado_producto": "ACTIVO",
        "location": "L1",
        "ubicacion": "U1",
        "stock": "ten",
        "precio": "abc",
        "fechaVencimiento": "31/20/9999"
    }
    errors = validate_row(row)
    assert "requierePrescripcion inválido (true/false)" in errors
    assert "stock inválido (entero)" in errors
    assert "precio inválido (numérico)" in errors
    assert "fechaVencimiento inválida (fecha)" in errors

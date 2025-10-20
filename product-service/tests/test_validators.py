# tests/test_validators.py
import pytest
from app.service.validators import validate_ean, validate_registro_sanitario

def test_validate_ean_ok():
    # EAN-13 válido (check digit correcto para "770123456789")
    assert validate_ean("7701234567897") is True

@pytest.mark.parametrize("bad", ["", "123", "ABCDEFGHIJKLM", None])
def test_validate_ean_bad_inputs(bad):
    assert validate_ean(bad) is False

def test_validate_registro_sanitario_ok():
    assert validate_registro_sanitario("INVIMA 2025M-000123-R1") is True

@pytest.mark.parametrize("bad", [
    "INV-XX",
    "INVIMA",
    "2025M-000123",
    "X-000123-R1",
    ""
])
def test_validate_registro_sanitario_bad(bad):
    assert validate_registro_sanitario(bad) is False

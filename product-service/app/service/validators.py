import re

EAN_REGEX = re.compile(r"^\d{8}$|^\d{12,14}$")  # EAN-8, UPC/EAN-13/14 simplificado

def validate_ean(code: str) -> bool:
    """Valida longitud y dígito de control EAN/GTIN de forma básica."""
    if not EAN_REGEX.match(code or ""):
        return False

    # Cálculo de dígito de control (GTIN mod-10)
    digits = [int(d) for d in code]
    check_digit = digits[-1]
    body = digits[:-1]
    # Ponderación alterna desde la derecha, 3 para posiciones impares
    total = 0
    parity = 1
    for d in reversed(body):
        total += d * (3 if parity else 1)
        parity = 1 - parity
    calc = (10 - (total % 10)) % 10
    return calc == check_digit

RS_REGEX = re.compile(r"^[A-Z]{4,10}\s?\d{4,}[A-Z0-9\-]*$", re.IGNORECASE)

def validate_registro_sanitario(rs: str) -> bool:
    """Validación de formato básico del registro sanitario (MVP)."""
    if not rs:
        return False
    return bool(RS_REGEX.match(rs.strip()))

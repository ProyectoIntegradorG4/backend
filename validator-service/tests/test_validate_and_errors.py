# tests/test_validate_and_errors.py
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models import ProductStaging, ProductStagingErrors

def test_validate_without_pending_returns_zeroes(client, db_session: Session):
    r = client.post("/validate")
    assert r.status_code == 200

    body = r.json()
    assert body["resumen"]["total_pendientes"] == 0
    assert body["resumen"]["total_validados"] == 0
    assert body["resumen"]["total_invalidos"] == 0
    assert body["resumen"]["total_errores"] == 0

def test_validate_mixed_valid_invalid_and_errors(client, db_session: Session):
    # Producto válido
    p_valid = ProductStaging(
        sku="SKU-VAL",
        name="Producto Bueno",
        category="categoria_a",
        unit_price=10,
        expiration_date=date.today() + timedelta(days=10),
        import_id="00000000-0000-0000-0000-000000000AAA",
        validation_status="PENDING",
    )

    # Producto inválido (expirado + precio negativo)
    p_invalid = ProductStaging(
        sku="SKU-INV",
        name="Producto Malo",
        category="categoria_a",
        unit_price=-5,
        expiration_date=date.today() - timedelta(days=1),
        import_id="00000000-0000-0000-0000-000000000BBB",
        validation_status="PENDING",
    )

    db_session.add_all([p_valid, p_invalid])
    db_session.commit()

    r = client.post("/validate")
    assert r.status_code == 200
    body = r.json()

    assert body["resumen"]["total_pendientes"] == 2
    assert body["resumen"]["total_validados"] == 1
    assert body["resumen"]["total_invalidos"] == 1
    assert body["resumen"]["total_errores"] >= 1  # normalmente 2

    # Validamos que existan errores guardados
    total_errors = db_session.query(ProductStagingErrors).count()
    assert total_errors >= 1

def test_validate_is_idempotent_when_no_pending_anymore(client, db_session: Session):
    # Semilla: un registro inválido y uno válido
    p_invalid = ProductStaging(
        sku="SKU-IDEM-INV",
        name="Expirado",
        category="categoria_a",
        unit_price=-1,
        expiration_date=date.today() - timedelta(days=1),
        import_id="00000000-0000-0000-0000-000000000000",
        validation_status="PENDING",
    )
    p_valid = ProductStaging(
        sku="SKU-IDEM-OK",
        name="Ok",
        category="categoria_a",
        unit_price=10,
        expiration_date=date.today() + timedelta(days=10),
        import_id="00000000-0000-0000-0000-000000000001",
        validation_status="PENDING",
    )
    db_session.add_all([p_invalid, p_valid])
    db_session.commit()

    # Primera validación
    r1 = client.post("/validate")
    assert r1.status_code == 200
    body1 = r1.json()

    assert body1["resumen"]["total_pendientes"] == 2
    assert body1["resumen"]["total_validados"] == 1
    assert body1["resumen"]["total_invalidos"] == 1
    assert body1["resumen"]["total_errores"] >= 1

    errors_after_first = db_session.query(ProductStagingErrors).count()

    # Segunda validación (no hay nuevos pendientes)
    r2 = client.post("/validate")
    assert r2.status_code == 200
    body2 = r2.json()

    assert body2["resumen"]["total_pendientes"] == 0
    assert body2["resumen"]["total_validados"] == 0
    assert body2["resumen"]["total_invalidos"] == 0
    assert body2["resumen"]["total_errores"] == 0  # no se procesó nada

    errors_after_second = db_session.query(ProductStagingErrors).count()
    assert errors_after_second == errors_after_first  # no duplica errores

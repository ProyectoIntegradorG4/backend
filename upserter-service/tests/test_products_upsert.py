from datetime import date, timedelta
from app.models import ProductStaging, Products

def make_staging(
    sku: str,
    *,
    name="Producto",
    category="categoria_a",
    unit_price=10.0,
    expiration_date=None,
    processed=False,
    validation_status="VALID",  # el upsert solo procesa VALID & processed=False
):
    return ProductStaging(
        sku=sku,
        name=name,
        description="desc",
        category=category,
        manufacturer="manu",
        storage_type="cold",
        min_shelf_life_months=24,
        expiration_date=expiration_date or (date.today() + timedelta(days=10)),
        batch_number="B1",
        cold_chain_required=False,
        certifications="cert",
        commercialization_auth="auth",
        country_regulations="reg",
        unit_price=unit_price,
        purchase_conditions="pc",
        delivery_time_hours=48,
        external_code="EXT",
        import_id="00000000-0000-0000-0000-000000000000",
        created_by="tester",
        validation_status=validation_status,
        processed=processed,
    )

def test_products_endpoint_empty(client, db_session):
    r = client.get("/products")
    assert r.status_code == 200
    assert r.json() == []

def test_upsert_no_valid_pending_returns_message(client, db_session):
    # Sin registros VALID & processed=False
    r = client.post("/products/upsert")
    assert r.status_code == 200
    assert r.json()["message"] == "No hay productos para insertar"

def test_upsert_inserts_and_marks_processed(client, db_session):
    p1 = make_staging("SKU-1", unit_price=100.5, processed=False, validation_status="VALID")
    p2 = make_staging("SKU-2", unit_price=200.0, processed=False, validation_status="VALID")
    # un pendiente no válido (INVALID) que no debe procesar
    p3 = make_staging("SKU-INV", unit_price=50, processed=False, validation_status="INVALID")
    db_session.add_all([p1, p2, p3])
    db_session.commit()

    r = client.post("/products/upsert")
    assert r.status_code == 200
    body = r.json()
    # Debe insertar 2
    assert "2 productos insertados correctamente" in body["message"]

    # Los dos deben quedar processed=True
    stg1 = db_session.query(ProductStaging).filter_by(sku="SKU-1").first()
    stg2 = db_session.query(ProductStaging).filter_by(sku="SKU-2").first()
    stg3 = db_session.query(ProductStaging).filter_by(sku="SKU-INV").first()
    assert stg1.processed is True
    assert stg2.processed is True
    assert stg3.processed is False  # INVALID no se procesa

    # Y deben existir en products
    prods = db_session.query(Products).all()
    assert {p.sku for p in prods} == {"SKU-1", "SKU-2"}

def test_upsert_is_idempotent(client, db_session):
    # Crea uno VALID sin procesar, lo subimos 2 veces
    p = make_staging("SKU-X", unit_price=10.0, processed=False, validation_status="VALID")
    db_session.add(p)
    db_session.commit()

    r1 = client.post("/products/upsert")
    assert r1.status_code == 200

    # Segunda corrida: ya quedó processed=True, por tanto no hay productos para insertar
    r2 = client.post("/products/upsert")
    assert r2.status_code == 200
    assert r2.json()["message"] == "No hay productos para insertar"

    # Products solo tiene una fila con ese SKU
    assert db_session.query(Products).filter_by(sku="SKU-X").count() == 1

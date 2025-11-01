from app.models import ProductStaging


def test_list_staging_products_empty(client):
    resp = client.get("/staging-products")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_staging_products_with_data(client, db_session):
    product = ProductStaging(
        sku="SKU2",
        name="P2",
        category="CAT",
        unit_price=10.0,
        created_by="tester",
    )
    db_session.add(product)
    db_session.commit()

    resp = client.get("/staging-products")
    assert resp.status_code == 200

    data = resp.json()[0]
    assert data["sku"] == "SKU2"
    assert data["category"] == "CAT"

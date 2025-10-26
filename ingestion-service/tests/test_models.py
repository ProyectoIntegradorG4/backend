from app.models import ProductStaging
import uuid


def test_model_insert_basic(db_session):
    product = ProductStaging(
        sku="T-001",
        name="Test Product",
        created_by="tester",
    )
    db_session.add(product)
    db_session.commit()

    assert product.product_id is not None
    assert isinstance(product.import_id, uuid.UUID)

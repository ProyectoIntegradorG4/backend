from app.service.product_service import ProductoService

def test_sku_visible_formato():
    sku = ProductoService.sku_visible("11111111-1111-1111-1111-111111111111")
    assert sku.startswith("PROD-")
    assert len(sku) >= 10  # prefijo + algo del id

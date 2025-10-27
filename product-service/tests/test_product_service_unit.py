from app.service.product_service import ProductoService

def test_sku_visible_formato():
    """
    SKU visible debe seguir patrón 'SKU-XXXXXXXX' (8 alfanum en mayúscula).
    """
    sku = ProductoService.sku_visible("11111111-1111-1111-1111-111111111111")
    assert sku.startswith("SKU-")
    code = sku.split("SKU-")[-1]
    assert len(code) == 8
    assert code.isalnum()
    assert code.upper() == code

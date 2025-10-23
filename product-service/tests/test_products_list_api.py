import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from uuid import uuid4

from app.main import app
from app.schemas.product import ProductosResponse, ProductoOut
from app.service import product_service as product_service_module
from app.service.rbac import require_role_admincompras


@pytest.fixture(autouse=True)
def _restore_overrides():
    """
    Limpia overrides de dependencias entre tests.
    """
    original = dict(app.dependency_overrides)
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original)


@pytest.fixture
def client_ok_rbac():
    """
    Cliente con RBAC permitido: sobreescribe require_role_admincompras
    para que no bloquee las requests.
    """
    app.dependency_overrides[require_role_admincompras] = lambda: None
    return TestClient(app)


def _sample_response():
    item = ProductoOut(
        productoId=uuid4(),
        nombre="Vacuna XYZ 10ml",
        categoria="Inmunológicos",
        formaFarmaceutica="suspension_inyectable",
        requierePrescripcion=True,
        registroSanitario="INVIMA 2025M-000123-R1",
        estado_producto="activo",
        actualizado_en=datetime(2025, 1, 11, 14, 22, 3, tzinfo=timezone.utc),
    )
    return ProductosResponse(page=1, page_size=25, total=1, items=[item])


def test_list_ok_structure(client_ok_rbac, monkeypatch):
    """
    Debe responder 200 y con la estructura paginada definida en la HU.
    """
    monkeypatch.setattr(
        product_service_module.ProductoService,
        "listar_productos",
        staticmethod(lambda **kwargs: _sample_response()),
    )

    resp = client_ok_rbac.get(
        "/api/v1/productos?page=1&page_size=25&sort=nombre&order=asc&estado_producto=activo"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"page", "page_size", "total", "items"}
    assert body["page"] == 1
    assert body["page_size"] == 25
    assert body["total"] == 1
    assert isinstance(body["items"], list) and len(body["items"]) == 1

    item = body["items"][0]
    # Columnas mínimas (HU)
    for k in [
        "productoId",
        "nombre",
        "categoria",
        "formaFarmaceutica",
        "requierePrescripcion",
        "registroSanitario",
        "estado_producto",
        "actualizado_en",
    ]:
        assert k in item


def test_list_passes_filters_and_sort_to_service(client_ok_rbac, monkeypatch):
    """
    Verifica que el endpoint pase correctamente los parámetros al service.
    """
    called = {}

    def fake_listar_productos(**kwargs):
        called.update(kwargs)
        return _sample_response()

    monkeypatch.setattr(
        product_service_module.ProductoService,
        "listar_productos",
        staticmethod(fake_listar_productos),
    )

    params = {
        "q": "vacu",
        "categoriaId": str(uuid4()),
        "estado_producto": "activo",
        "sort": "nombre",
        "order": "asc",
        "page": 2,
        "page_size": 25,
    }
    resp = client_ok_rbac.get("/api/v1/productos", params=params)
    assert resp.status_code == 200

    # Se pasaron los parámetros correctamente al service
    assert called["q"] == "vacu"
    assert called["categoria_id"] == params["categoriaId"]
    assert called["estado"] == "activo"
    assert called["sort"] == "nombre"
    assert called["order"] == "asc"
    assert called["page"] == 2
    assert called["page_size"] == 25


def test_list_default_pagination(client_ok_rbac, monkeypatch):
    """
    Si no se envían page/page_size, deben ser 1 y 25 por defecto.
    """
    called = {}

    def fake_listar_productos(**kwargs):
        called.update(kwargs)
        return _sample_response()

    monkeypatch.setattr(
        product_service_module.ProductoService,
        "listar_productos",
        staticmethod(fake_listar_productos),
    )

    resp = client_ok_rbac.get("/api/v1/productos")
    assert resp.status_code == 200
    assert called["page"] == 1
    assert called["page_size"] == 25


def test_list_rejects_invalid_categoria_uuid(monkeypatch):
    """
    Si categoriaId no es UUID válido, debe responder 400.
    """
    app.dependency_overrides[require_role_admincompras] = lambda: None

    # No necesitamos mockear el service porque no debe llegar a llamarse
    client = TestClient(app)
    resp = client.get("/api/v1/productos?categoriaId=NO-UUID")
    assert resp.status_code == 400
    data = resp.json()
    assert "categoriaId inválido" in data.get("detail", "")


def test_list_rbac_forbidden(monkeypatch):
    """
    Si el RBAC niega acceso, debe responder 403.
    """
    # Sobre-escribimos el RBAC para que falle
    from fastapi import HTTPException, status as st

    def deny():
        raise HTTPException(status_code=st.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    app.dependency_overrides[require_role_admincompras] = deny

    client = TestClient(app)
    resp = client.get("/api/v1/productos")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Acceso denegado"

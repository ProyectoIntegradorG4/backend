from uuid import uuid4
from starlette.testclient import TestClient
from app.main import app
from app.service import product_service as product_service_module
from app.service.rbac import require_role_admincompras

client = TestClient(app)

def _sample_response():
    # productoId como UUID para verificar que el endpoint normaliza a str
    return {
        "total": 1,
        "page": 1,
        "page_size": 25,
        "items": [
            {
                "productoId": uuid4(),
                "nombre": "Vacuna X",
                "categoria": "Biológicos",
                "formaFarmaceutica": "Suspensión",
                "requierePrescripcion": True,
                "registroSanitario": "INVIMA2024-M-000111",
                "estado_producto": "activo",
                "actualizado_en": None,
            }
        ],
    }

def test_list_ok_structure(monkeypatch):
    """
    Debe responder 200 y con la estructura paginada.
    """
    app.dependency_overrides[require_role_admincompras] = lambda: None
    monkeypatch.setattr(
        product_service_module.ProductoService,
        "listar_productos",
        staticmethod(lambda **kwargs: _sample_response()),
    )

    resp = client.get("/api/v1/productos?page=1&page_size=25&sort=nombre&order=asc&estado_producto=activo")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert isinstance(data["items"], list)
    assert isinstance(data["items"][0]["productoId"], str)

def test_list_passes_filters_and_sort_to_service(monkeypatch):
    """
    Verifica que el endpoint pase correctamente los parámetros al service.
    """
    app.dependency_overrides[require_role_admincompras] = lambda: None

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
    resp = client.get("/api/v1/productos", params=params)
    assert resp.status_code == 200

    # Los parámetros deben llegar al service con estas llaves
    assert called["q"] == "vacu"
    assert called["categoria_id"] == params["categoriaId"]
    assert called["estado"] == "activo"
    assert called["sort"] == "nombre"
    assert called["order"] == "asc"
    assert called["page"] == 2
    assert called["page_size"] == 25

def test_list_default_pagination(monkeypatch):
    """
    Si no se envían page/page_size, deben ser 1 y 25 por defecto.
    """
    app.dependency_overrides[require_role_admincompras] = lambda: None

    called = {}
    def fake_listar_productos(**kwargs):
        called.update(kwargs)
        return _sample_response()

    monkeypatch.setattr(
        product_service_module.ProductoService,
        "listar_productos",
        staticmethod(fake_listar_productos),
    )

    resp = client.get("/api/v1/productos")
    assert resp.status_code == 200
    assert called["page"] == 1
    assert called["page_size"] == 25

def test_list_rejects_invalid_categoria_uuid(monkeypatch):
    """
    Si categoriaId no es UUID válido, debe responder 400.
    """
    app.dependency_overrides[require_role_admincompras] = lambda: None

    resp = client.get("/api/v1/productos?categoriaId=NO-UUID")
    assert resp.status_code == 400

def test_list_rbac_forbidden(monkeypatch):
    """
    Si el RBAC niega acceso, debe responder 403 con 'Acceso denegado'.
    """
    from fastapi import HTTPException, status as st
    def deny():
        raise HTTPException(status_code=st.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    app.dependency_overrides[require_role_admincompras] = deny

    resp = client.get("/api/v1/productos")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Acceso denegado"

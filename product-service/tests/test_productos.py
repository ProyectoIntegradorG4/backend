from starlette.testclient import TestClient
import app.service.audit_client as audit_client
from app.main import app

client = TestClient(app)

ALLOWED_ROLE = "Administrador de Compras"

def _auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}

def _make_token(roles=None):
    # token dummy; los roles se pasan por header X-User-Role (legacy)
    return "dummy"

def test_listar_productos_requiere_token():
    r = client.get("/productos")  # sin token ni rol
    assert r.status_code == 401
    assert "Authorization" in r.json().get("detail", "")

def test_listar_productos_forbidden_sin_rol():
    # Con token pero sin rol válido => 403 "No autorizado"
    headers = _auth_header(_make_token())  # sin X-User-Role
    r = client.get("/productos", headers=headers)
    assert r.status_code == 403
    assert r.json().get("detail") == "No autorizado"

def test_listar_productos_ok_con_rol():
    # Con token y rol correcto => 200
    headers = _auth_header(_make_token())
    headers["X-User-Role"] = ALLOWED_ROLE
    r = client.get("/productos", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert "total" in body

def test_crear_producto_valida_categoria_inexistente():
    # Con token y rol pero categoriaId inválida => 400 "categoriaId inexistente"
    headers = _auth_header(_make_token())
    headers["X-User-Role"] = ALLOWED_ROLE
    payload = {
        "nombre": "X",
        "descripcion": "Y",
        "categoriaId": "NO-EXISTE",
        "formaFarmaceutica": "Tableta",
        "requierePrescripcion": False
    }
    r = client.post("/productos", headers=headers, json=payload)
    assert r.status_code == 400
    assert "categoriaId inexistente" in r.json().get("detail", "")

def test_crear_producto_valida_campos_obligatorios():
    # Falta descripcion y formaFarmaceutica => 422 (validación Pydantic)
    headers = _auth_header(_make_token())
    headers["X-User-Role"] = ALLOWED_ROLE
    payload = {
        "nombre": "Ibuprofeno",
        "categoriaId": "CAT-ANL-001",
        "requierePrescripcion": False
    }
    r = client.post("/productos", headers=headers, json=payload)
    assert r.status_code == 422

def test_crear_producto_ok_con_rbac_y_token(monkeypatch):
    # Evitar conexión a auditoría; redis ya vale None en tests.
    async def noop(*args, **kwargs):
        return None
    monkeypatch.setattr(audit_client, "send_audit_event", noop)

    headers = _auth_header(_make_token())
    headers["X-User-Role"] = ALLOWED_ROLE

    payload = {
        "nombre": "Acetaminofén 500mg",
        "descripcion": "Caja x 16 tabletas",
        "categoriaId": "CAT-ANL-001",
        "formaFarmaceutica": "Tableta",
        "requierePrescripcion": False,
        "registroSanitario": "INVIMA2020-M-123456"
    }
    r = client.post("/productos", headers=headers, json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["nombre"] == payload["nombre"]
    assert body["categoria"] in ("CAT-ANL-001", "Analgésicos")
    assert body["formaFarmaceutica"] == "Tableta"


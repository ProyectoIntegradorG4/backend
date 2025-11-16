from starlette.testclient import TestClient
from main import app

# NO usar cliente global - usar el fixture
# client = TestClient(app)  # REMOVIDO


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code in (200, 204)


def test_rbac_missing_header(client):
    """
    POST /productos debe validar headers ANTES del body.
    Sin Authorization => 401 y debe mencionar 'Authorization'.
    """
    r = client.post("/productos", json={"nombre": "X"})
    assert r.status_code == 401
    assert "Authorization" in r.json().get("detail", "")

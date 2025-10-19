# tests/test_health_and_rbac.py
from tests.conftest import client, descubrir_endpoint_creacion

def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    # En algunos entornos dev puede responder "degraded"; lo aceptamos.
    assert body.get("status") in ("healthy", "degraded")

def test_rbac_missing_header():
    create_path = descubrir_endpoint_creacion()
    assert create_path, "No pude inferir el endpoint de creación."
    r = client.post(create_path, json={"nombre": "X"})
    # Debe rechazar por falta de rol
    assert r.status_code in (401, 403)

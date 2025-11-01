from fastapi.testclient import TestClient
from app.main import app, safe_float, safe_int, safe_bool

def test_safe_helpers_cover_branches():
    # safe_float
    assert safe_float("1.23") == 1.23
    assert safe_float(5) == 5.0
    assert safe_float("nan") is None
    assert safe_float("inf") is None
    assert safe_float(None) is None
    assert safe_float("x") is None

    # safe_int
    assert safe_int("10") == 10
    assert safe_int(10.9) == 10
    assert safe_int(None) is None
    assert safe_int("x") is None

    # safe_bool
    assert safe_bool(True) is True
    assert safe_bool(False) is False
    assert safe_bool("true") is True
    assert safe_bool("1") is True
    assert safe_bool("yes") is True
    assert safe_bool("no") is False
    assert safe_bool(0) is False
    assert safe_bool(2) is True

def test_health_endpoint_ok():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

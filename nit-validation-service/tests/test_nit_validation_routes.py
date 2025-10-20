import pytest
from fastapi.testclient import TestClient
from app.routes.nit_validation import router
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

def test_health_check(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    monkeypatch.setattr(nit_validation, "test_db_connection", lambda: True)
    monkeypatch.setattr(nit_validation, "test_redis_connection", lambda: True)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["redis"] == "connected"

def test_validate_nit_post_success(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    from datetime import datetime
    class DummyResponse:
        def __init__(self):
            self.valid = True
            self.nit = "12345678"
            self.nombre_institucion = "Institución Test"
            self.pais = "CO"
            self.fecha_registro = datetime(2022, 1, 1, 0, 0, 0)
            self.activo = True
            self.mensaje = "NIT válido encontrado"
        def dict(self):
            d = self.__dict__.copy()
            d["fecha_registro"] = self.fecha_registro.isoformat()
            return d
    monkeypatch.setattr(nit_validation, "nit_service", MagicMock())
    monkeypatch.setattr(nit_validation.nit_service, "validate_nit", AsyncMock(return_value=DummyResponse()))
    payload = {"nit": "12345678", "pais": "CO"}
    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["nit"] == "12345678"
    assert data["nombre_institucion"] == "Institución Test"
    assert data["pais"] == "CO"
    assert data["activo"] is True
    assert "NIT válido encontrado" in data["mensaje"]

def test_validate_nit_post_not_found(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    class DummyResponse:
        def __init__(self):
            self.valid = False
            self.mensaje = "NIT no encontrado en instituciones asociadas"
        def dict(self):
            return self.__dict__
    monkeypatch.setattr(nit_validation, "nit_service", MagicMock())
    monkeypatch.setattr(nit_validation.nit_service, "validate_nit", AsyncMock(return_value=DummyResponse()))
    payload = {"nit": "00000000", "pais": "CO"}
    response = client.post("/validate", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["valid"] is False
    assert "no encontrado" in data["mensaje"].lower()

def test_validate_nit_post_format_error(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    class DummyResponse:
        def __init__(self):
            self.valid = False
            self.mensaje = "Formato de NIT inválido: NIT debe tener entre 8 y 20 caracteres"
        def dict(self):
            return self.__dict__
    monkeypatch.setattr(nit_validation, "nit_service", MagicMock())
    monkeypatch.setattr(nit_validation.nit_service, "validate_nit", AsyncMock(return_value=DummyResponse()))
    payload = {"nit": "123", "pais": "CO"}
    response = client.post("/validate", json=payload)
    assert response.status_code in (400, 422)
    data = response.json()
    # Puede ser error de validación de FastAPI/Pydantic
    if "valid" in data:
        assert data["valid"] is False
    else:
        assert "detail" in data
    if "mensaje" in data:
        assert "formato" in data["mensaje"].lower() or "detail" in data

def test_validate_nit_get_success(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    from datetime import datetime
    class DummyResponse:
        def __init__(self):
            self.valid = True
            self.nit = "12345678"
            self.nombre_institucion = "Institución Test"
            self.pais = "CO"
            self.fecha_registro = datetime(2022, 1, 1, 0, 0, 0)
            self.activo = True
            self.mensaje = "NIT válido encontrado"
        def dict(self):
            d = self.__dict__.copy()
            d["fecha_registro"] = self.fecha_registro.isoformat()
            return d
    monkeypatch.setattr(nit_validation, "nit_service", MagicMock())
    monkeypatch.setattr(nit_validation.nit_service, "validate_nit", AsyncMock(return_value=DummyResponse()))
    response = client.get("/validate/12345678?pais=CO")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["nit"] == "12345678"
    assert data["nombre_institucion"] == "Institución Test"
    assert data["pais"] == "CO"
    assert data["activo"] is True
    assert "NIT válido encontrado" in data["mensaje"]

def test_validate_nit_get_not_found(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    class DummyResponse:
        def __init__(self):
            self.valid = False
            self.mensaje = "NIT no encontrado en instituciones asociadas"
        def dict(self):
            return self.__dict__
    monkeypatch.setattr(nit_validation, "nit_service", MagicMock())
    monkeypatch.setattr(nit_validation.nit_service, "validate_nit", AsyncMock(return_value=DummyResponse()))
    response = client.get("/validate/00000000?pais=CO")
    assert response.status_code == 404
    data = response.json()
    assert data["valid"] is False
    assert "no encontrado" in data["mensaje"].lower()

def test_validate_nit_get_format_error(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    class DummyResponse:
        def __init__(self):
            self.valid = False
            self.mensaje = "Formato de NIT inválido: NIT debe tener entre 8 y 20 caracteres"
        def dict(self):
            return self.__dict__
    monkeypatch.setattr(nit_validation, "nit_service", MagicMock())
    monkeypatch.setattr(nit_validation.nit_service, "validate_nit", AsyncMock(return_value=DummyResponse()))
    response = client.get("/validate/123?pais=CO")
    assert response.status_code in (400, 422, 500)
    data = response.json()
    assert data.get("valid") is False or "detail" in data
    # Puede ser error de validación de FastAPI/Pydantic
    if "mensaje" in data:
        assert "formato" in data["mensaje"].lower() or "detail" in data

def test_get_institution_details_success(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    class DummyInstitucion:
        nit = "12345678"
        nombre_institucion = "Institución Test"
        pais = "CO"
        fecha_registro = "2022-01-01T00:00:00"
        activo = True
    monkeypatch.setattr(nit_validation.nit_service, "get_institution_details", AsyncMock(return_value=DummyInstitucion()))
    response = client.get("/institution/12345678")
    assert response.status_code == 200
    data = response.json()
    assert data["nit"] == "12345678"
    assert data["nombre_institucion"] == "Institución Test"
    assert data["pais"] == "CO"
    assert data["activo"] is True

def test_get_institution_details_not_found(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    monkeypatch.setattr(nit_validation.nit_service, "get_institution_details", AsyncMock(return_value=None))
    response = client.get("/institution/00000000")
    assert response.status_code == 404
    data = response.json()
    assert "codigo" in data["detail"]
    assert data["detail"]["codigo"] == nit_validation.NITErrorCodes.NO_ENCONTRADO

def test_get_institution_details_error(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    async def raise_exc(*args, **kwargs):
        raise Exception("fail")
    monkeypatch.setattr(nit_validation.nit_service, "get_institution_details", raise_exc)
    response = client.get("/institution/12345678")
    assert response.status_code == 500
    data = response.json()
    assert "codigo" in data["detail"]
    assert data["detail"]["codigo"] == nit_validation.NITErrorCodes.ERROR_INTERNO

def test_clear_nit_cache_success(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    monkeypatch.setattr(nit_validation.nit_service, "clear_cache_for_nit", MagicMock(return_value=True))
    response = client.delete("/cache/12345678?pais=CO")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Caché limpiado" in data["message"]

def test_clear_nit_cache_fail(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    monkeypatch.setattr(nit_validation.nit_service, "clear_cache_for_nit", MagicMock(return_value=False))
    response = client.delete("/cache/12345678?pais=CO")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "No se pudo limpiar" in data["message"]

def test_clear_nit_cache_error(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    def raise_exc(*args, **kwargs):
        raise Exception("fail")
    monkeypatch.setattr(nit_validation.nit_service, "clear_cache_for_nit", raise_exc)
    response = client.delete("/cache/12345678?pais=CO")
    assert response.status_code == 500
    data = response.json()
    assert "codigo" in data["detail"]
    assert data["detail"]["codigo"] == nit_validation.NITErrorCodes.CACHE_ERROR

def test_get_cache_stats_success(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    monkeypatch.setattr(nit_validation.nit_service, "get_cache_stats", MagicMock(return_value={"hits": 1}))
    response = client.get("/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cache_stats" in data
    assert data["cache_stats"]["hits"] == 1

def test_get_cache_stats_error(client, monkeypatch):
    import app.routes.nit_validation as nit_validation
    def raise_exc():
        raise Exception("fail")
    monkeypatch.setattr(nit_validation.nit_service, "get_cache_stats", raise_exc)
    response = client.get("/cache/stats")
    assert response.status_code == 500
    data = response.json()
    assert "codigo" in data["detail"]
    assert data["detail"]["codigo"] == nit_validation.NITErrorCodes.CACHE_ERROR

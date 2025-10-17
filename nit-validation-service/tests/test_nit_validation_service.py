import pytest
from unittest.mock import MagicMock
from app.services.nit_validation_service import NITValidationService
from app.models.institucion import NITValidationResponse, InstitucionAsociada

class DummyDB:
    def query(self, model):
        return self
    def filter(self, *args, **kwargs):
        return self
    def first(self):
        return None

def test_validate_nit_format_valid():
    service = NITValidationService()
    valid, error = service._validate_nit_format("12345678")
    assert valid
    assert error is None

def test_validate_nit_format_invalid():
    service = NITValidationService()
    valid, error = service._validate_nit_format("")
    assert not valid
    assert error == "NIT no puede estar vacío"

    valid, error = service._validate_nit_format("1234")
    assert not valid
    assert error == "NIT debe tener entre 8 y 20 caracteres"

    valid, error = service._validate_nit_format("12345678A")
    assert not valid
    assert error == "NIT debe contener solo números"

def test_generate_cache_key():
    service = NITValidationService()
    key = service._generate_cache_key("12345678", "GT")
    assert key == "nit_validation:12345678:GT"
    key = service._generate_cache_key("12345678")
    assert key == "nit_validation:12345678"

def test_get_from_cache_none(monkeypatch):
    service = NITValidationService()
    service.redis_client = None
    assert service._get_from_cache("key") is None

def test_set_cache_none(monkeypatch):
    service = NITValidationService()
    service.redis_client = None
    assert service._set_cache("key", {"a":1}) is None

def test_create_response_none():
    service = NITValidationService()
    resp = service._create_response(None)
    assert not resp.valid
    assert "no encontrado" in resp.mensaje

def test_create_response_valid():
    service = NITValidationService()
    from datetime import datetime
    institucion = InstitucionAsociada(
        nit="12345678",
        nombre_institucion="Test",
        pais="GT",
        fecha_registro=datetime(2023, 1, 1),
        activo=True
    )
    resp = service._create_response(institucion)
    assert resp.valid
    assert resp.nit == "12345678"
    assert resp.nombre_institucion == "Test"
    assert resp.pais == "GT"
    assert resp.activo

def test_query_database(monkeypatch):
    service = NITValidationService()
    db = DummyDB()
    result = service._query_database(db, "12345678", None)
    assert result is None

def test_clear_cache_for_nit(monkeypatch):
    service = NITValidationService()
    service.redis_client = MagicMock()
    service.redis_client.delete.return_value = 1
    assert service.clear_cache_for_nit("12345678")
    service.redis_client.delete.return_value = 0
    assert not service.clear_cache_for_nit("12345678")

def test_get_cache_stats(monkeypatch):
    service = NITValidationService()
    service.redis_client = MagicMock()
    service.redis_client.info.return_value = {
        "connected_clients": 2,
        "used_memory_human": "1MB",
        "keyspace_hits": 10,
        "keyspace_misses": 5,
        "uptime_in_seconds": 1000
    }
    stats = service.get_cache_stats()
    assert stats["connected_clients"] == 2
    assert stats["used_memory_human"] == "1MB"
    assert stats["keyspace_hits"] == 10
    assert stats["keyspace_misses"] == 5
    assert stats["uptime_in_seconds"] == 1000
    service.redis_client = None
    stats = service.get_cache_stats()
    assert "error" in stats

def test_validate_nit_public(monkeypatch):
    service = NITValidationService()
    # Mockear dependencias
    service._validate_nit_format = lambda nit: (True, None)
    service._generate_cache_key = lambda nit, pais=None: "key"
    service._get_from_cache = lambda key: None
    service._query_database = lambda db, nit, pais=None: None
    service._set_cache = lambda key, data, ttl: None
    # DummyDB para simular la sesión
    db = object()
    resp = service.validate_nit(db, "12345678")
    # Si es coroutine, ejecutar con asyncio
    import asyncio
    if asyncio.iscoroutine(resp):
        resp = asyncio.run(resp)
    assert not resp.valid
    assert "no encontrado" in resp.mensaje or "inválido" in resp.mensaje

def test_validate_nit_format_empty():
    service = NITValidationService()
    valid, error = service._validate_nit_format("")
    assert not valid
    assert error == "NIT no puede estar vacío"

def test_validate_nit_format_length():
    service = NITValidationService()
    valid, error = service._validate_nit_format("1234")
    assert not valid
    assert error == "NIT debe tener entre 8 y 20 caracteres"

def test_validate_nit_format_non_digit():
    service = NITValidationService()
    valid, error = service._validate_nit_format("12345678A")
    assert not valid
    assert error == "NIT debe contener solo números"

def test_get_from_cache_exception(monkeypatch):
    service = NITValidationService()
    class DummyRedis:
        def get(self, key):
            raise Exception("fail")
    service.redis_client = DummyRedis()
    assert service._get_from_cache("key") is None

def test_set_cache_exception(monkeypatch):
    service = NITValidationService()
    class DummyRedis:
        def setex(self, key, ttl, value):
            raise Exception("fail")
    service.redis_client = DummyRedis()
    # No debe lanzar excepción
    assert service._set_cache("key", {"a":1}) is None

def test_query_database_exception(monkeypatch):
    service = NITValidationService()
    class DummyDB:
        def query(self, model):
            raise Exception("fail")
    try:
        service._query_database(DummyDB(), "12345678", None)
    except Exception as e:
        assert "fail" in str(e)

def test_clear_cache_for_nit_exception(monkeypatch):
    service = NITValidationService()
    class DummyRedis:
        def delete(self, key):
            raise Exception("fail")
    service.redis_client = DummyRedis()
    assert not service.clear_cache_for_nit("12345678")

def test_get_cache_stats_exception(monkeypatch):
    service = NITValidationService()
    class DummyRedis:
        def info(self):
            raise Exception("fail")
    service.redis_client = DummyRedis()
    stats = service.get_cache_stats()
    assert "error" in stats

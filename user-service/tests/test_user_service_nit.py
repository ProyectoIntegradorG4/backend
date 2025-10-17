import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.services.user_service import UserService
from app.models.user import UserRegister, ErrorDetail

@pytest.mark.asyncio
async def test_validate_nit_exists_cache_hit(monkeypatch):
    db = MagicMock()
    service = UserService(db)
    # Simular Redis con resultado en cache
    class DummyRedis:
        async def get(self, key):
            return '{"exists": true, "institucion_id": 99}'
    monkeypatch.setattr(service, "get_redis_client", AsyncMock(return_value=DummyRedis()))
    result, institucion_id = await service.validate_nit_exists("123456789")
    assert result is True
    assert institucion_id == 99

@pytest.mark.asyncio
async def test_validate_nit_exists_cache_miss(monkeypatch):
    db = MagicMock()
    service = UserService(db)
    # Simular Redis sin resultado en cache y HTTP exitoso
    class DummyRedis:
        async def get(self, key):
            return None
        async def setex(self, key, ttl, value):
            return True
    class DummyHttpClient:
        async def get(self, url):
            class DummyResponse:
                status_code = 200
                def json(self):
                    return {"id": 77}
            return DummyResponse()
    monkeypatch.setattr(service, "get_redis_client", AsyncMock(return_value=DummyRedis()))
    monkeypatch.setattr(service, "get_http_client", AsyncMock(return_value=DummyHttpClient()))
    result, institucion_id = await service.validate_nit_exists("123456789")
    assert result is True
    assert institucion_id == 77

@pytest.mark.asyncio
async def test_validate_nit_exists_http_fail(monkeypatch):
    db = MagicMock()
    service = UserService(db)
    # Simular Redis sin resultado y HTTP error
    class DummyRedis:
        async def get(self, key):
            return None
        async def setex(self, key, ttl, value):
            return True
    class DummyHttpClient:
        async def get(self, url):
            class DummyResponse:
                status_code = 404
                def json(self):
                    return {}
            return DummyResponse()
    monkeypatch.setattr(service, "get_redis_client", AsyncMock(return_value=DummyRedis()))
    monkeypatch.setattr(service, "get_http_client", AsyncMock(return_value=DummyHttpClient()))
    result, institucion_id = await service.validate_nit_exists("123456789")
    assert result is False
    assert institucion_id is None

@pytest.mark.asyncio
async def test_validate_nit_exists_exception(monkeypatch):
    db = MagicMock()
    service = UserService(db)
    # Simular excepción en HTTP
    class DummyRedis:
        async def get(self, key):
            return None
    class DummyHttpClient:
        async def get(self, url):
            raise Exception("HTTP error")
    monkeypatch.setattr(service, "get_redis_client", AsyncMock(return_value=DummyRedis()))
    monkeypatch.setattr(service, "get_http_client", AsyncMock(return_value=DummyHttpClient()))
    result, institucion_id = await service.validate_nit_exists("123456789")
    assert result is False
    assert institucion_id is None

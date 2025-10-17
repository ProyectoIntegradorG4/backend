import pytest
from app.database import connection

def test_get_redis_client(monkeypatch):
    class DummyRedis:
        def ping(self):
            return True
    monkeypatch.setattr(connection.redis, "from_url", lambda url, decode_responses: DummyRedis())
    client = connection.get_redis_client()
    assert client is not None

def test_get_redis_client_fail(monkeypatch):
    class DummyRedis:
        def ping(self):
            raise Exception("fail")
    monkeypatch.setattr(connection.redis, "from_url", lambda url, decode_responses: DummyRedis())
    client = connection.get_redis_client()
    assert client is None

def test_test_redis_connection(monkeypatch):
    monkeypatch.setattr(connection, "get_redis_client", lambda: True)
    assert connection.test_redis_connection()
    monkeypatch.setattr(connection, "get_redis_client", lambda: None)
    assert not connection.test_redis_connection()

def test_test_db_connection(monkeypatch):
    class DummyConn:
        def execute(self, sql):
            return 1
    class DummyEngine:
        def connect(self):
            class DummyCtx:
                def __enter__(self):
                    return DummyConn()
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
            return DummyCtx()
    monkeypatch.setattr(connection, "engine", DummyEngine())
    assert connection.test_db_connection()
    # Simular fallo
    class FailEngine:
        def connect(self):
            raise Exception("fail")
    monkeypatch.setattr(connection, "engine", FailEngine())
    assert not connection.test_db_connection()

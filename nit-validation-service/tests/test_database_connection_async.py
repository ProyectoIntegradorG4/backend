import pytest
import os
from app.database import connection

class DummySession:
    def query(self, model):
        class DummyQuery:
            def count(self):
                return 0
        return DummyQuery()
    def close(self):
        pass
    def add(self, inst):
        pass
    def commit(self):
        pass

class DummySessionWithData(DummySession):
    def query(self, model):
        class DummyQuery:
            def count(self):
                return 5
        return DummyQuery()

class DummyInstitucion:
    pass

class DummyBase:
    class metadata:
        @staticmethod
        def create_all(bind=None):
            pass

@pytest.mark.asyncio
async def test_init_db_seed(monkeypatch, tmp_path):
    # Crear archivo JSON temporal
    data = [{
        "nit": "12345678",
        "nombre_institucion": "Test",
        "pais": "GT",
        "fecha_registro": "01/01/2023",
        "activo": True
    }]
    json_path = tmp_path / "NITValidationData.json"
    with open(json_path, "w", encoding="utf-8") as f:
        import json
        json.dump(data, f)
    # Parchear paths y dependencias
    monkeypatch.setattr(connection, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(connection, "engine", object())
    monkeypatch.setattr(connection, "get_redis_client", lambda: True)
    monkeypatch.setattr(connection, "logger", connection.logger)
    # Parchear Base y InstitucionAsociada
    monkeypatch.setattr("app.models.institucion.Base", DummyBase)
    monkeypatch.setattr("app.models.institucion.InstitucionAsociada", DummyInstitucion)
    # Parchear os.path.exists para devolver True solo para el archivo temporal
    monkeypatch.setattr(os.path, "exists", lambda path: str(json_path) == path)
    # Parchear open usando mock_open para evitar recursión
    from unittest.mock import mock_open
    m = mock_open(read_data='[{"nit": "12345678", "nombre_institucion": "Test", "pais": "GT", "fecha_registro": "01/01/2023", "activo": true}]')
    monkeypatch.setattr("builtins.open", m)
    # Parchear os.path.abspath y os.path.join para devolver el path temporal
    monkeypatch.setattr(os.path, "abspath", lambda path: str(tmp_path))
    monkeypatch.setattr(os.path, "join", lambda *args: str(json_path))
    # Ejecutar
    await connection.init_db()

@pytest.mark.asyncio
async def test_init_db_no_seed(monkeypatch, tmp_path):
    monkeypatch.setattr(connection, "SessionLocal", lambda: DummySessionWithData())
    monkeypatch.setattr(connection, "engine", object())
    monkeypatch.setattr(connection, "get_redis_client", lambda: True)
    monkeypatch.setattr(connection, "logger", connection.logger)
    monkeypatch.setattr("app.models.institucion.Base", DummyBase)
    monkeypatch.setattr("app.models.institucion.InstitucionAsociada", DummyInstitucion)
    await connection.init_db()

@pytest.mark.asyncio
async def test_init_db_exception(monkeypatch):
    def fail():
        raise Exception("fail")
    monkeypatch.setattr(connection, "SessionLocal", fail)
    monkeypatch.setattr(connection, "engine", object())
    monkeypatch.setattr(connection, "get_redis_client", lambda: True)
    monkeypatch.setattr(connection, "logger", connection.logger)
    monkeypatch.setattr("app.models.institucion.Base", DummyBase)
    monkeypatch.setattr("app.models.institucion.InstitucionAsociada", DummyInstitucion)
    import pytest
    with pytest.raises(Exception):
        await connection.init_db()

def test_get_db(monkeypatch):
    class DummyDB:
        def close(self):
            pass
    monkeypatch.setattr(connection, "SessionLocal", lambda: DummyDB())
    gen = connection.get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass

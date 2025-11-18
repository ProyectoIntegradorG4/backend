# tests/conftest.py
import os
os.environ.setdefault("AUTH_BYPASS_FOR_TESTS", "1")
os.environ.setdefault("JWT_SECRET_KEY", "testsecret")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Importa tu app FastAPI real
from main import app as fastapi_app
from app.database.connection import EntitiesBase, get_db
from app.database.seed import seed_categories


import sqlite3
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.sql import sqltypes

# Configuración para SQLite: mapear UUID a TEXT
class SQLiteUUID(sqltypes.TypeDecorator):
    impl = sqltypes.CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(sqltypes.CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        return value

@event.listens_for(EntitiesBase.metadata, "before_create")
def before_create(target, connection, **kw):
    # Reemplazar UUID con TEXT para SQLite
    for table in target.tables.values():
        for column in table.columns:
            if hasattr(column.type, '__visit_name__') and column.type.__visit_name__ == 'UUID':
                column.type = TEXT()


TEST_DB_URL = "sqlite:///./test_product.db"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False,
    bind=engine, expire_on_commit=False
)


@pytest.fixture(scope="function", autouse=True)
def db_session():
    """Crea y limpia la BD para cada test - máximo aislamiento"""
    # Recrear BD completa para cada test
    EntitiesBase.metadata.drop_all(bind=engine)
    EntitiesBase.metadata.create_all(bind=engine)
    
    # Crear sesión y hacer seed
    session = TestingSessionLocal()
    seed_categories(session)
    session.commit()
    
    yield session
    
    # Limpiar después del test
    session.close()
    
    # Limpiar dependency_overrides
    from main import app as fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def override_get_db(db_session, monkeypatch):
    """Override de get_db para usar la sesión de test"""
    def _override():
        try:
            yield db_session
        finally:
            pass
    monkeypatch.setattr("app.database.connection.get_db", _override)


@pytest.fixture(name="client")
def client_fixture():
    return TestClient(fastapi_app)

# También como objeto directo para imports
client = TestClient(fastapi_app)


def app():
    return fastapi_app

def descubrir_endpoint_creacion() -> str:
    return "/productos"

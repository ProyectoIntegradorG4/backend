# tests/conftest.py
import os
os.environ.setdefault("AUTH_BYPASS_FOR_TESTS", "1")
os.environ.setdefault("JWT_SECRET_KEY", "testsecret")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Importa tu app FastAPI real
from app.main import app as fastapi_app
from app.database.connection import EntitiesBase, get_db
from app.database.seed import seed_categories


import sqlite3
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.dialects.postgresql import UUID

@event.listens_for(EntitiesBase.metadata, "before_create")
def before_create(target, connection, **kw):
    connection.dialect.ischema_names["uuid"] = TEXT


TEST_DB_URL = "sqlite:///./test_product.db"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False,
    bind=engine, expire_on_commit=False
)


@pytest.fixture(scope="session")
def db_session():
    EntitiesBase.metadata.drop_all(bind=engine)
    EntitiesBase.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    seed_categories(db)

    yield db
    db.close()

@pytest.fixture(autouse=True)
def override_get_db(db_session, monkeypatch):
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

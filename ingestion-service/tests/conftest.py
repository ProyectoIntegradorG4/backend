# tests/conftest.py
import os

# 1) Define DATABASE_URL ANTES de importar la app
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db
from app.models import Base

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {},
        future=True,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)

@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, autocommit=False, autoflush=False, future=True)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


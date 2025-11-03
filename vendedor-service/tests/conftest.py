# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# IMPORTA SIEMPRE Base y get_db desde TU servicio
from app.database.connection import Base, get_db
from main import app  # donde defines FastAPI() y montas los routers

# Usa SQLite en memoria PERO con StaticPool para que sea una "misma" DB
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # <- clave para que no "desaparezcan" las tablas entre conexiones
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    # Crea todas las tablas al inicio de la sesión de pruebas
    Base.metadata.create_all(bind=engine)
    yield
    # Limpia al terminar todas las pruebas
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Sesión por prueba, hace rollback/close al terminar."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    # Overridea la dependencia antes de crear el TestClient
    app.dependency_overrides[get_db] = _get_test_db
    c = TestClient(app)
    try:
        yield c
    finally:
        # Quita overrides para no contaminar otras suites
        app.dependency_overrides.clear()


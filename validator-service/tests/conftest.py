import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# 1) Fijar DATABASE_URL ANTES de importar la app
os.environ.setdefault("DATABASE_URL", "sqlite:///./validator_test.db")

# 2) Ahora importa app y modelos
from app.database import SessionLocal  # se crea con el env anterior
from app.main import app, get_db
from app.models import Base

@pytest.fixture(scope="session")
def engine():
    # Usa el mismo URL que la app
    url = os.environ["DATABASE_URL"]
    eng = create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
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
    # Override de dependencia para que FastAPI use nuestra sesión transaccional
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

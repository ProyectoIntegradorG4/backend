import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database.connection import get_db
from app.models.cliente import Base
from main import app


# Base de datos de prueba en memoria
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_engine():
    """Crear engine de base de datos de prueba"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Crear sesión de base de datos de prueba"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Cliente de prueba de FastAPI con override de base de datos"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_jwt_token():
    """Token JWT mock para pruebas"""
    from jose import jwt
    import os
    
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production-2024")
    ALGORITHM = "HS256"
    
    payload = {
        "sub": "1",
        "email": "gerente@test.com",
        "roles": ["gerente_cuenta"]
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return f"Bearer {token}"


@pytest.fixture
def mock_jwt_token_wrong_role():
    """Token JWT mock con rol incorrecto"""
    from jose import jwt
    import os
    
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production-2024")
    ALGORITHM = "HS256"
    
    payload = {
        "sub": "2",
        "email": "usuario@test.com",
        "roles": ["usuario_institucional"]
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return f"Bearer {token}"


@pytest.fixture
def sample_cliente_data():
    """Datos de ejemplo para crear un cliente"""
    return {
        "nit": "800123456-1",
        "nombre_comercial": "Hospital Test",
        "razon_social": "Hospital Test SAS",
        "tipo_institucion": "Hospital",
        "pais": "Colombia",
        "ciudad": "Bogotá",
        "direccion": "Calle 10 # 20-30",
        "telefono": "+57 1 234 5678",
        "email": "test@hospital.com",
        "contacto_principal": "Dr. Test",
        "cargo_contacto": "Director",
        "activo": True
    }


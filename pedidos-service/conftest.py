import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
import sys

# Agregar el directorio padre al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Las importaciones deben hacerse después de agregar el path
from main import app
from app.database.connection import Base, get_db
from app.models.pedido import Pedido, DetallePedido, EstadoPedido

# Base de datos en memoria para tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_engine():
    """Crea un engine de SQLite en memoria para pruebas"""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Habilitar soporte para UUID en SQLite
    @event.listens_for(engine, "connect")
    def enable_uuid(connection, _):
        from sqlalchemy import UUID
        def convert_uuid(value):
            if isinstance(value, bytes):
                return str(value)
            return value
        
        connection.create_function("UUID", 0, lambda x=None: x)
    
    # Importar todos los modelos antes de crear las tablas
    import app.models.pedido
    
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Proporciona una sesión de base de datos para pruebas"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Proporciona un cliente de prueba con dependencias inyectadas"""
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
def usuario_institucional():
    """Datos de un usuario institucional para las pruebas"""
    return {
        "usuario_id": 1,
        "rol_usuario": "usuario_institucional",
        "nit": "900123456"
    }

@pytest.fixture
def usuario_vendedor():
    """Datos de un usuario vendedor/admin para las pruebas"""
    return {
        "usuario_id": 2,
        "rol_usuario": "admin",
        "nit": "800654321"
    }

@pytest.fixture
def producto_disponible():
    """Datos de un producto disponible para las pruebas"""
    return {
        "producto_id": "550e8400-e29b-41d4-a716-446655440000",
        "nombre": "Paracetamol 500mg",
        "cantidad_disponible": 100,
        "precio": 5000.00
    }

@pytest.fixture
def producto_sin_stock():
    """Datos de un producto sin stock"""
    return {
        "producto_id": "550e8400-e29b-41d4-a716-446655440001",
        "nombre": "Ibuprofeno 400mg",
        "cantidad_disponible": 0,
        "precio": 6000.00
    }

@pytest.fixture
def producto_stock_bajo():
    """Datos de un producto con stock bajo"""
    return {
        "producto_id": "550e8400-e29b-41d4-a716-446655440002",
        "nombre": "Amoxicilina 500mg",
        "cantidad_disponible": 5,
        "precio": 8000.00
    }


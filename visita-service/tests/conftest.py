import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database.connection import get_db
from app.models.visita import Base
from main import app
from datetime import date, time, datetime, timezone


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
def client(db_session, db_engine):
    """Cliente de prueba de FastAPI con override de base de datos"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from app.routes.visitas import router as visitas_router
    from app.database.connection import get_db
    
    # Crear app de prueba limpia (SIN startup events que hacen sleeps)
    test_app = FastAPI(
        title="Visita Service Test",
        description="App de prueba sin startup events"
    )
    
    # Configurar CORS
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Override de get_db para usar db_session de prueba
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Aplicar override
    test_app.dependency_overrides[get_db] = override_get_db
    
    # Incluir rutas
    test_app.include_router(visitas_router, prefix="/api/v1", tags=["visitas"])
    
    # Health check
    @test_app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "visita-service", "version": "1.0.0"}
    
    with TestClient(test_app) as test_client:
        yield test_client
    
    test_app.dependency_overrides.clear()


@pytest.fixture
def sample_visita_data():
    """Datos de ejemplo para crear una visita"""
    return {
        "gerente_id": 1,
        "cliente_id": 1,
        "fecha_visita": date(2025, 11, 25),
        "hora_inicio_sugerida": time(9, 0),
        "duracion_estimada_minutos": 60,
        "prioridad": "alta",
        "observaciones": "Primera visita del mes"
    }


@pytest.fixture
def sample_visita_dict():
    """Datos de ejemplo como dict para requests HTTP"""
    return {
        "gerente_id": 1,
        "cliente_id": 1,
        "fecha_visita": "2025-11-25",
        "hora_inicio_sugerida": "09:00:00",
        "duracion_estimada_minutos": 60,
        "prioridad": "alta",
        "observaciones": "Primera visita del mes"
    }


@pytest.fixture
def mock_cliente_response():
    """Mock de respuesta de cliente-service"""
    return {
        "cliente_id": 1,
        "nit": "800123456-1",
        "nombre_comercial": "Hospital San José",
        "razon_social": "Hospital San José SAS",
        "tipo_institucion": "Hospital",
        "pais": "Colombia",
        "ciudad": "Bogotá",
        "direccion": "Calle 10 #20-30",
        "latitud": 4.6533,
        "longitud": -74.0836,
        "activo": True
    }


@pytest.fixture
def mock_clientes_list_response():
    """Mock de respuesta de lista de clientes"""
    return {
        "total": 3,
        "page": 1,
        "limit": 50,
        "clientes": [
            {
                "cliente_id": 1,
                "nit": "800111111-1",
                "nombre_comercial": "Hospital San José",
                "latitud": 4.6533,
                "longitud": -74.0836,
                "pais": "Colombia",
                "activo": True
            },
            {
                "cliente_id": 2,
                "nit": "800222222-2",
                "nombre_comercial": "Clínica Los Andes",
                "latitud": 4.6697,
                "longitud": -74.0560,
                "pais": "Colombia",
                "activo": True
            },
            {
                "cliente_id": 3,
                "nit": "800333333-3",
                "nombre_comercial": "IPS Salud Total",
                "latitud": 6.2442,
                "longitud": -75.5812,
                "pais": "Colombia",
                "activo": True
            }
        ]
    }


@pytest.fixture
def mock_cliente_ids_response():
    """Mock de respuesta de cliente_ids de gerente"""
    return {
        "gerente_id": 1,
        "cliente_ids": [1, 2, 3, 4, 5],
        "total": 5
    }


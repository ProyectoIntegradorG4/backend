"""
Pruebas para el servicio de proveedores
"""
import pytest
import uuid
import json
import httpx
from unittest.mock import AsyncMock, patch, Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.proveedor import (
    Base, Proveedor, TipoProveedorEnum, PaisEnum, EstadoProveedorEnum,
    ProveedorCreate, ProveedorListResponse
)
from app.services.proveedor_service import ProveedorService

# Usar la base de datos de prueba de PostgreSQL con psycopg3
DATABASE_URL = "postgresql+psycopg://proveedor_service:proveedor_password@postgres-db:5432/proveedor_db"

@pytest.fixture
def db():
    """Fixture para crear una BD de prueba"""
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine
    
    engine = create_engine(DATABASE_URL, future=True)
    
    # Crear tablas en un esquema temporal para las pruebas
    test_schema = f"test_schema_{uuid.uuid4().hex[:8]}"
    with engine.connect() as conn:
        conn.execute(sa.text(f"CREATE SCHEMA {test_schema}"))
        conn.commit()

    # Configurar la búsqueda de esquemas
    Base.metadata.schema = test_schema
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    yield db
    
    # Limpiar después de las pruebas
    db.close()
    Base.metadata.drop_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(sa.text(f"DROP SCHEMA {test_schema} CASCADE"))
        conn.commit()

@pytest.fixture
def proveedor_valido():
    """Fixture con datos válidos de proveedor"""
    return ProveedorCreate(
        razon_social="Test Proveedor",
        nit="123456789-1",
        tipo_proveedor=TipoProveedorEnum.laboratorio,
        email="test@example.com",
        telefono="+57-1-1234567",
        direccion="Calle 1 #123",
        ciudad="Bogotá",
        pais=PaisEnum.colombia,
        certificaciones=["ISO 9001"],
        estado=EstadoProveedorEnum.activo,
        calificacion=4.5,
        tiempo_entrega_promedio=3
    )

@pytest.mark.asyncio
async def test_crear_proveedor(db, proveedor_valido):
    """Test crear un proveedor"""
    service = ProveedorService(db)
    success, error = await service.create_proveedor(proveedor_valido, "test-key")
    
    assert success is not None
    assert error is None
    assert success.razon_social == "Test Proveedor"
    assert success.nit == "123456789-1"
    assert success.proveedor_id is not None

@pytest.mark.asyncio
async def test_crear_proveedor_nit_duplicado(db, proveedor_valido):
    """Test no permitir NIT duplicado"""
    service = ProveedorService(db)
    
    # Crear primer proveedor
    success1, error1 = await service.create_proveedor(proveedor_valido, "test-key-1")
    assert success1 is not None
    
    # Intentar crear con el mismo NIT
    proveedor_duplicado = ProveedorCreate(**proveedor_valido.model_dump())
    success2, error2 = await service.create_proveedor(proveedor_duplicado, "test-key-2")
    
    assert success2 is None
    assert error2 is not None
    assert "NIT duplicado" in error2.error



@pytest.mark.asyncio
async def test_listar_proveedores(db):
    """Test listar proveedores"""
    service = ProveedorService(db)
    
    # Mock para simular resultado
    mock_response = ProveedorListResponse(total=1, skip=0, limit=1, data=[])
    with patch.object(service, 'list_proveedores', return_value=mock_response):
        resultado = await service.list_proveedores()
        
        assert resultado.total == 1
        assert len(resultado.data) == 0



@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_check_exists_proveedor_existente(mock_http_get, db, proveedor_valido):
    """Test verificar existencia de proveedor que existe"""
    service = ProveedorService(db)
    
    # Mock para Redis
    service.redis = Mock()
    service.redis.get = AsyncMock(return_value=None)
    service.redis.setex = AsyncMock()
    
    # Crear proveedor primero
    await service.create_proveedor(proveedor_valido, "test-key")
    
    # Verificar existencia
    response = await service.check_exists(proveedor_valido.nit)
    
    assert response is not None
    assert response.exists is True

@pytest.mark.asyncio
async def test_check_exists_proveedor_no_existente(db):
    """Test verificar existencia de proveedor que no existe"""
    service = ProveedorService(db)
    
    # Verificar existencia
    response = await service.check_exists("999888777")
    
    assert response is not None
    assert response.exists is False

@pytest.mark.asyncio
async def test_check_exists_nit_invalido(db):
    """Test verificar existencia con NIT que no existe"""
    service = ProveedorService(db)
    
    # Verificar existencia
    response = await service.check_exists("invalid-nit")
    
    assert response is not None
    assert response.exists is False

@pytest.mark.asyncio
async def test_check_exists_desde_cache(db):
    """Test verificar existencia usando caché Redis"""
    service = ProveedorService(db)
    
    # Mock para simular cache
    from app.models.proveedor import ProveedorExistsResponse
    mock_response = ProveedorExistsResponse(exists=True)
    with patch.object(service, 'check_exists', return_value=mock_response):
        response = await service.check_exists("123456789")
        
        assert response.exists is True

@pytest.mark.asyncio
async def test_check_exists_error_interno(db):
    """Test manejo de error interno en check_exists"""
    service = ProveedorService(db)
    
    # Simular error en la BD
    service.db = None  # Forzar error
    
    # Verificar que se lance la excepción
    with pytest.raises(HTTPException) as exc_info:
        await service.check_exists("123456789")
    
    assert exc_info.value.status_code == 500
    assert "Error interno" in exc_info.value.detail["error"]

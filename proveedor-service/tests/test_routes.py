"""
Tests para las rutas de la API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.models.proveedor import TipoProveedorEnum, PaisEnum, EstadoProveedorEnum

client = TestClient(app)

def test_health_check():
    """Test del endpoint health check"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
@patch('app.routes.proveedores.get_db')
@patch('app.routes.proveedores.ProveedorService')
async def test_create_proveedor_success(mock_service_class, mock_db):
    """Test crear proveedor exitosamente"""
    # Configurar el mock del servicio
    mock_service = mock_service_class.return_value
    
    from app.models.proveedor import ProveedorResponse
    from datetime import datetime, UTC
    import uuid
    
    proveedor_id = uuid.uuid4()
    mock_response = ProveedorResponse(
        proveedor_id=proveedor_id,
        razon_social="Test Proveedor",
        nit="123456789",
        tipo_proveedor=TipoProveedorEnum.laboratorio,
        email="test@example.com",
        telefono="+57-1-1234567",
        direccion="Calle 1 #123",
        ciudad="Bogotá",
        pais=PaisEnum.colombia,
        certificaciones=["ISO 9001"],
        estado=EstadoProveedorEnum.activo,
        calificacion=4.5,
        tiempo_entrega_promedio=3,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version=0
    )
    
    mock_service.create_proveedor = AsyncMock(return_value=(mock_response, None))
    
    data = {
        "razon_social": "Test Proveedor",
        "nit": "123456789",
        "tipo_proveedor": TipoProveedorEnum.laboratorio.value,
        "email": "test@example.com",
        "telefono": "+57-1-1234567",
        "direccion": "Calle 1 #123",
        "ciudad": "Bogotá",
        "pais": PaisEnum.colombia.value,
        "certificaciones": ["ISO 9001"],
        "estado": EstadoProveedorEnum.activo.value,
        "calificacion": 4.5,
        "tiempo_entrega_promedio": 3
    }
    
    response = client.post("/api/proveedores", json=data, headers={"X-Idempotency-Key": "test-key"})
    
    assert response.status_code == 201
    response_data = response.json()
    assert str(proveedor_id) == response_data["proveedor_id"]
    assert response_data["nit"] == "123456789"

@pytest.mark.asyncio
@patch('app.routes.proveedores.get_db')
@patch('app.routes.proveedores.ProveedorService')
async def test_create_proveedor_error(mock_service_class, mock_db):
    """Test crear proveedor con error"""
    mock_service = mock_service_class.return_value
    
    from app.models.proveedor import ErrorDetail
    error_detail = ErrorDetail(error="NIT duplicado", detalles={"nit": "ya existe"})
    mock_service.create_proveedor = AsyncMock(return_value=(None, error_detail))
    
    data = {
        "razon_social": "Test Proveedor",
        "nit": "123456789",
        "tipo_proveedor": "laboratorio",
        "email": "test@example.com",
        "telefono": "+57-1-1234567",
        "direccion": "Calle 1 #123",
        "ciudad": "Bogotá",
        "pais": "colombia",
        "certificaciones": ["ISO 9001"],
        "estado": "activo",
        "calificacion": 4.5,
        "tiempo_entrega_promedio": 3
    }
    
    response = client.post("/api/proveedores", json=data, headers={"X-Idempotency-Key": "test-key"})
    
    assert response.status_code == 409
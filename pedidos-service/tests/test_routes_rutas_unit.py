"""
Tests unitarios para rutas API (app/routes/rutas.py)
Cobertura de endpoints y validación RBAC
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from app.schemas.ruta import (
    GenerarRutasRequest, RecalcularRutaRequest,
    VehiculoRequest, CrearVehiculoRequest, UbicacionRequest
)


@pytest.fixture
def client():
    """Cliente HTTP para testing"""
    return TestClient(app)


@pytest.fixture
def valid_headers():
    """Headers válidos con rol admin"""
    return {
        "rol-usuario": "admin",
        "usuario-id": "1",
        "nit-usuario": "1234567890"
    }


@pytest.fixture
def gerente_headers():
    """Headers con rol gerente_cuenta"""
    return {
        "rol-usuario": "gerente_cuenta",
        "usuario-id": "2",
        "nit-usuario": "0987654321"
    }


@pytest.fixture
def invalid_role_headers():
    """Headers con rol sin permisos"""
    return {
        "rol-usuario": "vendedor",
        "usuario-id": "3",
        "nit-usuario": "1111111111"
    }


# ==================== Tests: Validación RBAC ====================

class TestRequireSupervisorLogistica:
    """Tests para la validación de rol en require_supervisor_logistica"""
    
    def test_health_check_sin_autenticacion(self, client):
        """Test que health check NO requiere autenticación"""
        response = client.get("/api/v1/logistica/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "rutas-logistica"
    
    def test_endpoint_protegido_sin_headers(self, client):
        """Test que endpoint protegido rechaza sin headers requeridos"""
        response = client.get("/api/v1/logistica/vehiculos")
        
        # Debe rechazar sin los headers requeridos
        assert response.status_code in [400, 422]  # Validation error o missing header
    
    def test_endpoint_protegido_rol_invalido(self, client):
        """Test que endpoint rechaza rol no autorizado"""
        headers = {
            "rol-usuario": "vendedor",
            "usuario-id": "1",
            "nit-usuario": "1234567890"
        }
        response = client.get("/api/v1/logistica/vehiculos", headers=headers)
        
        # Debe rechazar con 403 Forbidden
        assert response.status_code == 403
        assert "Acceso denegado" in response.json()["detail"]
    
    def test_endpoint_protegido_rol_admin(self, client, valid_headers):
        """Test que endpoint acepta rol admin"""
        # Este test verifica que el rol es validado correctamente
        # El endpoint puede fallar por otras razones (BD, etc) pero el RBAC pasará
        response = client.get("/api/v1/logistica/vehiculos", headers=valid_headers)
        
        # Puede ser 500 por BD, pero NO debe ser 403
        assert response.status_code != 403
    
    def test_endpoint_protegido_rol_gerente_cuenta(self, client, gerente_headers):
        """Test que endpoint acepta rol gerente_cuenta"""
        response = client.get("/api/v1/logistica/vehiculos", headers=gerente_headers)
        
        # Puede ser 500 por BD, pero NO debe ser 403
        assert response.status_code != 403


# ==================== Tests: Endpoint /rutas/generar ====================

class TestGenerarRutasEndpoint:
    """Tests para endpoint POST /rutas/generar"""
    
    def test_generar_rutas_sin_autenticacion(self, client):
        """Test que rechaza sin headers de autenticación"""
        request_data = {
            "objetivo": "min_distancia",
            "vehiculos": [],
            "pedidos": []
        }
        response = client.post("/api/v1/logistica/rutas/generar", json=request_data)
        
        assert response.status_code in [400, 422]
    
    def test_generar_rutas_rol_invalido(self, client, invalid_role_headers):
        """Test que rechaza rol sin permisos"""
        request_data = {
            "objetivo": "min_distancia",
            "vehiculos": [],
            "pedidos": []
        }
        response = client.post(
            "/api/v1/logistica/rutas/generar",
            json=request_data,
            headers=invalid_role_headers
        )
        
        assert response.status_code == 403
    
    @patch('app.routes.rutas.RutasService.generar_rutas')
    def test_generar_rutas_exitoso(self, mock_generar, client, valid_headers):
        """Test generación exitosa de rutas"""
        from app.schemas.ruta import GenerarRutasResponse
        
        mock_response = GenerarRutasResponse(
            rutas=[],
            tiempo_calculo_ms=150,
            warnings=[]
        )
        mock_generar.return_value = mock_response
        
        request_data = {
            "objetivo": "min_distancia",
            "vehiculos": [
                {
                    "id": "V1",
                    "capacidad_volumen": 100.0,
                    "capacidad_peso": 1000.0,
                    "depot": {"lat": 4.6097, "lon": -74.0817}
                }
            ],
            "pedidos": [
                {
                    "id": "P1",
                    "lat": 4.7456,
                    "lon": -74.3000,
                    "ventana_inicio": "08:00",
                    "ventana_fin": "12:00",
                    "volumen": 1.0,
                    "peso": 5.0
                }
            ]
        }
        
        with patch('app.database.connection.get_db'):
            response = client.post(
                "/api/v1/logistica/rutas/generar",
                json=request_data,
                headers=valid_headers
            )
        
        # Debe retornar 200 OK cuando el servicio funciona
        assert response.status_code == 200
        assert response.json()["tiempo_calculo_ms"] == 150
    
    
    def test_generar_rutas_query_params_validos(self, client, valid_headers):
        """Test que endpoint recibe parámetros válidos - Cobertura del try block"""
        # Este test verifica que el endpoint puede ser llamado
        # y que entra al bloque try/except
        request_data = {
            "objetivo": "min_distancia",
            "vehiculos": [],
            "pedidos": []
        }
        
        with patch('app.database.connection.get_db'):
            with patch('app.routes.rutas.RutasService.generar_rutas') as mock_gen:
                from app.schemas.ruta import GenerarRutasResponse
                mock_gen.return_value = GenerarRutasResponse(rutas=[], tiempo_calculo_ms=10, warnings=[])
                
                response = client.post(
                    "/api/v1/logistica/rutas/generar",
                    json=request_data,
                    headers=valid_headers
                )
        
        # Si alcanza aquí, el try block fue ejecutado
        assert response.status_code in [200, 422]


# ==================== Tests: Endpoint /rutas/recalcular ====================

class TestRecalcularRutaEndpoint:
    """Tests para endpoint POST /rutas/recalcular"""
    
    def test_recalcular_ruta_sin_autenticacion(self, client):
        """Test que rechaza sin headers"""
        request_data = {
            "ruta_id": "ruta-123",
            "nueva_secuencia": ["P1", "P2"]
        }
        response = client.post("/api/v1/logistica/rutas/recalcular", json=request_data)
        
        assert response.status_code in [400, 422]
    
    def test_recalcular_ruta_rol_invalido(self, client, invalid_role_headers):
        """Test que rechaza rol sin permisos"""
        request_data = {
            "ruta_id": "ruta-123",
            "nueva_secuencia": ["P1", "P2"]
        }
        response = client.post(
            "/api/v1/logistica/rutas/recalcular",
            json=request_data,
            headers=invalid_role_headers
        )
        
        assert response.status_code == 403
    
    
    def test_recalcular_ruta_parametros_validos(self, client, valid_headers):
        """Test que endpoint recibe parámetros válidos"""
        # Este test verifica que el endpoint puede ser llamado
        # y que entra al bloque try/except
        request_data = {
            "ruta_id": "ruta-123",
            "nueva_secuencia": ["P1"]
        }
        
        with patch('app.database.connection.get_db'):
            with patch('app.routes.rutas.RutasService.recalcular_ruta') as mock_rec:
                mock_rec.side_effect = ValueError("Pedidos no coinciden")
                response = client.post(
                    "/api/v1/logistica/rutas/recalcular",
                    json=request_data,
                    headers=valid_headers
                )
        
        # El ValueError debe retornar 400
        assert response.status_code == 400
    
    @patch('app.routes.rutas.RutasService.recalcular_ruta')
    def test_recalcular_ruta_validation_error(self, mock_recalcular, client, valid_headers):
        """Test que maneja ValueError del servicio"""
        mock_recalcular.side_effect = ValueError("Secuencia inválida")
        
        request_data = {
            "ruta_id": "ruta-123",
            "nueva_secuencia": ["P3"]
        }
        
        with patch('app.database.connection.get_db'):
            response = client.post(
                "/api/v1/logistica/rutas/recalcular",
                json=request_data,
                headers=valid_headers
            )
        
        # Debe retornar 400
        assert response.status_code == 400
        assert "Secuencia inválida" in response.json()["detail"]
    
    @patch('app.routes.rutas.RutasService.recalcular_ruta')
    def test_recalcular_ruta_error_interno(self, mock_recalcular, client, valid_headers):
        """Test que maneja errores inesperados"""
        mock_recalcular.side_effect = Exception("Conexión a BD perdida")
        
        request_data = {
            "ruta_id": "ruta-123",
            "nueva_secuencia": ["P1"]
        }
        
        with patch('app.database.connection.get_db'):
            response = client.post(
                "/api/v1/logistica/rutas/recalcular",
                json=request_data,
                headers=valid_headers
            )
        
        # Debe retornar 500
        assert response.status_code == 500


# ==================== Tests: Endpoint POST /vehiculos ====================

class TestCrearVehiculoEndpoint:
    """Tests para endpoint POST /vehiculos"""
    
    def test_crear_vehiculo_sin_autenticacion(self, client):
        """Test que rechaza sin headers"""
        request_data = {
            "vehiculo_id": "V1",
            "nombre": "Camión",
            "capacidad_volumen": 100.0,
            "capacidad_peso": 1000.0,
            "depot_latitud": 4.6097,
            "depot_longitud": -74.0817
        }
        response = client.post("/api/v1/logistica/vehiculos", json=request_data)
        
        assert response.status_code in [400, 422]
    
    def test_crear_vehiculo_rol_invalido(self, client, invalid_role_headers):
        """Test que rechaza rol sin permisos"""
        request_data = {
            "vehiculo_id": "V1",
            "nombre": "Camión",
            "capacidad_volumen": 100.0,
            "capacidad_peso": 1000.0,
            "depot_latitud": 4.6097,
            "depot_longitud": -74.0817
        }
        response = client.post(
            "/api/v1/logistica/vehiculos",
            json=request_data,
            headers=invalid_role_headers
        )
        
        assert response.status_code == 403
    
    @patch('app.routes.rutas.RutasService.crear_vehiculo')
    def test_crear_vehiculo_exitoso(self, mock_crear, client, valid_headers):
        """Test creación exitosa de vehículo"""
        mock_vehiculo = MagicMock()
        mock_vehiculo.vehiculo_id = "V1"
        mock_vehiculo.nombre = "Camión Prueba"
        mock_vehiculo.capacidad_volumen = 100.0
        mock_vehiculo.capacidad_peso = 1000.0
        mock_vehiculo.cadena_frio = False
        mock_vehiculo.depot_latitud = 4.6097
        mock_vehiculo.depot_longitud = -74.0817
        mock_vehiculo.depot_direccion = "Calle 1"
        mock_vehiculo.duracion_maxima_minutos = 480
        mock_vehiculo.activo = True
        
        mock_crear.return_value = mock_vehiculo
        
        request_data = {
            "vehiculo_id": "V1",
            "nombre": "Camión Prueba",
            "capacidad_volumen": 100.0,
            "capacidad_peso": 1000.0,
            "depot_latitud": 4.6097,
            "depot_longitud": -74.0817
        }
        
        with patch('app.database.connection.get_db'):
            response = client.post(
                "/api/v1/logistica/vehiculos",
                json=request_data,
                headers=valid_headers
            )
        
        # Debe retornar 201 Created
        assert response.status_code == 201
        assert response.json()["vehiculo_id"] == "V1"
    
    @patch('app.routes.rutas.RutasService.crear_vehiculo')
    def test_crear_vehiculo_error_interno(self, mock_crear, client, valid_headers):
        """Test que maneja errores del servicio"""
        mock_crear.side_effect = Exception("BD no disponible")
        
        request_data = {
            "vehiculo_id": "V1",
            "nombre": "Camión",
            "capacidad_volumen": 100.0,
            "capacidad_peso": 1000.0,
            "depot_latitud": 4.6097,
            "depot_longitud": -74.0817
        }
        
        with patch('app.database.connection.get_db'):
            response = client.post(
                "/api/v1/logistica/vehiculos",
                json=request_data,
                headers=valid_headers
            )
        
        # Debe retornar 500
        assert response.status_code == 500


# ==================== Tests: Endpoint GET /vehiculos ====================

class TestListarVehiculosEndpoint:
    """Tests para endpoint GET /vehiculos"""
    
    def test_listar_vehiculos_sin_autenticacion(self, client):
        """Test que rechaza sin headers"""
        response = client.get("/api/v1/logistica/vehiculos")
        
        assert response.status_code in [400, 422]
    
    def test_listar_vehiculos_rol_invalido(self, client, invalid_role_headers):
        """Test que rechaza rol sin permisos"""
        response = client.get(
            "/api/v1/logistica/vehiculos",
            headers=invalid_role_headers
        )
        
        assert response.status_code == 403
    
    @patch('app.routes.rutas.RutasService.listar_vehiculos')
    def test_listar_vehiculos_exitoso_vacio(self, mock_listar, client, valid_headers):
        """Test listado vacío de vehículos"""
        mock_listar.return_value = []
        
        with patch('app.database.connection.get_db'):
            response = client.get(
                "/api/v1/logistica/vehiculos",
                headers=valid_headers
            )
        
        # Debe retornar 200 OK
        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["vehiculos"] == []
    
    @patch('app.routes.rutas.RutasService.listar_vehiculos')
    def test_listar_vehiculos_exitoso_con_datos(self, mock_listar, client, valid_headers):
        """Test listado con vehículos"""
        mock_vehiculo = MagicMock()
        mock_vehiculo.vehiculo_id = "V1"
        mock_vehiculo.nombre = "Camión"
        mock_vehiculo.capacidad_volumen = 100.0
        mock_vehiculo.capacidad_peso = 1000.0
        mock_vehiculo.cadena_frio = False
        mock_vehiculo.depot_latitud = 4.6097
        mock_vehiculo.depot_longitud = -74.0817
        mock_vehiculo.depot_direccion = "Calle 1"
        mock_vehiculo.duracion_maxima_minutos = 480
        mock_vehiculo.activo = True
        
        mock_listar.return_value = [mock_vehiculo]
        
        with patch('app.database.connection.get_db'):
            response = client.get(
                "/api/v1/logistica/vehiculos",
                headers=valid_headers
            )
        
        # Debe retornar 200 OK
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert len(response.json()["vehiculos"]) == 1
    
    @patch('app.routes.rutas.RutasService.listar_vehiculos')
    def test_listar_vehiculos_con_filtro_activos(self, mock_listar, client, valid_headers):
        """Test listado con filtro solo_activos=True"""
        mock_listar.return_value = []
        
        with patch('app.database.connection.get_db'):
            response = client.get(
                "/api/v1/logistica/vehiculos?solo_activos=true",
                headers=valid_headers
            )
        
        # Debe retornar 200 OK
        assert response.status_code == 200
        # Verifica que el parámetro fue pasado
        mock_listar.assert_called_once()
    
    @patch('app.routes.rutas.RutasService.listar_vehiculos')
    def test_listar_vehiculos_con_filtro_todos(self, mock_listar, client, valid_headers):
        """Test listado con filtro solo_activos=False"""
        mock_listar.return_value = []
        
        with patch('app.database.connection.get_db'):
            response = client.get(
                "/api/v1/logistica/vehiculos?solo_activos=false",
                headers=valid_headers
            )
        
        # Debe retornar 200 OK
        assert response.status_code == 200
    
    @patch('app.routes.rutas.RutasService.listar_vehiculos')
    def test_listar_vehiculos_error_interno(self, mock_listar, client, valid_headers):
        """Test que maneja errores del servicio"""
        mock_listar.side_effect = Exception("Error en BD")
        
        with patch('app.database.connection.get_db'):
            response = client.get(
                "/api/v1/logistica/vehiculos",
                headers=valid_headers
            )
        
        # Debe retornar 500
        assert response.status_code == 500


# ==================== Tests: Endpoint GET /health ====================

class TestHealthCheckEndpoint:
    """Tests para endpoint GET /health"""
    
    def test_health_check_sin_autenticacion(self, client):
        """Test que health check funciona sin autenticación"""
        response = client.get("/api/v1/logistica/health")
        
        assert response.status_code == 200
    
    def test_health_check_estructura_respuesta(self, client):
        """Test que health check retorna estructura correcta"""
        response = client.get("/api/v1/logistica/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "rutas-logistica"
        assert "version" in data
    
    def test_health_check_multiple_requests(self, client):
        """Test que health check responde consistentemente"""
        for _ in range(3):
            response = client.get("/api/v1/logistica/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

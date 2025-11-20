"""
Tests de integración para los endpoints de Planes de Venta (HU-WEB-008 y HU-WEB-009)
"""
import pytest
from datetime import date
from uuid import uuid4
from unittest.mock import Mock, patch
from starlette.testclient import TestClient
from main import app
from app.service.rbac import require_role_admin_ventas


@pytest.fixture
def client_with_rbac_bypass():
    """Cliente de test con RBAC bypass"""
    # Mock RBAC para siempre retornar usuario válido
    def mock_rbac():
        return {
            "user_id": 1,
            "roles": ["admin_ventas"],
            "username": "test_user"
        }
    
    app.dependency_overrides[require_role_admin_ventas] = mock_rbac
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_rbac():
    """Cliente de test sin RBAC bypass"""
    app.dependency_overrides.clear()
    return TestClient(app)


class TestListarTerritoriosEndpoint:
    """Tests para GET /api/planes-venta/territorios/catalogo"""
    
    @patch('app.routes.plan_venta.PlanVentaService.listar_territorios')
    def test_listar_territorios_ok(self, mock_service, client_with_rbac_bypass):
        """Debe retornar lista de territorios (requiere RBAC)"""
        from app.models.territorio import Territorio
        
        terr1 = Territorio(
            territorio_id="TERR-001",
            nombre="Zona Norte",
            codigo="ZN-001",
            pais="Colombia",
            activo=True
        )
        
        mock_service.return_value = [terr1]
        
        response = client_with_rbac_bypass.get("/api/planes-venta/territorios/catalogo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["territorio_id"] == "TERR-001"
    
    @patch('app.routes.plan_venta.PlanVentaService.listar_territorios')
    def test_listar_territorios_vacio(self, mock_service, client_with_rbac_bypass):
        """Debe retornar lista vacía si no hay territorios"""
        mock_service.return_value = []
        
        response = client_with_rbac_bypass.get("/api/planes-venta/territorios/catalogo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestCrearPlanVentaEndpoint:
    """Tests para POST /api/planes-venta (HU-WEB-008)"""
    
    def _get_valid_payload(self):
        """Payload válido para crear plan"""
        return {
            "nombre": "Plan Q1 2025",
            "periodo": {
                "desde": "2025-01-01",
                "hasta": "2025-03-31"
            },
            "territorios": ["TERR-001"],
            "metas": [
                {
                    "productoId": "550e8400-e29b-41d4-a716-446655440000",
                    "territorioId": "TERR-001",
                    "vendedorId": 1,
                    "objetivo_cantidad": 100,
                    "objetivo_valor": 1000000
                }
            ]
        }
    
    @patch('app.routes.plan_venta.PlanVentaService.crear_plan_venta')
    def test_crear_plan_ok(self, mock_service, client_with_rbac_bypass):
        """Debe crear plan correctamente con rol admin_ventas"""
        from app.models.plan_venta import PlanVenta
        
        plan_id = uuid4()
        plan_mock = PlanVenta(
            plan_id=plan_id,
            nombre="Plan Q1 2025",
            periodo_desde=date(2025, 1, 1),
            periodo_hasta=date(2025, 3, 31),
            estado="borrador",
            created_by=1
        )
        
        mock_service.return_value = plan_mock
        
        response = client_with_rbac_bypass.post(
            "/api/planes-venta",
            json=self._get_valid_payload()
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "planId" in data
        assert "estado" in data
        assert data["estado"] == "borrador"
        mock_service.assert_called_once()
    
    def test_crear_plan_validacion_nombre_requerido(self, client_with_rbac_bypass):
        """Debe rechazar payload sin nombre"""
        payload = self._get_valid_payload()
        del payload["nombre"]
        
        response = client_with_rbac_bypass.post("/api/planes-venta", json=payload)
        
        assert response.status_code == 422
    
    def test_crear_plan_validacion_periodo_requerido(self, client_with_rbac_bypass):
        """Debe rechazar payload sin periodo"""
        payload = self._get_valid_payload()
        del payload["periodo"]
        
        response = client_with_rbac_bypass.post("/api/planes-venta", json=payload)
        
        assert response.status_code == 422
    
    def test_crear_plan_validacion_territorios_requeridos(self, client_with_rbac_bypass):
        """Debe rechazar payload sin territorios"""
        payload = self._get_valid_payload()
        payload["territorios"] = []
        
        response = client_with_rbac_bypass.post("/api/planes-venta", json=payload)
        
        assert response.status_code == 422
    
    @patch('app.routes.plan_venta.PlanVentaService.crear_plan_venta')
    def test_crear_plan_nombre_duplicado_409(self, mock_service, client_with_rbac_bypass):
        """Debe retornar 409 si nombre ya existe"""
        from fastapi import HTTPException
        
        mock_service.side_effect = HTTPException(
            status_code=409,
            detail="El nombre del plan ya existe"
        )
        
        response = client_with_rbac_bypass.post(
            "/api/planes-venta",
            json=self._get_valid_payload()
        )
        
        assert response.status_code == 409
    
    @patch('app.routes.plan_venta.PlanVentaService.crear_plan_venta')
    def test_crear_plan_validacion_negocio_400(self, mock_service, client_with_rbac_bypass):
        """Debe retornar 400 si hay errores de validación de negocio"""
        from fastapi import HTTPException
        
        mock_service.side_effect = HTTPException(
            status_code=400,
            detail="Territorios no válidos"
        )
        
        response = client_with_rbac_bypass.post(
            "/api/planes-venta",
            json=self._get_valid_payload()
        )
        
        assert response.status_code == 400


class TestListarPlanesVentaEndpoint:
    """Tests para GET /api/planes-venta (HU-WEB-009)"""
    
    @patch('app.routes.plan_venta.PlanVentaService.listar_planes_venta')
    def test_listar_planes_sin_filtros(self, mock_service, client_with_rbac_bypass):
        """Debe listar planes sin filtros"""
        from app.models.plan_venta import PlanVenta
        
        plan1 = PlanVenta(
            plan_id=uuid4(),
            nombre="Plan Q1",
            periodo_desde=date(2025, 1, 1),
            periodo_hasta=date(2025, 3, 31),
            estado="activo",
            created_by=1
        )
        plan1.territorios = []
        plan1.metas = []
        
        mock_service.return_value = ([plan1], 1)
        
        response = client_with_rbac_bypass.get("/api/planes-venta")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
    
    @patch('app.routes.plan_venta.PlanVentaService.listar_planes_venta')
    def test_listar_planes_con_busqueda(self, mock_service, client_with_rbac_bypass):
        """Debe buscar por nombre (q)"""
        mock_service.return_value = ([], 0)
        
        response = client_with_rbac_bypass.get("/api/planes-venta?q=Trimestre")
        
        assert response.status_code == 200
        mock_service.assert_called_once()
        args, kwargs = mock_service.call_args
        assert kwargs.get('q') == 'Trimestre' or args[1] == 'Trimestre'
    
    @patch('app.routes.plan_venta.PlanVentaService.listar_planes_venta')
    def test_listar_planes_filtro_periodo(self, mock_service, client_with_rbac_bypass):
        """Debe filtrar por periodo"""
        mock_service.return_value = ([], 0)
        
        response = client_with_rbac_bypass.get(
            "/api/planes-venta?periodo_from=2025-01-01&periodo_to=2025-12-31"
        )
        
        assert response.status_code == 200
        mock_service.assert_called_once()
    
    @patch('app.routes.plan_venta.PlanVentaService.listar_planes_venta')
    def test_listar_planes_filtro_estado(self, mock_service, client_with_rbac_bypass):
        """Debe filtrar por estado"""
        mock_service.return_value = ([], 0)
        
        response = client_with_rbac_bypass.get("/api/planes-venta?estado=borrador")
        
        assert response.status_code == 200
        mock_service.assert_called_once()
    
    @patch('app.routes.plan_venta.PlanVentaService.listar_planes_venta')
    def test_listar_planes_filtro_territorio(self, mock_service, client_with_rbac_bypass):
        """Debe filtrar por territorio"""
        mock_service.return_value = ([], 0)
        
        response = client_with_rbac_bypass.get("/api/planes-venta?territorio_id=TERR-001")
        
        assert response.status_code == 200
        mock_service.assert_called_once()
    
    @patch('app.routes.plan_venta.PlanVentaService.listar_planes_venta')
    def test_listar_planes_filtro_producto(self, mock_service, client_with_rbac_bypass):
        """Debe filtrar por producto"""
        mock_service.return_value = ([], 0)
        
        producto_id = str(uuid4())
        response = client_with_rbac_bypass.get(f"/api/planes-venta?producto_id={producto_id}")
        
        assert response.status_code == 200
        mock_service.assert_called_once()
    
    @patch('app.routes.plan_venta.PlanVentaService.listar_planes_venta')
    def test_listar_planes_ordenamiento(self, mock_service, client_with_rbac_bypass):
        """Debe aplicar ordenamiento"""
        mock_service.return_value = ([], 0)
        
        response = client_with_rbac_bypass.get("/api/planes-venta?sort=nombre&order=asc")
        
        assert response.status_code == 200
        mock_service.assert_called_once()
    
    @patch('app.routes.plan_venta.PlanVentaService.listar_planes_venta')
    def test_listar_planes_paginacion(self, mock_service, client_with_rbac_bypass):
        """Debe aplicar paginación"""
        mock_service.return_value = ([], 100)
        
        response = client_with_rbac_bypass.get("/api/planes-venta?page=3&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 3
        assert data["page_size"] == 10
    
    @patch('app.routes.plan_venta.PlanVentaService.listar_planes_venta')
    def test_listar_planes_page_size_maximo_50(self, mock_service, client_with_rbac_bypass):
        """Debe limitar page_size a 50"""
        mock_service.return_value = ([], 200)
        
        response = client_with_rbac_bypass.get("/api/planes-venta?page_size=50")
        
        assert response.status_code == 200
        # El endpoint debería aceptar 50 o menos
        mock_service.assert_called_once()


class TestObtenerPlanPorIdEndpoint:
    """Tests para GET /api/planes-venta/{plan_id}"""
    
    @patch('app.routes.plan_venta.PlanVentaService.obtener_plan_por_id')
    def test_obtener_plan_ok(self, mock_service, client_with_rbac_bypass):
        """Debe retornar plan por ID"""
        from app.models.plan_venta import PlanVenta
        
        plan_id = uuid4()
        plan_mock = PlanVenta(
            plan_id=plan_id,
            nombre="Plan Q1 2025",
            periodo_desde=date(2025, 1, 1),
            periodo_hasta=date(2025, 3, 31),
            estado="activo",
            created_by=1
        )
        plan_mock.territorios = []
        plan_mock.metas = []
        
        mock_service.return_value = plan_mock
        
        response = client_with_rbac_bypass.get(f"/api/planes-venta/{plan_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "nombre" in data
        assert data["nombre"] == "Plan Q1 2025"
        assert "estado" in data
        mock_service.assert_called_once()
    
    @patch('app.routes.plan_venta.PlanVentaService.obtener_plan_por_id')
    def test_obtener_plan_no_encontrado(self, mock_service, client_with_rbac_bypass):
        """Debe retornar 404 si plan no existe"""
        mock_service.return_value = None
        
        plan_id = uuid4()
        response = client_with_rbac_bypass.get(f"/api/planes-venta/{plan_id}")
        
        assert response.status_code == 404
    
    def test_obtener_plan_uuid_invalido(self, client_with_rbac_bypass):
        """Debe retornar 422 si UUID es inválido"""
        response = client_with_rbac_bypass.get("/api/planes-venta/not-a-uuid")
        
        assert response.status_code == 422

"""
Tests para las rutas de reportes de vendedores (HU-WEB-010)
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

from main import app
from app.schemas.reporte import (
    KPIVendedor, ReporteRegion, DashboardReportes,
    VendedorInfo, TerritorioInfo, PeriodoReporte,
    TendenciaItem, DashboardKPI, GraficoLinea
)


client = TestClient(app)


@pytest.fixture
def mock_kpi_vendedor():
    """KPI de vendedor de ejemplo"""
    return KPIVendedor(
        periodo=PeriodoReporte(
            desde=date(2026, 1, 1),
            hasta=date(2026, 1, 31)
        ),
        vendedor=VendedorInfo(id="1", nombre="Juan Pérez"),
        ventas_valor=2300000.0,
        ventas_unidades=15,
        pedidos=2,
        cumplimiento_unidades=0.75,
        cumplimiento_valor=0.7667,
        meta_unidades=20,
        meta_valor=3000000.0,
        tendencia=[
            TendenciaItem(
                fecha=date(2026, 1, 31),
                valor=2300000.0,
                unidades=15,
                pedidos=2
            )
        ]
    )


@pytest.fixture
def mock_reporte_region():
    """Reporte de región de ejemplo"""
    from app.schemas.reporte import ResumenRegion, VendedorRanking
    
    return ReporteRegion(
        periodo=PeriodoReporte(desde=date(2026, 1, 1), hasta=date(2026, 1, 31)),
        territorio=TerritorioInfo(id="ZONA_NORTE", nombre="Zona Norte"),
        resumen=ResumenRegion(
            ventas_valor=4100000.0,
            ventas_unidades=27,
            pedidos=3,
            cumplimiento_unidades=0.77,
            cumplimiento_valor=0.82,
            meta_unidades=35,
            meta_valor=5000000.0
        ),
        ranking=[
            VendedorRanking(
                posicion=1,
                vendedorId="1",
                nombre="Juan Pérez",
                ventas_valor=2300000.0,
                ventas_unidades=15,
                pedidos=2,
                cumplimiento_unidades=0.75
            ),
            VendedorRanking(
                posicion=2,
                vendedorId="2",
                nombre="María López",
                ventas_valor=1800000.0,
                ventas_unidades=12,
                pedidos=1,
                cumplimiento_unidades=0.80
            )
        ],
        tendencia=[]
    )


@pytest.fixture
def mock_dashboard():
    """Dashboard de ejemplo"""
    from app.schemas.reporte import GraficoBarras, GraficoDona, VendedorRanking
    
    return DashboardReportes(
        periodo=PeriodoReporte(desde=date(2026, 1, 1), hasta=date(2026, 1, 31)),
        kpis=[
            DashboardKPI(
                label="Ventas Totales",
                valor=4100000.0,
                unidad="COP",
                tendencia="up"
            ),
            DashboardKPI(
                label="Unidades Vendidas",
                valor=27.0,
                unidad="unidades",
                tendencia="up"
            )
        ],
        grafico_tendencia=GraficoLinea(
            labels=["Ene 2026"],
            datasets=[{
                "label": "Ventas (COP)",
                "data": [4100000.0]
            }]
        ),
        grafico_vendedores=GraficoBarras(
            labels=["Juan Pérez", "María López"],
            datasets=[{
                "label": "Ventas (COP)",
                "data": [2300000.0, 1800000.0]
            }]
        ),
        grafico_cumplimiento=GraficoDona(
            labels=["Juan Pérez", "María López"],
            datasets=[{
                "label": "Cumplimiento (%)",
                "data": [75.0, 80.0]
            }]
        ),
        top_vendedores=[
            VendedorRanking(
                posicion=1,
                vendedorId="1",
                nombre="Juan Pérez",
                ventas_valor=2300000.0,
                ventas_unidades=15,
                pedidos=2
            )
        ],
        alertas=[]
    )


class TestReportesRoutes:
    """Tests para los endpoints de reportes"""
    
    def test_health_check(self):
        """Test del endpoint de salud"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @patch('app.routes.reportes.ReportesService.generar_kpi_vendedor', new_callable=AsyncMock)
    def test_obtener_kpi_vendedor_success(self, mock_generar_kpi, mock_kpi_vendedor):
        """Test obtener KPI de vendedor exitoso"""
        mock_generar_kpi.return_value = mock_kpi_vendedor
        
        response = client.get(
            "/api/v1/reportes/vendedores/kpi",
            params={
                "vendedor_id": 1,
                "desde": "2026-01-01",
                "hasta": "2026-01-31"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["vendedor"]["id"] == "1"
        assert data["vendedor"]["nombre"] == "Juan Pérez"
        assert data["ventas_valor"] == 2300000.0
        assert data["ventas_unidades"] == 15
        assert data["cumplimiento_unidades"] == 0.75
    
    def test_obtener_kpi_vendedor_invalid_vendedor_id(self):
        """Test con vendedor_id inválido"""
        response = client.get(
            "/api/v1/reportes/vendedores/kpi",
            params={
                "vendedor_id": 0,  # Debe ser > 0
                "desde": "2026-01-01",
                "hasta": "2026-01-31"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_obtener_kpi_vendedor_invalid_periodo(self):
        """Test con periodo inválido (desde > hasta)"""
        response = client.get(
            "/api/v1/reportes/vendedores/kpi",
            params={
                "vendedor_id": 1,
                "desde": "2026-02-01",
                "hasta": "2026-01-01"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fecha 'desde' debe ser anterior" in response.json()["detail"]
    
    def test_obtener_kpi_vendedor_periodo_muy_largo(self):
        """Test con periodo mayor a 365 días"""
        desde = date(2026, 1, 1)
        hasta = desde + timedelta(days=400)
        
        response = client.get(
            "/api/v1/reportes/vendedores/kpi",
            params={
                "vendedor_id": 1,
                "desde": desde.isoformat(),
                "hasta": hasta.isoformat()
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no puede ser mayor a 365 días" in response.json()["detail"]
    
    @patch('app.routes.reportes.ReportesService.generar_kpi_vendedor', new_callable=AsyncMock)
    def test_obtener_kpi_vendedor_con_filtros(self, mock_generar_kpi, mock_kpi_vendedor):
        """Test KPI con filtros opcionales"""
        mock_generar_kpi.return_value = mock_kpi_vendedor
        
        response = client.get(
            "/api/v1/reportes/vendedores/kpi",
            params={
                "vendedor_id": 1,
                "desde": "2026-01-01",
                "hasta": "2026-01-31",
                "territorio_id": "ZONA_NORTE",
                "producto_id": "PROD001"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que se llamó con los parámetros correctos
        mock_generar_kpi.assert_called_once()
        call_kwargs = mock_generar_kpi.call_args.kwargs
        assert call_kwargs["vendedor_id"] == 1
        assert call_kwargs["territorio_id"] == "ZONA_NORTE"
        assert call_kwargs["producto_id"] == "PROD001"
    
    @patch('app.routes.reportes.ReportesService.generar_reporte_region', new_callable=AsyncMock)
    def test_obtener_reporte_region_success(self, mock_generar_reporte, mock_reporte_region):
        """Test obtener reporte de región exitoso"""
        mock_generar_reporte.return_value = mock_reporte_region
        
        response = client.get(
            "/api/v1/reportes/vendedores/region",
            params={
                "territorio_id": "ZONA_NORTE",
                "desde": "2026-01-01",
                "hasta": "2026-01-31"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["territorio"]["id"] == "ZONA_NORTE"
        assert data["territorio"]["nombre"] == "Zona Norte"
        assert len(data["ranking"]) == 2
        assert data["ranking"][0]["posicion"] == 1
        assert data["ranking"][0]["nombre"] == "Juan Pérez"
        assert data["resumen"]["ventas_valor"] == 4100000.0
    
    @patch('app.routes.reportes.ReportesService.generar_reporte_region', new_callable=AsyncMock)
    def test_obtener_reporte_region_con_producto(self, mock_generar_reporte, mock_reporte_region):
        """Test reporte región filtrado por producto"""
        mock_generar_reporte.return_value = mock_reporte_region
        
        response = client.get(
            "/api/v1/reportes/vendedores/region",
            params={
                "territorio_id": "ZONA_SUR",
                "desde": "2026-01-01",
                "hasta": "2026-01-31",
                "producto_id": "PROD002"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        mock_generar_reporte.assert_called_once()
    
    @patch('app.routes.reportes.ReportesService.generar_dashboard', new_callable=AsyncMock)
    def test_obtener_dashboard_success(self, mock_generar_dashboard, mock_dashboard):
        """Test obtener dashboard exitoso"""
        mock_generar_dashboard.return_value = mock_dashboard
        
        response = client.get(
            "/api/v1/reportes/vendedores/dashboard",
            params={
                "desde": "2026-01-01",
                "hasta": "2026-01-31"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "kpis" in data
        assert len(data["kpis"]) == 2
        assert data["kpis"][0]["label"] == "Ventas Totales"
        assert "grafico_tendencia" in data
        assert "grafico_vendedores" in data
        assert "grafico_cumplimiento" in data
        assert "top_vendedores" in data
    
    @patch('app.routes.reportes.ReportesService.generar_dashboard', new_callable=AsyncMock)
    def test_obtener_dashboard_verifica_chartjs_format(self, mock_generar_dashboard, mock_dashboard):
        """Test que el dashboard retorna datos en formato Chart.js"""
        mock_generar_dashboard.return_value = mock_dashboard
        
        response = client.get(
            "/api/v1/reportes/vendedores/dashboard",
            params={
                "desde": "2026-01-01",
                "hasta": "2026-01-31"
            }
        )
        
        data = response.json()
        
        # Verificar estructura Chart.js
        grafico_tendencia = data["grafico_tendencia"]
        assert "labels" in grafico_tendencia
        assert "datasets" in grafico_tendencia
        assert isinstance(grafico_tendencia["labels"], list)
        assert isinstance(grafico_tendencia["datasets"], list)
        
        grafico_vendedores = data["grafico_vendedores"]
        assert "labels" in grafico_vendedores
        assert "datasets" in grafico_vendedores
        
        grafico_cumplimiento = data["grafico_cumplimiento"]
        assert "labels" in grafico_cumplimiento
        assert "datasets" in grafico_cumplimiento
    
    @patch('app.routes.reportes.ReportesService.calcular_ventas_periodo')
    @patch('app.routes.reportes.ReportesService.obtener_metas_periodo', new_callable=AsyncMock)
    def test_obtener_resumen_kpis(self, mock_metas, mock_ventas):
        """Test endpoint de resumen rápido"""
        mock_ventas.return_value = (2300000.0, 15, 2)
        mock_metas.return_value = (20, 3000000.0)
        
        response = client.get(
            "/api/v1/reportes/vendedores/kpi/resumen",
            params={
                "vendedor_id": 1,
                "desde": "2026-01-01",
                "hasta": "2026-01-31"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["vendedor_id"] == 1
        assert data["ventas_valor"] == 2300000.0
        assert data["ventas_unidades"] == 15
        assert data["pedidos"] == 2
        assert data["cumplimiento_porcentaje"] == 75.0  # (15/20)*100
    
    @patch('app.routes.reportes.ReportesService.generar_kpi_vendedor', new_callable=AsyncMock)
    def test_obtener_kpi_vendedor_error_interno(self, mock_generar_kpi):
        """Test manejo de error interno"""
        mock_generar_kpi.side_effect = Exception("Database connection error")
        
        response = client.get(
            "/api/v1/reportes/vendedores/kpi",
            params={
                "vendedor_id": 1,
                "desde": "2026-01-01",
                "hasta": "2026-01-31"
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error interno" in response.json()["detail"]
    
    def test_missing_required_params(self):
        """Test sin parámetros requeridos"""
        response = client.get("/api/v1/reportes/vendedores/kpi")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_invalid_date_format(self):
        """Test con formato de fecha inválido"""
        response = client.get(
            "/api/v1/reportes/vendedores/kpi",
            params={
                "vendedor_id": 1,
                "desde": "01/01/2026",  # Formato incorrecto
                "hasta": "2026-01-31"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.routes.reportes.ReportesService.generar_reporte_region', new_callable=AsyncMock)
    def test_obtener_reporte_region_invalid_periodo(self, mock_generar_reporte):
        """Test reporte región con periodo inválido"""
        response = client.get(
            "/api/v1/reportes/vendedores/region",
            params={
                "territorio_id": "ZONA_NORTE",
                "desde": "2026-03-01",
                "hasta": "2026-01-01"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "anterior o igual" in response.json()["detail"]
    
    @patch('app.routes.reportes.ReportesService.generar_reporte_region', new_callable=AsyncMock)
    def test_obtener_reporte_region_periodo_muy_largo(self, mock_generar_reporte):
        """Test reporte región con periodo > 365 días"""
        desde = date(2026, 1, 1)
        hasta = desde + timedelta(days=400)
        
        response = client.get(
            "/api/v1/reportes/vendedores/region",
            params={
                "territorio_id": "ZONA_NORTE",
                "desde": str(desde),
                "hasta": str(hasta)
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "365 días" in response.json()["detail"]
    
    @patch('app.routes.reportes.ReportesService.generar_reporte_region', new_callable=AsyncMock)
    def test_obtener_reporte_region_error_interno(self, mock_generar_reporte):
        """Test manejo de error interno en reporte región"""
        mock_generar_reporte.side_effect = Exception("Database error")
        
        response = client.get(
            "/api/v1/reportes/vendedores/region",
            params={
                "territorio_id": "ZONA_NORTE",
                "desde": "2026-01-01",
                "hasta": "2026-01-31"
            }
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error interno" in response.json()["detail"]
    
    @patch('app.routes.reportes.ReportesService.generar_dashboard', new_callable=AsyncMock)
    def test_obtener_dashboard_invalid_periodo(self, mock_generar_dashboard):
        """Test dashboard con periodo inválido"""
        response = client.get(
            "/api/v1/reportes/vendedores/dashboard",
            params={
                "desde": "2026-06-01",
                "hasta": "2026-01-01"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "anterior o igual" in response.json()["detail"]
    
    @patch('app.routes.reportes.ReportesService.generar_dashboard', new_callable=AsyncMock)
    def test_obtener_dashboard_periodo_muy_largo(self, mock_generar_dashboard):
        """Test dashboard con periodo > 365 días"""
        response = client.get(
            "/api/v1/reportes/vendedores/dashboard",
            params={
                "desde": "2025-01-01",
                "hasta": "2027-01-01"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "365 días" in response.json()["detail"]
    
    @patch('app.routes.reportes.ReportesService.generar_dashboard', new_callable=AsyncMock)
    def test_obtener_dashboard_error_interno(self, mock_generar_dashboard):
        """Test manejo de error interno en dashboard"""
        mock_generar_dashboard.side_effect = Exception("Service error")
        
        response = client.get(
            "/api/v1/reportes/vendedores/dashboard",
            params={
                "desde": "2026-01-01",
                "hasta": "2026-01-31"
            }
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error interno" in response.json()["detail"]
    
    @patch('app.routes.reportes.ReportesService.obtener_metas_periodo', new_callable=AsyncMock)
    def test_obtener_resumen_kpis_invalid_periodo(self, mock_obtener_metas):
        """Test resumen con periodo inválido"""
        response = client.get(
            "/api/v1/reportes/vendedores/kpi/resumen",
            params={
                "vendedor_id": 1,
                "desde": "2026-06-01",
                "hasta": "2026-01-01"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "inválido" in response.json()["detail"]
    
    @patch('app.routes.reportes.ReportesService.obtener_metas_periodo', new_callable=AsyncMock)
    def test_obtener_resumen_kpis_error_interno(self, mock_obtener_metas):
        """Test manejo de error interno en resumen"""
        mock_obtener_metas.side_effect = Exception("Service unavailable")
        
        response = client.get(
            "/api/v1/reportes/vendedores/kpi/resumen",
            params={
                "vendedor_id": 1,
                "desde": "2026-01-01",
                "hasta": "2026-01-31"
            }
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error generando resumen" in response.json()["detail"]


@pytest.mark.integration
class TestReportesRoutesIntegration:
    """Tests de integración con servicios reales"""
    
    @pytest.mark.skip(reason="Requiere servicios externos activos")
    def test_kpi_vendedor_integracion_completa(self):
        """Test de integración con product-service y user-service"""
        # TODO: Implementar con servicios reales
        pass
    
    @pytest.mark.skip(reason="Requiere servicios externos activos")
    def test_dashboard_performance_sla(self):
        """Test que verifica SLA de ≤2 segundos"""
        import time
        
        inicio = time.time()
        response = client.get(
            "/api/v1/reportes/vendedores/dashboard",
            params={
                "desde": "2026-01-01",
                "hasta": "2026-03-31"
            }
        )
        duracion = time.time() - inicio
        
        assert response.status_code == status.HTTP_200_OK
        assert duracion <= 2.0, f"SLA excedido: {duracion}s > 2s"

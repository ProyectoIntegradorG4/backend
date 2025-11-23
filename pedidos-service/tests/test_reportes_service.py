"""
Tests para el servicio de reportes de vendedores (HU-WEB-010)
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.orm import Session

from app.services.reportes import ReportesService
from app.models.pedido import Pedido, DetallePedido, EstadoPedido
from app.schemas.reporte import (
    KPIVendedor, ReporteRegion, DashboardReportes,
    TendenciaItem, VendedorRanking
)


@pytest.fixture
def mock_db():
    """Mock de sesión de base de datos"""
    return MagicMock(spec=Session)


@pytest.fixture
def pedidos_sample(mock_db):
    """Pedidos de ejemplo para tests"""
    # Crear pedidos del vendedor 1
    pedido1 = Pedido(
        pedido_id="550e8400-e29b-41d4-a716-446655440001",
        usuario_id=1,
        cliente_id="CLI001",
        nit="900123456-1",
        estado=EstadoPedido.ENTREGADO,
        monto_total=Decimal("1500000.00"),
        fecha_creacion=datetime(2026, 1, 15),
        detalles=[
            DetallePedido(
                detalle_id="DET001",
                producto_id="PROD001",
                cantidad_solicitada=10,
                precio_unitario=Decimal("150000.00"),
                subtotal=Decimal("1500000.00")
            )
        ]
    )
    
    pedido2 = Pedido(
        pedido_id="550e8400-e29b-41d4-a716-446655440002",
        usuario_id=1,
        cliente_id="CLI002",
        nit="900123456-2",
        estado=EstadoPedido.ENVIADO,
        monto_total=Decimal("800000.00"),
        fecha_creacion=datetime(2026, 1, 20),
        detalles=[
            DetallePedido(
                detalle_id="DET002",
                producto_id="PROD001",
                cantidad_solicitada=5,
                precio_unitario=Decimal("160000.00"),
                subtotal=Decimal("800000.00")
            )
        ]
    )
    
    # Pedido cancelado (no debe contarse)
    pedido3 = Pedido(
        pedido_id="550e8400-e29b-41d4-a716-446655440003",
        usuario_id=1,
        cliente_id="CLI003",
        nit="900123456-3",
        estado=EstadoPedido.CANCELADO,
        monto_total=Decimal("500000.00"),
        fecha_creacion=datetime(2026, 1, 25)
    )
    
    # Pedido de otro vendedor
    pedido4 = Pedido(
        pedido_id="550e8400-e29b-41d4-a716-446655440004",
        usuario_id=2,
        cliente_id="CLI004",
        nit="900123456-4",
        estado=EstadoPedido.ENTREGADO,
        monto_total=Decimal("2000000.00"),
        fecha_creacion=datetime(2026, 1, 18)
    )
    
    return [pedido1, pedido2, pedido3, pedido4]


class TestReportesService:
    """Tests para ReportesService"""
    
    @pytest.mark.asyncio
    async def test_obtener_nombre_vendedor_success(self):
        """Test obtener nombre de vendedor exitoso"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "usuario_id": 1,
                "nombre_completo": "Juan Pérez"
            }
            
            mock_async_client = AsyncMock()
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_async_client
            
            nombre = await ReportesService.obtener_nombre_vendedor(1)
            assert nombre == "Juan Pérez"
    
    @pytest.mark.asyncio
    async def test_obtener_nombre_vendedor_fallback(self):
        """Test fallback cuando no se encuentra vendedor"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 404
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            nombre = await ReportesService.obtener_nombre_vendedor(999)
            assert nombre == "Vendedor 999"
    
    @pytest.mark.asyncio
    async def test_obtener_metas_periodo(self, mock_db):
        """Test obtener metas del periodo"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "total_unidades": 100,
                "total_valor": 10000000.0
            }
            
            mock_async_client = AsyncMock()
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_async_client
            
            meta_unidades, meta_valor = await ReportesService.obtener_metas_periodo(
                mock_db, 1, None, None, date(2026, 1, 1), date(2026, 1, 31)
            )
            
            assert meta_unidades == 100
            assert meta_valor == 10000000.0
    
    @pytest.mark.asyncio
    async def test_obtener_metas_periodo_sin_metas(self, mock_db):
        """Test cuando no hay metas definidas"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "total_unidades": 0,
                "total_valor": 0.0
            }
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            meta_unidades, meta_valor = await ReportesService.obtener_metas_periodo(
                mock_db, 1, None, None, date(2026, 1, 1), date(2026, 1, 31)
            )
            
            assert meta_unidades is None
            assert meta_valor is None
    
    def test_calcular_ventas_periodo_vendedor_especifico(self, mock_db):
        """Test cálculo de ventas para vendedor específico"""
        # Mock query results
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MagicMock(total_valor=2300000.0, num_pedidos=2)
        mock_db.query.return_value = mock_query
        
        # Mock query de unidades
        mock_query_unidades = MagicMock()
        mock_query_unidades.join.return_value = mock_query_unidades
        mock_query_unidades.filter.return_value = mock_query_unidades
        mock_query_unidades.first.return_value = MagicMock(total_unidades=15)
        
        # Alternar entre queries
        mock_db.query.side_effect = [mock_query, mock_query_unidades]
        
        ventas_valor, ventas_unidades, num_pedidos = ReportesService.calcular_ventas_periodo(
            mock_db, 1, None, None, date(2026, 1, 1), date(2026, 1, 31)
        )
        
        assert ventas_valor == 2300000.0
        assert ventas_unidades == 15
        assert num_pedidos == 2
    
    def test_calcular_ventas_periodo_sin_ventas(self, mock_db):
        """Test cuando no hay ventas en el periodo"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MagicMock(total_valor=0, num_pedidos=0)
        mock_db.query.return_value = mock_query
        
        mock_query_unidades = MagicMock()
        mock_query_unidades.join.return_value = mock_query_unidades
        mock_query_unidades.filter.return_value = mock_query_unidades
        mock_query_unidades.first.return_value = MagicMock(total_unidades=0)
        
        mock_db.query.side_effect = [mock_query, mock_query_unidades]
        
        ventas_valor, ventas_unidades, num_pedidos = ReportesService.calcular_ventas_periodo(
            mock_db, 999, None, None, date(2026, 1, 1), date(2026, 1, 31)
        )
        
        assert ventas_valor == 0.0
        assert ventas_unidades == 0
        assert num_pedidos == 0
    
    def test_calcular_tendencia_mensual(self, mock_db):
        """Test cálculo de tendencia con granularidad mensual"""
        # Mock resultado agrupado por mes
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            MagicMock(periodo=datetime(2026, 1, 1), valor=1500000.0, pedidos=5),
            MagicMock(periodo=datetime(2026, 2, 1), valor=1800000.0, pedidos=6),
            MagicMock(periodo=datetime(2026, 3, 1), valor=2000000.0, pedidos=7)
        ]
        mock_db.query.return_value = mock_query
        
        # Mock queries de unidades
        mock_unidades_query = MagicMock()
        mock_unidades_query.join.return_value = mock_unidades_query
        mock_unidades_query.filter.return_value = mock_unidades_query
        mock_unidades_query.scalar.return_value = 50
        
        mock_db.query.side_effect = [mock_query] + [mock_unidades_query] * 3
        
        tendencia = ReportesService.calcular_tendencia(
            mock_db, 1, None, None, date(2026, 1, 1), date(2026, 3, 31)
        )
        
        assert len(tendencia) == 3
        assert all(isinstance(t, TendenciaItem) for t in tendencia)
        assert tendencia[0].valor == 1500000.0
        assert tendencia[1].valor == 1800000.0
        assert tendencia[2].valor == 2000000.0
    
    @pytest.mark.asyncio
    async def test_generar_kpi_vendedor_completo(self, mock_db):
        """Test generación completa de KPI de vendedor"""
        # Mock de todas las llamadas necesarias
        with patch.object(ReportesService, 'obtener_nombre_vendedor', new_callable=AsyncMock) as mock_nombre, \
             patch.object(ReportesService, 'calcular_ventas_periodo') as mock_ventas, \
             patch.object(ReportesService, 'obtener_metas_periodo', new_callable=AsyncMock) as mock_metas, \
             patch.object(ReportesService, 'calcular_tendencia') as mock_tendencia:
            
            mock_nombre.return_value = "Juan Pérez"
            mock_ventas.return_value = (2300000.0, 15, 2)
            mock_metas.return_value = (20, 3000000.0)
            mock_tendencia.return_value = [
                TendenciaItem(fecha=date(2026, 1, 31), valor=2300000.0, unidades=15, pedidos=2)
            ]
            
            kpi = await ReportesService.generar_kpi_vendedor(
                mock_db, 1, date(2026, 1, 1), date(2026, 1, 31)
            )
            
            assert isinstance(kpi, KPIVendedor)
            assert kpi.vendedor.id == "1"
            assert kpi.vendedor.nombre == "Juan Pérez"
            assert kpi.ventas_valor == 2300000.0
            assert kpi.ventas_unidades == 15
            assert kpi.pedidos == 2
            assert kpi.meta_unidades == 20
            assert kpi.meta_valor == 3000000.0
            assert kpi.cumplimiento_unidades == 0.75  # 15/20
            assert kpi.cumplimiento_valor == pytest.approx(0.7667, abs=0.001)  # 2300000/3000000
            assert len(kpi.tendencia) == 1
    
    @pytest.mark.asyncio
    async def test_generar_kpi_vendedor_sin_metas(self, mock_db):
        """Test KPI cuando no hay metas definidas"""
        with patch.object(ReportesService, 'obtener_nombre_vendedor', new_callable=AsyncMock) as mock_nombre, \
             patch.object(ReportesService, 'calcular_ventas_periodo') as mock_ventas, \
             patch.object(ReportesService, 'obtener_metas_periodo', new_callable=AsyncMock) as mock_metas, \
             patch.object(ReportesService, 'calcular_tendencia') as mock_tendencia:
            
            mock_nombre.return_value = "María López"
            mock_ventas.return_value = (1500000.0, 10, 1)
            mock_metas.return_value = (None, None)  # Sin metas
            mock_tendencia.return_value = []
            
            kpi = await ReportesService.generar_kpi_vendedor(
                mock_db, 2, date(2026, 1, 1), date(2026, 1, 31)
            )
            
            assert kpi.ventas_valor == 1500000.0
            assert kpi.meta_unidades is None
            assert kpi.meta_valor is None
            assert kpi.cumplimiento_unidades is None
            assert kpi.cumplimiento_valor is None
    
    @pytest.mark.asyncio
    async def test_generar_reporte_region(self, mock_db):
        """Test generación de reporte por región"""
        # Mock vendedores activos
        mock_query_vendedores = MagicMock()
        mock_query_vendedores.filter.return_value = mock_query_vendedores
        mock_query_vendedores.all.return_value = [(1,), (2,)]
        
        mock_db.query.return_value = mock_query_vendedores
        
        with patch.object(ReportesService, 'obtener_territorio_info', new_callable=AsyncMock) as mock_territorio, \
             patch.object(ReportesService, 'obtener_nombre_vendedor', new_callable=AsyncMock) as mock_nombre, \
             patch.object(ReportesService, 'calcular_ventas_periodo') as mock_ventas, \
             patch.object(ReportesService, 'obtener_metas_periodo', new_callable=AsyncMock) as mock_metas, \
             patch.object(ReportesService, 'calcular_tendencia') as mock_tendencia:
            
            mock_territorio.return_value = {"territorio_id": "ZONA_NORTE", "nombre": "Zona Norte"}
            mock_nombre.side_effect = ["Juan Pérez", "María López"]
            mock_ventas.side_effect = [
                (2300000.0, 15, 2),  # Vendedor 1
                (1800000.0, 12, 1),  # Vendedor 2
                (4100000.0, 27, 3)   # Totales región
            ]
            mock_metas.side_effect = [
                (20, 3000000.0),  # Meta vendedor 1
                (15, 2000000.0),  # Meta vendedor 2
                (35, 5000000.0)   # Meta región
            ]
            mock_tendencia.return_value = []
            
            reporte = await ReportesService.generar_reporte_region(
                mock_db, "ZONA_NORTE", date(2026, 1, 1), date(2026, 1, 31)
            )
            
            assert isinstance(reporte, ReporteRegion)
            assert reporte.territorio.id == "ZONA_NORTE"
            assert reporte.territorio.nombre == "Zona Norte"
            assert len(reporte.ranking) == 2
            assert reporte.ranking[0].posicion == 1
            assert reporte.ranking[0].nombre == "Juan Pérez"
            assert reporte.ranking[1].posicion == 2
            assert reporte.ranking[1].nombre == "María López"
            assert reporte.resumen.ventas_valor == 4100000.0
            assert reporte.resumen.ventas_unidades == 27
    
    @pytest.mark.asyncio
    async def test_generar_dashboard(self, mock_db):
        """Test generación de dashboard completo"""
        # Mock vendedores query
        mock_query_vendedores = MagicMock()
        mock_query_vendedores.filter.return_value = mock_query_vendedores
        mock_query_vendedores.group_by.return_value = mock_query_vendedores
        mock_query_vendedores.order_by.return_value = mock_query_vendedores
        mock_query_vendedores.limit.return_value = mock_query_vendedores
        mock_query_vendedores.all.return_value = [
            MagicMock(usuario_id=1, total_ventas=2300000.0, num_pedidos=2),
            MagicMock(usuario_id=2, total_ventas=1800000.0, num_pedidos=1)
        ]
        
        # Mock queries adicionales
        mock_query_unidades = MagicMock()
        mock_query_unidades.join.return_value = mock_query_unidades
        mock_query_unidades.filter.return_value = mock_query_unidades
        mock_query_unidades.scalar.side_effect = [15, 12]
        
        mock_db.query.side_effect = [
            mock_query_vendedores,  # Para vendedores
            mock_query_unidades,     # Unidades vendedor 1
            mock_query_unidades      # Unidades vendedor 2
        ]
        
        with patch.object(ReportesService, 'calcular_ventas_periodo') as mock_ventas, \
             patch.object(ReportesService, 'obtener_metas_periodo', new_callable=AsyncMock) as mock_metas, \
             patch.object(ReportesService, 'calcular_tendencia') as mock_tendencia, \
             patch.object(ReportesService, 'obtener_nombre_vendedor', new_callable=AsyncMock) as mock_nombre:
            
            mock_ventas.return_value = (4100000.0, 27, 3)
            mock_metas.side_effect = [
                (30, 5000000.0),  # Meta total
                (20, 3000000.0),  # Meta vendedor 1
                (15, 2000000.0)   # Meta vendedor 2
            ]
            mock_tendencia.return_value = [
                TendenciaItem(fecha=date(2026, 1, 31), valor=4100000.0, unidades=27, pedidos=3)
            ]
            mock_nombre.side_effect = ["Juan Pérez", "María López"]
            
            dashboard = await ReportesService.generar_dashboard(
                mock_db, date(2026, 1, 1), date(2026, 1, 31)
            )
            
            assert isinstance(dashboard, DashboardReportes)
            assert len(dashboard.kpis) == 4
            assert dashboard.kpis[0].label == "Ventas Totales"
            assert dashboard.kpis[0].valor == 4100000.0
            assert dashboard.grafico_tendencia is not None
            assert dashboard.grafico_vendedores is not None
            assert dashboard.grafico_cumplimiento is not None
            assert len(dashboard.top_vendedores) == 2
            assert dashboard.top_vendedores[0].posicion == 1
            assert dashboard.top_vendedores[0].ventas_valor == 2300000.0


@pytest.mark.integration
class TestReportesServiceIntegration:
    """Tests de integración con base de datos real (opcional)"""
    
    @pytest.mark.skip(reason="Requiere base de datos configurada")
    def test_kpi_vendedor_con_db_real(self, test_db):
        """Test con base de datos real"""
        # TODO: Implementar con fixtures de DB real
        pass

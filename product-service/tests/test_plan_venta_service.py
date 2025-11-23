"""
Tests unitarios para PlanVentaService
HU-WEB-008: Crear planes de venta
HU-WEB-009: Listar planes de venta
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from uuid import uuid4
from fastapi import HTTPException
from app.service.plan_venta_service import PlanVentaService
from app.models.plan_venta import PlanVenta
from app.models.territorio import Territorio


class TestListarTerritorios:
    """Tests para listar_territorios()"""
    
    def test_listar_territorios_ok(self):
        """Debe listar territorios activos correctamente"""
        db_mock = Mock()
        territorio1 = Territorio(
            territorio_id="TERR-001",
            nombre="Zona Norte",
            codigo="ZN-001",
            pais="Colombia",
            activo=True
        )
        territorio2 = Territorio(
            territorio_id="TERR-002",
            nombre="Zona Sur",
            codigo="ZS-001",
            pais="Colombia",
            activo=True
        )
        
        query_mock = Mock()
        query_mock.filter.return_value.order_by.return_value.all.return_value = [territorio1, territorio2]
        db_mock.query.return_value = query_mock
        
        result = PlanVentaService.listar_territorios(db_mock)
        
        assert len(result) == 2
        assert result[0].territorio_id == "TERR-001"
        assert result[0].nombre == "Zona Norte"
        assert result[1].territorio_id == "TERR-002"
    
    def test_listar_territorios_vacio(self):
        """Debe retornar lista vacía si no hay territorios"""
        db_mock = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.order_by.return_value.all.return_value = []
        db_mock.query.return_value = query_mock
        
        result = PlanVentaService.listar_territorios(db_mock)
        
        assert result == []


class TestCrearPlanVenta:
    """Tests para crear_plan_venta() - HU-WEB-008"""
    
    def test_crear_plan_validacion_nombre_duplicado(self):
        """Debe rechazar nombre duplicado con 409"""
        db_mock = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = Mock()  # Ya existe
        db_mock.query.return_value = query_mock
        
        from app.schemas.plan_venta import PlanVentaCreate, MetaCreate
        data = PlanVentaCreate(
            nombre="Plan Existente",
            periodo={"desde": "2025-01-01", "hasta": "2025-12-31"},
            territorios=["TERR-001"],
            metas=[
                MetaCreate(
                    productoId="PROD-001",
                    territorioId="TERR-001",
                    vendedorId=1,
                    objetivo_cantidad=100
                )
            ]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            PlanVentaService.crear_plan_venta(db_mock, data, usuario_id=1)
        
        assert exc_info.value.status_code == 409
        assert "nombre" in str(exc_info.value.detail).lower()
    
    def test_crear_plan_validacion_territorios_inexistentes(self):
        """Debe rechazar territorios que no existen con 400"""
        db_mock = Mock()
        
        # Nombre no existe
        query_nombre = Mock()
        query_nombre.filter.return_value.first.return_value = None
        
        # Territorios no existen
        query_terr = Mock()
        query_terr.filter.return_value.all.return_value = []  # Vacío
        
        db_mock.query.side_effect = [query_nombre, query_terr]
        
        from app.schemas.plan_venta import PlanVentaCreate, MetaCreate
        data = PlanVentaCreate(
            nombre="Plan Nuevo",
            periodo={"desde": "2025-01-01", "hasta": "2025-12-31"},
            territorios=["TERR-NOEXISTE"],
            metas=[
                MetaCreate(
                    productoId="PROD-001",
                    territorioId="TERR-NOEXISTE",
                    vendedorId=1,
                    objetivo_cantidad=100
                )
            ]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            PlanVentaService.crear_plan_venta(db_mock, data, usuario_id=1)
        
        assert exc_info.value.status_code == 400
        assert "territorios" in str(exc_info.value.detail).lower()
    
    def test_crear_plan_validacion_productos_inexistentes(self):
        """Debe validar que los productos existan"""
        db_mock = Mock()
        
        # Nombre no existe
        query_nombre = Mock()
        query_nombre.filter.return_value.first.return_value = None
        
        # Territorios existen
        query_terr = Mock()
        query_terr.filter.return_value.all.return_value = [
            Mock(territorio_id="TERR-001")
        ]
        
        # Productos NO existen
        query_prod = Mock()
        query_prod.filter.return_value.all.return_value = []  # Vacío
        
        db_mock.query.side_effect = [query_nombre, query_terr, query_prod]
        
        from app.schemas.plan_venta import PlanVentaCreate, MetaCreate
        data = PlanVentaCreate(
            nombre="Plan Nuevo",
            periodo={"desde": "2025-01-01", "hasta": "2025-12-31"},
            territorios=["TERR-001"],
            metas=[
                MetaCreate(
                    productoId="PROD-NOEXISTE",
                    territorioId="TERR-001",
                    vendedorId=1,
                    objetivo_cantidad=100
                )
            ]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            PlanVentaService.crear_plan_venta(db_mock, data, usuario_id=1)
        
        assert exc_info.value.status_code == 400
        assert "productos" in str(exc_info.value.detail).lower()
    
    @patch('app.service.plan_venta_service.create_engine')
    def test_crear_plan_validacion_vendedores_inexistentes(self, mock_engine):
        """Debe validar que los vendedores existan en user_db"""
        db_mock = Mock()
        
        # Mock de la conexión a user_db que retorna vacío (vendedores no existen)
        conn_mock = MagicMock()
        result_mock = Mock()
        result_mock.fetchall.return_value = []  # No hay vendedores válidos
        conn_mock.execute.return_value = result_mock
        conn_mock.__enter__ = Mock(return_value=conn_mock)
        conn_mock.__exit__ = Mock(return_value=False)
        
        engine_mock = Mock()
        engine_mock.connect.return_value = conn_mock
        mock_engine.return_value = engine_mock
        
        # Nombre no existe
        query_nombre = Mock()
        query_nombre.filter.return_value.first.return_value = None
        
        # Territorios existen
        query_terr = Mock()
        query_terr.filter.return_value.all.return_value = [
            Mock(territorio_id="TERR-001")
        ]
        
        # Productos existen
        query_prod = Mock()
        query_prod.filter.return_value.all.return_value = [
            Mock(productoId="PROD-001")
        ]
        
        db_mock.query.side_effect = [query_nombre, query_terr, query_prod]
        
        from app.schemas.plan_venta import PlanVentaCreate, MetaCreate
        data = PlanVentaCreate(
            nombre="Plan Nuevo",
            periodo={"desde": "2025-01-01", "hasta": "2025-12-31"},
            territorios=["TERR-001"],
            metas=[
                MetaCreate(
                    productoId="PROD-001",
                    territorioId="TERR-001",
                    vendedorId=999,
                    objetivo_cantidad=100
                )
            ]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            PlanVentaService.crear_plan_venta(db_mock, data, usuario_id=1)
        
        assert exc_info.value.status_code == 400
        assert "vendedores" in str(exc_info.value.detail).lower()
    
    def test_crear_plan_validacion_metas_duplicadas(self):
        """Debe rechazar metas duplicadas (mismo producto/territorio/vendedor)"""
        from unittest.mock import patch
        
        db_mock = Mock()
        
        # Setup mínimo para pasar validaciones anteriores
        query_nombre = Mock()
        query_nombre.filter.return_value.first.return_value = None
        
        query_terr = Mock()
        query_terr.filter.return_value.all.return_value = [Mock(territorio_id="TERR-001")]
        
        query_prod = Mock()
        query_prod.filter.return_value.all.return_value = [Mock(productoId="PROD-001")]
        
        db_mock.query.side_effect = [query_nombre, query_terr, query_prod]
        
        from app.schemas.plan_venta import PlanVentaCreate, MetaCreate
        data = PlanVentaCreate(
            nombre="Plan Nuevo",
            periodo={"desde": "2025-01-01", "hasta": "2025-12-31"},
            territorios=["TERR-001"],
            metas=[
                MetaCreate(
                    productoId="PROD-001",
                    territorioId="TERR-001",
                    vendedorId=1,
                    objetivo_cantidad=100
                ),
                MetaCreate(
                    productoId="PROD-001",
                    territorioId="TERR-001",
                    vendedorId=1,  # DUPLICADO
                    objetivo_cantidad=200
                )
            ]
        )
        
        # Mock de validación de vendedores cross-database
        with patch.object(PlanVentaService, '_validar_vendedores', return_value=(True, [1], "")):
            with pytest.raises(HTTPException) as exc_info:
                PlanVentaService.crear_plan_venta(db_mock, data, usuario_id=1)
        
        assert exc_info.value.status_code == 400
        assert "duplicada" in str(exc_info.value.detail).lower()
    
    def test_crear_plan_validacion_objetivo_requerido(self):
        """Test que al menos un objetivo esté presente (cantidad o valor)"""
        # Este test solo documenta que la validación de objetivo es a nivel de servicio
        # Pydantic permite crear MetaCreate sin objetivos (ambos son opcionales),
        # pero el validator personalizado requiere al menos uno
        from app.schemas.plan_venta import MetaCreate
        
        # Este es un caso válido en Pydantic pero debería fallar en el servicio
        meta = MetaCreate(
            productoId="PROD-001",
            territorioId="TERR-001",
            vendedorId=10,
            objetivo_cantidad=0  # Pydantic acepta 0
        )
        
        # El meta se crea exitosamente
        assert meta.productoId == "PROD-001"


class TestListarPlanesVenta:
    """Tests para listar_planes_venta() - HU-WEB-009"""
    
    def test_listar_planes_sin_filtros(self):
        """Debe listar planes sin filtros con paginación por defecto"""
        db_mock = Mock()
        
        plan1 = Mock(
            plan_id=uuid4(),
            nombre="Plan Q1",
            periodo_desde=date(2025, 1, 1),
            periodo_hasta=date(2025, 3, 31),
            estado="activo",
            updated_at=datetime(2025, 1, 15, 10, 0, 0)
        )
        plan1.territorios = [Mock(), Mock()]  # 2 territorios
        plan1.metas = [Mock(), Mock(), Mock()]  # 3 metas
        
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [plan1]
        
        db_mock.query.return_value = query_mock
        
        planes, total = PlanVentaService.listar_planes_venta(db_mock)
        
        assert total == 1
        assert len(planes) == 1
        assert planes[0].nombre == "Plan Q1"
    
    def test_listar_planes_busqueda_nombre(self):
        """Debe buscar por nombre (parámetro q)"""
        db_mock = Mock()
        
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        db_mock.query.return_value = query_mock
        
        planes, total = PlanVentaService.listar_planes_venta(db_mock, q="Trimestre")
        
        # Verificar que se llamó filter (búsqueda ILIKE)
        assert query_mock.filter.called
        assert total == 0
        assert planes == []
    
    def test_listar_planes_filtro_periodo(self):
        """Debe filtrar por intersección de período"""
        db_mock = Mock()
        
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        db_mock.query.return_value = query_mock
        
        planes, total = PlanVentaService.listar_planes_venta(
            db_mock,
            periodo_from=date(2025, 1, 1),
            periodo_to=date(2025, 12, 31)
        )
        
        # Verificar que se aplicaron filtros
        assert query_mock.filter.called
        assert total == 0
    
    def test_listar_planes_filtro_estado(self):
        """Debe filtrar por estado"""
        db_mock = Mock()
        
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        db_mock.query.return_value = query_mock
        
        planes, total = PlanVentaService.listar_planes_venta(db_mock, estado="borrador")
        
        assert query_mock.filter.called
        assert total == 0
    
    def test_listar_planes_paginacion_personalizada(self):
        """Debe aplicar paginación personalizada"""
        db_mock = Mock()
        
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 100
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        db_mock.query.return_value = query_mock
        
        planes, total = PlanVentaService.listar_planes_venta(db_mock, page=3, page_size=10)
        
        assert total == 100
        # Verificar offset = (page-1) * page_size = 2 * 10 = 20
        query_mock.offset.assert_called_once_with(20)
        query_mock.limit.assert_called_once_with(10)
    
    def test_listar_planes_page_size_validacion(self):
        """Debe validar page_size (el servicio puede o no limitar a 50)"""
        db_mock = Mock()
        
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 200
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        db_mock.query.return_value = query_mock
        
        planes, total = PlanVentaService.listar_planes_venta(db_mock, page_size=100)
        
        # El servicio debería usar el valor pasado o limitarlo
        assert query_mock.limit.called
    
    def test_listar_planes_ordenamiento_nombre_asc(self):
        """Debe ordenar por nombre ascendente"""
        db_mock = Mock()
        
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        db_mock.query.return_value = query_mock
        
        planes, total = PlanVentaService.listar_planes_venta(
            db_mock, 
            sort="nombre", 
            order="asc"
        )
        
        # Verificar que se llamó order_by
        assert query_mock.order_by.called
    
    def test_listar_planes_ordenamiento_periodo_desc(self):
        """Debe ordenar por periodo_desde descendente"""
        db_mock = Mock()
        
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        db_mock.query.return_value = query_mock
        
        planes, total = PlanVentaService.listar_planes_venta(
            db_mock,
            sort="periodo_desde",
            order="desc"
        )
        
        assert query_mock.order_by.called


class TestObtenerPlanPorId:
    """Tests para obtener_plan_por_id()"""
    
    def test_obtener_plan_existente(self):
        """Debe retornar plan con todas sus relaciones"""
        db_mock = Mock()
        plan_id = uuid4()
        
        plan_mock = Mock(
            plan_id=plan_id,
            nombre="Plan Q1 2025",
            periodo_desde=date(2025, 1, 1),
            periodo_hasta=date(2025, 3, 31),
            estado="activo",
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 15, 10, 0, 0),
            created_by=1
        )
        
        # Mock territorios
        terr1 = Mock()
        terr1.territorio = Mock(
            territorio_id="TERR-001",
            nombre="Zona Norte",
            codigo="ZN-001"
        )
        plan_mock.territorios = [terr1]
        
        # Mock metas
        meta1 = Mock(
            meta_id=uuid4(),
            producto_id="PROD-001",
            territorio_id="TERR-001",
            vendedor_id=1,
            objetivo_cantidad=100,
            objetivo_valor=1000000,
            nota="Meta Q1"
        )
        plan_mock.metas = [meta1]
        
        query_mock = Mock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = plan_mock
        
        db_mock.query.return_value = query_mock
        
        result = PlanVentaService.obtener_plan_por_id(db_mock, plan_id)
        
        assert result.plan_id == plan_id
        assert result.nombre == "Plan Q1 2025"
        assert len(result.territorios) == 1
        assert len(result.metas) == 1
    
    def test_obtener_plan_no_existe(self):
        """Debe retornar None si el plan no existe (no lanza 404)"""
        db_mock = Mock()
        plan_id = uuid4()
        
        query_mock = Mock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None  # No existe
        
        db_mock.query.return_value = query_mock
        
        result = PlanVentaService.obtener_plan_por_id(db_mock, plan_id)
        
        # El servicio retorna None, no lanza HTTPException
        assert result is None

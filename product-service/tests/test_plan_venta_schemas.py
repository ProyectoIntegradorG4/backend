# tests/test_plan_venta_schemas.py
"""
Tests para validaciones de schemas de Planes de Venta
"""
import pytest
from datetime import date
from pydantic import ValidationError
from app.schemas.plan_venta import PlanVentaCreate, MetaCreate


class TestMetaCreateSchema:
    """Tests para MetaCreate"""
    
    def test_meta_valida_con_cantidad(self):
        """Debe aceptar meta con objetivo de cantidad"""
        meta = MetaCreate(
            productoId="PROD-001",
            territorioId="TERR-001",
            vendedorId=1,
            objetivo_cantidad=100,
            objetivo_valor=0
        )
        
        assert meta.objetivo_cantidad == 100
        assert meta.objetivo_valor == 0
    
    def test_meta_valida_con_valor(self):
        """Debe aceptar meta con objetivo de valor"""
        meta = MetaCreate(
            productoId="PROD-001",
            territorioId="TERR-001",
            vendedorId=1,
            objetivo_cantidad=0,
            objetivo_valor=5000000
        )
        
        assert meta.objetivo_cantidad == 0
        assert meta.objetivo_valor == 5000000
    
    def test_meta_valida_con_ambos_objetivos(self):
        """Debe aceptar meta con ambos objetivos"""
        meta = MetaCreate(
            productoId="PROD-001",
            territorioId="TERR-001",
            vendedorId=1,
            objetivo_cantidad=100,
            objetivo_valor=5000000
        )
        
        assert meta.objetivo_cantidad == 100
        assert meta.objetivo_valor == 5000000
    
    def test_meta_con_nota_opcional(self):
        """Debe aceptar nota opcional"""
        meta = MetaCreate(
            productoId="PROD-001",
            territorioId="TERR-001",
            vendedorId=1,
            objetivo_cantidad=100,
            nota="Meta importante"
        )
        
        assert meta.nota == "Meta importante"
    
    def test_meta_producto_id_requerido(self):
        """Debe rechazar si falta productoId"""
        with pytest.raises(ValidationError) as exc_info:
            MetaCreate(
                territorioId="TERR-001",
                vendedorId=1,
                objetivo_cantidad=100
            )
        
        assert "productoId" in str(exc_info.value)
    
    def test_meta_territorio_id_requerido(self):
        """Debe rechazar si falta territorioId"""
        with pytest.raises(ValidationError) as exc_info:
            MetaCreate(
                productoId="PROD-001",
                vendedorId=1,
                objetivo_cantidad=100
            )
        
        assert "territorioId" in str(exc_info.value)
    
    def test_meta_vendedor_id_requerido(self):
        """Debe rechazar si falta vendedorId"""
        with pytest.raises(ValidationError) as exc_info:
            MetaCreate(
                productoId="PROD-001",
                territorioId="TERR-001",
                objetivo_cantidad=100
            )
        
        assert "vendedorId" in str(exc_info.value)


class TestPlanVentaCreateSchema:
    """Tests para PlanVentaCreate"""
    
    def test_plan_valido_minimo(self):
        """Debe aceptar plan con campos mínimos requeridos"""
        plan = PlanVentaCreate(
            nombre="Plan Q1 2025",
            periodo={"desde": "2025-01-01", "hasta": "2025-03-31"},
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
        
        assert plan.nombre == "Plan Q1 2025"
        assert len(plan.territorios) == 1
        assert len(plan.metas) == 1
    
    def test_plan_valido_completo(self):
        """Debe aceptar plan con múltiples territorios y metas"""
        plan = PlanVentaCreate(
            nombre="Plan Q1 2025",
            periodo={"desde": "2025-01-01", "hasta": "2025-03-31"},
            territorios=["TERR-001", "TERR-002"],
            metas=[
                MetaCreate(
                    productoId="PROD-001",
                    territorioId="TERR-001",
                    vendedorId=1,
                    objetivo_cantidad=100
                ),
                MetaCreate(
                    productoId="PROD-002",
                    territorioId="TERR-002",
                    vendedorId=2,
                    objetivo_cantidad=200
                )
            ]
        )
        
        assert len(plan.territorios) == 2
        assert len(plan.metas) == 2
    
    def test_plan_nombre_requerido(self):
        """Debe rechazar si falta nombre"""
        with pytest.raises(ValidationError) as exc_info:
            PlanVentaCreate(
                periodo={"desde": "2025-01-01", "hasta": "2025-03-31"},
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
        
        assert "nombre" in str(exc_info.value)
    
    def test_plan_nombre_no_vacio(self):
        """Debe rechazar nombre vacío"""
        with pytest.raises(ValidationError) as exc_info:
            PlanVentaCreate(
                nombre="",
                periodo={"desde": "2025-01-01", "hasta": "2025-03-31"},
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
        
        assert "nombre" in str(exc_info.value)
    
    def test_plan_nombre_max_255_caracteres(self):
        """Debe rechazar nombre mayor a 255 caracteres"""
        with pytest.raises(ValidationError) as exc_info:
            PlanVentaCreate(
                nombre="X" * 256,
                periodo={"desde": "2025-01-01", "hasta": "2025-03-31"},
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
        
        assert "nombre" in str(exc_info.value)
    
    def test_plan_periodo_requerido(self):
        """Debe rechazar si falta periodo"""
        with pytest.raises(ValidationError) as exc_info:
            PlanVentaCreate(
                nombre="Plan Q1",
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
        
        assert "periodo" in str(exc_info.value)
    
    def test_plan_periodo_formato_valido(self):
        """Debe validar formato de período"""
        with pytest.raises(ValidationError) as exc_info:
            PlanVentaCreate(
                nombre="Plan Q1",
                periodo={"desde": "invalid"},  # Formato inválido
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
        
        assert "periodo" in str(exc_info.value).lower()
    
    def test_plan_periodo_hasta_mayor_desde(self):
        """Debe rechazar si hasta < desde"""
        with pytest.raises(ValidationError) as exc_info:
            PlanVentaCreate(
                nombre="Plan Q1",
                periodo={"desde": "2025-12-31", "hasta": "2025-01-01"},
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
        
        assert "hasta" in str(exc_info.value).lower() or "mayor" in str(exc_info.value).lower()
    
    def test_plan_territorios_requeridos(self):
        """Debe rechazar si falta territorios"""
        with pytest.raises(ValidationError) as exc_info:
            PlanVentaCreate(
                nombre="Plan Q1",
                periodo={"desde": "2025-01-01", "hasta": "2025-03-31"},
                metas=[
                    MetaCreate(
                        productoId="PROD-001",
                        territorioId="TERR-001",
                        vendedorId=1,
                        objetivo_cantidad=100
                    )
                ]
            )
        
        assert "territorios" in str(exc_info.value)
    
    def test_plan_territorios_no_vacio(self):
        """Debe rechazar lista vacía de territorios"""
        with pytest.raises(ValidationError) as exc_info:
            PlanVentaCreate(
                nombre="Plan Q1",
                periodo={"desde": "2025-01-01", "hasta": "2025-03-31"},
                territorios=[],
                metas=[
                    MetaCreate(
                        productoId="PROD-001",
                        territorioId="TERR-001",
                        vendedorId=1,
                        objetivo_cantidad=100
                    )
                ]
            )
        
        errors = str(exc_info.value)
        assert "territorios" in errors or "min_items" in errors.lower()
    
    def test_plan_metas_requeridas(self):
        """Debe rechazar si faltan metas"""
        with pytest.raises(ValidationError) as exc_info:
            PlanVentaCreate(
                nombre="Plan Q1",
                periodo={"desde": "2025-01-01", "hasta": "2025-03-31"},
                territorios=["TERR-001"]
            )
        
        assert "metas" in str(exc_info.value)
    
    def test_plan_metas_no_vacio(self):
        """Debe rechazar lista vacía de metas"""
        with pytest.raises(ValidationError) as exc_info:
            PlanVentaCreate(
                nombre="Plan Q1",
                periodo={"desde": "2025-01-01", "hasta": "2025-03-31"},
                territorios=["TERR-001"],
                metas=[]
            )
        
        errors = str(exc_info.value)
        assert "metas" in errors or "min_items" in errors.lower()


# Removido TestPeriodoVentaSchema y TestEstadoPlanEnum ya que no existen en el schema actual

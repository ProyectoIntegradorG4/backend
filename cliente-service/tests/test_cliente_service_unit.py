import pytest
from unittest.mock import Mock, patch
from app.services.cliente_service import ClienteService
from app.models.cliente import Cliente, TipoInstitucion
from fastapi import HTTPException


class TestClienteService:
    """Tests unitarios para ClienteService"""

    def test_get_tipos_institucion(self, db_session):
        """Test: Obtener tipos de institución"""
        service = ClienteService(db_session)
        result = service.get_tipos_institucion()
        
        assert len(result.tipos) == 6
        assert "Hospital" in result.tipos
        assert "Clínica" in result.tipos
        assert "IPS" in result.tipos

    def test_get_cliente_by_nit_existente(self, db_session):
        """Test: Buscar cliente por NIT existente"""
        # Crear cliente
        cliente = Cliente(
            nit="800123456-1",
            nombre_comercial="Test Hospital",
            razon_social="Test Hospital SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        db_session.add(cliente)
        db_session.commit()
        
        service = ClienteService(db_session)
        result = service.get_cliente_by_nit("800123456-1")
        
        assert result is not None
        assert result.nombre_comercial == "Test Hospital"

    def test_get_cliente_by_nit_no_existe(self, db_session):
        """Test: Buscar cliente por NIT que no existe"""
        service = ClienteService(db_session)
        result = service.get_cliente_by_nit("999999999-9")
        
        assert result is None

    def test_get_clientes_by_gerente_sin_filtros(self, db_session):
        """Test: Obtener clientes sin filtros"""
        # Crear clientes
        for i in range(3):
            cliente = Cliente(
                nit=f"80012345{i}-1",
                nombre_comercial=f"Cliente {i}",
                razon_social=f"Cliente {i} SAS",
                tipo_institucion=TipoInstitucion.HOSPITAL.value,
                pais="Colombia",
                activo=True
            )
            db_session.add(cliente)
        db_session.commit()
        
        service = ClienteService(db_session)
        result = service.get_clientes_by_gerente(
            gerente_id=1,
            gerente_pais="Colombia"
        )
        
        assert result.total == 3
        assert len(result.clientes) == 3

    def test_get_clientes_by_gerente_con_filtro_tipo(self, db_session):
        """Test: Filtrar clientes por tipo de institución"""
        # Crear clientes de diferentes tipos
        cliente1 = Cliente(
            nit="800111111-1",
            nombre_comercial="Hospital",
            razon_social="Hospital SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        cliente2 = Cliente(
            nit="800222222-2",
            nombre_comercial="Clínica",
            razon_social="Clínica Ltda",
            tipo_institucion=TipoInstitucion.CLINICA.value,
            pais="Colombia",
            activo=True
        )
        db_session.add_all([cliente1, cliente2])
        db_session.commit()
        
        service = ClienteService(db_session)
        result = service.get_clientes_by_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            tipo_institucion=TipoInstitucion.HOSPITAL.value
        )
        
        assert result.total == 1
        assert result.clientes[0].tipo_institucion == "Hospital"

    def test_get_clientes_by_gerente_con_search(self, db_session):
        """Test: Buscar clientes por texto"""
        cliente = Cliente(
            nit="800123456-1",
            nombre_comercial="Hospital San Juan",
            razon_social="Hospital San Juan de Dios",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            ciudad="Bogotá",
            activo=True
        )
        db_session.add(cliente)
        db_session.commit()
        
        service = ClienteService(db_session)
        
        # Buscar por nombre
        result = service.get_clientes_by_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            search="San Juan"
        )
        assert result.total == 1
        
        # Buscar por ciudad
        result = service.get_clientes_by_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            search="Bogotá"
        )
        assert result.total == 1

    def test_get_clientes_paginacion(self, db_session):
        """Test: Paginación de clientes"""
        # Crear 10 clientes
        for i in range(10):
            cliente = Cliente(
                nit=f"80000000{i:02d}-1",
                nombre_comercial=f"Cliente {i:02d}",
                razon_social=f"Cliente {i:02d} SAS",
                tipo_institucion=TipoInstitucion.HOSPITAL.value,
                pais="Colombia",
                activo=True
            )
            db_session.add(cliente)
        db_session.commit()
        
        service = ClienteService(db_session)
        
        # Primera página
        result = service.get_clientes_by_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            page=1,
            limit=5
        )
        assert result.total == 10
        assert len(result.clientes) == 5
        assert result.page == 1
        
        # Segunda página
        result = service.get_clientes_by_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            page=2,
            limit=5
        )
        assert result.total == 10
        assert len(result.clientes) == 5
        assert result.page == 2

    def test_get_cliente_detail_existente(self, db_session):
        """Test: Obtener detalle de cliente existente"""
        cliente = Cliente(
            nit="800123456-1",
            nombre_comercial="Hospital Test",
            razon_social="Hospital Test SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        db_session.add(cliente)
        db_session.commit()
        db_session.refresh(cliente)
        
        service = ClienteService(db_session)
        result = service.get_cliente_detail(
            cliente_id=cliente.cliente_id,
            gerente_id=1,
            gerente_pais="Colombia"
        )
        
        assert result.cliente_id == cliente.cliente_id
        assert result.nombre_comercial == "Hospital Test"

    def test_get_cliente_detail_otro_pais(self, db_session):
        """Test: No se puede acceder a cliente de otro país"""
        cliente = Cliente(
            nit="800123456-1",
            nombre_comercial="Hospital Peru",
            razon_social="Hospital Peru SAC",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Peru",
            activo=True
        )
        db_session.add(cliente)
        db_session.commit()
        db_session.refresh(cliente)
        
        service = ClienteService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_cliente_detail(
                cliente_id=cliente.cliente_id,
                gerente_id=1,
                gerente_pais="Colombia"
            )
        
        assert exc_info.value.status_code == 404

    def test_verify_gerente_access_mismo_pais(self, db_session):
        """Test: Verificar acceso de gerente a cliente del mismo país"""
        cliente = Cliente(
            nit="800123456-1",
            nombre_comercial="Hospital Test",
            razon_social="Hospital Test SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        db_session.add(cliente)
        db_session.commit()
        db_session.refresh(cliente)
        
        service = ClienteService(db_session)
        result = service.verify_gerente_access(
            gerente_id=1,
            cliente_id=cliente.cliente_id,
            gerente_pais="Colombia"
        )
        
        assert result is True

    def test_verify_gerente_access_otro_pais(self, db_session):
        """Test: Verificar que gerente no tiene acceso a cliente de otro país"""
        cliente = Cliente(
            nit="800123456-1",
            nombre_comercial="Hospital Peru",
            razon_social="Hospital Peru SAC",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Peru",
            activo=True
        )
        db_session.add(cliente)
        db_session.commit()
        db_session.refresh(cliente)
        
        service = ClienteService(db_session)
        result = service.verify_gerente_access(
            gerente_id=1,
            cliente_id=cliente.cliente_id,
            gerente_pais="Colombia"
        )
        
        assert result is False

    def test_filtrar_solo_activos(self, db_session):
        """Test: Solo se retornan clientes activos por defecto"""
        cliente_activo = Cliente(
            nit="800111111-1",
            nombre_comercial="Cliente Activo",
            razon_social="Cliente Activo SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        cliente_inactivo = Cliente(
            nit="800222222-2",
            nombre_comercial="Cliente Inactivo",
            razon_social="Cliente Inactivo SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=False
        )
        db_session.add_all([cliente_activo, cliente_inactivo])
        db_session.commit()
        
        service = ClienteService(db_session)
        result = service.get_clientes_by_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            activo=True
        )
        
        assert result.total == 1
        assert result.clientes[0].activo is True

    def test_clientes_diferentes_paises(self, db_session):
        """Test: Gerentes de diferentes países ven diferentes clientes"""
        cliente_colombia = Cliente(
            nit="800111111-1",
            nombre_comercial="Hospital Colombia",
            razon_social="Hospital Colombia SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        cliente_peru = Cliente(
            nit="800222222-2",
            nombre_comercial="Hospital Peru",
            razon_social="Hospital Peru SAC",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Peru",
            activo=True
        )
        cliente_mexico = Cliente(
            nit="800333333-3",
            nombre_comercial="Hospital Mexico",
            razon_social="Hospital Mexico SA de CV",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Mexico",
            activo=True
        )
        db_session.add_all([cliente_colombia, cliente_peru, cliente_mexico])
        db_session.commit()
        
        service = ClienteService(db_session)
        
        # Gerente de Colombia
        result_colombia = service.get_clientes_by_gerente(
            gerente_id=1,
            gerente_pais="Colombia"
        )
        assert result_colombia.total == 1
        assert result_colombia.clientes[0].pais == "Colombia"
        
        # Gerente de Peru
        result_peru = service.get_clientes_by_gerente(
            gerente_id=2,
            gerente_pais="Peru"
        )
        assert result_peru.total == 1
        assert result_peru.clientes[0].pais == "Peru"


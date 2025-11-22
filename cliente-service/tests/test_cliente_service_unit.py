import pytest
from unittest.mock import Mock, patch
from app.services.cliente_service import ClienteService
from app.models.cliente import Cliente, TipoInstitucion, GerenteClienteAsignacion
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
        """Test: Obtener clientes asignados a gerente sin filtros"""
        # Crear clientes y asignaciones
        clientes = []
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
            clientes.append(cliente)
        db_session.commit()
        
        # Crear asignaciones
        for cliente in clientes:
            asignacion = GerenteClienteAsignacion(
                gerente_id=1,
                cliente_id=cliente.cliente_id,
                nit=cliente.nit,
                pais="Colombia",
                activo=True
            )
            db_session.add(asignacion)
        db_session.commit()
        
        service = ClienteService(db_session)
        result = service.get_clientes_asignados_a_gerente(
            gerente_id=1,
            gerente_pais="Colombia"
        )
        
        assert result.total == 3
        assert len(result.clientes) == 3

    def test_get_clientes_by_gerente_con_filtro_tipo(self, db_session):
        """Test: Filtrar clientes asignados por tipo de institución"""
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
        
        # Crear asignaciones
        for cliente in [cliente1, cliente2]:
            asignacion = GerenteClienteAsignacion(
                gerente_id=1,
                cliente_id=cliente.cliente_id,
                nit=cliente.nit,
                pais="Colombia",
                activo=True
            )
            db_session.add(asignacion)
        db_session.commit()
        
        service = ClienteService(db_session)
        result = service.get_clientes_asignados_a_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            tipo_institucion=TipoInstitucion.HOSPITAL.value
        )
        
        assert result.total == 1
        assert result.clientes[0].tipo_institucion == "Hospital"

    def test_get_clientes_by_gerente_con_search(self, db_session):
        """Test: Buscar clientes asignados por texto"""
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
        
        # Crear asignación
        asignacion = GerenteClienteAsignacion(
            gerente_id=1,
            cliente_id=cliente.cliente_id,
            nit=cliente.nit,
            pais="Colombia",
            activo=True
        )
        db_session.add(asignacion)
        db_session.commit()
        
        service = ClienteService(db_session)
        
        # Buscar por nombre
        result = service.get_clientes_asignados_a_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            search="San Juan"
        )
        assert result.total == 1
        
        # Buscar por ciudad
        result = service.get_clientes_asignados_a_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            search="Bogotá"
        )
        assert result.total == 1

    def test_get_clientes_paginacion(self, db_session):
        """Test: Paginación de clientes asignados"""
        # Crear 10 clientes
        clientes = []
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
            clientes.append(cliente)
        db_session.commit()
        
        # Crear asignaciones
        for cliente in clientes:
            asignacion = GerenteClienteAsignacion(
                gerente_id=1,
                cliente_id=cliente.cliente_id,
                nit=cliente.nit,
                pais="Colombia",
                activo=True
            )
            db_session.add(asignacion)
        db_session.commit()
        
        service = ClienteService(db_session)
        
        # Primera página
        result = service.get_clientes_asignados_a_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            page=1,
            limit=5
        )
        assert result.total == 10
        assert len(result.clientes) == 5
        assert result.page == 1
        
        # Segunda página
        result = service.get_clientes_asignados_a_gerente(
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
        """Test: Solo se retornan clientes activos asignados por defecto"""
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
        
        # Crear asignaciones solo para el activo
        asignacion = GerenteClienteAsignacion(
            gerente_id=1,
            cliente_id=cliente_activo.cliente_id,
            nit=cliente_activo.nit,
            pais="Colombia",
            activo=True
        )
        db_session.add(asignacion)
        db_session.commit()
        
        service = ClienteService(db_session)
        result = service.get_clientes_asignados_a_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            activo=True
        )
        
        assert result.total == 1
        assert result.clientes[0].activo is True

    def test_clientes_diferentes_paises(self, db_session):
        """Test: Gerentes de diferentes países ven diferentes clientes asignados"""
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
        
        # Crear asignaciones
        asignacion_col = GerenteClienteAsignacion(
            gerente_id=1,
            cliente_id=cliente_colombia.cliente_id,
            nit=cliente_colombia.nit,
            pais="Colombia",
            activo=True
        )
        asignacion_peru = GerenteClienteAsignacion(
            gerente_id=2,
            cliente_id=cliente_peru.cliente_id,
            nit=cliente_peru.nit,
            pais="Peru",
            activo=True
        )
        db_session.add_all([asignacion_col, asignacion_peru])
        db_session.commit()
        
        service = ClienteService(db_session)
        
        # Gerente de Colombia
        result_colombia = service.get_clientes_asignados_a_gerente(
            gerente_id=1,
            gerente_pais="Colombia"
        )
        assert result_colombia.total == 1
        assert result_colombia.clientes[0].pais == "Colombia"
        
        # Gerente de Peru
        result_peru = service.get_clientes_asignados_a_gerente(
            gerente_id=2,
            gerente_pais="Peru"
        )
        assert result_peru.total == 1
        assert result_peru.clientes[0].pais == "Peru"

    def test_get_clientes_simple_sin_filtros(self, db_session):
        """Test: Obtener clientes sin filtros usando get_clientes_simple"""
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
        result = service.get_clientes_simple()
        
        assert result.total == 3
        assert len(result.clientes) == 3

    def test_get_clientes_simple_con_filtro_pais(self, db_session):
        """Test: Filtrar clientes por país usando get_clientes_simple"""
        cliente_colombia = Cliente(
            nit="800111111-1",
            nombre_comercial="Cliente Colombia",
            razon_social="Cliente Colombia SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        cliente_peru = Cliente(
            nit="800222222-2",
            nombre_comercial="Cliente Peru",
            razon_social="Cliente Peru SAC",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Peru",
            activo=True
        )
        db_session.add_all([cliente_colombia, cliente_peru])
        db_session.commit()
        
        service = ClienteService(db_session)
        result = service.get_clientes_simple(pais="Colombia")
        
        assert result.total == 1
        assert result.clientes[0].pais == "Colombia"

    def test_get_clientes_simple_con_filtro_tipo(self, db_session):
        """Test: Filtrar clientes por tipo usando get_clientes_simple"""
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
        result = service.get_clientes_simple(tipo_institucion="Hospital")
        
        assert result.total == 1
        assert result.clientes[0].tipo_institucion == "Hospital"

    def test_get_clientes_simple_con_search(self, db_session):
        """Test: Buscar clientes por texto usando get_clientes_simple"""
        cliente = Cliente(
            nit="800123456-1",
            nombre_comercial="Hospital San Juan",
            razon_social="Hospital San Juan de Dios",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            ciudad="Bogotá",
            direccion="Calle 10",
            activo=True
        )
        db_session.add(cliente)
        db_session.commit()
        
        service = ClienteService(db_session)
        
        # Buscar por nombre
        result = service.get_clientes_simple(search="San Juan")
        assert result.total == 1
        
        # Buscar por ciudad
        result = service.get_clientes_simple(search="Bogotá")
        assert result.total == 1
        
        # Buscar por dirección
        result = service.get_clientes_simple(search="Calle 10")
        assert result.total == 1

    def test_get_clientes_simple_paginacion(self, db_session):
        """Test: Paginación usando get_clientes_simple"""
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
        result = service.get_clientes_simple(page=1, limit=5)
        assert result.total == 10
        assert len(result.clientes) == 5
        assert result.page == 1
        
        # Segunda página
        result = service.get_clientes_simple(page=2, limit=5)
        assert result.total == 10
        assert len(result.clientes) == 5
        assert result.page == 2

    def test_get_clientes_simple_filtrar_inactivos(self, db_session):
        """Test: Filtrar clientes inactivos usando get_clientes_simple"""
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
        
        # Solo activos (default)
        result = service.get_clientes_simple(activo=True)
        assert result.total == 1
        
        # Solo inactivos
        result = service.get_clientes_simple(activo=False)
        assert result.total == 1

    def test_get_cliente_detail_simple_existente(self, db_session):
        """Test: Obtener detalle de cliente usando get_cliente_detail_simple"""
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
        result = service.get_cliente_detail_simple(cliente_id=cliente.cliente_id)
        
        assert result.cliente_id == cliente.cliente_id
        assert result.nombre_comercial == "Hospital Test"

    def test_get_cliente_detail_simple_no_existe(self, db_session):
        """Test: Cliente no encontrado usando get_cliente_detail_simple"""
        service = ClienteService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_cliente_detail_simple(cliente_id=99999)
        
        assert exc_info.value.status_code == 404

    def test_get_gerente_nits(self, db_session):
        """Test: Obtener NITs de un gerente"""
        # Crear clientes
        cliente1 = Cliente(
            nit="800111111-1",
            nombre_comercial="Cliente 1",
            razon_social="Cliente 1 SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        cliente2 = Cliente(
            nit="800222222-2",
            nombre_comercial="Cliente 2",
            razon_social="Cliente 2 SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        # Cliente con mismo NIT (diferente sede)
        cliente3 = Cliente(
            nit="800111111-1",
            nombre_comercial="Cliente 3",
            razon_social="Cliente 3 SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        db_session.add_all([cliente1, cliente2, cliente3])
        db_session.commit()
        
        # Crear asignaciones
        asignacion1 = GerenteClienteAsignacion(
            gerente_id=1,
            cliente_id=cliente1.cliente_id,
            nit="800111111-1",
            pais="Colombia",
            activo=True
        )
        asignacion2 = GerenteClienteAsignacion(
            gerente_id=1,
            cliente_id=cliente2.cliente_id,
            nit="800222222-2",
            pais="Colombia",
            activo=True
        )
        asignacion3 = GerenteClienteAsignacion(
            gerente_id=1,
            cliente_id=cliente3.cliente_id,
            nit="800111111-1",
            pais="Colombia",
            activo=True
        )
        db_session.add_all([asignacion1, asignacion2, asignacion3])
        db_session.commit()
        
        service = ClienteService(db_session)
        nits = service.get_gerente_nits(gerente_id=1)
        
        # Debe retornar NITs únicos
        assert len(nits) == 2
        assert "800111111-1" in nits
        assert "800222222-2" in nits

    def test_get_gerente_nits_sin_asignaciones(self, db_session):
        """Test: Obtener NITs de gerente sin asignaciones"""
        service = ClienteService(db_session)
        nits = service.get_gerente_nits(gerente_id=999)
        
        assert len(nits) == 0
        assert nits == []

    def test_get_gerente_cliente_ids(self, db_session):
        """Test: Obtener cliente_ids de un gerente"""
        # Crear clientes
        cliente1 = Cliente(
            nit="800111111-1",
            nombre_comercial="Cliente 1",
            razon_social="Cliente 1 SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        cliente2 = Cliente(
            nit="800222222-2",
            nombre_comercial="Cliente 2",
            razon_social="Cliente 2 SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        db_session.add_all([cliente1, cliente2])
        db_session.commit()
        
        # Crear asignaciones
        asignacion1 = GerenteClienteAsignacion(
            gerente_id=1,
            cliente_id=cliente1.cliente_id,
            nit="800111111-1",
            pais="Colombia",
            activo=True
        )
        asignacion2 = GerenteClienteAsignacion(
            gerente_id=1,
            cliente_id=cliente2.cliente_id,
            nit="800222222-2",
            pais="Colombia",
            activo=True
        )
        db_session.add_all([asignacion1, asignacion2])
        db_session.commit()
        
        service = ClienteService(db_session)
        cliente_ids = service.get_gerente_cliente_ids(gerente_id=1)
        
        assert len(cliente_ids) == 2
        assert cliente1.cliente_id in cliente_ids
        assert cliente2.cliente_id in cliente_ids

    def test_get_gerente_cliente_ids_sin_asignaciones(self, db_session):
        """Test: Obtener cliente_ids de gerente sin asignaciones"""
        service = ClienteService(db_session)
        cliente_ids = service.get_gerente_cliente_ids(gerente_id=999)
        
        assert len(cliente_ids) == 0
        assert cliente_ids == []

    def test_create_asignacion(self, db_session):
        """Test: Crear asignación de cliente a gerente"""
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
        asignacion = service.create_asignacion(
            gerente_id=1,
            cliente_id=cliente.cliente_id,
            pais="Colombia"
        )
        
        assert asignacion.gerente_id == 1
        assert asignacion.cliente_id == cliente.cliente_id
        assert asignacion.pais == "Colombia"
        assert asignacion.activo is True

    def test_create_asignacion_duplicada(self, db_session):
        """Test: Crear asignación duplicada debe fallar"""
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
        
        # Crear primera asignación
        service.create_asignacion(
            gerente_id=1,
            cliente_id=cliente.cliente_id,
            pais="Colombia"
        )
        
        # Intentar crear duplicada
        with pytest.raises(HTTPException) as exc_info:
            service.create_asignacion(
                gerente_id=1,
                cliente_id=cliente.cliente_id,
                pais="Colombia"
            )
        
        assert exc_info.value.status_code == 409

    def test_get_clientes_asignados_a_gerente_sin_resultados(self, db_session):
        """Test: Obtener clientes asignados cuando no hay resultados"""
        service = ClienteService(db_session)
        result = service.get_clientes_asignados_a_gerente(
            gerente_id=999,
            gerente_pais="Colombia"
        )
        
        assert result.total == 0
        assert len(result.clientes) == 0

    def test_get_clientes_asignados_a_gerente_combinacion_filtros(self, db_session):
        """Test: Combinación de filtros en get_clientes_asignados_a_gerente"""
        cliente1 = Cliente(
            nit="800111111-1",
            nombre_comercial="Hospital San Juan",
            razon_social="Hospital San Juan SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            ciudad="Bogotá",
            activo=True
        )
        cliente2 = Cliente(
            nit="800222222-2",
            nombre_comercial="Clínica Central",
            razon_social="Clínica Central Ltda",
            tipo_institucion=TipoInstitucion.CLINICA.value,
            pais="Colombia",
            ciudad="Medellín",
            activo=True
        )
        db_session.add_all([cliente1, cliente2])
        db_session.commit()
        
        # Crear asignaciones
        for cliente in [cliente1, cliente2]:
            asignacion = GerenteClienteAsignacion(
                gerente_id=1,
                cliente_id=cliente.cliente_id,
                nit=cliente.nit,
                pais="Colombia",
                activo=True
            )
            db_session.add(asignacion)
        db_session.commit()
        
        service = ClienteService(db_session)
        
        # Filtrar por tipo y búsqueda
        result = service.get_clientes_asignados_a_gerente(
            gerente_id=1,
            gerente_pais="Colombia",
            tipo_institucion="Hospital",
            search="San Juan"
        )
        assert result.total == 1
        assert result.clientes[0].tipo_institucion == "Hospital"

    @patch('app.services.cliente_service.create_engine')
    def test_validate_nit_institucion_valido(self, mock_create_engine, db_session):
        """Test: Validar NIT válido y activo"""
        # Mock de conexión a nit_db
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.nit = "800123456-1"
        mock_result.nombre_institucion = "Test Hospital"
        mock_result.pais = "Colombia"
        mock_result.activo = True
        mock_conn.execute.return_value.fetchone.return_value = mock_result
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_engine.dispose = Mock()
        mock_create_engine.return_value = mock_engine
        
        service = ClienteService(db_session)
        es_valido, mensaje = service.validate_nit_institucion("800123456-1", "Colombia")
        
        assert es_valido is True
        assert mensaje is None

    @patch('app.services.cliente_service.create_engine')
    def test_validate_nit_institucion_no_existe(self, mock_create_engine, db_session):
        """Test: Validar NIT que no existe"""
        # Mock de conexión a nit_db
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = None
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_engine.dispose = Mock()
        mock_create_engine.return_value = mock_engine
        
        service = ClienteService(db_session)
        es_valido, mensaje = service.validate_nit_institucion("999999999-9")
        
        assert es_valido is False
        assert "no existe" in mensaje.lower()

    @patch('app.services.cliente_service.create_engine')
    def test_validate_nit_institucion_inactivo(self, mock_create_engine, db_session):
        """Test: Validar NIT inactivo"""
        # Mock de conexión a nit_db
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.nit = "800123456-1"
        mock_result.nombre_institucion = "Test Hospital"
        mock_result.pais = "Colombia"
        mock_result.activo = False
        mock_conn.execute.return_value.fetchone.return_value = mock_result
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_engine.dispose = Mock()
        mock_create_engine.return_value = mock_engine
        
        service = ClienteService(db_session)
        es_valido, mensaje = service.validate_nit_institucion("800123456-1")
        
        assert es_valido is False
        assert "inactiva" in mensaje.lower()

    @patch('app.services.cliente_service.create_engine')
    def test_validate_nit_institucion_pais_no_coincide(self, mock_create_engine, db_session):
        """Test: Validar NIT con país que no coincide"""
        # Mock de conexión a nit_db
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.nit = "800123456-1"
        mock_result.nombre_institucion = "Test Hospital"
        mock_result.pais = "Colombia"
        mock_result.activo = True
        mock_conn.execute.return_value.fetchone.return_value = mock_result
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_engine.dispose = Mock()
        mock_create_engine.return_value = mock_engine
        
        service = ClienteService(db_session)
        es_valido, mensaje = service.validate_nit_institucion("800123456-1", "Peru")
        
        assert es_valido is False
        assert "no coincide" in mensaje.lower()

    @patch('app.services.cliente_service.create_engine')
    def test_validate_nit_institucion_error_conexion(self, mock_create_engine, db_session):
        """Test: Manejo de error en conexión"""
        mock_create_engine.side_effect = Exception("Error de conexión")
        
        service = ClienteService(db_session)
        es_valido, mensaje = service.validate_nit_institucion("800123456-1")
        
        assert es_valido is False
        assert "error" in mensaje.lower()

    @patch('app.services.cliente_service.create_engine')
    def test_get_gerente_pais_valido(self, mock_create_engine, db_session):
        """Test: Obtener país de gerente con NIT válido"""
        # Mock de conexión a user_db
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.nit = "111111111-1"
        mock_conn.execute.return_value.fetchone.return_value = mock_result
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_engine.dispose = Mock()
        mock_create_engine.return_value = mock_engine
        
        service = ClienteService(db_session)
        pais = service.get_gerente_pais(gerente_id=1)
        
        assert pais == "Colombia"

    @patch('app.services.cliente_service.create_engine')
    def test_get_gerente_pais_sin_nit(self, mock_create_engine, db_session):
        """Test: Obtener país de gerente sin NIT"""
        # Mock de conexión a user_db
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = None
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_engine.dispose = Mock()
        mock_create_engine.return_value = mock_engine
        
        service = ClienteService(db_session)
        pais = service.get_gerente_pais(gerente_id=999)
        
        assert pais is None

    @patch('app.services.cliente_service.create_engine')
    def test_get_gerente_pais_nit_no_en_mapeo(self, mock_create_engine, db_session):
        """Test: Obtener país de gerente con NIT no en mapeo"""
        # Mock de conexión a user_db
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.nit = "999999999-9"
        mock_conn.execute.return_value.fetchone.return_value = mock_result
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_engine.dispose = Mock()
        mock_create_engine.return_value = mock_engine
        
        service = ClienteService(db_session)
        pais = service.get_gerente_pais(gerente_id=999)
        
        assert pais is None

    @patch('app.services.cliente_service.create_engine')
    def test_get_gerente_pais_error_conexion(self, mock_create_engine, db_session):
        """Test: Manejo de error en conexión para get_gerente_pais"""
        mock_create_engine.side_effect = Exception("Error de conexión")
        
        service = ClienteService(db_session)
        pais = service.get_gerente_pais(gerente_id=1)
        
        assert pais is None


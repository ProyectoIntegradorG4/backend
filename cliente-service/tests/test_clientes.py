import pytest
from app.models.cliente import Cliente, TipoInstitucion


class TestClientesAPI:
    """Tests de integración para endpoints de clientes"""

    def test_health_check(self, client):
        """Test del endpoint de health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cliente-service"

    # Nota: Los endpoints actualmente NO requieren autenticación (modo desarrollo)
    # Estos tests se comentan hasta que se implemente autenticación
    # def test_get_clientes_sin_token(self, client):
    #     """Test: Acceder sin token debe retornar 401"""
    #     response = client.get("/api/v1/clientes/mis-clientes")
    #     assert response.status_code == 401
    #     assert "Token no proporcionado" in response.json()["detail"]

    # def test_get_clientes_token_invalido(self, client):
    #     """Test: Token inválido debe retornar 401"""
    #     response = client.get(
    #         "/api/v1/clientes/mis-clientes",
    #         headers={"Authorization": "Bearer token_invalido"}
    #     )
    #     assert response.status_code == 401

    # def test_get_clientes_rol_incorrecto(self, client, mock_jwt_token_wrong_role):
    #     """Test: Usuario sin rol gerente_cuenta debe retornar 403"""
    #     response = client.get(
    #         "/api/v1/clientes/mis-clientes",
    #         headers={"Authorization": mock_jwt_token_wrong_role}
    #     )
    #     assert response.status_code == 403
    #     assert "gerente_cuenta" in response.json()["detail"]

    def test_get_clientes_vacio(self, client, db_session):
        """Test: Lista vacía cuando no hay clientes"""
        response = client.get("/api/v1/clientes/mis-clientes")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["clientes"] == []

    def test_get_clientes_con_datos(self, client, db_session, sample_cliente_data):
        """Test: Retornar lista de clientes correctamente"""
        # Crear cliente de prueba en Colombia
        cliente = Cliente(**sample_cliente_data)
        db_session.add(cliente)
        db_session.commit()
        
        response = client.get("/api/v1/clientes/mis-clientes?pais=Colombia")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["clientes"]) == 1
        assert data["clientes"][0]["nombre_comercial"] == "Hospital Test"
        assert data["clientes"][0]["nit"] == "800123456-1"

    def test_filtrar_por_tipo_institucion(self, client, db_session):
        """Test: Filtrar clientes por tipo de institución"""
        # Crear clientes de diferentes tipos
        cliente1 = Cliente(
            nit="800111111-1",
            nombre_comercial="Hospital Uno",
            razon_social="Hospital Uno SAS",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        cliente2 = Cliente(
            nit="800222222-2",
            nombre_comercial="Clínica Dos",
            razon_social="Clínica Dos Ltda",
            tipo_institucion=TipoInstitucion.CLINICA.value,
            pais="Colombia",
            activo=True
        )
        db_session.add_all([cliente1, cliente2])
        db_session.commit()
        
        response = client.get("/api/v1/clientes/mis-clientes?pais=Colombia&tipo_institucion=Hospital")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["clientes"][0]["tipo_institucion"] == "Hospital"

    def test_buscar_por_nombre(self, client, db_session):
        """Test: Buscar clientes por nombre"""
        cliente = Cliente(
            nit="800123456-1",
            nombre_comercial="Hospital San Juan",
            razon_social="Hospital San Juan de Dios",
            tipo_institucion=TipoInstitucion.HOSPITAL.value,
            pais="Colombia",
            activo=True
        )
        db_session.add(cliente)
        db_session.commit()
        
        response = client.get("/api/v1/clientes/mis-clientes?pais=Colombia&search=San Juan")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "San Juan" in data["clientes"][0]["nombre_comercial"]

    def test_paginacion(self, client, db_session):
        """Test: Paginación funciona correctamente"""
        # Crear 5 clientes
        for i in range(5):
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
        
        # Primera página con 3 elementos
        response = client.get("/api/v1/clientes/mis-clientes?pais=Colombia&page=1&limit=3")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["clientes"]) == 3
        assert data["page"] == 1
        assert data["limit"] == 3

    def test_get_cliente_detail(self, client, db_session, sample_cliente_data):
        """Test: Obtener detalle de un cliente"""
        cliente = Cliente(**sample_cliente_data)
        db_session.add(cliente)
        db_session.commit()
        db_session.refresh(cliente)
        
        response = client.get(f"/api/v1/clientes/{cliente.cliente_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cliente_id"] == cliente.cliente_id
        assert data["nombre_comercial"] == "Hospital Test"
        assert data["email"] == "test@hospital.com"

    def test_get_cliente_detail_no_encontrado(self, client, db_session):
        """Test: Cliente no encontrado retorna 404"""
        # Asegurar que las tablas existen
        from app.models.cliente import Base
        Base.metadata.create_all(bind=db_session.bind)
        
        response = client.get("/api/v1/clientes/99999")
        
        assert response.status_code == 404

    def test_get_tipos_institucion(self, client):
        """Test: Obtener tipos de institución disponibles"""
        response = client.get("/api/v1/clientes/tipos-institucion")
        
        assert response.status_code == 200
        data = response.json()
        assert "tipos" in data
        assert "Hospital" in data["tipos"]
        assert "Clínica" in data["tipos"]
        assert len(data["tipos"]) == 6  # 6 tipos definidos en el enum

    def test_filtrar_por_pais(self, client, db_session):
        """Test: Filtrar clientes por país"""
        # Crear clientes en diferentes países
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
        db_session.add_all([cliente_colombia, cliente_peru])
        db_session.commit()
        
        # Filtrar por Colombia
        response = client.get("/api/v1/clientes/mis-clientes?pais=Colombia")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["clientes"][0]["pais"] == "Colombia"

    def test_filtrar_solo_activos(self, client, db_session):
        """Test: Por defecto solo se muestran clientes activos"""
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
        
        response = client.get("/api/v1/clientes/mis-clientes?pais=Colombia")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["clientes"][0]["activo"] is True

    def test_get_mis_clientes_sin_gerente_id(self, client, db_session):
        """Test: Obtener clientes sin especificar gerente_id"""
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
        
        response = client.get("/api/v1/clientes/mis-clientes?pais=Colombia")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_mis_clientes_con_gerente_id(self, client, db_session):
        """Test: Obtener clientes con gerente_id"""
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
        
        from app.models.cliente import GerenteClienteAsignacion
        from unittest.mock import patch
        
        asignacion = GerenteClienteAsignacion(
            gerente_id=1,
            cliente_id=cliente.cliente_id,
            nit=cliente.nit,
            pais="Colombia",
            activo=True
        )
        db_session.add(asignacion)
        db_session.commit()
        
        with patch('app.services.cliente_service.ClienteService.get_gerente_pais', return_value='Colombia'):
            response = client.get("/api/v1/clientes/mis-clientes?gerente_id=1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_mis_clientes_gerente_no_encontrado(self, client, db_session):
        """Test: Gerente no encontrado retorna 404"""
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_gerente_pais', return_value=None):
            response = client.get("/api/v1/clientes/mis-clientes?gerente_id=999")
        
        assert response.status_code == 404

    def test_get_gerente_nits(self, client, db_session):
        """Test: Obtener NITs de un gerente"""
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
        
        from app.models.cliente import GerenteClienteAsignacion
        
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
        
        response = client.get("/api/v1/clientes/mis-nits?gerente_id=1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["gerente_id"] == 1
        assert len(data["nits"]) == 2
        assert "800111111-1" in data["nits"]
        assert "800222222-2" in data["nits"]
        assert data["total"] == 2

    def test_get_gerente_nits_sin_asignaciones(self, client, db_session):
        """Test: Obtener NITs de gerente sin asignaciones"""
        response = client.get("/api/v1/clientes/mis-nits?gerente_id=999")
        
        assert response.status_code == 200
        data = response.json()
        assert data["gerente_id"] == 999
        assert len(data["nits"]) == 0
        assert data["total"] == 0

    def test_get_gerente_cliente_ids(self, client, db_session):
        """Test: Obtener cliente_ids de un gerente"""
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
        
        from app.models.cliente import GerenteClienteAsignacion
        
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
        
        response = client.get("/api/v1/clientes/mis-cliente-ids?gerente_id=1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["gerente_id"] == 1
        assert len(data["cliente_ids"]) == 2
        assert cliente1.cliente_id in data["cliente_ids"]
        assert cliente2.cliente_id in data["cliente_ids"]
        assert data["total"] == 2

    def test_get_gerente_cliente_ids_sin_asignaciones(self, client, db_session):
        """Test: Obtener cliente_ids de gerente sin asignaciones"""
        response = client.get("/api/v1/clientes/mis-cliente-ids?gerente_id=999")
        
        assert response.status_code == 200
        data = response.json()
        assert data["gerente_id"] == 999
        assert len(data["cliente_ids"]) == 0
        assert data["total"] == 0

    def test_get_tipos_institucion_error(self, client, db_session):
        """Test: Manejo de error en get_tipos_institucion"""
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_tipos_institucion', side_effect=Exception("Error")):
            response = client.get("/api/v1/clientes/tipos-institucion")
        
        assert response.status_code == 500

    def test_get_mis_clientes_error(self, client, db_session):
        """Test: Manejo de error en get_mis_clientes"""
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_clientes_simple', side_effect=Exception("Error")):
            response = client.get("/api/v1/clientes/mis-clientes")
        
        assert response.status_code == 500

    def test_get_cliente_detail_error(self, client, db_session):
        """Test: Manejo de error en get_cliente_detail"""
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_cliente_detail_simple', side_effect=Exception("Error")):
            response = client.get("/api/v1/clientes/1")
        
        assert response.status_code == 500


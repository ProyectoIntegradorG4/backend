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

    def test_get_clientes_sin_token(self, client):
        """Test: Acceder sin token debe retornar 401"""
        response = client.get("/api/v1/clientes/mis-clientes")
        assert response.status_code == 401
        assert "Token no proporcionado" in response.json()["detail"]

    def test_get_clientes_token_invalido(self, client):
        """Test: Token inválido debe retornar 401"""
        response = client.get(
            "/api/v1/clientes/mis-clientes",
            headers={"Authorization": "Bearer token_invalido"}
        )
        assert response.status_code == 401

    def test_get_clientes_rol_incorrecto(self, client, mock_jwt_token_wrong_role):
        """Test: Usuario sin rol gerente_cuenta debe retornar 403"""
        response = client.get(
            "/api/v1/clientes/mis-clientes",
            headers={"Authorization": mock_jwt_token_wrong_role}
        )
        assert response.status_code == 403
        assert "gerente_cuenta" in response.json()["detail"]

    def test_get_clientes_vacio(self, client, mock_jwt_token, db_session):
        """Test: Lista vacía cuando no hay clientes"""
        # Mock de get_gerente_pais para retornar Colombia
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_gerente_pais', return_value='Colombia'):
            response = client.get(
                "/api/v1/clientes/mis-clientes",
                headers={"Authorization": mock_jwt_token}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["clientes"] == []

    def test_get_clientes_con_datos(self, client, mock_jwt_token, db_session, sample_cliente_data):
        """Test: Retornar lista de clientes correctamente"""
        # Crear cliente de prueba en Colombia
        cliente = Cliente(**sample_cliente_data)
        db_session.add(cliente)
        db_session.commit()
        
        # Mock de get_gerente_pais
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_gerente_pais', return_value='Colombia'):
            response = client.get(
                "/api/v1/clientes/mis-clientes",
                headers={"Authorization": mock_jwt_token}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["clientes"]) == 1
        assert data["clientes"][0]["nombre_comercial"] == "Hospital Test"
        assert data["clientes"][0]["nit"] == "800123456-1"

    def test_filtrar_por_tipo_institucion(self, client, mock_jwt_token, db_session):
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
        
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_gerente_pais', return_value='Colombia'):
            response = client.get(
                "/api/v1/clientes/mis-clientes?tipo_institucion=Hospital",
                headers={"Authorization": mock_jwt_token}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["clientes"][0]["tipo_institucion"] == "Hospital"

    def test_buscar_por_nombre(self, client, mock_jwt_token, db_session):
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
        
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_gerente_pais', return_value='Colombia'):
            response = client.get(
                "/api/v1/clientes/mis-clientes?search=San Juan",
                headers={"Authorization": mock_jwt_token}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "San Juan" in data["clientes"][0]["nombre_comercial"]

    def test_paginacion(self, client, mock_jwt_token, db_session):
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
        
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_gerente_pais', return_value='Colombia'):
            # Primera página con 3 elementos
            response = client.get(
                "/api/v1/clientes/mis-clientes?page=1&limit=3",
                headers={"Authorization": mock_jwt_token}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["clientes"]) == 3
        assert data["page"] == 1
        assert data["limit"] == 3

    def test_get_cliente_detail(self, client, mock_jwt_token, db_session, sample_cliente_data):
        """Test: Obtener detalle de un cliente"""
        cliente = Cliente(**sample_cliente_data)
        db_session.add(cliente)
        db_session.commit()
        db_session.refresh(cliente)
        
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_gerente_pais', return_value='Colombia'):
            response = client.get(
                f"/api/v1/clientes/{cliente.cliente_id}",
                headers={"Authorization": mock_jwt_token}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["cliente_id"] == cliente.cliente_id
        assert data["nombre_comercial"] == "Hospital Test"
        assert data["email"] == "test@hospital.com"

    def test_get_cliente_detail_no_encontrado(self, client, mock_jwt_token):
        """Test: Cliente no encontrado retorna 404"""
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_gerente_pais', return_value='Colombia'):
            response = client.get(
                "/api/v1/clientes/99999",
                headers={"Authorization": mock_jwt_token}
            )
        
        assert response.status_code == 404

    def test_get_tipos_institucion(self, client, mock_jwt_token):
        """Test: Obtener tipos de institución disponibles"""
        response = client.get(
            "/api/v1/clientes/tipos-institucion",
            headers={"Authorization": mock_jwt_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tipos" in data
        assert "Hospital" in data["tipos"]
        assert "Clínica" in data["tipos"]
        assert len(data["tipos"]) == 6  # 6 tipos definidos en el enum

    def test_gerente_solo_ve_clientes_de_su_pais(self, client, mock_jwt_token, db_session):
        """Test: Gerente solo ve clientes de su país"""
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
        
        from unittest.mock import patch
        
        # Gerente de Colombia
        with patch('app.services.cliente_service.ClienteService.get_gerente_pais', return_value='Colombia'):
            response = client.get(
                "/api/v1/clientes/mis-clientes",
                headers={"Authorization": mock_jwt_token}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["clientes"][0]["pais"] == "Colombia"

    def test_filtrar_solo_activos(self, client, mock_jwt_token, db_session):
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
        
        from unittest.mock import patch
        
        with patch('app.services.cliente_service.ClienteService.get_gerente_pais', return_value='Colombia'):
            response = client.get(
                "/api/v1/clientes/mis-clientes",
                headers={"Authorization": mock_jwt_token}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["clientes"][0]["activo"] is True


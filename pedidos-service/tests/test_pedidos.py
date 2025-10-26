import pytest
from unittest.mock import patch, AsyncMock
import json

"""
Tests para los requisitos de negocio BDD especificados:

1. Gerente de Cuenta - Crear pedido con consulta de inventario en tiempo real
   - Scenario: Crear un pedido con productos en inventario
   - Scenario: Intentar crear un pedido con producto sin inventario suficiente

2. Cliente Institucional - Crear pedido basado en inventario disponible
   - Scenario: Crear pedido con productos disponibles
   - Scenario: Intentar pedir un producto sin stock
   - Scenario: Intentar pedir más unidades que las disponibles
"""

class TestCrearPedidoGerente:
    """Tests para el flujo del Gerente de Cuenta (rol: admin)"""
    
    @pytest.mark.asyncio
    async def test_crear_pedido_exitoso_con_inventario_disponible(
        self, 
        client, 
        usuario_vendedor,
        producto_disponible
    ):
        """
        Scenario: Crear un pedido con productos en inventario
        - Given: Gerente ha iniciado sesión
        - When: Agrega productos disponibles y confirma
        - Then: Pedido se crea exitosamente
        """
        # Mock de la respuesta del product-service
        mock_response = {
            "producto_id": producto_disponible["producto_id"],
            "nombre": producto_disponible["nombre"],
            "cantidad_disponible": producto_disponible["cantidad_disponible"],
            "precio": producto_disponible["precio"]
        }
        
        payload = {
            "nit": usuario_vendedor["nit"],
            "productos": [
                {
                    "producto_id": producto_disponible["producto_id"],
                    "cantidad_solicitada": 5
                }
            ]
        }
        
        with patch("app.services.pedidos.PedidosService.validar_inventario_producto") as mock_validar:
            mock_validar.return_value = (
                True,
                producto_disponible["cantidad_disponible"],
                producto_disponible["precio"],
                "Inventario disponible"
            )
            
            with patch("app.services.pedidos.PedidosService.obtener_info_producto") as mock_info:
                mock_info.return_value = mock_response
                
                response = client.post(
                    "/api/v1/pedidos/",
                    json=payload,
                    headers={
                        "usuario_id": str(usuario_vendedor["usuario_id"]),
                        "rol_usuario": usuario_vendedor["rol_usuario"]
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["exito"] == True
        assert "numero_pedido" in data
        assert data["numero_pedido"].startswith("PED-")
        assert data["mensaje"] == f"Pedido creado exitosamente con número #{data['numero_pedido']}"
        assert data["pedido"]["estado"] == "pendiente"
        assert data["pedido"]["nit"] == usuario_vendedor["nit"]
        assert data["pedido"]["rol_usuario"] == "admin"
        assert len(data["pedido"]["detalles"]) == 1
    
    @pytest.mark.asyncio
    async def test_crear_pedido_falla_inventario_insuficiente(
        self,
        client,
        usuario_vendedor,
        producto_stock_bajo
    ):
        """
        Scenario: Intentar crear un pedido con producto sin inventario suficiente
        - Given: Gerente está creando pedido
        - When: Selecciona producto con cantidad > disponible
        - Then: Sistema muestra error y ofrece sugerencia
        """
        payload = {
            "nit": usuario_vendedor["nit"],
            "productos": [
                {
                    "producto_id": producto_stock_bajo["producto_id"],
                    "cantidad_solicitada": 10  # Más de lo disponible (5)
                }
            ]
        }
        
        with patch("app.services.pedidos.PedidosService.validar_inventario_producto") as mock_validar:
            mock_validar.return_value = (
                False,
                producto_stock_bajo["cantidad_disponible"],  # 5
                producto_stock_bajo["precio"],
                f"Inventario insuficiente. Disponible: {producto_stock_bajo['cantidad_disponible']}"
            )
            
            response = client.post(
                "/api/v1/pedidos/",
                json=payload,
                headers={
                    "usuario_id": str(usuario_vendedor["usuario_id"]),
                    "rol_usuario": usuario_vendedor["rol_usuario"]
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        detail = data["detail"]
        assert detail["error"] == "INVENTARIO_INSUFICIENTE"
        assert "Inventario insuficiente" in detail["mensaje"]
        assert len(detail["sugerencias"]) > 0
        assert detail["sugerencias"][0]["cantidad_maxima"] == 5
        assert detail["sugerencias"][0]["cantidad_solicitada"] == 10


class TestCrearPedidoClienteInstitucional:
    """Tests para el flujo del Cliente Institucional (rol: usuario_institucional)"""
    
    @pytest.mark.asyncio
    async def test_crear_pedido_cliente_exitoso(
        self,
        client,
        usuario_institucional,
        producto_disponible
    ):
        """
        Scenario: Crear pedido con productos disponibles
        - Given: Cliente institucional ha iniciado sesión
        - When: Selecciona productos con inventario disponible y confirma
        - Then: Pedido se registra exitosamente con número generado
        """
        payload = {
            "nit": usuario_institucional["nit"],
            "productos": [
                {
                    "producto_id": producto_disponible["producto_id"],
                    "cantidad_solicitada": 3
                }
            ]
        }
        
        with patch("app.services.pedidos.PedidosService.validar_inventario_producto") as mock_validar:
            mock_validar.return_value = (
                True,
                producto_disponible["cantidad_disponible"],
                producto_disponible["precio"],
                "Inventario disponible"
            )
            
            with patch("app.services.pedidos.PedidosService.obtener_info_producto") as mock_info:
                mock_info.return_value = {
                    "producto_id": producto_disponible["producto_id"],
                    "nombre": producto_disponible["nombre"]
                }
                
                response = client.post(
                    "/api/v1/pedidos/",
                    json=payload,
                    headers={
                        "usuario_id": str(usuario_institucional["usuario_id"]),
                        "rol_usuario": usuario_institucional["rol_usuario"]
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["exito"] == True
        assert "numero_pedido" in data
        assert data["pedido"]["rol_usuario"] == "usuario_institucional"
        assert data["pedido"]["nit"] == usuario_institucional["nit"]
    
    @pytest.mark.asyncio
    async def test_intentar_pedir_producto_sin_stock(
        self,
        client,
        usuario_institucional,
        producto_sin_stock
    ):
        """
        Scenario: Intentar pedir un producto sin stock
        - Given: Cliente institucional está creando pedido
        - When: Selecciona producto con cantidad = 0
        - Then: Sistema muestra error "Producto sin disponibilidad"
        """
        payload = {
            "nit": usuario_institucional["nit"],
            "productos": [
                {
                    "producto_id": producto_sin_stock["producto_id"],
                    "cantidad_solicitada": 1
                }
            ]
        }
        
        with patch("app.services.pedidos.PedidosService.validar_inventario_producto") as mock_validar:
            mock_validar.return_value = (
                False,
                0,  # Sin stock
                producto_sin_stock["precio"],
                "Producto sin disponibilidad"
            )
            
            response = client.post(
                "/api/v1/pedidos/",
                json=payload,
                headers={
                    "usuario_id": str(usuario_institucional["usuario_id"]),
                    "rol_usuario": usuario_institucional["rol_usuario"]
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "INVENTARIO_INSUFICIENTE"
        assert data["detail"]["sugerencias"][0]["cantidad_maxima"] == 0
    
    @pytest.mark.asyncio
    async def test_intentar_pedir_mas_unidades_que_disponibles(
        self,
        client,
        usuario_institucional,
        producto_stock_bajo
    ):
        """
        Scenario: Intentar pedir más unidades que las disponibles
        - Given: Cliente está creando pedido
        - When: Ingresa cantidad > disponible en inventario
        - Then: Sistema muestra error y sugiere cantidad máxima
        """
        payload = {
            "nit": usuario_institucional["nit"],
            "productos": [
                {
                    "producto_id": producto_stock_bajo["producto_id"],
                    "cantidad_solicitada": 20  # Más de los 5 disponibles
                }
            ]
        }
        
        with patch("app.services.pedidos.PedidosService.validar_inventario_producto") as mock_validar:
            mock_validar.return_value = (
                False,
                producto_stock_bajo["cantidad_disponible"],
                producto_stock_bajo["precio"],
                "Cantidad solicitada supera inventario disponible"
            )
            
            response = client.post(
                "/api/v1/pedidos/",
                json=payload,
                headers={
                    "usuario_id": str(usuario_institucional["usuario_id"]),
                    "rol_usuario": usuario_institucional["rol_usuario"]
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "INVENTARIO_INSUFICIENTE"
        assert len(data["detail"]["sugerencias"]) > 0
        assert data["detail"]["sugerencias"][0]["cantidad_maxima"] == 5  # Cantidad disponible
        assert data["detail"]["sugerencias"][0]["cantidad_solicitada"] == 20


class TestObtenerPedido:
    """Tests para obtener información de un pedido"""
    
    @pytest.mark.asyncio
    async def test_obtener_pedido_existente(self, client, db_session):
        """Test obtener un pedido que existe"""
        # Este test requeriría crear un pedido real en la BD
        # Por ahora verificamos que el endpoint responde correctamente
        from app.models.pedido import Pedido, EstadoPedido
        from uuid import uuid4
        
        # Crear un pedido de prueba
        pedido = Pedido(
            pedido_id=uuid4(),
            usuario_id=1,
            nit="900123456",
            rol_usuario="usuario_institucional",
            numero_pedido="PED-000001",
            estado=EstadoPedido.PENDIENTE,
            monto_total=50000.00
        )
        db_session.add(pedido)
        db_session.commit()
        
        response = client.get(f"/api/v1/pedidos/{str(pedido.pedido_id)}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["numero_pedido"] == "PED-000001"
        assert data["estado"] == "pendiente"
    
    def test_obtener_pedido_no_existente(self, client):
        """Test obtener un pedido que no existe"""
        response = client.get("/api/v1/pedidos/550e8400-e29b-41d4-a716-446655440099")
        
        assert response.status_code == 404


class TestListarPedidos:
    """Tests para listar pedidos con filtros"""
    
    def test_listar_pedidos_sin_filtros(self, client):
        """Test listar todos los pedidos"""
        response = client.get("/api/v1/pedidos/")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pagina" in data
        assert "por_pagina" in data
        assert "pedidos" in data
    
    def test_listar_pedidos_con_filtro_nit(self, client, db_session):
        """Test listar pedidos filtrando por NIT"""
        from app.models.pedido import Pedido, EstadoPedido
        from uuid import uuid4
        
        # Crear dos pedidos con NITs diferentes
        pedido1 = Pedido(
            pedido_id=uuid4(),
            usuario_id=1,
            nit="900123456",
            rol_usuario="usuario_institucional",
            numero_pedido="PED-000001",
            estado=EstadoPedido.PENDIENTE,
            monto_total=50000.00
        )
        
        pedido2 = Pedido(
            pedido_id=uuid4(),
            usuario_id=2,
            nit="900654321",
            rol_usuario="usuario_institucional",
            numero_pedido="PED-000002",
            estado=EstadoPedido.PENDIENTE,
            monto_total=75000.00
        )
        
        db_session.add_all([pedido1, pedido2])
        db_session.commit()
        
        response = client.get("/api/v1/pedidos/?nit=900123456")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["pedidos"][0]["nit"] == "900123456"


class TestValidarInventario:
    """Tests para validación de inventario sin crear pedido"""
    
    @pytest.mark.asyncio
    async def test_validar_inventario_exitoso(
        self,
        client,
        usuario_institucional,
        producto_disponible
    ):
        """Test validación de inventario sin crear pedido"""
        payload = {
            "nit": usuario_institucional["nit"],
            "productos": [
                {
                    "producto_id": producto_disponible["producto_id"],
                    "cantidad_solicitada": 5
                }
            ]
        }
        
        with patch("app.services.pedidos.PedidosService.validar_pedido") as mock_validar:
            mock_validar.return_value = (True, [], "")
            
            response = client.post(
                "/api/v1/pedidos/validar-inventario",
                json=payload,
                headers={
                    "usuario_id": str(usuario_institucional["usuario_id"]),
                    "rol_usuario": usuario_institucional["rol_usuario"]
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valido"] == True


class TestErrorHandling:
    """Tests para validación de errores"""
    
    def test_rol_usuario_invalido(self, client, usuario_vendedor):
        """Test con rol de usuario inválido"""
        payload = {
            "nit": usuario_vendedor["nit"],
            "productos": []
        }
        
        response = client.post(
            "/api/v1/pedidos/",
            json=payload,
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": "rol_invalido"
            }
        )
        
        assert response.status_code == 400
    
    def test_pedido_sin_productos(self, client, usuario_vendedor):
        """Test intento de crear pedido sin productos"""
        payload = {
            "nit": usuario_vendedor["nit"],
            "productos": []
        }
        
        response = client.post(
            "/api/v1/pedidos/",
            json=payload,
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": usuario_vendedor["rol_usuario"]
            }
        )
        
        assert response.status_code == 400

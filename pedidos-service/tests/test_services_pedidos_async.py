"""
Tests para métodos async de servicios de pedidos usando mocks simples
Cubre métodos HTTP sin usar AsyncMock complejo
"""

import pytest
from unittest.mock import patch, Mock
from uuid import uuid4

from app.services.pedidos import PedidosService
from app.models.pedido import Pedido, EstadoPedido, DetallePedido, CanalPedido
from app.schemas.pedido import CrearPedidoRequest, ProductoEnPedidoCreate


class TestPedidosServiceObtenerClientePorId:
    """Tests para obtener_cliente_por_id"""
    
    @pytest.mark.asyncio
    async def test_obtener_cliente_por_id_existente(self):
        """Test obtener cliente existente"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cliente_id": 100,
            "nit": "123456789",
            "nombre": "Cliente Test"
        }
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.obtener_cliente_por_id(100)
        
        assert resultado is not None
        assert resultado["cliente_id"] == 100
        assert resultado["nit"] == "123456789"
    
    @pytest.mark.asyncio
    async def test_obtener_cliente_por_id_no_encontrado(self):
        """Test obtener cliente no encontrado"""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.obtener_cliente_por_id(999)
        
        assert resultado is None
    
    @pytest.mark.asyncio
    async def test_obtener_cliente_por_id_error_servidor(self):
        """Test obtener cliente con error del servidor"""
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.obtener_cliente_por_id(100)
        
        assert resultado is None


class TestPedidosServiceObtenerSedesPorNit:
    """Tests para obtener_sedes_por_nit"""
    
    @pytest.mark.asyncio
    async def test_obtener_sedes_por_nit_exitoso(self):
        """Test obtener sedes de un NIT"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "clientes": [
                {"cliente_id": 100, "nit": "123456789"},
                {"cliente_id": 101, "nit": "123456789"}
            ]
        }
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.obtener_sedes_por_nit("123456789")
        
        assert len(resultado) == 2
        assert resultado[0]["cliente_id"] == 100
        assert resultado[1]["cliente_id"] == 101
    
    @pytest.mark.asyncio
    async def test_obtener_sedes_por_nit_sin_sedes(self):
        """Test obtener sedes cuando no hay"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"clientes": []}
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.obtener_sedes_por_nit("999999999")
        
        assert resultado == []
    
    @pytest.mark.asyncio
    async def test_obtener_sedes_por_nit_error(self):
        """Test obtener sedes con error"""
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.obtener_sedes_por_nit("123456789")
        
        assert resultado == []


class TestPedidosServiceValidarInventarioProducto:
    """Tests para validar_inventario_producto"""
    
    @pytest.mark.asyncio
    async def test_validar_inventario_disponible(self):
        """Test validar inventario cuando hay disponibilidad"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cantidad_disponible": 100,
            "precio": 1500.0
        }
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            disponible, cantidad, precio, mensaje = await PedidosService.validar_inventario_producto(
                "PROD-001", 50
            )
        
        assert disponible is True
        assert cantidad == 100
        assert precio == 1500.0
        assert mensaje == "Inventario disponible"
    
    @pytest.mark.asyncio
    async def test_validar_inventario_insuficiente(self):
        """Test validar inventario insuficiente"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cantidad_disponible": 10,
            "precio": 1500.0
        }
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            disponible, cantidad, precio, mensaje = await PedidosService.validar_inventario_producto(
                "PROD-001", 50
            )
        
        assert disponible is False
        assert cantidad == 10
        assert precio == 1500.0
        assert "Inventario insuficiente" in mensaje
    
    @pytest.mark.asyncio
    async def test_validar_inventario_producto_no_encontrado(self):
        """Test validar inventario producto no encontrado"""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            disponible, cantidad, precio, mensaje = await PedidosService.validar_inventario_producto(
                "PROD-999", 10
            )
        
        assert disponible is False
        assert cantidad == 0
        assert precio == 0.0
        assert mensaje == "Producto no encontrado"


class TestPedidosServiceActualizarStockProducto:
    """Tests para actualizar_stock_producto"""
    
    @pytest.mark.asyncio
    async def test_actualizar_stock_exitoso(self):
        """Test actualizar stock exitosamente"""
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch("httpx.AsyncClient.patch", return_value=mock_response):
            exito, mensaje = await PedidosService.actualizar_stock_producto("PROD-001", 10)
        
        assert exito is True
        assert mensaje is None
    
    @pytest.mark.asyncio
    async def test_actualizar_stock_error(self):
        """Test actualizar stock con error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Error"
        
        with patch("httpx.AsyncClient.patch", return_value=mock_response):
            exito, mensaje = await PedidosService.actualizar_stock_producto("PROD-001", 10)
        
        assert exito is False
        assert mensaje is not None


class TestPedidosServiceObtenerInfoProducto:
    """Tests para obtener_info_producto"""
    
    @pytest.mark.asyncio
    async def test_obtener_info_producto_existente(self):
        """Test obtener info de producto existente"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "producto_id": "PROD-001",
            "nombre": "Producto Test",
            "sku": "SKU001"
        }
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.obtener_info_producto("PROD-001")
        
        assert resultado is not None
        assert resultado["nombre"] == "Producto Test"
        assert resultado["sku"] == "SKU001"
    
    @pytest.mark.asyncio
    async def test_obtener_info_producto_no_encontrado(self):
        """Test obtener info de producto no encontrado"""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.obtener_info_producto("PROD-999")
        
        assert resultado is None


class TestPedidosServiceSeleccionarLoteFEFO:
    """Tests para seleccionar_lote_fefo"""
    
    @pytest.mark.asyncio
    async def test_seleccionar_lote_fefo_disponible(self):
        """Test seleccionar lote FEFO cuando hay lotes"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "loteId": "LOTE-001",
                    "fechaVencimiento": "2025-12-31",
                    "bodegaId": "BOD-001"
                }
            ]
        }
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.seleccionar_lote_fefo("PROD-001")
        
        assert resultado is not None
        assert resultado["loteId"] == "LOTE-001"
    
    @pytest.mark.asyncio
    async def test_seleccionar_lote_fefo_sin_lotes(self):
        """Test seleccionar lote FEFO sin lotes disponibles"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.seleccionar_lote_fefo("PROD-001")
        
        assert resultado is None


class TestPedidosServiceObtenerNitsGerente:
    """Tests para obtener_nits_gerente"""
    
    @pytest.mark.asyncio
    async def test_obtener_nits_gerente_exitoso(self):
        """Test obtener NITs de un gerente"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nits": ["123456789", "987654321"]
        }
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.obtener_nits_gerente(1)
        
        assert len(resultado) == 2
        assert "123456789" in resultado
        assert "987654321" in resultado
    
    @pytest.mark.asyncio
    async def test_obtener_nits_gerente_sin_nits(self):
        """Test obtener NITs cuando gerente no tiene"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"nits": []}
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.obtener_nits_gerente(999)
        
        assert resultado == []


class TestPedidosServiceObtenerClienteIdsGerente:
    """Tests para obtener_cliente_ids_gerente"""
    
    @pytest.mark.asyncio
    async def test_obtener_cliente_ids_gerente_exitoso(self):
        """Test obtener cliente_ids de un gerente"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cliente_ids": [100, 101, 102]
        }
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            resultado = await PedidosService.obtener_cliente_ids_gerente(1)
        
        assert len(resultado) == 3
        assert 100 in resultado
        assert 101 in resultado


class TestPedidosServiceValidarNitUsuarioInstitucional:
    """Tests para validar_nit_usuario_institucional"""
    
    @pytest.mark.asyncio
    async def test_validar_nit_usuario_institucional_valido(self):
        """Test validar NIT coincide con usuario institucional"""
        valido, mensaje = await PedidosService.validar_nit_usuario_institucional(
            "123456789", "123456789"
        )
        
        assert valido is True
        assert mensaje == ""
    
    @pytest.mark.asyncio
    async def test_validar_nit_usuario_institucional_no_coincide(self):
        """Test validar NIT no coincide"""
        valido, mensaje = await PedidosService.validar_nit_usuario_institucional(
            "123456789", "987654321"
        )
        
        assert valido is False
        assert "no coincide" in mensaje
    
    @pytest.mark.asyncio
    async def test_validar_nit_usuario_institucional_sin_nit_usuario(self):
        """Test validar sin NIT de usuario"""
        valido, mensaje = await PedidosService.validar_nit_usuario_institucional(
            "123456789", None
        )
        
        assert valido is False
        assert "no proporcionado" in mensaje


class TestPedidosServiceValidarNitGerenteCuenta:
    """Tests para validar_nit_gerente_cuenta"""
    
    @pytest.mark.asyncio
    async def test_validar_nit_gerente_cuenta_valido(self):
        """Test validar NIT pertenece a gerente"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nits": ["123456789", "987654321"]
        }
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            valido, mensaje = await PedidosService.validar_nit_gerente_cuenta(
                "123456789", 1
            )
        
        assert valido is True
        assert mensaje == ""
    
    @pytest.mark.asyncio
    async def test_validar_nit_gerente_cuenta_no_pertenece(self):
        """Test validar NIT no pertenece a gerente"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nits": ["987654321"]
        }
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            valido, mensaje = await PedidosService.validar_nit_gerente_cuenta(
                "123456789", 1
            )
        
        assert valido is False
        assert "no pertenece" in mensaje
    
    @pytest.mark.asyncio
    async def test_validar_nit_gerente_cuenta_sin_clientes(self):
        """Test validar gerente sin clientes asignados"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"nits": []}
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            valido, mensaje = await PedidosService.validar_nit_gerente_cuenta(
                "123456789", 999
            )
        
        assert valido is False
        assert "no tiene clientes asignados" in mensaje


class TestPedidosServiceValidarPedido:
    """Tests para validar_pedido"""
    
    @pytest.mark.asyncio
    async def test_validar_pedido_todos_productos_disponibles(self):
        """Test validar pedido con todos los productos disponibles"""
        request = CrearPedidoRequest(
            nit="123456789",
            cliente_id=100,
            productos=[
                ProductoEnPedidoCreate(producto_id="PROD-001", cantidad_solicitada=10),
                ProductoEnPedidoCreate(producto_id="PROD-002", cantidad_solicitada=5)
            ]
        )
        
        mock_response_prod1 = Mock()
        mock_response_prod1.status_code = 200
        mock_response_prod1.json.return_value = {
            "cantidad_disponible": 100,
            "precio": 1500.0
        }
        
        mock_response_prod2 = Mock()
        mock_response_prod2.status_code = 200
        mock_response_prod2.json.return_value = {
            "cantidad_disponible": 50,
            "precio": 2000.0
        }
        
        with patch("httpx.AsyncClient.get", side_effect=[mock_response_prod1, mock_response_prod2]):
            valido, validaciones, mensaje = await PedidosService.validar_pedido(
                request, 1, "usuario_institucional"
            )
        
        assert valido is True
        assert len(validaciones) == 2
        assert mensaje == ""
    
    @pytest.mark.asyncio
    async def test_validar_pedido_con_producto_sin_inventario(self):
        """Test validar pedido con producto sin inventario"""
        request = CrearPedidoRequest(
            nit="123456789",
            cliente_id=100,
            productos=[
                ProductoEnPedidoCreate(producto_id="PROD-001", cantidad_solicitada=10)
            ]
        )
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cantidad_disponible": 5,
            "precio": 1500.0
        }
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            valido, validaciones, mensaje = await PedidosService.validar_pedido(
                request, 1, "usuario_institucional"
            )
        
        assert valido is False
        assert len(validaciones) == 1
        assert "Inventario insuficiente" in mensaje

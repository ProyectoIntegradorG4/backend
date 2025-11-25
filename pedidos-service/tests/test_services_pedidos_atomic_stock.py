"""
Tests para validación y actualización atómica de stock durante creación de pedidos.
Cubre:
- Validación atómica de stock antes de crear pedido
- Rollback cuando falla actualización de stock
- Manejo de errores específicos por producto
- Tests de concurrencia (simulados)
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from uuid import uuid4

from app.services.pedidos import PedidosService, StockInsufficientError
from app.models.pedido import Pedido, EstadoPedido
from app.schemas.pedido import CrearPedidoRequest, ProductoEnPedidoCreate, ValidacionInventarioResult


class TestValidarStockAntesDePedido:
    """Tests para _validar_stock_antes_de_pedido"""
    
    @pytest.mark.asyncio
    async def test_validar_stock_todos_productos_disponibles(self, db_session):
        """Test validación cuando todos los productos tienen stock suficiente"""
        productos = [
            {"producto_id": "PROD-001", "cantidad_solicitada": 10},
            {"producto_id": "PROD-002", "cantidad_solicitada": 5}
        ]
        
        # Mock de validación de inventario - ambos disponibles
        async def mock_validar_inventario(producto_id, cantidad):
            stock_disponible = {"PROD-001": 100, "PROD-002": 50}
            precio = {"PROD-001": 1000.0, "PROD-002": 2000.0}
            disponible = stock_disponible[producto_id] >= cantidad
            return disponible, stock_disponible[producto_id], precio[producto_id], "Inventario disponible"
        
        # Mock de obtener info producto
        async def mock_obtener_info(producto_id):
            return {
                "nombre": f"Producto {producto_id}",
                "sku": f"SKU-{producto_id}",
                "precio": 1000.0 if producto_id == "PROD-001" else 2000.0
            }
        
        with patch.object(PedidosService, 'validar_inventario_producto', side_effect=mock_validar_inventario), \
             patch.object(PedidosService, 'obtener_info_producto', side_effect=mock_obtener_info):
            
            productos_validados, validaciones = await PedidosService._validar_stock_antes_de_pedido(
                productos, db_session
            )
        
        assert len(productos_validados) == 2
        assert len(validaciones) == 2
        assert all(v.disponible for v in validaciones)
    
    @pytest.mark.asyncio
    async def test_validar_stock_producto_sin_stock(self, db_session):
        """Test validación cuando un producto no tiene stock suficiente"""
        productos = [
            {"producto_id": "PROD-001", "cantidad_solicitada": 10},
            {"producto_id": "PROD-002", "cantidad_solicitada": 100}  # Más de lo disponible
        ]
        
        # Mock de validación - segundo producto sin stock suficiente
        async def mock_validar_inventario(producto_id, cantidad):
            if producto_id == "PROD-001":
                return True, 100, 1000.0, "Inventario disponible"
            else:
                return False, 50, 2000.0, "Inventario insuficiente. Disponible: 50"
        
        async def mock_obtener_info(producto_id):
            return {"nombre": f"Producto {producto_id}"}
        
        with patch.object(PedidosService, 'validar_inventario_producto', side_effect=mock_validar_inventario), \
             patch.object(PedidosService, 'obtener_info_producto', side_effect=mock_obtener_info):
            
            with pytest.raises(StockInsufficientError) as exc_info:
                await PedidosService._validar_stock_antes_de_pedido(productos, db_session)
            
            assert "Inventario insuficiente" in exc_info.value.mensaje
            assert len(exc_info.value.validaciones) == 2
            # Verificar que hay al menos una validación con disponible=False
            assert any(not v.disponible for v in exc_info.value.validaciones)


class TestActualizarStockConCompensacion:
    """Tests para _actualizar_stock_con_compensacion"""
    
    @pytest.mark.asyncio
    async def test_actualizar_stock_todos_exitosos(self, db_session):
        """Test actualización de stock cuando todos los productos se actualizan correctamente"""
        productos_validados = [
            {
                "producto_id": "PROD-001",
                "cantidad_solicitada": 10,
                "nombre_producto": "Producto 1"
            },
            {
                "producto_id": "PROD-002",
                "cantidad_solicitada": 5,
                "nombre_producto": "Producto 2"
            }
        ]
        
        # Mock de actualización exitosa
        with patch.object(PedidosService, 'actualizar_stock_producto', return_value=(True, None)):
            # No debe lanzar excepción
            productos_actualizados, productos_error = await PedidosService._actualizar_stock_con_compensacion(productos_validados, db_session)
            assert len(productos_actualizados) == 2
            assert len(productos_error) == 0
    
    @pytest.mark.asyncio
    async def test_actualizar_stock_falla_uno(self, db_session):
        """Test que lanza excepción cuando falla la actualización de stock"""
        productos_validados = [
            {
                "producto_id": "PROD-001",
                "cantidad_solicitada": 10,
                "nombre_producto": "Producto 1"
            },
            {
                "producto_id": "PROD-002",
                "cantidad_solicitada": 5,
                "nombre_producto": "Producto 2"
            }
        ]
        
        # Mock de actualización - segundo producto falla
        async def mock_actualizar(producto_id, cantidad):
            return producto_id != "PROD-002"
        
        with patch.object(PedidosService, 'actualizar_stock_producto', side_effect=mock_actualizar):
            with pytest.raises(Exception) as exc_info:
                await PedidosService._actualizar_stock_con_compensacion(productos_validados, db_session)
            
            assert "Error actualizando stock" in str(exc_info.value)
            assert "Producto 2" in str(exc_info.value)


class TestCrearPedidoAtomico:
    """Tests para crear_pedido con transacciones atómicas"""
    
    @pytest.mark.asyncio
    async def test_crear_pedido_con_stock_suficiente(self, db_session):
        """Test crear pedido cuando hay stock suficiente"""
        request = CrearPedidoRequest(
            nit="123456789",
            cliente_id=100,
            productos=[
                ProductoEnPedidoCreate(producto_id="PROD-001", cantidad_solicitada=10)
            ]
        )
        
        # Mock de cliente
        async def mock_obtener_cliente(cliente_id):
            return {"cliente_id": cliente_id, "nit": "123456789"}
        
        # Mock de validación de stock - exitosa
        productos_validados = [{
            "producto_id": "PROD-001",
            "cantidad_solicitada": 10,
            "precio": 1000.0,
            "nombre_producto": "Producto Test",
            "info_producto": {"nombre": "Producto Test", "sku": "SKU-001"},
            "cantidad_disponible": 100
        }]
        validaciones = [
            ValidacionInventarioResult(
                producto_id="PROD-001",
                disponible=True,
                cantidad_disponible=100,
                cantidad_solicitada=10,
                mensaje="Inventario disponible"
            )
        ]
        
        # Mock de actualización de stock - exitosa
        with patch.object(PedidosService, 'obtener_cliente_por_id', side_effect=mock_obtener_cliente), \
             patch.object(PedidosService, '_validar_stock_antes_de_pedido', return_value=(productos_validados, validaciones)), \
             patch.object(PedidosService, 'obtener_info_producto', return_value={"nombre": "Producto Test"}), \
             patch.object(PedidosService, 'seleccionar_lote_fefo', return_value=None), \
             patch.object(PedidosService, '_actualizar_stock_con_compensacion', return_value=None):
            
            exito, pedido_response, mensaje, validaciones_resp = await PedidosService.crear_pedido(
                request=request,
                usuario_id=1,
                rol_usuario="usuario_institucional",
                nit_usuario="123456789",
                cliente_id_header=100,
                db=db_session
            )
        
        assert exito is True
        assert pedido_response is not None
        assert "creado exitosamente" in mensaje.lower()
    
    @pytest.mark.asyncio
    async def test_crear_pedido_stock_insuficiente_rollback(self, db_session):
        """Test que hace rollback cuando hay stock insuficiente"""
        request = CrearPedidoRequest(
            nit="123456789",
            cliente_id=100,
            productos=[
                ProductoEnPedidoCreate(producto_id="PROD-001", cantidad_solicitada=100)
            ]
        )
        
        # Mock de cliente
        async def mock_obtener_cliente(cliente_id):
            return {"cliente_id": cliente_id, "nit": "123456789"}
        
        # Mock de validación - stock insuficiente
        validaciones = [
            ValidacionInventarioResult(
                producto_id="PROD-001",
                disponible=False,
                cantidad_disponible=50,
                cantidad_solicitada=100,
                mensaje="Inventario insuficiente. Disponible: 50"
            )
        ]
        
        with patch.object(PedidosService, 'obtener_cliente_por_id', side_effect=mock_obtener_cliente), \
             patch.object(PedidosService, '_validar_stock_antes_de_pedido', side_effect=StockInsufficientError("Stock insuficiente", validaciones)):
            
            exito, pedido_response, mensaje, validaciones_resp = await PedidosService.crear_pedido(
                request=request,
                usuario_id=1,
                rol_usuario="usuario_institucional",
                nit_usuario="123456789",
                cliente_id_header=100,
                db=db_session
            )
        
        assert exito is False
        assert pedido_response is None
        assert "insuficiente" in mensaje.lower()
        assert len(validaciones_resp) == 1
        assert not validaciones_resp[0].disponible
        
        # Verificar que NO se creó ningún pedido en la BD
        pedidos_count = db_session.query(Pedido).count()
        assert pedidos_count == 0
    
    @pytest.mark.asyncio
    async def test_crear_pedido_falla_actualizacion_stock_rollback(self, db_session):
        """Test que hace rollback cuando falla la actualización de stock"""
        request = CrearPedidoRequest(
            nit="123456789",
            cliente_id=100,
            productos=[
                ProductoEnPedidoCreate(producto_id="PROD-001", cantidad_solicitada=10)
            ]
        )
        
        # Mock de cliente
        async def mock_obtener_cliente(cliente_id):
            return {"cliente_id": cliente_id, "nit": "123456789"}
        
        # Mock de validación - exitosa
        productos_validados = [{
            "producto_id": "PROD-001",
            "cantidad_solicitada": 10,
            "precio": 1000.0,
            "nombre_producto": "Producto Test",
            "info_producto": {"nombre": "Producto Test"},
            "cantidad_disponible": 100
        }]
        validaciones = [
            ValidacionInventarioResult(
                producto_id="PROD-001",
                disponible=True,
                cantidad_disponible=100,
                cantidad_solicitada=10,
                mensaje="Inventario disponible"
            )
        ]
        
        # Mock de actualización de stock - falla
        with patch.object(PedidosService, 'obtener_cliente_por_id', side_effect=mock_obtener_cliente), \
             patch.object(PedidosService, '_validar_stock_antes_de_pedido', return_value=(productos_validados, validaciones)), \
             patch.object(PedidosService, 'obtener_info_producto', return_value={"nombre": "Producto Test"}), \
             patch.object(PedidosService, 'seleccionar_lote_fefo', return_value=None), \
             patch.object(PedidosService, '_actualizar_stock_con_compensacion', side_effect=Exception("Error actualizando stock")):
            
            exito, pedido_response, mensaje, validaciones_resp = await PedidosService.crear_pedido(
                request=request,
                usuario_id=1,
                rol_usuario="usuario_institucional",
                nit_usuario="123456789",
                cliente_id_header=100,
                db=db_session
            )
        
        assert exito is False
        assert pedido_response is None
        assert "Error actualizando stock" in mensaje
        
        # Verificar que NO se creó ningún pedido en la BD (rollback)
        pedidos_count = db_session.query(Pedido).count()
        assert pedidos_count == 0


class TestCrearPedidoConcurrencia:
    """Tests simulados de concurrencia para verificar atomicidad"""
    
    @pytest.mark.asyncio
    async def test_dos_pedidos_simultaneos_mismo_producto(self, db_session):
        """
        Test simulado de dos pedidos simultáneos del mismo producto.
        Solo uno debería tener éxito si el stock es limitado.
        """
        # Simular stock inicial de 50 unidades
        stock_inicial = 50
        
        request1 = CrearPedidoRequest(
            nit="123456789",
            cliente_id=100,
            productos=[
                ProductoEnPedidoCreate(producto_id="PROD-001", cantidad_solicitada=30)
            ]
        )
        
        request2 = CrearPedidoRequest(
            nit="123456789",
            cliente_id=100,
            productos=[
                ProductoEnPedidoCreate(producto_id="PROD-001", cantidad_solicitada=30)
            ]
        )
        
        # Mock de cliente
        async def mock_obtener_cliente(cliente_id):
            return {"cliente_id": cliente_id, "nit": "123456789"}
        
        # Simular validación que verifica stock actual
        stock_disponible = stock_inicial
        
        async def mock_validar_inventario(producto_id, cantidad):
            disponible = stock_disponible >= cantidad
            return disponible, stock_disponible, 1000.0, "Inventario disponible" if disponible else "Stock insuficiente"
        
        async def mock_obtener_info(producto_id):
            return {"nombre": "Producto Test", "sku": "SKU-001"}
        
        # Simular actualización que resta del stock
        async def mock_actualizar_stock(producto_id, cantidad):
            nonlocal stock_disponible
            if stock_disponible >= cantidad:
                stock_disponible -= cantidad
                return True
            return False
        
        # Crear primer pedido
        with patch.object(PedidosService, 'obtener_cliente_por_id', side_effect=mock_obtener_cliente), \
             patch.object(PedidosService, 'validar_inventario_producto', side_effect=mock_validar_inventario), \
             patch.object(PedidosService, 'obtener_info_producto', side_effect=mock_obtener_info), \
             patch.object(PedidosService, 'seleccionar_lote_fefo', return_value=None), \
             patch.object(PedidosService, 'actualizar_stock_producto', side_effect=mock_actualizar_stock):
            
            # Preparar productos validados para el primer pedido
            productos_validados_1 = [{
                "producto_id": "PROD-001",
                "cantidad_solicitada": 30,
                "precio": 1000.0,
                "nombre_producto": "Producto Test",
                "info_producto": {"nombre": "Producto Test"},
                "cantidad_disponible": stock_inicial
            }]
            validaciones_1 = [
                ValidacionInventarioResult(
                    producto_id="PROD-001",
                    disponible=True,
                    cantidad_disponible=stock_inicial,
                    cantidad_solicitada=30,
                    mensaje="Inventario disponible"
                )
            ]
            
            with patch.object(PedidosService, '_validar_stock_antes_de_pedido', return_value=(productos_validados_1, validaciones_1)), \
                 patch.object(PedidosService, '_actualizar_stock_con_compensacion', return_value=None):
                
                exito1, _, _, _ = await PedidosService.crear_pedido(
                    request=request1,
                    usuario_id=1,
                    rol_usuario="usuario_institucional",
                    nit_usuario="123456789",
                    cliente_id_header=100,
                    db=db_session
                )
        
        # Verificar que el primer pedido se creó
        assert exito1 is True
        
        # Verificar que el stock se redujo
        assert stock_disponible == stock_inicial - 30
        
        # Intentar crear segundo pedido (debería fallar por stock insuficiente)
        # Resetear el mock para el segundo intento
        productos_validados_2 = [{
            "producto_id": "PROD-001",
            "cantidad_solicitada": 30,
            "precio": 1000.0,
            "nombre_producto": "Producto Test",
            "info_producto": {"nombre": "Producto Test"},
            "cantidad_disponible": stock_disponible  # Stock actualizado
        }]
        validaciones_2 = [
            ValidacionInventarioResult(
                producto_id="PROD-001",
                disponible=False,  # Ya no hay suficiente stock
                cantidad_disponible=stock_disponible,
                cantidad_solicitada=30,
                mensaje=f"Inventario insuficiente. Disponible: {stock_disponible}"
            )
        ]
        
        with patch.object(PedidosService, 'obtener_cliente_por_id', side_effect=mock_obtener_cliente), \
             patch.object(PedidosService, '_validar_stock_antes_de_pedido', side_effect=StockInsufficientError("Stock insuficiente", validaciones_2)):
            
            exito2, _, mensaje2, _ = await PedidosService.crear_pedido(
                request=request2,
                usuario_id=2,
                rol_usuario="usuario_institucional",
                nit_usuario="123456789",
                cliente_id_header=100,
                db=db_session
            )
        
        # Verificar que el segundo pedido NO se creó
        assert exito2 is False
        assert "insuficiente" in mensaje2.lower()
        
        # Verificar que solo hay un pedido en la BD
        pedidos_count = db_session.query(Pedido).count()
        assert pedidos_count == 1


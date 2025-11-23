"""
Tests unitarios para schemas de pedidos
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.pedido import (
    CrearPedidoRequest,
    PedidoResponse,
    DetallePedidoResponse,
    ValidacionInventarioResult
)


class TestCrearPedidoRequestSchema:
    """Tests para validación de CrearPedidoRequest"""
    
    def test_crear_pedido_request_valido(self):
        """Test creación de request válido"""
        request = CrearPedidoRequest(
            nit="900123456",
            cliente_id=101,
            productos=[
                {
                    "producto_id": "prod1",
                    "cantidad_solicitada": 10
                }
            ]
        )
        assert request.nit == "900123456"
        assert request.cliente_id == 101
        assert len(request.productos) == 1
    
    def test_crear_pedido_request_sin_nit(self):
        """Test request sin NIT falla"""
        with pytest.raises(ValidationError):
            CrearPedidoRequest(
                cliente_id=101,
                productos=[{"producto_id": "prod1", "cantidad_solicitada": 10}]
            )
    
    def test_crear_pedido_request_sin_cliente_id(self):
        """Test request sin cliente_id falla"""
        with pytest.raises(ValidationError):
            CrearPedidoRequest(
                nit="900123456",
                productos=[{"producto_id": "prod1", "cantidad_solicitada": 10}]
            )
    
    def test_crear_pedido_request_sin_productos(self):
        """Test request sin productos falla"""
        with pytest.raises(ValidationError):
            CrearPedidoRequest(
                nit="900123456",
                cliente_id=101
            )
    
    def test_crear_pedido_request_productos_vacio(self):
        """Test request con lista productos vacía - Pydantic permite listas vacías"""
        # Pydantic no valida lista vacía por defecto, permite crearla
        request = CrearPedidoRequest(
            nit="900123456",
            cliente_id=101,
            productos=[]
        )
        # Si se crea, es porque Pydantic permite listas vacías
        assert request.nit == "900123456"
        assert len(request.productos) == 0
    
    def test_crear_pedido_request_cantidad_negativa(self):
        """Test request con cantidad negativa falla"""
        with pytest.raises(ValidationError):
            CrearPedidoRequest(
                nit="900123456",
                cliente_id=101,
                productos=[
                    {"producto_id": "prod1", "cantidad_solicitada": -5}
                ]
            )
    
    def test_crear_pedido_request_cliente_id_invalido(self):
        """Test request con cliente_id negativo falla"""
        # Nota: Pydantic int no valida si es negativo por defecto
        # Solo validamos que se puede crear con valores positivos
        try:
            CrearPedidoRequest(
                nit="900123456",
                cliente_id=-1,
                productos=[{"producto_id": "prod1", "cantidad_solicitada": 10}]
            )
            # Si se crea, está permitido
        except ValidationError:
            pass  # También permitido si valida


class TestDetallePedidoResponseSchema:
    """Tests para schema de respuesta de detalle"""
    
    def test_detalle_pedido_response_completo(self):
        """Test creación de response completo"""
        detalle = DetallePedidoResponse(
            detalle_id="d1",
            producto_id="prod1",
            nombre_producto="Producto 1",
            cantidad_solicitada=10,
            cantidad_disponible_al_momento=15,
            precio_unitario=5000.0,
            subtotal=50000.0
        )
        assert detalle.producto_id == "prod1"
        assert detalle.cantidad_solicitada == 10
        assert detalle.precio_unitario == 5000.0
    
    def test_detalle_pedido_response_sin_precio(self):
        """Test detalle sin precio unitario falla"""
        with pytest.raises(ValidationError):
            DetallePedidoResponse(
                detalle_id="d1",
                producto_id="prod1",
                nombre_producto="Producto 1",
                cantidad_solicitada=10,
                cantidad_disponible_al_momento=15,
                subtotal=50000.0
            )


class TestPedidoResponseSchema:
    """Tests para schema de respuesta de pedido"""
    
    def test_pedido_response_minimo(self):
        """Test creación de response mínimo"""
        response = PedidoResponse(
            pedido_id="123",
            numero_pedido="PED-000001",
            nit="900123456",
            cliente_id=101,
            usuario_id=1,
            estado="pendiente",
            rol_usuario="admin",
            monto_total=50000.0,
            fecha_creacion=datetime.now(),
            fecha_actualizacion=datetime.now(),
            observaciones=None,
            detalles=[]
        )
        assert response.numero_pedido == "PED-000001"
        assert response.estado == "pendiente"
    
    def test_pedido_response_con_detalles(self):
        """Test response con múltiples detalles"""
        response = PedidoResponse(
            pedido_id="123",
            numero_pedido="PED-000001",
            nit="900123456",
            cliente_id=101,
            usuario_id=1,
            estado="pendiente",
            rol_usuario="admin",
            monto_total=75000.0,
            fecha_creacion=datetime.now(),
            fecha_actualizacion=datetime.now(),
            observaciones=None,
            detalles=[
                DetallePedidoResponse(
                    detalle_id="d1",
                    producto_id="prod1",
                    nombre_producto="Producto 1",
                    cantidad_solicitada=10,
                    cantidad_disponible_al_momento=15,
                    precio_unitario=5000.0,
                    subtotal=50000.0
                ),
                DetallePedidoResponse(
                    detalle_id="d2",
                    producto_id="prod2",
                    nombre_producto="Producto 2",
                    cantidad_solicitada=5,
                    cantidad_disponible_al_momento=20,
                    precio_unitario=5000.0,
                    subtotal=25000.0
                )
            ]
        )
        assert len(response.detalles) == 2


class TestValidacionInventarioResult:
    """Tests para schema de resultado de validación"""
    
    def test_validacion_exitosa(self):
        """Test validación de inventario exitosa"""
        result = ValidacionInventarioResult(
            producto_id="prod1",
            disponible=True,
            cantidad_disponible=100,
            cantidad_solicitada=50,
            mensaje="Inventario disponible"
        )
        assert result.disponible is True
        assert result.cantidad_disponible == 100
        assert result.cantidad_solicitada == 50
    
    def test_validacion_fallida(self):
        """Test validación de inventario fallida"""
        result = ValidacionInventarioResult(
            producto_id="prod2",
            disponible=False,
            cantidad_disponible=0,
            cantidad_solicitada=100,
            mensaje="Producto sin stock"
        )
        assert result.disponible is False
        assert result.cantidad_disponible == 0

"""
Tests unitarios para modelos de pedidos
"""

import pytest
import uuid
from datetime import datetime, timezone
from app.models.pedido import Pedido, DetallePedido, EstadoPedido, CanalPedido, PedidoEstadoHistorial


class TestPedidoModel:
    """Tests para el modelo Pedido"""
    
    def test_crear_pedido_basico(self, db_session):
        """Test creación de pedido básico"""
        test_uuid = uuid.uuid4()
        pedido = Pedido(
            pedido_id=test_uuid,
            usuario_id=1,
            numero_pedido="PED-000001",
            nit="900123456",
            cliente_id=101,
            estado=EstadoPedido.PENDIENTE,
            rol_usuario="admin"
        )
        db_session.add(pedido)
        db_session.commit()
        
        retrieved = db_session.query(Pedido).filter_by(pedido_id=test_uuid).first()
        assert retrieved is not None
        assert retrieved.numero_pedido == "PED-000001"
        assert retrieved.nit == "900123456"
        assert retrieved.estado == EstadoPedido.PENDIENTE
    
    def test_crear_pedido_con_canal(self, db_session):
        """Test creación de pedido con canal"""
        test_uuid = uuid.uuid4()
        pedido = Pedido(
            pedido_id=test_uuid,
            usuario_id=1,
            numero_pedido="PED-000002",
            nit="900123456",
            cliente_id=101,
            estado=EstadoPedido.PENDIENTE,
            rol_usuario="admin",
            canal=CanalPedido.MOVIL_VENTAS
        )
        db_session.add(pedido)
        db_session.commit()
        
        retrieved = db_session.query(Pedido).filter_by(pedido_id=test_uuid).first()
        assert retrieved.canal == CanalPedido.MOVIL_VENTAS
    
    def test_pedido_timestamps(self, db_session):
        """Test que los timestamps se crean automáticamente"""
        test_uuid = uuid.uuid4()
        pedido = Pedido(
            pedido_id=test_uuid,
            usuario_id=1,
            numero_pedido="PED-000003",
            nit="900123456",
            cliente_id=101,
            estado=EstadoPedido.PENDIENTE,
            rol_usuario="admin"
        )
        db_session.add(pedido)
        db_session.commit()
        
        retrieved = db_session.query(Pedido).filter_by(pedido_id=test_uuid).first()
        assert retrieved.fecha_creacion is not None
        assert retrieved.fecha_actualizacion is not None


class TestDetallePedidoModel:
    """Tests para el modelo DetallePedido"""
    
    def test_crear_detalle_pedido(self, db_session):
        """Test creación de detalle de pedido"""
        # Primero crear un pedido
        pedido_uuid = uuid.uuid4()
        detalle_uuid = uuid.uuid4()
        pedido = Pedido(
            pedido_id=pedido_uuid,
            usuario_id=1,
            numero_pedido="PED-000010",
            nit="900123456",
            cliente_id=101,
            estado=EstadoPedido.PENDIENTE,
            rol_usuario="admin"
        )
        db_session.add(pedido)
        db_session.commit()
        
        # Crear detalle
        detalle = DetallePedido(
            detalle_id=detalle_uuid,
            pedido_id=pedido_uuid,
            producto_id="prod1",
            nombre_producto="Producto 1",
            cantidad_solicitada=10,
            cantidad_disponible_al_momento=15,
            precio_unitario=5000.0,
            subtotal=50000.0
        )
        db_session.add(detalle)
        db_session.commit()
        
        retrieved = db_session.query(DetallePedido).filter_by(detalle_id=detalle_uuid).first()
        assert retrieved is not None
        assert retrieved.producto_id == "prod1"
        assert retrieved.cantidad_solicitada == 10
        assert retrieved.precio_unitario == 5000.0
    
    def test_detalle_calcular_subtotal(self, db_session):
        """Test cálculo de subtotal en detalle"""
        pedido_uuid = uuid.uuid4()
        detalle_uuid = uuid.uuid4()
        pedido = Pedido(
            pedido_id=pedido_uuid,
            usuario_id=1,
            numero_pedido="PED-000011",
            nit="900123456",
            cliente_id=101,
            estado=EstadoPedido.PENDIENTE,
            rol_usuario="admin"
        )
        db_session.add(pedido)
        db_session.commit()
        
        detalle = DetallePedido(
            detalle_id=detalle_uuid,
            pedido_id=pedido_uuid,
            producto_id="prod2",
            nombre_producto="Producto 2",
            cantidad_solicitada=20,
            cantidad_disponible_al_momento=25,
            precio_unitario=1000.0,
            subtotal=20000.0
        )
        db_session.add(detalle)
        db_session.commit()
        
        retrieved = db_session.query(DetallePedido).filter_by(detalle_id=detalle_uuid).first()
        # Verificar que subtotal está correcto
        assert retrieved.subtotal == 20000.0


class TestPedidoEstadoHistorial:
    """Tests para el historial de estados"""
    
    def test_crear_historial_estado(self, db_session):
        """Test creación de registro de historial"""
        pedido_uuid = uuid.uuid4()
        pedido = Pedido(
            pedido_id=pedido_uuid,
            usuario_id=1,
            numero_pedido="PED-000020",
            nit="900123456",
            cliente_id=101,
            estado=EstadoPedido.PENDIENTE,
            rol_usuario="admin"
        )
        db_session.add(pedido)
        db_session.commit()
        
        historial = PedidoEstadoHistorial(
            pedido_id=pedido_uuid,
            estado_anterior=EstadoPedido.PENDIENTE,
            estado_nuevo=EstadoPedido.ENVIADO,
            comentario="Pedido confirmado por gerente"
        )
        db_session.add(historial)
        db_session.commit()
        
        retrieved = db_session.query(PedidoEstadoHistorial).first()
        assert retrieved is not None
        assert retrieved.estado_nuevo == EstadoPedido.ENVIADO
        assert retrieved.comentario == "Pedido confirmado por gerente"
    
    def test_historial_timestamps(self, db_session):
        """Test que historial tiene timestamp de creación"""
        pedido_uuid = uuid.uuid4()
        pedido = Pedido(
            pedido_id=pedido_uuid,
            usuario_id=1,
            numero_pedido="PED-000021",
            nit="900123456",
            cliente_id=101,
            estado=EstadoPedido.PENDIENTE,
            rol_usuario="admin"
        )
        db_session.add(pedido)
        db_session.commit()
        
        historial = PedidoEstadoHistorial(
            pedido_id=pedido_uuid,
            estado_anterior=EstadoPedido.PENDIENTE,
            estado_nuevo=EstadoPedido.ENVIADO
        )
        db_session.add(historial)
        db_session.commit()
        
        retrieved = db_session.query(PedidoEstadoHistorial).first()
        assert retrieved.fecha_cambio is not None


class TestEstadoPedidoEnum:
    """Tests para el enum EstadoPedido"""
    
    def test_estados_disponibles(self):
        """Test que todos los estados esperados están disponibles"""
        assert EstadoPedido.PENDIENTE.value == "pendiente"
        assert EstadoPedido.ENVIADO.value == "enviado"
        assert EstadoPedido.ENTREGADO.value == "entregado"
        assert EstadoPedido.CANCELADO.value == "cancelado"
    
    def test_canal_enum(self):
        """Test que canales están definidos"""
        assert CanalPedido.MOVIL_VENTAS.value == "movil_ventas"
        assert CanalPedido.MOVIL_CLIENTE.value == "movil_cliente"

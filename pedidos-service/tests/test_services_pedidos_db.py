"""
Tests para servicios de pedidos usando base de datos
Enfocado en métodos síncronos que usan db_session
"""

import pytest
from uuid import uuid4

from app.services.pedidos import PedidosService
from app.models.pedido import Pedido, EstadoPedido, CanalPedido


class TestPedidosServiceGenerarNumeroPedido:
    """Tests para generación de número de pedido"""
    
    def test_generar_numero_pedido_primero(self, db_session):
        """Test generar primer número de pedido"""
        numero = PedidosService.generar_numero_pedido(db_session)
        assert numero == "PED-000001"
    
    def test_generar_numero_pedido_secuencial(self, db_session):
        """Test generar números de pedido secuenciales"""
        pedido1 = Pedido(
            pedido_id=str(uuid4()),
            numero_pedido="PED-000001",
            usuario_id=1,
            cliente_id=100,
            nit="123456789",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.PENDIENTE,
            monto_total=100.0
        )
        db_session.add(pedido1)
        db_session.commit()
        
        numero = PedidosService.generar_numero_pedido(db_session)
        assert numero == "PED-000002"
    
    def test_generar_numero_pedido_con_gap(self, db_session):
        """Test generar número cuando hay gap en secuencia"""
        pedido1 = Pedido(
            pedido_id=str(uuid4()),
            numero_pedido="PED-000001",
            usuario_id=1,
            cliente_id=100,
            nit="123456789",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.PENDIENTE,
            monto_total=100.0
        )
        pedido2 = Pedido(
            pedido_id=str(uuid4()),
            numero_pedido="PED-000005",
            usuario_id=1,
            cliente_id=100,
            nit="123456789",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.PENDIENTE,
            monto_total=200.0
        )
        db_session.add_all([pedido1, pedido2])
        db_session.commit()
        
        numero = PedidosService.generar_numero_pedido(db_session)
        assert numero == "PED-000006"


class TestPedidosServiceObtenerPedido:
    """Tests para obtener un pedido por ID"""
    
    def test_obtener_pedido_existente(self, db_session):
        """Test obtener pedido que existe"""
        pedido_id = str(uuid4())
        pedido = Pedido(
            pedido_id=pedido_id,
            numero_pedido="PED-000001",
            usuario_id=1,
            cliente_id=100,
            nit="123456789",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.PENDIENTE,
            monto_total=100.0,
            canal=CanalPedido.MOVIL_CLIENTE
        )
        db_session.add(pedido)
        db_session.commit()
        
        resultado = PedidosService.obtener_pedido(pedido_id, db_session)
        
        assert resultado is not None
        assert resultado.pedido_id == pedido_id
        assert resultado.numero_pedido == "PED-000001"
        assert resultado.estado == EstadoPedido.PENDIENTE
        assert resultado.monto_total == 100.0
    
    def test_obtener_pedido_no_existe(self, db_session):
        """Test obtener pedido que no existe"""
        pedido_id = str(uuid4())
        
        resultado = PedidosService.obtener_pedido(pedido_id, db_session)
        
        assert resultado is None

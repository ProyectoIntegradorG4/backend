"""
Tests para listar_pedidos con filtros y paginación
Usando base de datos para tests síncronos
"""

import pytest
from uuid import uuid4

from app.services.pedidos import PedidosService
from app.models.pedido import Pedido, EstadoPedido, CanalPedido


class TestPedidosServiceListarPedidos:
    """Tests para listar_pedidos con diferentes filtros"""
    
    def test_listar_pedidos_sin_filtros(self, db_session):
        """Test listar todos los pedidos sin filtros"""
        # Crear pedidos de prueba
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
            numero_pedido="PED-000002",
            usuario_id=2,
            cliente_id=101,
            nit="987654321",
            rol_usuario="gerente_cuenta",
            estado=EstadoPedido.ENVIADO,
            monto_total=200.0
        )
        db_session.add_all([pedido1, pedido2])
        db_session.commit()
        
        pedidos, total = PedidosService.listar_pedidos(db=db_session)
        
        assert total == 2
        assert len(pedidos) == 2
    
    def test_listar_pedidos_filtro_por_nit(self, db_session):
        """Test listar pedidos filtrados por NIT"""
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
            numero_pedido="PED-000002",
            usuario_id=2,
            cliente_id=101,
            nit="987654321",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.PENDIENTE,
            monto_total=200.0
        )
        db_session.add_all([pedido1, pedido2])
        db_session.commit()
        
        pedidos, total = PedidosService.listar_pedidos(
            nit="123456789",
            db=db_session
        )
        
        assert total == 1
        assert pedidos[0].nit == "123456789"
    
    def test_listar_pedidos_filtro_por_usuario_id(self, db_session):
        """Test listar pedidos filtrados por usuario_id"""
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
            numero_pedido="PED-000002",
            usuario_id=2,
            cliente_id=101,
            nit="987654321",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.PENDIENTE,
            monto_total=200.0
        )
        db_session.add_all([pedido1, pedido2])
        db_session.commit()
        
        pedidos, total = PedidosService.listar_pedidos(
            usuario_id=1,
            db=db_session
        )
        
        assert total == 1
        assert pedidos[0].usuario_id == 1
    
    def test_listar_pedidos_filtro_por_estado(self, db_session):
        """Test listar pedidos filtrados por estado"""
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
            numero_pedido="PED-000002",
            usuario_id=1,
            cliente_id=100,
            nit="123456789",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.ENVIADO,
            monto_total=200.0
        )
        db_session.add_all([pedido1, pedido2])
        db_session.commit()
        
        pedidos, total = PedidosService.listar_pedidos(
            estado=EstadoPedido.ENVIADO,
            db=db_session
        )
        
        assert total == 1
        assert pedidos[0].estado == EstadoPedido.ENVIADO
    
    def test_listar_pedidos_filtro_por_cliente_id(self, db_session):
        """Test listar pedidos filtrados por cliente_id"""
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
            numero_pedido="PED-000002",
            usuario_id=1,
            cliente_id=101,
            nit="123456789",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.PENDIENTE,
            monto_total=200.0
        )
        db_session.add_all([pedido1, pedido2])
        db_session.commit()
        
        pedidos, total = PedidosService.listar_pedidos(
            cliente_id=100,
            db=db_session
        )
        
        assert total == 1
        assert pedidos[0].cliente_id == 100
    
    def test_listar_pedidos_con_paginacion(self, db_session):
        """Test listar pedidos con paginación"""
        # Crear 5 pedidos
        for i in range(1, 6):
            pedido = Pedido(
                pedido_id=str(uuid4()),
                numero_pedido=f"PED-{i:06d}",
                usuario_id=1,
                cliente_id=100,
                nit="123456789",
                rol_usuario="usuario_institucional",
                estado=EstadoPedido.PENDIENTE,
                monto_total=100.0 * i
            )
            db_session.add(pedido)
        db_session.commit()
        
        # Primera página (2 registros)
        pedidos_pag1, total = PedidosService.listar_pedidos(
            pagina=1,
            por_pagina=2,
            db=db_session
        )
        
        assert total == 5
        assert len(pedidos_pag1) == 2
        
        # Segunda página (2 registros)
        pedidos_pag2, _ = PedidosService.listar_pedidos(
            pagina=2,
            por_pagina=2,
            db=db_session
        )
        
        assert len(pedidos_pag2) == 2
        
        # Tercera página (1 registro)
        pedidos_pag3, _ = PedidosService.listar_pedidos(
            pagina=3,
            por_pagina=2,
            db=db_session
        )
        
        assert len(pedidos_pag3) == 1
    
    def test_listar_pedidos_filtro_por_cliente_ids_gerente(self, db_session):
        """Test listar pedidos usando cliente_ids del gerente"""
        pedido1 = Pedido(
            pedido_id=str(uuid4()),
            numero_pedido="PED-000001",
            usuario_id=1,
            cliente_id=100,
            nit="123456789",
            rol_usuario="gerente_cuenta",
            estado=EstadoPedido.PENDIENTE,
            monto_total=100.0
        )
        pedido2 = Pedido(
            pedido_id=str(uuid4()),
            numero_pedido="PED-000002",
            usuario_id=1,
            cliente_id=101,
            nit="123456789",
            rol_usuario="gerente_cuenta",
            estado=EstadoPedido.PENDIENTE,
            monto_total=200.0
        )
        pedido3 = Pedido(
            pedido_id=str(uuid4()),
            numero_pedido="PED-000003",
            usuario_id=2,
            cliente_id=102,
            nit="987654321",
            rol_usuario="gerente_cuenta",
            estado=EstadoPedido.PENDIENTE,
            monto_total=300.0
        )
        db_session.add_all([pedido1, pedido2, pedido3])
        db_session.commit()
        
        # Filtrar por cliente_ids del gerente
        cliente_ids_gerente = [100, 101]
        pedidos, total = PedidosService.listar_pedidos(
            cliente_ids_gerente=cliente_ids_gerente,
            db=db_session
        )
        
        assert total == 2
        assert all(p.cliente_id in cliente_ids_gerente for p in pedidos)
    
    def test_listar_pedidos_ordenados_por_fecha_creacion_desc(self, db_session):
        """Test que pedidos se ordenan por fecha_creacion descendente"""
        # Crear 3 pedidos
        for i in range(1, 4):
            pedido = Pedido(
                pedido_id=str(uuid4()),
                numero_pedido=f"PED-{i:06d}",
                usuario_id=1,
                cliente_id=100,
                nit="123456789",
                rol_usuario="usuario_institucional",
                estado=EstadoPedido.PENDIENTE,
                monto_total=100.0 * i
            )
            db_session.add(pedido)
            db_session.flush()  # Asignar fecha_creacion
        db_session.commit()
        
        pedidos, total = PedidosService.listar_pedidos(db=db_session)
        
        assert len(pedidos) == 3
        # El último creado debe ser el primero en la lista
        assert pedidos[0].numero_pedido == "PED-000003"
        assert pedidos[1].numero_pedido == "PED-000002"
        assert pedidos[2].numero_pedido == "PED-000001"

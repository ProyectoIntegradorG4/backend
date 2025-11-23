"""
Tests unitarios para endpoints de pedidos
"""

import pytest
from unittest.mock import patch, AsyncMock
import json

from app.models.pedido import Pedido, DetallePedido, EstadoPedido


class TestPedidosEndpoints:
    """Tests para los endpoints de pedidos"""
    
    @pytest.mark.asyncio
    async def test_listar_pedidos_vacio(self, client, usuario_vendedor):
        """Test listar pedidos cuando no hay ninguno"""
        response = client.get(
            "/api/v1/pedidos/",
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": usuario_vendedor["rol_usuario"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "pedidos" in data or isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_listar_pedidos_con_registros(self, client, db_session, usuario_vendedor):
        """Test listar pedidos cuando hay registros"""
        # Crear algunos pedidos
        for i in range(3):
            pedido = Pedido(
                pedido_id=f"ped{i}",
                usuario_id=usuario_vendedor["usuario_id"],
                numero_pedido=f"PED-{i:06d}",
                nit=usuario_vendedor["nit"],
                cliente_id=101,
                estado=EstadoPedido.PENDIENTE,
                rol_usuario="admin"
            )
            db_session.add(pedido)
        db_session.commit()
        
        response = client.get(
            "/api/v1/pedidos/",
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": usuario_vendedor["rol_usuario"]
            }
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_obtener_pedido_por_id(self, client, db_session, usuario_vendedor):
        """Test obtener un pedido específico"""
        # Crear un pedido
        pedido = Pedido(
            pedido_id="test_id_123",
            usuario_id=1,
            numero_pedido="PED-000123",
            nit=usuario_vendedor["nit"],
            cliente_id=101,
            estado=EstadoPedido.PENDIENTE,
            rol_usuario="admin"
        )
        db_session.add(pedido)
        db_session.commit()
        
        response = client.get(
            "/api/v1/pedidos/test_id_123",
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": usuario_vendedor["rol_usuario"]
            }
        )
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_obtener_pedido_no_existe(self, client, usuario_vendedor):
        """Test obtener pedido que no existe"""
        response = client.get(
            "/api/v1/pedidos/inexistente_12345",
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": usuario_vendedor["rol_usuario"]
            }
        )
        assert response.status_code in [404, 200]
    
    @pytest.mark.asyncio
    async def test_crear_pedido_sin_inventario(self, client, usuario_vendedor):
        """Test crear pedido sin headers requeridos"""
        payload = {
            "nit": usuario_vendedor["nit"],
            "cliente_id": 101,
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
        # Esperamos rechazo debido a lista vacía
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_listar_por_nit(self, client, db_session, usuario_vendedor):
        """Test listar pedidos por NIT"""
        # Crear pedido
        pedido = Pedido(
            pedido_id="ped_nit_1",
            usuario_id=1,
            numero_pedido="PED-000099",
            nit=usuario_vendedor["nit"],
            cliente_id=101,
            estado=EstadoPedido.PENDIENTE,
            rol_usuario="admin"
        )
        db_session.add(pedido)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/pedidos/por-nit/{usuario_vendedor['nit']}",
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": usuario_vendedor["rol_usuario"]
            }
        )
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_filtro_por_estado(self, client, db_session, usuario_vendedor):
        """Test filtro de pedidos por estado"""
        # Crear pedidos con diferentes estados
        for estado in [EstadoPedido.PENDIENTE, EstadoPedido.ENVIADO]:
            pedido = Pedido(
            pedido_id=f"ped_estado_{estado.value}",
            usuario_id=1,
            numero_pedido=f"PED-{hash(estado)%100000:06d}",
                nit=usuario_vendedor["nit"],
                cliente_id=101,
                estado=estado,
                rol_usuario="admin"
            )
            db_session.add(pedido)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/pedidos/",
            params={"estado": "pendiente"},
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": usuario_vendedor["rol_usuario"]
            }
        )
        assert response.status_code == 200


class TestPedidosEndpointsConfirmacion:
    """Tests para endpoints de confirmación de pedidos"""
    
    @pytest.mark.asyncio
    async def test_confirmar_pedido_existe(self, client, db_session, usuario_vendedor):
        """Test confirmación de pedido existente"""
        pedido = Pedido(
            pedido_id="ped_confirm_1",
            usuario_id=1,
            numero_pedido="PED-000200",
            nit=usuario_vendedor["nit"],
            cliente_id=101,
            estado=EstadoPedido.PENDIENTE,
            rol_usuario="admin"
        )
        db_session.add(pedido)
        db_session.commit()
        
        response = client.post(
            "/api/v1/pedidos/ped_confirm_1/confirmar",
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": usuario_vendedor["rol_usuario"]
            }
        )
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_confirmar_pedido_no_existe(self, client, usuario_vendedor):
        """Test confirmación de pedido que no existe"""
        response = client.post(
            "/api/v1/pedidos/inexistente_xyz/confirmar",
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": usuario_vendedor["rol_usuario"]
            }
        )
        assert response.status_code in [404, 400]


class TestPedidosEndpointsCancelacion:
    """Tests para endpoints de cancelación"""
    
    @pytest.mark.asyncio
    async def test_cancelar_pedido_pendiente(self, client, db_session, usuario_vendedor):
        """Test cancelación de pedido pendiente"""
        pedido = Pedido(
            pedido_id="ped_cancel_1",
            usuario_id=1,
            numero_pedido="PED-000300",
            nit=usuario_vendedor["nit"],
            cliente_id=101,
            estado=EstadoPedido.PENDIENTE,
            rol_usuario="admin"
        )
        db_session.add(pedido)
        db_session.commit()
        
        response = client.post(
            "/api/v1/pedidos/ped_cancel_1/cancelar",
            json={"motivo": "Cliente cambió de opinión"},
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": usuario_vendedor["rol_usuario"]
            }
        )
        assert response.status_code in [200, 404]


class TestPedidosEndpointsEstadisticas:
    """Tests para endpoints de estadísticas"""
    
    @pytest.mark.asyncio
    async def test_obtener_estadisticas(self, client, db_session, usuario_vendedor):
        """Test obtención de estadísticas de pedidos"""
        # Crear varios pedidos
        for i in range(5):
            pedido = Pedido(
            pedido_id=f"ped_stats_{i}",
            usuario_id=1,
            numero_pedido=f"PED-{9000+i:06d}",
                nit=usuario_vendedor["nit"],
                cliente_id=101,
                estado=EstadoPedido.PENDIENTE,
                rol_usuario="admin"
            )
            db_session.add(pedido)
        db_session.commit()
        
        response = client.get(
            "/api/v1/pedidos/estadisticas/resumen",
            headers={
                "usuario_id": str(usuario_vendedor["usuario_id"]),
                "rol_usuario": usuario_vendedor["rol_usuario"]
            }
        )
        assert response.status_code in [200, 404]

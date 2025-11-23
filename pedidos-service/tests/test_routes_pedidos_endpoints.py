"""
Tests para endpoints de pedidos (app/routes/pedidos.py)
Cubre casos de éxito y errores HTTP
"""

import pytest
from unittest.mock import patch, Mock
from uuid import uuid4

from app.models.pedido import EstadoPedido
from app.schemas.pedido import PedidoResponse, DetallePedidoResponse


class TestCrearPedidoEndpoint:
    """Tests para POST /api/v1/pedidos/"""
    
    def test_crear_pedido_rol_invalido(self, client):
        """Test crear pedido con rol inválido"""
        payload = {
            "nit": "123456789",
            "cliente_id": 100,
            "productos": [
                {"producto_id": "PROD-001", "cantidad_solicitada": 10}
            ]
        }
        
        response = client.post(
            "/api/v1/pedidos/",
            json=payload,
            headers={
                "usuario-id": "1",
                "rol-usuario": "rol_invalido"
            }
        )
        
        assert response.status_code == 400
        assert "Rol inválido" in response.json()["detail"]
    
    def test_crear_pedido_sin_productos(self, client):
        """Test crear pedido sin productos"""
        payload = {
            "nit": "123456789",
            "cliente_id": 100,
            "productos": []
        }
        
        response = client.post(
            "/api/v1/pedidos/",
            json=payload,
            headers={
                "usuario-id": "1",
                "rol-usuario": "usuario_institucional"
            }
        )
        
        assert response.status_code == 400
        assert "al menos un producto" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_crear_pedido_exitoso(self, client):
        """Test crear pedido exitoso"""
        payload = {
            "nit": "123456789",
            "cliente_id": 100,
            "productos": [
                {"producto_id": "PROD-001", "cantidad_solicitada": 10}
            ]
        }
        
        mock_pedido = PedidoResponse(
            pedido_id=str(uuid4()),
            numero_pedido="PED-000001",
            usuario_id=1,
            cliente_id=100,
            nit="123456789",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.PENDIENTE,
            monto_total=150000.0,
            fecha_creacion="2025-11-23T10:00:00",
            fecha_actualizacion="2025-11-23T10:00:00",
            observaciones=None,
            detalles=[
                DetallePedidoResponse(
                    detalle_id=str(uuid4()),
                    producto_id="PROD-001",
                    nombre_producto="Producto Test",
                    cantidad_solicitada=10,
                    cantidad_disponible_al_momento=100,
                    precio_unitario=15000.0,
                    subtotal=150000.0
                )
            ]
        )
        
        with patch("app.services.pedidos.PedidosService.crear_pedido") as mock_crear:
            mock_crear.return_value = (True, mock_pedido, "Pedido creado", [])
            
            response = client.post(
                "/api/v1/pedidos/",
                json=payload,
                headers={
                    "usuario-id": "1",
                    "rol-usuario": "usuario_institucional",
                    "nit-usuario": "123456789",
                    "cliente-id": "100"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["numero_pedido"] == "PED-000001"
        assert data["mensaje"] == "Pedido creado"
    
    @pytest.mark.asyncio
    async def test_crear_pedido_inventario_insuficiente(self, client):
        """Test crear pedido con inventario insuficiente"""
        payload = {
            "nit": "123456789",
            "cliente_id": 100,
            "productos": [
                {"producto_id": "PROD-001", "cantidad_solicitada": 100}
            ]
        }
        
        from app.schemas.pedido import ValidacionInventarioResult
        
        validaciones = [
            ValidacionInventarioResult(
                producto_id="PROD-001",
                disponible=False,
                cantidad_disponible=10,
                cantidad_solicitada=100,
                mensaje="Inventario insuficiente"
            )
        ]
        
        with patch("app.services.pedidos.PedidosService.crear_pedido") as mock_crear:
            mock_crear.return_value = (False, None, "Inventario insuficiente", validaciones)
            
            response = client.post(
                "/api/v1/pedidos/",
                json=payload,
                headers={
                    "usuario-id": "1",
                    "rol-usuario": "usuario_institucional",
                    "nit-usuario": "123456789"
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "INVENTARIO_INSUFICIENTE"
        assert len(data["detail"]["sugerencias"]) > 0


class TestObtenerPedidoEndpoint:
    """Tests para GET /api/v1/pedidos/{pedido_id}"""
    
    def test_obtener_pedido_existente(self, client):
        """Test obtener pedido que existe"""
        pedido_id = str(uuid4())
        
        mock_pedido = PedidoResponse(
            pedido_id=pedido_id,
            numero_pedido="PED-000001",
            usuario_id=1,
            cliente_id=100,
            nit="123456789",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.PENDIENTE,
            monto_total=100000.0,
            fecha_creacion="2025-11-23T10:00:00",
            fecha_actualizacion="2025-11-23T10:00:00",
            observaciones=None,
            detalles=[]
        )
        
        with patch("app.services.pedidos.PedidosService.obtener_pedido") as mock_obtener:
            mock_obtener.return_value = mock_pedido
            
            response = client.get(f"/api/v1/pedidos/{pedido_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["pedido_id"] == pedido_id
        assert data["numero_pedido"] == "PED-000001"
    
    def test_obtener_pedido_no_encontrado(self, client):
        """Test obtener pedido que no existe"""
        pedido_id = str(uuid4())
        
        with patch("app.services.pedidos.PedidosService.obtener_pedido") as mock_obtener:
            mock_obtener.return_value = None
            
            response = client.get(f"/api/v1/pedidos/{pedido_id}")
        
        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"].lower()


class TestObtenerHistorialEndpoint:
    """Tests para GET /api/v1/pedidos/{pedido_id}/historial"""
    
    def test_obtener_historial_pedido_no_encontrado(self, client):
        """Test obtener historial de pedido que no existe"""
        pedido_id = str(uuid4())
        
        response = client.get(f"/api/v1/pedidos/{pedido_id}/historial")
        
        assert response.status_code == 404


class TestListarPedidosEndpoint:
    """Tests para GET /api/v1/pedidos/"""
    
    def test_listar_pedidos_sin_filtros(self, client):
        """Test listar pedidos sin filtros"""
        with patch("app.services.pedidos.PedidosService.listar_pedidos") as mock_listar:
            mock_listar.return_value = ([], 0)
            
            response = client.get("/api/v1/pedidos/")
        
        assert response.status_code == 200
        data = response.json()
        assert "pedidos" in data
        assert "total" in data
        assert "pagina" in data
    
    def test_listar_pedidos_usuario_institucional(self, client):
        """Test listar pedidos como usuario institucional"""
        with patch("app.services.pedidos.PedidosService.listar_pedidos") as mock_listar:
            mock_listar.return_value = ([], 0)
            
            response = client.get(
                "/api/v1/pedidos/",
                headers={
                    "usuario-id": "1",
                    "rol-usuario": "usuario_institucional",
                    "nit-usuario": "123456789"
                }
            )
        
        assert response.status_code == 200
        # Verificar que se llamó con el NIT del usuario
        mock_listar.assert_called_once()
        args = mock_listar.call_args
        assert args.kwargs["nit"] == "123456789"
    
    @pytest.mark.asyncio
    async def test_listar_pedidos_gerente_con_nit_invalido(self, client):
        """Test listar pedidos como gerente con NIT no asignado"""
        with patch("app.services.pedidos.PedidosService.validar_nit_gerente_cuenta") as mock_validar:
            mock_validar.return_value = (False, "NIT no asignado")
            
            response = client.get(
                "/api/v1/pedidos/?nit=999999999",
                headers={
                    "usuario-id": "1",
                    "rol-usuario": "gerente_cuenta"
                }
            )
        
        assert response.status_code == 403
    
    def test_listar_pedidos_con_estado_invalido(self, client):
        """Test listar pedidos con estado inválido"""
        response = client.get("/api/v1/pedidos/?estado=estado_invalido")
        
        assert response.status_code == 400
        assert "Estado inválido" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_listar_pedidos_gerente_sin_nit(self, client):
        """Test listar pedidos como gerente sin especificar NIT"""
        with patch("app.services.pedidos.PedidosService.obtener_cliente_ids_gerente") as mock_ids:
            with patch("app.services.pedidos.PedidosService.listar_pedidos") as mock_listar:
                mock_ids.return_value = [100, 101, 102]
                mock_listar.return_value = ([], 0)
                
                response = client.get(
                    "/api/v1/pedidos/",
                    headers={
                        "usuario-id": "1",
                        "rol-usuario": "gerente_cuenta"
                    }
                )
        
        assert response.status_code == 200


class TestActualizarEstadoEndpoint:
    """Tests para PUT /api/v1/pedidos/{pedido_id}/estado"""
    
    def test_actualizar_estado_sin_permiso(self, client):
        """Test actualizar estado sin ser admin"""
        pedido_id = str(uuid4())
        payload = {
            "nuevo_estado": "enviado",
            "observaciones": "Test"
        }
        
        response = client.put(
            f"/api/v1/pedidos/{pedido_id}/estado",
            json=payload,
            headers={
                "rol-usuario": "usuario_institucional"
            }
        )
        
        assert response.status_code == 403
        assert "administradores" in response.json()["detail"].lower()
    
    def test_actualizar_estado_pedido_no_encontrado(self, client):
        """Test actualizar estado de pedido que no existe"""
        pedido_id = str(uuid4())
        payload = {
            "nuevo_estado": "enviado"
        }
        
        with patch("app.services.pedidos.PedidosService.obtener_pedido") as mock_obtener:
            mock_obtener.return_value = None
            
            response = client.put(
                f"/api/v1/pedidos/{pedido_id}/estado",
                json=payload,
                headers={
                    "rol-usuario": "admin"
                }
            )
        
        assert response.status_code == 404
    
    def test_actualizar_estado_exitoso(self, client):
        """Test actualizar estado exitosamente"""
        pedido_id = str(uuid4())
        payload = {
            "nuevo_estado": "enviado",
            "observaciones": "Pedido enviado"
        }
        
        mock_pedido_actual = PedidoResponse(
            pedido_id=pedido_id,
            numero_pedido="PED-000001",
            usuario_id=1,
            cliente_id=100,
            nit="123456789",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.PENDIENTE,
            monto_total=100000.0,
            fecha_creacion="2025-11-23T10:00:00",
            fecha_actualizacion="2025-11-23T10:00:00",
            observaciones=None,
            detalles=[]
        )
        
        mock_pedido_actualizado = PedidoResponse(
            pedido_id=pedido_id,
            numero_pedido="PED-000001",
            usuario_id=1,
            cliente_id=100,
            nit="123456789",
            rol_usuario="usuario_institucional",
            estado=EstadoPedido.ENVIADO,
            monto_total=100000.0,
            fecha_creacion="2025-11-23T10:00:00",
            fecha_actualizacion="2025-11-23T10:00:00",
            observaciones="Pedido enviado",
            detalles=[]
        )
        
        with patch("app.services.pedidos.PedidosService.obtener_pedido") as mock_obtener:
            with patch("app.services.pedidos.PedidosService.actualizar_estado_pedido") as mock_actualizar:
                mock_obtener.return_value = mock_pedido_actual
                mock_actualizar.return_value = mock_pedido_actualizado
                
                response = client.put(
                    f"/api/v1/pedidos/{pedido_id}/estado",
                    json=payload,
                    headers={
                        "rol-usuario": "admin"
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["estado_nuevo"] == "enviado"


class TestValidarInventarioEndpoint:
    """Tests para POST /api/v1/pedidos/validar-inventario"""
    
    @pytest.mark.asyncio
    async def test_validar_inventario_exitoso(self, client):
        """Test validar inventario sin crear pedido"""
        payload = {
            "nit": "123456789",
            "cliente_id": 100,
            "productos": [
                {"producto_id": "PROD-001", "cantidad_solicitada": 10}
            ]
        }
        
        with patch("app.services.pedidos.PedidosService.validar_pedido") as mock_validar:
            mock_validar.return_value = (True, [], "")
            
            response = client.post(
                "/api/v1/pedidos/validar-inventario",
                json=payload,
                headers={
                    "usuario-id": "1",
                    "rol-usuario": "usuario_institucional"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valido"] is True
    
    @pytest.mark.asyncio
    async def test_validar_inventario_insuficiente(self, client):
        """Test validar inventario con productos insuficientes"""
        payload = {
            "nit": "123456789",
            "cliente_id": 100,
            "productos": [
                {"producto_id": "PROD-001", "cantidad_solicitada": 1000}
            ]
        }
        
        from app.schemas.pedido import ValidacionInventarioResult
        
        validaciones = [
            ValidacionInventarioResult(
                producto_id="PROD-001",
                disponible=False,
                cantidad_disponible=10,
                cantidad_solicitada=1000,
                mensaje="Insuficiente"
            )
        ]
        
        with patch("app.services.pedidos.PedidosService.validar_pedido") as mock_validar:
            mock_validar.return_value = (False, validaciones, "Inventario insuficiente")
            
            response = client.post(
                "/api/v1/pedidos/validar-inventario",
                json=payload,
                headers={
                    "usuario-id": "1",
                    "rol-usuario": "usuario_institucional"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valido"] is False
        assert len(data["validaciones"]) > 0

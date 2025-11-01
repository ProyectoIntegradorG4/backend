"""
Test de Integración Completa: Flujo de Usuario → Crear Pedido

Este test valida el flujo completo:
1. Registrar usuario con NIT válido (que existe en la BD nit_db)
2. Crear pedido con al menos 3 productos desde el pedidos-service
3. Validar que el pedido se crea correctamente
"""

import pytest
import httpx
import json
from unittest.mock import patch, AsyncMock
import uuid

# URLs base de los servicios
USER_SERVICE_URL = "http://user-service:8001"
PEDIDOS_SERVICE_URL = "http://pedidos-service:8007"
PRODUCT_SERVICE_URL = "http://product-service:8005"

# NITs válidos que existen en la BD (de init-db.sql)
NITS_VALIDOS = [
    "901234567",  # Clínica Central
    "800123456",  # Hospital Universitario
    "900987654",  # Centro Médico Los Andes
]

# Datos de productos de prueba (simulados)
PRODUCTOS_PRUEBA = [
    {
        "producto_id": str(uuid.uuid4()),
        "nombre": "Vacuna COVID-19",
        "categoria": "Vacunas",
        "precio": 50000,
        "cantidad_disponible": 100,
        "requiere_cadena_frio": True
    },
    {
        "producto_id": str(uuid.uuid4()),
        "nombre": "Ibuprofeno 400mg",
        "categoria": "Analgésicos",
        "precio": 5000,
        "cantidad_disponible": 500,
        "requiere_cadena_frio": False
    },
    {
        "producto_id": str(uuid.uuid4()),
        "nombre": "Jeringa estéril 10ml",
        "categoria": "Dispositivos médicos",
        "precio": 2000,
        "cantidad_disponible": 1000,
        "requiere_cadena_frio": False
    },
    {
        "producto_id": str(uuid.uuid4()),
        "nombre": "Guantes de látex (caja 100)",
        "categoria": "Dispositivos médicos",
        "precio": 15000,
        "cantidad_disponible": 300,
        "requiere_cadena_frio": False
    }
]


class TestIntegracionCompleta:
    """Tests de integración completa entre servicios"""

    @pytest.mark.asyncio
    async def test_crear_usuario_y_pedido_con_3_productos(self, client):
        """
        Scenario: Crear usuario institucional y luego crear pedido con 3+ productos
        
        Given: Un NIT válido que existe en la BD
        When: Se registra un usuario con ese NIT
        And: Se crea un pedido con al menos 3 productos
        Then: El pedido se crea exitosamente
        """
        
        # 1. Preparar datos
        nit = NITS_VALIDOS[0]  # "901234567" - Clínica Central
        usuario_id = 1  # Usuario ID debe ser un entero
        email = f"test_cliente_{usuario_id}@clinica-central.com"
        nombre = "Test Cliente Institucional"
        password = "TestPassword123!"
        
        # 2. Mock del registro de usuario (normalmente se haría en user-service)
        # Para este test, simularemos que el usuario ya existe
        usuario_registrado = {
            "id": usuario_id,
            "nombre": nombre,
            "correo_electronico": email,
            "nit": nit,
            "rol": "usuario_institucional",
            "activo": True
        }
        
        print(f"\n✓ Usuario preparado: {nombre} con NIT: {nit}")
        
        # 3. Crear pedido con 3 productos
        productos_pedido = [
            {
                "producto_id": PRODUCTOS_PRUEBA[0]["producto_id"],
                "cantidad_solicitada": 10
            },
            {
                "producto_id": PRODUCTOS_PRUEBA[1]["producto_id"],
                "cantidad_solicitada": 50
            },
            {
                "producto_id": PRODUCTOS_PRUEBA[2]["producto_id"],
                "cantidad_solicitada": 25
            }
        ]
        
        payload = {
            "nit": nit,
            "productos": productos_pedido
        }
        
        # Mock del servicio de inventario
        def mock_validar_inventario(producto_id, cantidad):
            """Mock que valida inventario de los productos de prueba"""
            for producto in PRODUCTOS_PRUEBA:
                if producto["producto_id"] == producto_id:
                    if cantidad <= producto["cantidad_disponible"]:
                        return (
                            True,
                            producto["cantidad_disponible"],
                            producto["precio"],
                            "Inventario disponible"
                        )
                    else:
                        return (
                            False,
                            producto["cantidad_disponible"],
                            producto["precio"],
                            f"Cantidad insuficiente. Disponible: {producto['cantidad_disponible']}"
                        )
            return (False, 0, 0, "Producto no encontrado")
        
        def mock_obtener_info_producto(producto_id):
            """Mock que obtiene información del producto"""
            for producto in PRODUCTOS_PRUEBA:
                if producto["producto_id"] == producto_id:
                    return {
                        "producto_id": producto["producto_id"],
                        "nombre": producto["nombre"],
                        "precio": producto["precio"],
                        "cantidad_disponible": producto["cantidad_disponible"]
                    }
            return None
        
        # Ejecutar el request con mocks
        with patch("app.services.pedidos.PedidosService.validar_inventario_producto") as mock_validar:
            with patch("app.services.pedidos.PedidosService.obtener_info_producto") as mock_info:
                
                # Configurar los mocks para que usen nuestras funciones
                mock_validar.side_effect = lambda producto_id, cantidad: mock_validar_inventario(producto_id, cantidad)
                mock_info.side_effect = lambda producto_id: mock_obtener_info_producto(producto_id)
                
                # Crear el pedido con headers correctos
                response = client.post(
                    "/api/v1/pedidos/",
                    json=payload,
                    headers={
                        "usuario-id": str(usuario_id),
                        "rol-usuario": "usuario_institucional"
                    }
                )
        
        # 4. Validar respuesta
        print(f"\nRespuesta del servidor: {response.status_code}")
        data = response.json()
        print(f"Data: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 200, f"Error: {data}"
        assert data["exito"] == True, f"Pedido no creado: {data.get('mensaje')}"
        assert "numero_pedido" in data
        assert data["numero_pedido"].startswith("PED-")
        assert data["pedido"]["nit"] == nit
        assert data["pedido"]["rol_usuario"] == "usuario_institucional"
        assert len(data["pedido"]["detalles"]) == 3, "Debe tener 3 productos"
        
        print(f"\n✓ Pedido creado exitosamente: {data['numero_pedido']}")
        print(f"✓ Total productos: {len(data['pedido']['detalles'])}")
        print(f"✓ Monto total: ${data['pedido']['monto_total']}")
        
        return data

    @pytest.mark.asyncio
    async def test_crear_pedido_gerente_con_3_productos(self, client):
        """
        Scenario: Crear pedido como Gerente (admin) con 3+ productos
        
        Given: Un usuario con rol 'admin' (gerente de cuenta)
        When: Crea un pedido asociado a un NIT válido
        Then: El pedido se crea con estado 'pendiente'
        """
        
        # 1. Preparar datos del gerente
        gerente_id = 2  # Usuario ID debe ser un entero
        nit = NITS_VALIDOS[1]  # "800123456" - Hospital Universitario
        
        # 2. Preparar productos
        productos_pedido = [
            {
                "producto_id": PRODUCTOS_PRUEBA[1]["producto_id"],  # Ibuprofeno
                "cantidad_solicitada": 100
            },
            {
                "producto_id": PRODUCTOS_PRUEBA[2]["producto_id"],  # Jeringa
                "cantidad_solicitada": 200
            },
            {
                "producto_id": PRODUCTOS_PRUEBA[3]["producto_id"],  # Guantes
                "cantidad_solicitada": 50
            }
        ]
        
        payload = {
            "nit": nit,
            "productos": productos_pedido
        }
        
        # 3. Mock de validación
        def mock_validar_inventario(producto_id, cantidad):
            for producto in PRODUCTOS_PRUEBA:
                if producto["producto_id"] == producto_id:
                    if cantidad <= producto["cantidad_disponible"]:
                        return (True, producto["cantidad_disponible"], producto["precio"], "OK")
                    else:
                        return (False, producto["cantidad_disponible"], producto["precio"], "Insuficiente")
            return (False, 0, 0, "No encontrado")
        
        def mock_obtener_info_producto(producto_id):
            for producto in PRODUCTOS_PRUEBA:
                if producto["producto_id"] == producto_id:
                    return {
                        "producto_id": producto["producto_id"],
                        "nombre": producto["nombre"],
                        "precio": producto["precio"],
                        "cantidad_disponible": producto["cantidad_disponible"]
                    }
            return None
        
        with patch("app.services.pedidos.PedidosService.validar_inventario_producto") as mock_validar:
            with patch("app.services.pedidos.PedidosService.obtener_info_producto") as mock_info:
                
                mock_validar.side_effect = lambda producto_id, cantidad: mock_validar_inventario(producto_id, cantidad)
                mock_info.side_effect = lambda producto_id: mock_obtener_info_producto(producto_id)
                
                response = client.post(
                    "/api/v1/pedidos/",
                    json=payload,
                    headers={
                        "usuario-id": str(gerente_id),
                        "rol-usuario": "admin"
                    }
                )
        
        # 4. Validar respuesta
        print(f"\n[GERENTE] Respuesta: {response.status_code}")
        data = response.json()
        print(f"[GERENTE] Pedido: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 200
        assert data["exito"] == True
        assert len(data["pedido"]["detalles"]) == 3
        assert data["pedido"]["rol_usuario"] == "admin"
        
        print(f"\n✓ Pedido de gerente creado: {data['numero_pedido']}")
        print(f"✓ Para NIT: {nit}")
        print(f"✓ Productos: {len(data['pedido']['detalles'])}")
        
        return data

    @pytest.mark.asyncio
    async def test_listar_pedidos_del_usuario(self, client):
        """
        Scenario: Listar todos los pedidos del usuario
        
        Given: Un usuario ha creado varios pedidos
        When: Solicita listar sus pedidos
        Then: Obtiene lista con filtros aplicables
        """
        usuario_id = 3  # Usuario ID debe ser un entero
        nit = NITS_VALIDOS[2]  # "900987654" - Centro Médico Los Andes
        
        # Crear 2 pedidos primero
        for i in range(2):
            productos_pedido = [
                {
                    "producto_id": PRODUCTOS_PRUEBA[i]["producto_id"],
                    "cantidad_solicitada": 10 * (i + 1)
                }
            ]
            
            payload = {
                "nit": nit,
                "productos": productos_pedido
            }
            
            def mock_validar_inventario(producto_id, cantidad):
                for producto in PRODUCTOS_PRUEBA:
                    if producto["producto_id"] == producto_id:
                        return (True, producto["cantidad_disponible"], producto["precio"], "OK")
                return (False, 0, 0, "No encontrado")
            
            def mock_obtener_info_producto(producto_id):
                for producto in PRODUCTOS_PRUEBA:
                    if producto["producto_id"] == producto_id:
                        return {
                            "producto_id": producto["producto_id"],
                            "nombre": producto["nombre"],
                            "precio": producto["precio"],
                            "cantidad_disponible": producto["cantidad_disponible"]
                        }
                return None
            
            with patch("app.services.pedidos.PedidosService.validar_inventario_producto") as mock_validar:
                with patch("app.services.pedidos.PedidosService.obtener_info_producto") as mock_info:
                    
                    mock_validar.side_effect = lambda pid, cant: mock_validar_inventario(pid, cant)
                    mock_info.side_effect = lambda pid: mock_obtener_info_producto(pid)
                    
                    client.post(
                        "/api/v1/pedidos/",
                        json=payload,
                        headers={
                            "usuario-id": str(usuario_id),
                            "rol-usuario": "usuario_institucional"
                        }
                    )
        
        # Listar pedidos del usuario
        response = client.get(
            "/api/v1/pedidos/",
            headers={
                "usuario-id": str(usuario_id),
                "rol-usuario": "usuario_institucional"
            }
        )
        
        print(f"\n[LISTAR] Respuesta: {response.status_code}")
        data = response.json()
        print(f"[LISTAR] Total pedidos: {len(data.get('pedidos', []))}")
        
        assert response.status_code == 200
        assert "pedidos" in data
        assert len(data["pedidos"]) >= 2
        
        print(f"✓ Se encontraron {len(data['pedidos'])} pedidos")

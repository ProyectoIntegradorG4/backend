"""
Tests extendidos para ProductoService
Cubre métodos con baja cobertura: listar_productos, obtener_producto_por_id, 
actualizar_stock_producto, obtener_inventario_producto
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date, datetime
from app.service.product_service import ProductoService
from app.models.product import Producto
from app.models.category import CategoriaProducto
from app.models.inventory import InventarioLote


class TestProductoServiceListar:
    """Tests para listar_productos con diferentes filtros y ordenamiento"""
    
    def test_listar_productos_sin_filtros(self, db_session):
        """Listar todos los productos sin filtros"""
        # Crear categoría
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test Categoría",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add(categoria)
        
        # Crear productos
        for i in range(3):
            producto = Producto(
                productoId=f"PROD-{i:03d}",
                nombre=f"Producto {i}",
                descripcion=f"Descripción {i}",
                categoriaId="CAT-TEST-001",
                formaFarmaceutica="Tableta",
                requierePrescripcion=False,
                estado_producto="activo",
                stock=100 + i * 10,
                precio=1000.0 + i * 100
            )
            db_session.add(producto)
        
        db_session.commit()
        
        # Listar
        result = ProductoService.listar_productos(
            db=db_session,
            q=None,
            categoria_id=None,
            estado=None,
            sort="nombre",
            order="asc",
            page=1,
            page_size=25
        )
        
        assert result["total"] == 3
        assert len(result["items"]) == 3
        assert result["page"] == 1
        assert result["page_size"] == 25
        assert result["items"][0]["nombre"] == "Producto 0"
    
    def test_listar_productos_con_busqueda_nombre(self, db_session):
        """Buscar productos por nombre"""
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add(categoria)
        
        productos = [
            Producto(
                productoId="PROD-001",
                nombre="Acetaminofén 500mg",
                categoriaId="CAT-TEST-001",
                estado_producto="activo"
            ),
            Producto(
                productoId="PROD-002",
                nombre="Ibuprofeno 400mg",
                categoriaId="CAT-TEST-001",
                estado_producto="activo"
            ),
            Producto(
                productoId="PROD-003",
                nombre="Acetaminofén Forte",
                categoriaId="CAT-TEST-001",
                estado_producto="activo"
            )
        ]
        for p in productos:
            db_session.add(p)
        db_session.commit()
        
        # Buscar "Acetaminofén"
        result = ProductoService.listar_productos(
            db=db_session,
            q="Acetaminofén",
            categoria_id=None,
            estado=None,
            sort="nombre",
            order="asc",
            page=1,
            page_size=25
        )
        
        assert result["total"] == 2
        assert all("Acetaminofén" in item["nombre"] for item in result["items"])
    
    def test_listar_productos_filtro_categoria(self, db_session):
        """Filtrar productos por categoría"""
        # Crear 2 categorías
        cat1 = CategoriaProducto(
            categoriaId="CAT-001",
            nombre="Analgésicos",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        cat2 = CategoriaProducto(
            categoriaId="CAT-002",
            nombre="Antibióticos",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add_all([cat1, cat2])
        
        # Productos en diferentes categorías
        db_session.add(Producto(
            productoId="PROD-001",
            nombre="Acetaminofén",
            categoriaId="CAT-001",
            estado_producto="activo"
        ))
        db_session.add(Producto(
            productoId="PROD-002",
            nombre="Amoxicilina",
            categoriaId="CAT-002",
            estado_producto="activo"
        ))
        db_session.commit()
        
        # Filtrar por CAT-001
        result = ProductoService.listar_productos(
            db=db_session,
            q=None,
            categoria_id="CAT-001",
            estado=None,
            sort="nombre",
            order="asc",
            page=1,
            page_size=25
        )
        
        assert result["total"] == 1
        assert result["items"][0]["categoria"] == "Analgésicos"
    
    def test_listar_productos_filtro_estado(self, db_session):
        """Filtrar productos por estado"""
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add(categoria)
        
        # Productos con diferentes estados
        db_session.add(Producto(
            productoId="PROD-001",
            nombre="Producto Activo",
            categoriaId="CAT-TEST-001",
            estado_producto="activo"
        ))
        db_session.add(Producto(
            productoId="PROD-002",
            nombre="Producto Inactivo",
            categoriaId="CAT-TEST-001",
            estado_producto="inactivo"
        ))
        db_session.commit()
        
        # Filtrar por activo
        result = ProductoService.listar_productos(
            db=db_session,
            q=None,
            categoria_id=None,
            estado="activo",
            sort="nombre",
            order="asc",
            page=1,
            page_size=25
        )
        
        assert result["total"] == 1
        assert result["items"][0]["estado_producto"] == "activo"
    
    def test_listar_productos_ordenamiento_descendente(self, db_session):
        """Ordenar productos de forma descendente"""
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add(categoria)
        
        # Crear productos con diferentes nombres
        for nombre in ["Alpha", "Beta", "Gamma"]:
            db_session.add(Producto(
                productoId=f"PROD-{nombre}",
                nombre=nombre,
                categoriaId="CAT-TEST-001",
                estado_producto="activo"
            ))
        db_session.commit()
        
        # Ordenar desc
        result = ProductoService.listar_productos(
            db=db_session,
            q=None,
            categoria_id=None,
            estado=None,
            sort="nombre",
            order="desc",
            page=1,
            page_size=25
        )
        
        assert result["items"][0]["nombre"] == "Gamma"
        assert result["items"][-1]["nombre"] == "Alpha"
    
    def test_listar_productos_paginacion(self, db_session):
        """Verificar paginación funciona correctamente"""
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add(categoria)
        
        # Crear 10 productos
        for i in range(10):
            db_session.add(Producto(
                productoId=f"PROD-{i:03d}",
                nombre=f"Producto {i:03d}",
                categoriaId="CAT-TEST-001",
                estado_producto="activo"
            ))
        db_session.commit()
        
        # Página 1, 3 por página
        result = ProductoService.listar_productos(
            db=db_session,
            q=None,
            categoria_id=None,
            estado=None,
            sort="nombre",
            order="asc",
            page=1,
            page_size=3
        )
        
        assert result["total"] == 10
        assert len(result["items"]) == 3
        assert result["page"] == 1
        
        # Página 2
        result2 = ProductoService.listar_productos(
            db=db_session,
            q=None,
            categoria_id=None,
            estado=None,
            sort="nombre",
            order="asc",
            page=2,
            page_size=3
        )
        
        assert result2["page"] == 2
        assert len(result2["items"]) == 3
        # Verificar que son productos diferentes
        assert result["items"][0]["productoId"] != result2["items"][0]["productoId"]
    
    def test_listar_productos_con_lotes(self, db_session):
        """Listar productos con lotes asociados"""
        from app.models.warehouse import Bodega
        
        # Crear categoría y bodega
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        bodega = Bodega(
            bodegaId="BOD-001",
            nombre="Bodega Principal",
            pais="CO"
        )
        db_session.add_all([categoria, bodega])
        
        # Crear producto
        producto = Producto(
            productoId="PROD-001",
            nombre="Producto con Lotes",
            categoriaId="CAT-TEST-001",
            estado_producto="activo"
        )
        db_session.add(producto)
        db_session.commit()
        
        # Crear lote
        lote = InventarioLote(
            loteId="LOTE-001",
            productoId="PROD-001",
            bodegaId="BOD-001",
            pais="CO",
            stock=100,
            fechaVencimiento=date(2026, 12, 31)
        )
        db_session.add(lote)
        db_session.commit()
        
        # Listar
        result = ProductoService.listar_productos(
            db=db_session,
            q=None,
            categoria_id=None,
            estado=None,
            sort="nombre",
            order="asc",
            page=1,
            page_size=25
        )
        
        assert result["total"] == 1
        assert "lotes" in result["items"][0]
        assert len(result["items"][0]["lotes"]) == 1
        assert result["items"][0]["lotes"][0]["loteId"] == "LOTE-001"


class TestProductoServiceObtenerPorId:
    """Tests para obtener_producto_por_id"""
    
    def test_obtener_producto_existente(self, db_session):
        """Obtener producto que existe"""
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add(categoria)
        
        producto = Producto(
            productoId="PROD-001",
            nombre="Producto Test",
            categoriaId="CAT-TEST-001",
            estado_producto="activo"
        )
        db_session.add(producto)
        db_session.commit()
        
        # Obtener
        result = ProductoService.obtener_producto_por_id(db_session, "PROD-001")
        
        assert result is not None
        assert result.productoId == "PROD-001"
        assert result.nombre == "Producto Test"
    
    def test_obtener_producto_no_existe(self, db_session):
        """Obtener producto que no existe retorna None"""
        result = ProductoService.obtener_producto_por_id(db_session, "PROD-NOEXISTE")
        assert result is None


class TestProductoServiceActualizarStock:
    """Tests para actualizar_stock_producto"""
    
    def test_actualizar_stock_exitoso(self, db_session):
        """Actualizar stock de producto exitosamente"""
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add(categoria)
        
        producto = Producto(
            productoId="PROD-001",
            nombre="Producto Test",
            categoriaId="CAT-TEST-001",
            estado_producto="activo",
            stock=100
        )
        db_session.add(producto)
        db_session.commit()
        
        # Restar 30
        exito, nuevo_stock, mensaje = ProductoService.actualizar_stock_producto(
            db_session, "PROD-001", 30
        )
        
        assert exito is True
        assert nuevo_stock == 70
        assert "Stock actualizado" in mensaje
        
        # Verificar en DB
        db_session.refresh(producto)
        assert producto.stock == 70
    
    def test_actualizar_stock_insuficiente(self, db_session):
        """Intentar restar más stock del disponible"""
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add(categoria)
        
        producto = Producto(
            productoId="PROD-001",
            nombre="Producto Test",
            categoriaId="CAT-TEST-001",
            estado_producto="activo",
            stock=50
        )
        db_session.add(producto)
        db_session.commit()
        
        # Intentar restar 100 (solo hay 50)
        exito, stock_actual, mensaje = ProductoService.actualizar_stock_producto(
            db_session, "PROD-001", 100
        )
        
        assert exito is False
        assert stock_actual == 50
        assert "Stock insuficiente" in mensaje
        
        # Verificar que no cambió
        db_session.refresh(producto)
        assert producto.stock == 50
    
    def test_actualizar_stock_cantidad_invalida(self, db_session):
        """Intentar restar cantidad negativa o cero"""
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add(categoria)
        
        producto = Producto(
            productoId="PROD-001",
            nombre="Producto Test",
            categoriaId="CAT-TEST-001",
            estado_producto="activo",
            stock=100
        )
        db_session.add(producto)
        db_session.commit()
        
        # Cantidad negativa
        exito, _, mensaje = ProductoService.actualizar_stock_producto(
            db_session, "PROD-001", -10
        )
        
        assert exito is False
        assert "mayor que cero" in mensaje
        
        # Cantidad cero
        exito, _, mensaje = ProductoService.actualizar_stock_producto(
            db_session, "PROD-001", 0
        )
        
        assert exito is False
        assert "mayor que cero" in mensaje
    
    def test_actualizar_stock_producto_no_existe(self, db_session):
        """Intentar actualizar stock de producto inexistente"""
        exito, stock, mensaje = ProductoService.actualizar_stock_producto(
            db_session, "PROD-NOEXISTE", 10
        )
        
        assert exito is False
        assert stock == 0
        assert "no encontrado" in mensaje


class TestProductoServiceObtenerInventario:
    """Tests para obtener_inventario_producto"""
    
    def test_obtener_inventario_exitoso(self, db_session):
        """Obtener inventario de producto con stock"""
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add(categoria)
        
        producto = Producto(
            productoId="PROD-001",
            nombre="Producto Test",
            categoriaId="CAT-TEST-001",
            estado_producto="activo",
            stock=150,
            precio=2500.0,
            fechaVencimiento=date(2026, 6, 30)
        )
        db_session.add(producto)
        db_session.commit()
        
        # Obtener inventario
        cantidad, precio, fecha_venc = ProductoService.obtener_inventario_producto(
            db_session, "PROD-001"
        )
        
        assert cantidad == 150
        assert precio == 2500.0
        assert fecha_venc == date(2026, 6, 30)
    
    def test_obtener_inventario_sin_stock(self, db_session):
        """Obtener inventario de producto sin stock"""
        categoria = CategoriaProducto(
            categoriaId="CAT-TEST-001",
            nombre="Test",
            requiereCadenaFrio=False,
            requiereRegistroSanitario=False
        )
        db_session.add(categoria)
        
        producto = Producto(
            productoId="PROD-001",
            nombre="Producto Test",
            categoriaId="CAT-TEST-001",
            estado_producto="activo",
            stock=None,
            precio=1000.0
        )
        db_session.add(producto)
        db_session.commit()
        
        cantidad, precio, fecha_venc = ProductoService.obtener_inventario_producto(
            db_session, "PROD-001"
        )
        
        assert cantidad == 0
        assert precio == 1000.0
    
    def test_obtener_inventario_producto_no_existe(self, db_session):
        """Obtener inventario de producto inexistente"""
        cantidad, precio, fecha_venc = ProductoService.obtener_inventario_producto(
            db_session, "PROD-NOEXISTE"
        )
        
        assert cantidad == 0
        assert precio == 0.0
        assert fecha_venc is None


class TestProductoServiceNormalizePagination:
    """Tests para _normalize_pagination"""
    
    def test_normalize_valores_normales(self):
        """Normalizar valores válidos"""
        page, page_size, offset = ProductoService._normalize_pagination(2, 10)
        
        assert page == 2
        assert page_size == 10
        assert offset == 10  # (2-1) * 10
    
    def test_normalize_valores_none(self):
        """Normalizar cuando valores son None"""
        page, page_size, offset = ProductoService._normalize_pagination(None, None)
        
        assert page == 1
        assert page_size == 25
        assert offset == 0
    
    def test_normalize_primera_pagina(self):
        """Normalizar primera página"""
        page, page_size, offset = ProductoService._normalize_pagination(1, 50)
        
        assert page == 1
        assert page_size == 50
        assert offset == 0


class TestProductoServiceSkuVisible:
    """Tests para sku_visible"""
    
    def test_sku_visible_genera_formato_correcto(self):
        """Generar SKU visible con formato correcto"""
        producto_id = "12345678-1234-5678-1234-567812345678"
        sku = ProductoService.sku_visible(producto_id)
        
        assert sku.startswith("SKU-")
        assert len(sku) == 12  # SKU- (4) + 8 caracteres
        assert sku == "SKU-12345678"

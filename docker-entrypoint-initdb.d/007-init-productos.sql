-- Script de inicialización para tabla producto
-- Conectar a product_db
\c product_db

-- ============================================================
-- CREAR TABLA categoria_producto (requerida como FK)
-- ============================================================
CREATE TABLE IF NOT EXISTS categoria_producto (
    "categoriaId" VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion VARCHAR(500),
    "requiereCadenaFrio" BOOLEAN DEFAULT FALSE,
    "requiereRegistroSanitario" BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insertar categorías de ejemplo
INSERT INTO categoria_producto ("categoriaId", nombre, descripcion, "requiereCadenaFrio", "requiereRegistroSanitario", activo) VALUES
    ('CAT-ANL-001', 'Analgésicos', 'Medicamentos para el dolor', false, false, true),
    ('CAT-MED-001', 'Medicamentos Generales', 'Medicamentos de uso general', false, false, true),
    ('CAT-VIT-001', 'Vitaminas y Suplementos', 'Vitaminas y suplementos dietéticos', false, false, true)
ON CONFLICT ("categoriaId") DO UPDATE SET 
    nombre = excluded.nombre,
    "requiereCadenaFrio" = excluded."requiereCadenaFrio",
    "requiereRegistroSanitario" = excluded."requiereRegistroSanitario";

-- ============================================================
-- CREAR TABLA producto
-- ============================================================
CREATE TABLE IF NOT EXISTS producto (
    "productoId" VARCHAR(255) PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion VARCHAR(500),
    "categoriaId" VARCHAR(50) NOT NULL REFERENCES categoria_producto("categoriaId"),
    "formaFarmaceutica" VARCHAR(100),
    "requierePrescripcion" BOOLEAN DEFAULT FALSE,
    "registroSanitario" VARCHAR(255),
    sku VARCHAR(100),
    location VARCHAR(255),
    ubicacion VARCHAR(255),
    stock INTEGER DEFAULT 0,
    precio FLOAT DEFAULT 0.0,
    "estado_producto" VARCHAR(50) DEFAULT 'activo',
    "actualizado_en" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "fechaVencimiento" DATE
);

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_producto_sku ON producto(sku);
CREATE INDEX IF NOT EXISTS idx_producto_categoriaId ON producto("categoriaId");
CREATE INDEX IF NOT EXISTS idx_producto_estado ON producto("estado_producto");

-- ============================================================
-- INSERTAR PRODUCTOS DE PRUEBA
-- ============================================================
-- Estos productos son reales de tu base de datos y se usan en las rutas de entrega

INSERT INTO producto ("productoId", nombre, descripcion, "categoriaId", "formaFarmaceutica", "requierePrescripcion", sku, stock, precio, "estado_producto", "fechaVencimiento")
VALUES
    ('550e8400-e29b-41d4-a716-446655440000', 'Paracetamol 500mg', 'Analgésico y antipirético de uso común para el alivio del dolor y la fiebre', 'CAT-ANL-001', 'Tableta', false, 'PARA-500-TAB', 1000, 5000.00, 'activo', '2026-12-31'),
    ('550e8400-e29b-41d4-a716-446655440001', 'Ibuprofeno 400mg', 'Antiinflamatorio no esteroideo para dolor e inflamación', 'CAT-ANL-001', 'Tableta', false, 'IBU-400-TAB', 800, 7500.00, 'activo', '2026-12-31'),
    ('550e8400-e29b-41d4-a716-446655440002', 'Amoxicilina 500mg', 'Antibiótico de amplio espectro para infecciones bacterianas', 'CAT-MED-001', 'Cápsula', true, 'AMOX-500-CAP', 500, 12000.00, 'activo', '2026-06-30'),
    ('550e8400-e29b-41d4-a716-446655440003', 'Vitamina C 500mg', 'Suplemento de vitamina C para refuerzo inmunológico', 'CAT-VIT-001', 'Tableta', false, 'VIT-C-500-TAB', 1200, 3500.00, 'activo', '2026-12-31'),
    ('550e8400-e29b-41d4-a716-446655440004', 'Metformina 500mg', 'Medicamento para control de diabetes tipo 2', 'CAT-MED-001', 'Tableta', true, 'MET-500-TAB', 600, 2800.00, 'activo', '2026-12-31'),
    ('550e8400-e29b-41d4-a716-446655440005', 'Losartán 50mg', 'Medicamento para control de presión arterial alta', 'CAT-MED-001', 'Tableta', true, 'LOS-50-TAB', 450, 4200.00, 'activo', '2026-12-31'),
    ('550e8400-e29b-41d4-a716-446655440006', 'Diclofenaco 50mg', 'Antiinflamatorio para dolor agudo y crónico', 'CAT-ANL-001', 'Tableta', true, 'DICL-50-TAB', 700, 3800.00, 'activo', '2026-12-31'),
    ('550e8400-e29b-41d4-a716-446655440007', 'Omeprazol 20mg', 'Inhibidor de bomba de protones para problemas gástricos', 'CAT-MED-001', 'Cápsula', true, 'OMP-20-CAP', 550, 5200.00, 'activo', '2026-12-31')
ON CONFLICT ("productoId") DO NOTHING;

-- Otorgar permisos a product_service
GRANT ALL PRIVILEGES ON TABLE categoria_producto TO product_service;
GRANT ALL PRIVILEGES ON TABLE producto TO product_service;

-- ============================================================
-- CREAR TABLA bodega (requerida para inventario)
-- ============================================================
CREATE TABLE IF NOT EXISTS bodega (
    "bodegaId" VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    ciudad VARCHAR(255),
    pais VARCHAR(100),
    direccion VARCHAR(500),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insertar bodegas de ejemplo
INSERT INTO bodega ("bodegaId", nombre, ciudad, pais, direccion, activo)
VALUES
    ('BOD-BOGOTA-001', 'Bodega Principal Bogotá', 'Bogotá', 'Colombia', 'Calle 26 #68-90, Bogotá', true),
    ('BOD-MEDELLIN-001', 'Bodega Medellín', 'Medellín', 'Colombia', 'Carrera 43 #13-45, Medellín', true),
    ('BOD-CALI-001', 'Bodega Cali', 'Cali', 'Colombia', 'Carrera 2 #2-50, Cali', true)
ON CONFLICT ("bodegaId") DO NOTHING;

GRANT ALL PRIVILEGES ON TABLE bodega TO product_service;

-- ============================================================
-- CREAR TABLA inventario_lote
-- ============================================================
CREATE TABLE IF NOT EXISTS inventario_lote (
    loteId VARCHAR(255) PRIMARY KEY,
    "productoId" VARCHAR(255) NOT NULL REFERENCES producto("productoId"),
    "bodegaId" VARCHAR(50) NOT NULL REFERENCES bodega("bodegaId"),
    bodega VARCHAR(255),
    pais VARCHAR(100),
    stock INTEGER DEFAULT 0,
    "fechaVencimiento" DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_inventario_lote_producto ON inventario_lote("productoId");
CREATE INDEX IF NOT EXISTS idx_inventario_lote_bodega ON inventario_lote("bodegaId");

-- Insertar lotes de inventario
INSERT INTO inventario_lote (loteId, "productoId", "bodegaId", bodega, pais, stock, "fechaVencimiento")
VALUES
    ('LOTE-PARA-001', '550e8400-e29b-41d4-a716-446655440000', 'BOD-BOGOTA-001', 'Bodega Principal Bogotá', 'Colombia', 500, '2026-12-31'),
    ('LOTE-IBU-001', '550e8400-e29b-41d4-a716-446655440001', 'BOD-BOGOTA-001', 'Bodega Principal Bogotá', 'Colombia', 400, '2026-12-31'),
    ('LOTE-AMOX-001', '550e8400-e29b-41d4-a716-446655440002', 'BOD-BOGOTA-001', 'Bodega Principal Bogotá', 'Colombia', 250, '2026-06-30'),
    ('LOTE-VIT-001', '550e8400-e29b-41d4-a716-446655440003', 'BOD-BOGOTA-001', 'Bodega Principal Bogotá', 'Colombia', 600, '2026-12-31'),
    ('LOTE-MET-001', '550e8400-e29b-41d4-a716-446655440004', 'BOD-BOGOTA-001', 'Bodega Principal Bogotá', 'Colombia', 300, '2026-12-31'),
    ('LOTE-LOS-001', '550e8400-e29b-41d4-a716-446655440005', 'BOD-BOGOTA-001', 'Bodega Principal Bogotá', 'Colombia', 225, '2026-12-31'),
    ('LOTE-DICL-001', '550e8400-e29b-41d4-a716-446655440006', 'BOD-BOGOTA-001', 'Bodega Principal Bogotá', 'Colombia', 350, '2026-12-31'),
    ('LOTE-OMP-001', '550e8400-e29b-41d4-a716-446655440007', 'BOD-BOGOTA-001', 'Bodega Principal Bogotá', 'Colombia', 275, '2026-12-31')
ON CONFLICT (loteId) DO NOTHING;

GRANT ALL PRIVILEGES ON TABLE inventario_lote TO product_service;

-- ============================================================
-- MENSAJE DE CONFIRMACIÓN
-- ============================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Inicialización de tabla producto completada';
    RAISE NOTICE '📦 Categorías creadas: 3';
    RAISE NOTICE '📦 Productos insertados: 8';
    RAISE NOTICE '🏢 Bodegas creadas: 3';
    RAISE NOTICE '📊 Lotes de inventario: 8';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Para verificar los productos:';
    RAISE NOTICE '   docker exec -it postgres-db psql -U product_service -d product_db -c "SELECT * FROM producto LIMIT 5;"';
END $$;

-- Script de inicialización para Planes de Venta (HU-WEB-008)
-- Base de datos: product_db

\c product_db;

-- ========================================
-- TABLA: territorios
-- ========================================
CREATE TABLE IF NOT EXISTS territorios (
    territorio_id VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    pais VARCHAR(100) NOT NULL DEFAULT 'Colombia',
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insertar datos de territorios de ejemplo
INSERT INTO territorios (territorio_id, nombre, codigo, pais, activo) VALUES
('TERR-NORTE-BOG', 'Zona Norte Bogotá', 'ZN-BOG', 'Colombia', true),
('TERR-SUR-BOG', 'Zona Sur Bogotá', 'ZS-BOG', 'Colombia', true),
('TERR-SABANA', 'Sabana de Bogotá', 'SABANA', 'Colombia', true),
('TERR-ANTIOQUIA', 'Antioquia', 'ANTQ', 'Colombia', true),
('TERR-VALLE', 'Valle del Cauca', 'VALLE', 'Colombia', true),
('TERR-CARIBE', 'Región Caribe', 'CARIBE', 'Colombia', true),
('TERR-EJE-CAFETERO', 'Eje Cafetero', 'EJE-CAF', 'Colombia', true),
('TERR-SANTANDERES', 'Santanderes', 'STDR', 'Colombia', true),
('TERR-CENTRO', 'Región Centro', 'CENTRO', 'Colombia', true),
('TERR-PACIFICO', 'Región Pacífico', 'PACIF', 'Colombia', true)
ON CONFLICT (territorio_id) DO NOTHING;

-- Índices para optimizar búsquedas
CREATE INDEX IF NOT EXISTS idx_territorios_codigo ON territorios(codigo);
CREATE INDEX IF NOT EXISTS idx_territorios_pais ON territorios(pais);
CREATE INDEX IF NOT EXISTS idx_territorios_activo ON territorios(activo);

-- ========================================
-- DATOS DE PRUEBA: Productos
-- ========================================
-- Nota: Los productos se crean desde product-service en su inicialización
-- Esta sección está comentada porque la tabla producto se crea en el servicio
-- INSERT INTO producto ("productoId", nombre, descripcion, "categoriaId", "formaFarmaceutica", "requierePrescripcion", sku, stock, precio, estado_producto) VALUES
-- ('550e8400-e29b-41d4-a716-446655440000', 'Paracetamol 500mg', 'Analgésico y antipirético de uso común', 'CAT-ANL-001', 'Tableta', false, 'PARA-500-TAB', 1000, 5000.00, 'activo'),
-- ('550e8400-e29b-41d4-a716-446655440001', 'Ibuprofeno 400mg', 'Antiinflamatorio no esteroideo', 'CAT-ANL-001', 'Tableta', false, 'IBU-400-TAB', 800, 7500.00, 'activo'),
-- ('550e8400-e29b-41d4-a716-446655440002', 'Amoxicilina 500mg', 'Antibiótico de amplio espectro', 'CAT-MED-001', 'Cápsula', true, 'AMOX-500-CAP', 500, 12000.00, 'activo')
-- ON CONFLICT ("productoId") DO NOTHING;

-- ========================================
-- TABLA: plan_venta
-- ========================================
CREATE TABLE IF NOT EXISTS plan_venta (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(255) NOT NULL,
    periodo_desde DATE NOT NULL,
    periodo_hasta DATE NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'activo' CHECK (estado IN ('borrador', 'activo', 'cerrado')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    CONSTRAINT periodo_valido CHECK (periodo_hasta >= periodo_desde)
);

-- Índices para plan_venta
CREATE INDEX IF NOT EXISTS idx_plan_venta_estado ON plan_venta(estado);
CREATE INDEX IF NOT EXISTS idx_plan_venta_periodo ON plan_venta(periodo_desde, periodo_hasta);
CREATE INDEX IF NOT EXISTS idx_plan_venta_nombre ON plan_venta(nombre);

-- ========================================
-- TABLA: plan_venta_territorio
-- ========================================
CREATE TABLE IF NOT EXISTS plan_venta_territorio (
    id SERIAL PRIMARY KEY,
    plan_id UUID NOT NULL REFERENCES plan_venta(plan_id) ON DELETE CASCADE,
    territorio_id VARCHAR(50) NOT NULL REFERENCES territorios(territorio_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(plan_id, territorio_id)
);

-- Índices para plan_venta_territorio
CREATE INDEX IF NOT EXISTS idx_plan_territorio_plan ON plan_venta_territorio(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_territorio_territorio ON plan_venta_territorio(territorio_id);

-- ========================================
-- TABLA: plan_meta
-- ========================================
CREATE TABLE IF NOT EXISTS plan_meta (
    meta_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES plan_venta(plan_id) ON DELETE CASCADE,
    producto_id VARCHAR(255) NOT NULL,
    territorio_id VARCHAR(50) NOT NULL REFERENCES territorios(territorio_id),
    vendedor_id INTEGER NOT NULL,
    objetivo_cantidad INTEGER DEFAULT 0 CHECK (objetivo_cantidad >= 0),
    objetivo_valor DECIMAL(15,2) DEFAULT 0 CHECK (objetivo_valor >= 0),
    nota TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT meta_objetivo_requerido CHECK (objetivo_cantidad > 0 OR objetivo_valor > 0),
    UNIQUE(plan_id, producto_id, territorio_id, vendedor_id)
);

-- Índices para plan_meta
CREATE INDEX IF NOT EXISTS idx_plan_meta_plan ON plan_meta(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_meta_producto ON plan_meta(producto_id);
CREATE INDEX IF NOT EXISTS idx_plan_meta_territorio ON plan_meta(territorio_id);
CREATE INDEX IF NOT EXISTS idx_plan_meta_vendedor ON plan_meta(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_plan_meta_combinacion ON plan_meta(plan_id, producto_id, territorio_id, vendedor_id);

-- Otorgar permisos al usuario product_service
GRANT ALL PRIVILEGES ON TABLE territorios TO product_service;
GRANT ALL PRIVILEGES ON TABLE plan_venta TO product_service;
GRANT ALL PRIVILEGES ON TABLE plan_venta_territorio TO product_service;
GRANT ALL PRIVILEGES ON TABLE plan_meta TO product_service;
GRANT ALL PRIVILEGES ON SEQUENCE plan_venta_territorio_id_seq TO product_service;

-- Comentarios para documentación
COMMENT ON TABLE territorios IS 'Catálogo de territorios de venta';
COMMENT ON TABLE plan_venta IS 'Planes de venta con período de vigencia';
COMMENT ON TABLE plan_venta_territorio IS 'Relación entre planes de venta y territorios';
COMMENT ON TABLE plan_meta IS 'Metas de ventas por producto, territorio y vendedor dentro de un plan';
COMMENT ON CONSTRAINT meta_objetivo_requerido ON plan_meta IS 'Al menos un objetivo (cantidad o valor) debe ser mayor a 0';
COMMENT ON CONSTRAINT periodo_valido ON plan_venta IS 'La fecha hasta debe ser mayor o igual a la fecha desde';

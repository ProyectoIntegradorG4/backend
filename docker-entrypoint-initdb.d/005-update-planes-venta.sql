-- 005-update-planes-venta.sql
-- Optimizaciones para HU-WEB-009: Listado de Planes de Venta
-- Agrega índices para mejorar el rendimiento de búsquedas y filtros

\c product_db;

-- ========================================
-- EXTENSIÓN PARA BÚSQUEDA FUZZY (pg_trgm)
-- ========================================

-- Habilitar extensión para búsqueda con ILIKE optimizada (CREAR PRIMERO)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ========================================
-- ÍNDICES PARA PLAN_VENTA
-- ========================================

-- Índice para búsqueda por nombre (ILIKE)
CREATE INDEX IF NOT EXISTS idx_plan_venta_nombre ON plan_venta USING gin (nombre gin_trgm_ops);

-- Índice para filtro por estado
CREATE INDEX IF NOT EXISTS idx_plan_venta_estado ON plan_venta (estado);

-- Índice para ordenamiento por periodo_desde
CREATE INDEX IF NOT EXISTS idx_plan_venta_periodo_desde ON plan_venta (periodo_desde DESC);

-- Índice para ordenamiento por updated_at
CREATE INDEX IF NOT EXISTS idx_plan_venta_updated_at ON plan_venta (updated_at DESC);

-- Índice compuesto para filtros de período (intersección)
CREATE INDEX IF NOT EXISTS idx_plan_venta_periodo_range ON plan_venta (periodo_desde, periodo_hasta);

-- Índice para nombre único (ya existe constraint, pero mejora búsquedas exactas)
CREATE UNIQUE INDEX IF NOT EXISTS idx_plan_venta_nombre_unique ON plan_venta (nombre);


-- ========================================
-- ÍNDICES PARA PLAN_VENTA_TERRITORIO
-- ========================================

-- Índice para filtro por territorio
CREATE INDEX IF NOT EXISTS idx_plan_territorio_territorio_id ON plan_venta_territorio (territorio_id);

-- Índice compuesto para JOIN eficiente
CREATE INDEX IF NOT EXISTS idx_plan_territorio_plan_territorio ON plan_venta_territorio (plan_id, territorio_id);


-- ========================================
-- ÍNDICES PARA PLAN_META
-- ========================================

-- Índice para filtro por producto (opcional en HU-009)
CREATE INDEX IF NOT EXISTS idx_plan_meta_producto_id ON plan_meta (producto_id);

-- Índice compuesto para JOIN eficiente con plan
CREATE INDEX IF NOT EXISTS idx_plan_meta_plan_id ON plan_meta (plan_id);


-- ========================================
-- VERIFICACIÓN
-- ========================================

-- Listar todos los índices creados en plan_venta
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('plan_venta', 'plan_venta_territorio', 'plan_meta')
ORDER BY tablename, indexname;

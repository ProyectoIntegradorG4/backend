-- Script para datos de prueba de reportes (HU-WEB-010)
-- Crea pedidos históricos y metas para probar los endpoints de reportes

-- ========================================
-- DATOS DE PRUEBA: Pedidos para Reportes
-- ========================================

\c pedidos_db;

-- Nota: Los pedidos necesitan detalles para calcular unidades vendidas
-- Primero verificamos si existe la tabla detalles_pedido

CREATE TABLE IF NOT EXISTS detalles_pedido (
    detalle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pedido_id UUID NOT NULL REFERENCES pedidos(pedido_id) ON DELETE CASCADE,
    producto_id VARCHAR(255) NOT NULL,
    cantidad_solicitada INTEGER NOT NULL CHECK (cantidad_solicitada > 0),
    cantidad_confirmada INTEGER DEFAULT 0 CHECK (cantidad_confirmada >= 0),
    precio_unitario DECIMAL(15,2) NOT NULL CHECK (precio_unitario >= 0),
    subtotal DECIMAL(15,2) NOT NULL CHECK (subtotal >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_detalles_pedido_id ON detalles_pedido(pedido_id);
CREATE INDEX IF NOT EXISTS idx_detalles_producto_id ON detalles_pedido(producto_id);

-- Actualizar tabla pedidos para agregar monto_total si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='pedidos' AND column_name='monto_total') THEN
        ALTER TABLE pedidos ADD COLUMN monto_total DECIMAL(15,2) DEFAULT 0;
    END IF;
END $$;

-- Otorgar permisos
GRANT ALL PRIVILEGES ON TABLE detalles_pedido TO pedidos_service;

-- Insertar pedidos de prueba para Q1 2026 (Enero - Marzo)
-- Vendedor 3 (Carlos Vendedor) - Zona Norte Bogotá

-- Enero 2026 - 5 pedidos
INSERT INTO pedidos (pedido_id, usuario_id, cliente_id, nit, estado, monto_total, fecha_creacion, fecha_actualizacion) VALUES
('a1111111-0000-0000-0000-000000000001', 3, 1, '901234567', 'entregado', 1500000.00, '2026-01-05 10:00:00+00', '2026-01-06 10:00:00+00'),
('a1111111-0000-0000-0000-000000000002', 3, 2, '800123456', 'entregado', 2300000.00, '2026-01-12 14:30:00+00', '2026-01-13 14:30:00+00'),
('a1111111-0000-0000-0000-000000000003', 3, 1, '901234567', 'entregado', 800000.00, '2026-01-18 09:15:00+00', '2026-01-19 09:15:00+00'),
('a1111111-0000-0000-0000-000000000004', 3, 3, '900987654', 'entregado', 1200000.00, '2026-01-22 16:45:00+00', '2026-01-23 16:45:00+00'),
('a1111111-0000-0000-0000-000000000005', 3, 2, '800123456', 'cancelado', 500000.00, '2026-01-28 11:20:00+00', '2026-01-28 11:20:00+00')
ON CONFLICT (pedido_id) DO NOTHING;

-- Detalles de pedidos Enero
INSERT INTO detalles_pedido (pedido_id, producto_id, cantidad_solicitada, cantidad_confirmada, precio_unitario, subtotal) VALUES
-- Pedido 1: 100 unidades Paracetamol
('a1111111-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440000', 100, 100, 15000.00, 1500000.00),
-- Pedido 2: 50 Paracetamol + 30 Ibuprofeno
('a1111111-0000-0000-0000-000000000002', '550e8400-e29b-41d4-a716-446655440000', 50, 50, 15000.00, 750000.00),
('a1111111-0000-0000-0000-000000000002', '550e8400-e29b-41d4-a716-446655440001', 30, 30, 25000.00, 750000.00),
('a1111111-0000-0000-0000-000000000002', '550e8400-e29b-41d4-a716-446655440002', 20, 20, 40000.00, 800000.00),
-- Pedido 3: 40 unidades Ibuprofeno
('a1111111-0000-0000-0000-000000000003', '550e8400-e29b-41d4-a716-446655440001', 40, 40, 20000.00, 800000.00),
-- Pedido 4: 30 Amoxicilina
('a1111111-0000-0000-0000-000000000004', '550e8400-e29b-41d4-a716-446655440002', 30, 30, 40000.00, 1200000.00),
-- Pedido 5 (cancelado - no cuenta)
('a1111111-0000-0000-0000-000000000005', '550e8400-e29b-41d4-a716-446655440000', 25, 0, 20000.00, 500000.00)
ON CONFLICT (detalle_id) DO NOTHING;

-- Febrero 2026 - 6 pedidos
INSERT INTO pedidos (pedido_id, usuario_id, cliente_id, nit, estado, monto_total, fecha_creacion, fecha_actualizacion) VALUES
('a2222222-0000-0000-0000-000000000001', 3, 1, '901234567', 'entregado', 1800000.00, '2026-02-03 08:00:00+00', '2026-02-04 08:00:00+00'),
('a2222222-0000-0000-0000-000000000002', 3, 4, '811234567', 'entregado', 2500000.00, '2026-02-10 12:30:00+00', '2026-02-11 12:30:00+00'),
('a2222222-0000-0000-0000-000000000003', 3, 2, '800123456', 'entregado', 950000.00, '2026-02-15 10:20:00+00', '2026-02-16 10:20:00+00'),
('a2222222-0000-0000-0000-000000000004', 3, 1, '901234567', 'entregado', 1400000.00, '2026-02-20 15:45:00+00', '2026-02-21 15:45:00+00'),
('a2222222-0000-0000-0000-000000000005', 3, 3, '900987654', 'entregado', 2100000.00, '2026-02-24 09:30:00+00', '2026-02-25 09:30:00+00'),
('a2222222-0000-0000-0000-000000000006', 3, 4, '811234567', 'enviado', 1650000.00, '2026-02-27 14:00:00+00', '2026-02-27 14:00:00+00')
ON CONFLICT (pedido_id) DO NOTHING;

-- Detalles Febrero
INSERT INTO detalles_pedido (pedido_id, producto_id, cantidad_solicitada, cantidad_confirmada, precio_unitario, subtotal) VALUES
('a2222222-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440000', 120, 120, 15000.00, 1800000.00),
('a2222222-0000-0000-0000-000000000002', '550e8400-e29b-41d4-a716-446655440001', 50, 50, 25000.00, 1250000.00),
('a2222222-0000-0000-0000-000000000002', '550e8400-e29b-41d4-a716-446655440002', 30, 30, 41666.67, 1250000.00),
('a2222222-0000-0000-0000-000000000003', '550e8400-e29b-41d4-a716-446655440000', 60, 60, 15833.33, 950000.00),
('a2222222-0000-0000-0000-000000000004', '550e8400-e29b-41d4-a716-446655440001', 56, 56, 25000.00, 1400000.00),
('a2222222-0000-0000-0000-000000000005', '550e8400-e29b-41d4-a716-446655440002', 50, 50, 42000.00, 2100000.00),
('a2222222-0000-0000-0000-000000000006', '550e8400-e29b-41d4-a716-446655440000', 110, 110, 15000.00, 1650000.00)
ON CONFLICT (detalle_id) DO NOTHING;

-- Marzo 2026 - 7 pedidos
INSERT INTO pedidos (pedido_id, usuario_id, cliente_id, nit, estado, monto_total, fecha_creacion, fecha_actualizacion) VALUES
('a3333333-0000-0000-0000-000000000001', 3, 1, '901234567', 'entregado', 2200000.00, '2026-03-02 09:15:00+00', '2026-03-03 09:15:00+00'),
('a3333333-0000-0000-0000-000000000002', 3, 2, '800123456', 'entregado', 1750000.00, '2026-03-08 13:40:00+00', '2026-03-09 13:40:00+00'),
('a3333333-0000-0000-0000-000000000003', 3, 4, '811234567', 'entregado', 2800000.00, '2026-03-12 10:50:00+00', '2026-03-13 10:50:00+00'),
('a3333333-0000-0000-0000-000000000004', 3, 3, '900987654', 'entregado', 1200000.00, '2026-03-18 16:20:00+00', '2026-03-19 16:20:00+00'),
('a3333333-0000-0000-0000-000000000005', 3, 1, '901234567', 'entregado', 3100000.00, '2026-03-22 11:30:00+00', '2026-03-23 11:30:00+00'),
('a3333333-0000-0000-0000-000000000006', 3, 2, '800123456', 'entregado', 1950000.00, '2026-03-26 14:10:00+00', '2026-03-27 14:10:00+00'),
('a3333333-0000-0000-0000-000000000007', 3, 4, '811234567', 'pendiente', 2300000.00, '2026-03-30 15:45:00+00', '2026-03-30 15:45:00+00')
ON CONFLICT (pedido_id) DO NOTHING;

-- Detalles Marzo
INSERT INTO detalles_pedido (pedido_id, producto_id, cantidad_solicitada, cantidad_confirmada, precio_unitario, subtotal) VALUES
('a3333333-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440000', 100, 100, 15000.00, 1500000.00),
('a3333333-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440001', 28, 28, 25000.00, 700000.00),
('a3333333-0000-0000-0000-000000000002', '550e8400-e29b-41d4-a716-446655440002', 42, 42, 41666.67, 1750000.00),
('a3333333-0000-0000-0000-000000000003', '550e8400-e29b-41d4-a716-446655440000', 140, 140, 20000.00, 2800000.00),
('a3333333-0000-0000-0000-000000000004', '550e8400-e29b-41d4-a716-446655440001', 48, 48, 25000.00, 1200000.00),
('a3333333-0000-0000-0000-000000000005', '550e8400-e29b-41d4-a716-446655440000', 150, 150, 15000.00, 2250000.00),
('a3333333-0000-0000-0000-000000000005', '550e8400-e29b-41d4-a716-446655440002', 20, 20, 42500.00, 850000.00),
('a3333333-0000-0000-0000-000000000006', '550e8400-e29b-41d4-a716-446655440001', 78, 78, 25000.00, 1950000.00),
('a3333333-0000-0000-0000-000000000007', '550e8400-e29b-41d4-a716-446655440000', 92, 92, 25000.00, 2300000.00)
ON CONFLICT (detalle_id) DO NOTHING;

-- Pedidos de otros vendedores para comparación
-- Vendedor 4 (Ana Comercial) - Zona Norte
INSERT INTO pedidos (pedido_id, usuario_id, cliente_id, nit, estado, monto_total, fecha_creacion, fecha_actualizacion) VALUES
('b1111111-0000-0000-0000-000000000001', 4, 1, '901234567', 'entregado', 1900000.00, '2026-01-15 10:00:00+00', '2026-01-16 10:00:00+00'),
('b1111111-0000-0000-0000-000000000002', 4, 2, '800123456', 'entregado', 2700000.00, '2026-02-12 14:30:00+00', '2026-02-13 14:30:00+00'),
('b1111111-0000-0000-0000-000000000003', 4, 3, '900987654', 'entregado', 3200000.00, '2026-03-10 09:15:00+00', '2026-03-11 09:15:00+00')
ON CONFLICT (pedido_id) DO NOTHING;

INSERT INTO detalles_pedido (pedido_id, producto_id, cantidad_solicitada, cantidad_confirmada, precio_unitario, subtotal) VALUES
('b1111111-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440000', 95, 95, 20000.00, 1900000.00),
('b1111111-0000-0000-0000-000000000002', '550e8400-e29b-41d4-a716-446655440001', 108, 108, 25000.00, 2700000.00),
('b1111111-0000-0000-0000-000000000003', '550e8400-e29b-41d4-a716-446655440000', 160, 160, 20000.00, 3200000.00)
ON CONFLICT (detalle_id) DO NOTHING;

-- Vendedor 5 (Luis Ventas) - Zona Sur
INSERT INTO pedidos (pedido_id, usuario_id, cliente_id, nit, estado, monto_total, fecha_creacion, fecha_actualizacion) VALUES
('c1111111-0000-0000-0000-000000000001', 5, 5, '123456789', 'entregado', 1500000.00, '2026-01-20 11:00:00+00', '2026-01-21 11:00:00+00'),
('c1111111-0000-0000-0000-000000000002', 5, 6, '555123456', 'entregado', 2100000.00, '2026-02-18 13:30:00+00', '2026-02-19 13:30:00+00'),
('c1111111-0000-0000-0000-000000000003', 5, 5, '123456789', 'entregado', 1800000.00, '2026-03-15 10:20:00+00', '2026-03-16 10:20:00+00')
ON CONFLICT (pedido_id) DO NOTHING;

INSERT INTO detalles_pedido (pedido_id, producto_id, cantidad_solicitada, cantidad_confirmada, precio_unitario, subtotal) VALUES
('c1111111-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440001', 60, 60, 25000.00, 1500000.00),
('c1111111-0000-0000-0000-000000000002', '550e8400-e29b-41d4-a716-446655440002', 50, 50, 42000.00, 2100000.00),
('c1111111-0000-0000-0000-000000000003', '550e8400-e29b-41d4-a716-446655440001', 72, 72, 25000.00, 1800000.00)
ON CONFLICT (detalle_id) DO NOTHING;

-- ========================================
-- DATOS DE PRUEBA: Metas (PlanVenta)
-- ========================================

\c product_db;

-- Crear plan de venta Q1 2026
INSERT INTO plan_venta (plan_id, nombre, periodo_desde, periodo_hasta, estado, created_by) VALUES
('plan-q1-2026-0000-0000-000000000001', 'Plan Q1 2026 - Colombia', '2026-01-01', '2026-03-31', 'activo', 1)
ON CONFLICT (plan_id) DO NOTHING;

-- Asignar territorios al plan
INSERT INTO plan_venta_territorio (plan_id, territorio_id) VALUES
('plan-q1-2026-0000-0000-000000000001', 'TERR-NORTE-BOG'),
('plan-q1-2026-0000-0000-000000000001', 'TERR-SUR-BOG'),
('plan-q1-2026-0000-0000-000000000001', 'TERR-SABANA')
ON CONFLICT (plan_id, territorio_id) DO NOTHING;

-- Metas para vendedor 3 (Carlos) - Zona Norte
-- Meta total Q1: 2000 unidades, $40,000,000 COP
INSERT INTO plan_meta (meta_id, plan_id, producto_id, territorio_id, vendedor_id, objetivo_cantidad, objetivo_valor, nota) VALUES
-- Paracetamol: 1200 unidades, $20,000,000
('meta-q1-2026-0000-0000-000000000001', 'plan-q1-2026-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440000', 'TERR-NORTE-BOG', 3, 1200, 20000000.00, 'Producto estrella Q1'),
-- Ibuprofeno: 500 unidades, $12,000,000
('meta-q1-2026-0000-0000-000000000002', 'plan-q1-2026-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440001', 'TERR-NORTE-BOG', 3, 500, 12000000.00, 'Crecimiento esperado'),
-- Amoxicilina: 300 unidades, $8,000,000
('meta-q1-2026-0000-0000-000000000003', 'plan-q1-2026-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440002', 'TERR-NORTE-BOG', 3, 300, 8000000.00, 'Producto recetado')
ON CONFLICT (meta_id) DO NOTHING;

-- Metas para vendedor 4 (Ana) - Zona Norte
INSERT INTO plan_meta (meta_id, plan_id, producto_id, territorio_id, vendedor_id, objetivo_cantidad, objetivo_valor, nota) VALUES
('meta-q1-2026-0000-0000-000000000004', 'plan-q1-2026-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440000', 'TERR-NORTE-BOG', 4, 800, 15000000.00, 'Zona consolidada'),
('meta-q1-2026-0000-0000-000000000005', 'plan-q1-2026-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440001', 'TERR-NORTE-BOG', 4, 400, 10000000.00, 'Crecimiento')
ON CONFLICT (meta_id) DO NOTHING;

-- Metas para vendedor 5 (Luis) - Zona Sur
INSERT INTO plan_meta (meta_id, plan_id, producto_id, territorio_id, vendedor_id, objetivo_cantidad, objetivo_valor, nota) VALUES
('meta-q1-2026-0000-0000-000000000006', 'plan-q1-2026-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440001', 'TERR-SUR-BOG', 5, 600, 14000000.00, 'Zona en desarrollo'),
('meta-q1-2026-0000-0000-000000000007', 'plan-q1-2026-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440002', 'TERR-SUR-BOG', 5, 350, 9000000.00, 'Expansión')
ON CONFLICT (meta_id) DO NOTHING;

-- ========================================
-- RESUMEN DE DATOS PARA REPORTES
-- ========================================
-- Vendedor 3 (Carlos) - Q1 2026:
--   Enero: $5,800,000 (270 unidades) - 4 pedidos entregados
--   Febrero: $10,400,000 (496 unidades) - 6 pedidos entregados/enviados
--   Marzo: $15,300,000 (758 unidades) - 7 pedidos
--   TOTAL Q1: $31,500,000 - 1,524 unidades - 17 pedidos
--   
--   Metas Q1: 2,000 unidades, $40,000,000
--   Cumplimiento: 76.2% unidades, 78.75% valor
--
-- Vendedor 4 (Ana) - Q1 2026:
--   TOTAL: $7,800,000 - 363 unidades - 3 pedidos
--   Metas Q1: 1,200 unidades, $25,000,000
--   Cumplimiento: 30.25% unidades, 31.2% valor
--
-- Vendedor 5 (Luis) - Q1 2026:
--   TOTAL: $5,400,000 - 182 unidades - 3 pedidos
--   Metas Q1: 950 unidades, $23,000,000
--   Cumplimiento: 19.16% unidades, 23.48% valor

\echo 'Datos de prueba para reportes insertados correctamente'
\echo 'Vendedores configurados: 3 (Carlos), 4 (Ana), 5 (Luis)'
\echo 'Periodo: Q1 2026 (2026-01-01 a 2026-03-31)'
\echo 'Total pedidos: 23 (20 entregados/enviados, 1 pendiente, 2 cancelados)'
\echo 'Metas configuradas en plan_venta para comparación de cumplimiento'

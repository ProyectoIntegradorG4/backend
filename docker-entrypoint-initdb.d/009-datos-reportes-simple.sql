-- Datos de prueba simplificados para reportes (HU-WEB-010)
-- Ejecutar después de que los servicios estén corriendo

\c pedidos_db;

-- Insertar algunos pedidos de ejemplo para reportes Q1 2026
-- Vendedor 3 (Carlos) - Enero

-- Solo insertar si no existen ya
DO $$
BEGIN
    -- Pedido 1
    IF NOT EXISTS (SELECT 1 FROM pedidos WHERE pedido_id = '11111111-1111-4111-8111-111111111111') THEN
        INSERT INTO pedidos (pedido_id, usuario_id, cliente_id, nit, estado, monto_total, fecha_creacion, fecha_actualizacion) VALUES
        ('11111111-1111-4111-8111-111111111111', 3, 1, '901234567', 'entregado', 1500000.00, '2026-01-05 10:00:00+00', '2026-01-06 10:00:00+00');
        
        INSERT INTO detalles_pedido (detalle_id, pedido_id, producto_id, nombre_producto, cantidad_solicitada, cantidad_disponible_al_momento, cantidad_confirmada, precio_unitario, subtotal, fecha_agregado) VALUES
        ('d1111111-1111-4111-8111-111111111111', '11111111-1111-4111-8111-111111111111', '550e8400-e29b-41d4-a716-446655440000', 'Paracetamol 500mg', 100, 1000, 100, 15000.00, 1500000.00, '2026-01-05 10:00:00+00');
    END IF;
    
    -- Pedido 2
    IF NOT EXISTS (SELECT 1 FROM pedidos WHERE pedido_id = '22222222-2222-4222-8222-222222222222') THEN
        INSERT INTO pedidos (pedido_id, usuario_id, cliente_id, nit, estado, monto_total, fecha_creacion, fecha_actualizacion) VALUES
        ('22222222-2222-4222-8222-222222222222', 3, 2, '800123456', 'entregado', 2300000.00, '2026-01-12 14:30:00+00', '2026-01-13 14:30:00+00');
        
        INSERT INTO detalles_pedido (detalle_id, pedido_id, producto_id, nombre_producto, cantidad_solicitada, cantidad_disponible_al_momento, cantidad_confirmada, precio_unitario, subtotal, fecha_agregado) VALUES
        ('d2222222-1111-4111-8111-111111111111', '22222222-2222-4222-8222-222222222222', '550e8400-e29b-41d4-a716-446655440000', 'Paracetamol 500mg', 50, 900, 50, 15000.00, 750000.00, '2026-01-12 14:30:00+00'),
        ('d2222222-2222-4222-8222-222222222222', '22222222-2222-4222-8222-222222222222', '550e8400-e29b-41d4-a716-446655440001', 'Ibuprofeno 400mg', 30, 800, 30, 25000.00, 750000.00, '2026-01-12 14:30:00+00'),
        ('d2222222-3333-4333-8333-333333333333', '22222222-2222-4222-8222-222222222222', '550e8400-e29b-41d4-a716-446655440002', 'Amoxicilina 500mg', 20, 500, 20, 40000.00, 800000.00, '2026-01-12 14:30:00+00');
    END IF;
    
    -- Pedido 3 - Febrero
    IF NOT EXISTS (SELECT 1 FROM pedidos WHERE pedido_id = '33333333-3333-4333-8333-333333333333') THEN
        INSERT INTO pedidos (pedido_id, usuario_id, cliente_id, nit, estado, monto_total, fecha_creacion, fecha_actualizacion) VALUES
        ('33333333-3333-4333-8333-333333333333', 3, 1, '901234567', 'entregado', 1800000.00, '2026-02-03 08:00:00+00', '2026-02-04 08:00:00+00');
        
        INSERT INTO detalles_pedido (detalle_id, pedido_id, producto_id, nombre_producto, cantidad_solicitada, cantidad_disponible_al_momento, cantidad_confirmada, precio_unitario, subtotal, fecha_agregado) VALUES
        ('d3333333-3333-4333-8333-333333333333', '33333333-3333-4333-8333-333333333333', '550e8400-e29b-41d4-a716-446655440000', 'Paracetamol 500mg', 120, 850, 120, 15000.00, 1800000.00, '2026-02-03 08:00:00+00');
    END IF;
    
    -- Vendedor 4 (Ana) - para comparación
    IF NOT EXISTS (SELECT 1 FROM pedidos WHERE pedido_id = '44444444-4444-4444-8444-444444444444') THEN
        INSERT INTO pedidos (pedido_id, usuario_id, cliente_id, nit, estado, monto_total, fecha_creacion, fecha_actualizacion) VALUES
        ('44444444-4444-4444-8444-444444444444', 4, 1, '901234567', 'entregado', 1900000.00, '2026-01-15 10:00:00+00', '2026-01-16 10:00:00+00');
        
        INSERT INTO detalles_pedido (detalle_id, pedido_id, producto_id, nombre_producto, cantidad_solicitada, cantidad_disponible_al_momento, cantidad_confirmada, precio_unitario, subtotal, fecha_agregado) VALUES
        ('d4444444-4444-4444-8444-444444444444', '44444444-4444-4444-8444-444444444444', '550e8400-e29b-41d4-a716-446655440000', 'Paracetamol 500mg', 95, 755, 95, 20000.00, 1900000.00, '2026-01-15 10:00:00+00');
    END IF;
END $$;

\c product_db;

-- Crear plan de venta Q1 2026 con UUID válidos
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM plan_venta WHERE plan_id = '11111111-1111-4111-a111-111111111111') THEN
        INSERT INTO plan_venta (plan_id, nombre, periodo_desde, periodo_hasta, estado, created_by) VALUES
        ('11111111-1111-4111-a111-111111111111', 'Plan Q1 2026 - Colombia', '2026-01-01', '2026-03-31', 'activo', 1);
        
        -- Asignar territorios
        INSERT INTO plan_venta_territorio (plan_id, territorio_id) VALUES
        ('11111111-1111-4111-a111-111111111111', 'TERR-NORTE-BOG'),
        ('11111111-1111-4111-a111-111111111111', 'TERR-SUR-BOG');
        
        -- Metas para vendedor 3 (Carlos)
        INSERT INTO plan_meta (meta_id, plan_id, producto_id, territorio_id, vendedor_id, objetivo_cantidad, objetivo_valor, nota) VALUES
        ('22222222-2222-4222-a222-222222222222', '11111111-1111-4111-a111-111111111111', '550e8400-e29b-41d4-a716-446655440000', 'TERR-NORTE-BOG', 3, 1200, 20000000.00, 'Meta Q1 Paracetamol'),
        ('33333333-3333-4333-a333-333333333333', '11111111-1111-4111-a111-111111111111', '550e8400-e29b-41d4-a716-446655440001', 'TERR-NORTE-BOG', 3, 500, 12000000.00, 'Meta Q1 Ibuprofeno'),
        ('44444444-4444-4444-a444-444444444444', '11111111-1111-4111-a111-111111111111', '550e8400-e29b-41d4-a716-446655440002', 'TERR-NORTE-BOG', 3, 300, 8000000.00, 'Meta Q1 Amoxicilina');
        
        -- Metas para vendedor 4 (Ana)
        INSERT INTO plan_meta (meta_id, plan_id, producto_id, territorio_id, vendedor_id, objetivo_cantidad, objetivo_valor, nota) VALUES
        ('55555555-5555-4555-a555-555555555555', '11111111-1111-4111-a111-111111111111', '550e8400-e29b-41d4-a716-446655440000', 'TERR-NORTE-BOG', 4, 800, 15000000.00, 'Meta Q1 Paracetamol'),
        ('66666666-6666-4666-a666-666666666666', '11111111-1111-4111-a111-111111111111', '550e8400-e29b-41d4-a716-446655440001', 'TERR-NORTE-BOG', 4, 400, 10000000.00, 'Meta Q1 Ibuprofeno');
    END IF;
END $$;

\echo '================================'
\echo 'Datos de prueba cargados:'
\echo '- 4 pedidos (3 para vendedor 3, 1 para vendedor 4)'
\echo '- Periodo: Enero-Febrero 2026'
\echo '- 1 Plan de venta Q1 2026 con metas'
\echo '- Vendedor 3: ~270 unidades, ~$5.6M'
\echo '- Vendedor 4: 95 unidades, $1.9M'
\echo '- Metas configuradas para comparación'
\echo '================================'

-- Script de inicialización para módulo de rutas de entrega
-- Conectar a la base de datos pedidos_db
\c pedidos_db

-- ============================================================
-- INSERTAR USUARIOS SUPERVISORES DE LOGÍSTICA
-- ============================================================
-- Nota: Los usuarios se crean en user_db, pero aquí registramos sus IDs
-- para usar en el campo usuario_creador_id de las rutas

\c user_db

-- Insertar supervisor de logística de prueba (si no existe)
INSERT INTO Usuarios (nombre, correo_electronico, password_hash, nit, rol, activo)
VALUES 
    ('Juan Supervisor', 'juan.supervisor@medisupply.com', '$2b$12$dummyhashfortest', '111111111-1', 'admin', true),
    ('María Logística', 'maria.logistica@medisupply.com', '$2b$12$dummyhashfortest', '111111111-1', 'admin', true)
ON CONFLICT (correo_electronico) DO NOTHING;

-- Insertar gerentes de cuenta (vendedores) para pedidos
INSERT INTO Usuarios (nombre, correo_electronico, password_hash, nit, rol, activo)
VALUES 
    ('Carlos Vendedor', 'carlos.vendedor@medisupply.com', '$2b$12$dummyhashfortest', '111111111-1', 'gerente_cuenta', true),
    ('Ana Comercial', 'ana.comercial@medisupply.com', '$2b$12$dummyhashfortest', '111111111-1', 'gerente_cuenta', true),
    ('Luis Ventas', 'luis.ventas@medisupply.com', '$2b$12$dummyhashfortest', '111111111-1', 'gerente_cuenta', true)
ON CONFLICT (correo_electronico) DO NOTHING;

-- ============================================================
-- VOLVER A pedidos_db PARA CREAR DATOS DE RUTAS
-- ============================================================
\c pedidos_db

-- ============================================================
-- INSERTAR VEHÍCULOS DE PRUEBA
-- ============================================================

-- Crear tabla vehiculos si no existe (normalmente SQLAlchemy la crea)
CREATE TABLE IF NOT EXISTS vehiculos (
    vehiculo_id VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    capacidad_volumen FLOAT NOT NULL,
    capacidad_peso FLOAT NOT NULL,
    cadena_frio BOOLEAN NOT NULL DEFAULT FALSE,
    depot_latitud FLOAT NOT NULL,
    depot_longitud FLOAT NOT NULL,
    depot_direccion VARCHAR(500),
    duracion_maxima_minutos INTEGER,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE
);

-- Insertar vehículos de prueba
INSERT INTO vehiculos (vehiculo_id, nombre, capacidad_volumen, capacidad_peso, cadena_frio, depot_latitud, depot_longitud, depot_direccion, duracion_maxima_minutos, activo)
VALUES 
    ('VEH-001', 'Camión Refrigerado Grande', 60.0, 1500.0, true, 4.6097, -74.0817, 'Calle 26 #68-90, Bogotá', 480, true),
    ('VEH-002', 'Camioneta Estándar', 30.0, 600.0, false, 4.6097, -74.0817, 'Calle 26 #68-90, Bogotá', 360, true),
    ('VEH-003', 'Camión Refrigerado Mediano', 40.0, 1000.0, true, 4.6097, -74.0817, 'Calle 26 #68-90, Bogotá', 420, true),
    ('VEH-004', 'Furgón Pequeño', 15.0, 300.0, false, 4.6097, -74.0817, 'Calle 26 #68-90, Bogotá', 300, true),
    ('VEH-005', 'Camión Termo King', 70.0, 2000.0, true, 4.6097, -74.0817, 'Calle 26 #68-90, Bogotá', 540, true)
ON CONFLICT (vehiculo_id) DO NOTHING;

-- ============================================================
-- INSERTAR PEDIDOS DE PRUEBA PARA RUTAS
-- ============================================================
-- Datos reales de clientes, vendedores (gerentes) y ubicaciones de Bogotá

-- Insertar pedidos de prueba vinculados con clientes reales y gerentes existentes
-- Los gerentes son: 1=Colombia, 2=Colombia, 3=Perú, 4=Perú, 5=México, 6=México, 7=Ecuador, 8=Ecuador
-- Los clientes en Bogotá son: 1 (Hospital San Juan), 6 (Laboratorio Clínico Central), 9 (IPS Vida Plena)

INSERT INTO pedidos (pedido_id, usuario_id, cliente_id, nit, estado, fecha_entrega_estimada, observaciones, fecha_creacion)
VALUES 
    -- Pedidos de gerente 1 (Colombia) - Cliente 1: Hospital San Juan - Bogotá
    (gen_random_uuid(), 1, 1, '800123456-1', 'pendiente', CURRENT_DATE + INTERVAL '2 days', 'Paracetamol 500mg - Hospital San Juan Bogotá', CURRENT_TIMESTAMP),
    (gen_random_uuid(), 1, 1, '800123456-1', 'pendiente', CURRENT_DATE + INTERVAL '2 days', 'Ibuprofeno 400mg - Hospital San Juan Bogotá', CURRENT_TIMESTAMP),
    
    -- Pedidos de gerente 2 (Colombia) - Cliente 6: Laboratorio Clínico Central - Bogotá
    (gen_random_uuid(), 2, 6, '800678901-6', 'pendiente', CURRENT_DATE + INTERVAL '2 days', 'Amoxicilina 500mg - Laboratorio Central Bogotá', CURRENT_TIMESTAMP),
    (gen_random_uuid(), 2, 6, '800678901-6', 'pendiente', CURRENT_DATE + INTERVAL '2 days', 'Vitamina C 500mg - Laboratorio Central Bogotá', CURRENT_TIMESTAMP),
    
    -- Pedidos de gerente 1 (Colombia) - Cliente 9: IPS Vida Plena - Bogotá
    (gen_random_uuid(), 1, 9, '800901234-9', 'pendiente', CURRENT_DATE + INTERVAL '2 days', 'Metformina 500mg - IPS Vida Plena Bogotá', CURRENT_TIMESTAMP),
    (gen_random_uuid(), 1, 9, '800901234-9', 'pendiente', CURRENT_DATE + INTERVAL '2 days', 'Losartán 50mg - IPS Vida Plena Bogotá', CURRENT_TIMESTAMP),
    
    -- Pedidos de gerente 2 (Colombia) - Cliente 1: Hospital San Juan - Bogotá (segundo conjunto)
    (gen_random_uuid(), 2, 1, '800123456-1', 'pendiente', CURRENT_DATE + INTERVAL '3 days', 'Diclofenaco 50mg - Hospital San Juan Bogotá', CURRENT_TIMESTAMP),
    (gen_random_uuid(), 2, 1, '800123456-1', 'pendiente', CURRENT_DATE + INTERVAL '3 days', 'Omeprazol 20mg - Hospital San Juan Bogotá', CURRENT_TIMESTAMP)
ON CONFLICT (pedido_id) DO NOTHING;

-- ============================================================
-- ACTUALIZAR COORDENADAS DE CLIENTES EN BOGOTÁ
-- ============================================================
-- Agregar latitud y longitud a los clientes de Bogotá para optimización de rutas

-- \c cliente_db

-- Actualizar cliente 1: Hospital San Juan - Bogotá (Zona Centro)
-- UPDATE clientes SET latitud = 4.6426, longitud = -74.0829 WHERE cliente_id = 1;

-- Actualizar cliente 6: Laboratorio Clínico Central - Bogotá (Zona Centro)
-- UPDATE clientes SET latitud = 4.6359, longitud = -74.0759 WHERE cliente_id = 6;

-- Actualizar cliente 9: IPS Vida Plena - Bogotá (Zona Norte)
-- UPDATE clientes SET latitud = 4.7200, longitud = -74.0480 WHERE cliente_id = 9;

-- Nota: Las coordenadas de clientes se actualizarán después en un script separado
-- cuando la tabla cliente_db esté completamente creada por el servicio cliente-service

\c pedidos_db

-- ============================================================
-- ÍNDICES ADICIONALES PARA PERFORMANCE
-- ============================================================

-- Índices en la tabla pedidos para búsquedas de rutas
CREATE INDEX IF NOT EXISTS idx_pedidos_estado_fecha ON pedidos(estado, fecha_entrega_estimada);
CREATE INDEX IF NOT EXISTS idx_pedidos_nit ON pedidos(nit);

-- Índices en la tabla vehiculos
CREATE INDEX IF NOT EXISTS idx_vehiculos_activo_cadena_frio ON vehiculos(activo, cadena_frio);

-- ============================================================
-- VISTAS ÚTILES PARA REPORTES DE RUTAS
-- ============================================================

-- Vista de pedidos pendientes (versión simplificada sin dblink)
-- Nota: dblink no está disponible, se comenta esta vista
-- CREATE OR REPLACE VIEW v_pedidos_pendientes_rutas AS
-- SELECT 
--     p.pedido_id,
--     p.usuario_id,
--     p.cliente_id,
--     p.nit,
--     p.fecha_entrega_estimada,
--     p.observaciones,
--     p.fecha_creacion,
--     i.nombre_institucion,
--     i.pais
-- FROM pedidos p
-- LEFT JOIN (
--     SELECT nit, nombre_institucion, pais FROM dblink(
--         'dbname=nit_db',
--         'SELECT nit, nombre_institucion, pais FROM instituciones_asociadas WHERE activo = true'
--     ) AS instituciones(nit VARCHAR, nombre_institucion VARCHAR, pais VARCHAR)
-- ) i ON p.nit = i.nit
-- WHERE p.estado = 'pendiente';

-- Vista de resumen de vehículos disponibles
CREATE OR REPLACE VIEW v_vehiculos_disponibles AS
SELECT 
    vehiculo_id,
    nombre,
    capacidad_volumen,
    capacidad_peso,
    cadena_frio,
    depot_latitud,
    depot_longitud,
    depot_direccion,
    duracion_maxima_minutos,
    CASE 
        WHEN cadena_frio THEN 'Refrigerado'
        ELSE 'Estándar'
    END as tipo_vehiculo
FROM vehiculos
WHERE activo = true
ORDER BY capacidad_peso DESC;

-- ============================================================
-- MENSAJES DE CONFIRMACIÓN
-- ============================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Inicialización de módulo de rutas completada';
    RAISE NOTICE '📦 Vehículos insertados: 5';
    RAISE NOTICE '📋 Pedidos de prueba creados';
    RAISE NOTICE '👤 Usuarios admin (supervisores) creados en user_db';
    RAISE NOTICE '👤 Usuarios gerente_cuenta (vendedores) creados en user_db';
    RAISE NOTICE '🏢 NIT: 111111111-1 | Dominio: @medisupply.com';
    RAISE NOTICE '🔍 Vistas de reporte creadas';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Para probar el módulo de rutas:';
    RAISE NOTICE '   docker exec -it pedidos-service python test_rutas.py';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Para ver vehículos disponibles:';
    RAISE NOTICE '   docker exec -it postgres-db psql -U pedidos_service -d pedidos_db -c "SELECT * FROM v_vehiculos_disponibles;"';
END $$;

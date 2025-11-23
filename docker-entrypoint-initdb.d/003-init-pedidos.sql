-- Script de inicialización para pedidos_db
-- Crea el usuario y la base de datos

-- Crear usuario para el servicio de pedidos (si no existe)
DO
$$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'pedidos_service') THEN
        CREATE USER pedidos_service WITH PASSWORD 'pedidos_password';
    END IF;
END
$$;

-- Crear base de datos si no existe
SELECT 'CREATE DATABASE pedidos_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pedidos_db')
\gexec

-- Conectar a la base de datos
\c pedidos_db

-- Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE pedidos_db TO pedidos_service;

-- Otorgar permisos en el schema public
GRANT ALL PRIVILEGES ON SCHEMA public TO pedidos_service;

-- Otorgar permisos por defecto para nuevas tablas, secuencias y tipos
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO pedidos_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO pedidos_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TYPES TO pedidos_service;

-- ============================================================
-- CREAR TABLA pedidos (necesaria para rutas)
-- ============================================================

CREATE TABLE IF NOT EXISTS pedidos (
    pedido_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id INTEGER NOT NULL,
    cliente_id INTEGER NOT NULL,
    nit VARCHAR(50) NOT NULL,
    estado VARCHAR(50) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'asignado', 'en_transito', 'entregado', 'cancelado')),
    fecha_entrega_estimada DATE,
    observaciones TEXT,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para optimizar búsquedas
CREATE INDEX IF NOT EXISTS idx_pedidos_estado_fecha ON pedidos(estado, fecha_entrega_estimada);
CREATE INDEX IF NOT EXISTS idx_pedidos_nit ON pedidos(nit);
CREATE INDEX IF NOT EXISTS idx_pedidos_usuario ON pedidos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos(cliente_id);

-- Otorgar permisos
GRANT ALL PRIVILEGES ON TABLE pedidos TO pedidos_service;

-- Cambiar propietario de la tabla a pedidos_service para que pueda hacer ALTER TABLE
ALTER TABLE pedidos OWNER TO pedidos_service;


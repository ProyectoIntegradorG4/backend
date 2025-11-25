-- Migration: Add canal to pedidos, FEFO/snapshot fields to detalles_pedido,
-- create pedido_estado_historial, entregas and eventos_entrega tables.
-- Safe to run multiple times (checks for existence).

DO $$
BEGIN
    -- Create enum type for canal if not exists
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'canalpedido') THEN
        CREATE TYPE canalpedido AS ENUM ('movil_ventas', 'movil_cliente');
    END IF;

    -- Add column canal to pedidos if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='pedidos' AND column_name='canal'
    ) THEN
        ALTER TABLE pedidos ADD COLUMN canal canalpedido NULL;
    END IF;
END
$$;

DO $$
BEGIN
    -- Add columns to detalles_pedido if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='detalles_pedido' AND column_name='sku') THEN
        ALTER TABLE detalles_pedido ADD COLUMN sku VARCHAR(100) NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='detalles_pedido' AND column_name='cantidad_confirmada') THEN
        ALTER TABLE detalles_pedido ADD COLUMN cantidad_confirmada INTEGER NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='detalles_pedido' AND column_name='lote_id') THEN
        ALTER TABLE detalles_pedido ADD COLUMN lote_id VARCHAR(64) NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='detalles_pedido' AND column_name='bodega_id') THEN
        ALTER TABLE detalles_pedido ADD COLUMN bodega_id VARCHAR(64) NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='detalles_pedido' AND column_name='bodega_nombre') THEN
        ALTER TABLE detalles_pedido ADD COLUMN bodega_nombre VARCHAR(255) NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='detalles_pedido' AND column_name='pais') THEN
        ALTER TABLE detalles_pedido ADD COLUMN pais VARCHAR(64) NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='detalles_pedido' AND column_name='fecha_vencimiento_lote') THEN
        ALTER TABLE detalles_pedido ADD COLUMN fecha_vencimiento_lote timestamptz NULL;
    END IF;
END
$$;

DO $$
DECLARE
    estado_enum regtype;
BEGIN
    -- Determine the enum type used by pedidos.estado to reuse in historial
    SELECT atttypid::regtype INTO estado_enum
    FROM pg_attribute
    WHERE attrelid = 'public.pedidos'::regclass
      AND attname = 'estado';

    -- Create table pedido_estado_historial if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name='pedido_estado_historial'
    ) THEN
        EXECUTE format($f$
            CREATE TABLE pedido_estado_historial (
                id uuid PRIMARY KEY,
                pedido_id uuid NOT NULL REFERENCES pedidos(pedido_id) ON DELETE CASCADE,
                estado_anterior %s NOT NULL,
                estado_nuevo %s NOT NULL,
                fecha_cambio timestamptz NOT NULL DEFAULT now(),
                comentario text NULL
            );
        $f$, estado_enum::text, estado_enum::text);
        CREATE INDEX IF NOT EXISTS idx_historial_pedido ON pedido_estado_historial(pedido_id);
        CREATE INDEX IF NOT EXISTS idx_historial_fecha ON pedido_estado_historial(fecha_cambio);
    END IF;
END
$$;

DO $$
BEGIN
    -- Create enum for estado_entrega if not exists
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estadoentrega') THEN
        CREATE TYPE estadoentrega AS ENUM ('programada', 'en_ruta', 'entregada', 'devuelta');
    END IF;

    -- Create table entregas if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name='entregas'
    ) THEN
        CREATE TABLE entregas (
            entrega_id uuid PRIMARY KEY,
            pedido_id uuid NOT NULL REFERENCES pedidos(pedido_id) ON DELETE CASCADE,
            nit VARCHAR(20) NOT NULL,
            estado_entrega estadoentrega NOT NULL DEFAULT 'programada',
            fecha_hora_programada timestamptz NULL,
            fecha_hora_estimada_llegada timestamptz NULL,
            fecha_hora_entrega_real timestamptz NULL,
            vehiculo_id VARCHAR(64) NULL,
            conductor_id VARCHAR(64) NULL,
            placa_vehiculo VARCHAR(32) NULL
        );
        CREATE INDEX IF NOT EXISTS idx_entregas_nit ON entregas(nit);
        CREATE INDEX IF NOT EXISTS idx_entregas_pedido ON entregas(pedido_id);
    END IF;

    -- Create table eventos_entrega if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name='eventos_entrega'
    ) THEN
        CREATE TABLE eventos_entrega (
            evento_id uuid PRIMARY KEY,
            entrega_id uuid NOT NULL REFERENCES entregas(entrega_id) ON DELETE CASCADE,
            timestamp timestamptz NOT NULL DEFAULT now(),
            latitud double precision NULL,
            longitud double precision NULL,
            tipo_evento VARCHAR(64) NOT NULL,
            descripcion VARCHAR(512) NULL
        );
        CREATE INDEX IF NOT EXISTS idx_eventos_entrega_entrega ON eventos_entrega(entrega_id);
        CREATE INDEX IF NOT EXISTS idx_eventos_entrega_time ON eventos_entrega(timestamp DESC);
    END IF;
END
$$;



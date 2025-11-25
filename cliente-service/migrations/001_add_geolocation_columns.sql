-- Migration: Agregar columnas de geolocalización a tabla clientes
-- Fecha: 2025-11-17
-- Propósito: Soporte para HU-MOV-003 (Rutas de visitas optimizadas)

-- Agregar columna latitud si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'clientes' AND column_name = 'latitud') THEN
        ALTER TABLE clientes 
        ADD COLUMN latitud NUMERIC(10, 8) NULL;
        
        COMMENT ON COLUMN clientes.latitud IS 'Latitud de la sede para geolocalización y optimización de rutas';
        
        RAISE NOTICE 'Columna latitud agregada exitosamente';
    ELSE
        RAISE NOTICE 'Columna latitud ya existe, saltando';
    END IF;
END $$;

-- Agregar columna longitud si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'clientes' AND column_name = 'longitud') THEN
        ALTER TABLE clientes 
        ADD COLUMN longitud NUMERIC(11, 8) NULL;
        
        COMMENT ON COLUMN clientes.longitud IS 'Longitud de la sede para geolocalización y optimización de rutas';
        
        RAISE NOTICE 'Columna longitud agregada exitosamente';
    ELSE
        RAISE NOTICE 'Columna longitud ya existe, saltando';
    END IF;
END $$;

-- Crear índice para búsquedas por coordenadas (opcional, para optimización futura)
CREATE INDEX IF NOT EXISTS idx_clientes_geolocation 
ON clientes (latitud, longitud) 
WHERE latitud IS NOT NULL AND longitud IS NOT NULL;

-- Confirmar cambios
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'clientes' 
  AND column_name IN ('latitud', 'longitud')
ORDER BY column_name;


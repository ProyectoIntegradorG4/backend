-- Migración: Agregar columna nit a gerente_cuenta_clientes
-- Fecha: 2025-11-05
-- Propósito: Optimizar consultas de pedidos por NIT evitando joins con la tabla clientes

-- Agregar columna nit (nullable para permitir migración de datos existentes)
ALTER TABLE gerente_cuenta_clientes 
ADD COLUMN IF NOT EXISTS nit VARCHAR(20);

-- Crear índice para búsquedas por NIT
CREATE INDEX IF NOT EXISTS idx_gerente_cuenta_clientes_nit ON gerente_cuenta_clientes(nit);

-- Actualizar registros existentes con el NIT del cliente correspondiente
UPDATE gerente_cuenta_clientes gcc
SET nit = c.nit
FROM clientes c
WHERE gcc.cliente_id = c.cliente_id
  AND gcc.nit IS NULL;

-- Verificación: Mostrar registros actualizados
SELECT 
    COUNT(*) as total_asignaciones,
    COUNT(nit) as asignaciones_con_nit,
    COUNT(*) - COUNT(nit) as asignaciones_sin_nit
FROM gerente_cuenta_clientes;

-- Nota: La columna se deja como nullable para permitir casos excepcionales
-- En producción, considerar hacerla NOT NULL después de validar que todos los registros tienen NIT


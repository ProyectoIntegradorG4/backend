-- Migration: Add granular fields to clients_visits table
-- HU-MOV-004: Add contacto_nombre, tipo_visita, objetivo_visita

ALTER TABLE clients_visits
ADD COLUMN IF NOT EXISTS contacto_nombre VARCHAR(200) NULL,
ADD COLUMN IF NOT EXISTS tipo_visita VARCHAR(100) NULL,
ADD COLUMN IF NOT EXISTS objetivo_visita TEXT NULL;

-- Add index for tipo_visita if needed for filtering
CREATE INDEX IF NOT EXISTS idx_clients_visits_tipo_visita
    ON clients_visits (tipo_visita);


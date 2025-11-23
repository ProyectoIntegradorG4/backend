\c proveedor_db;

ALTER TABLE proveedores
ADD COLUMN IF NOT EXISTS validacion_regulatoria VARCHAR(20) NOT NULL DEFAULT 'en_revision';
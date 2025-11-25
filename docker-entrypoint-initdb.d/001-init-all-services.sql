-- Create databases and users for all microservices
-- Idempotent: uses DO blocks to avoid errors if rerun

-- Create roles
DO $$
BEGIN
   -- User Service
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'user_service') THEN
      CREATE ROLE user_service LOGIN PASSWORD 'user_password';
   END IF;
   
   -- Audit Service
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'audit_service') THEN
      CREATE ROLE audit_service LOGIN PASSWORD 'audit_password';
   END IF;
   
   -- NIT Validation Service
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'nit_service') THEN
      CREATE ROLE nit_service LOGIN PASSWORD 'nit_password';
   END IF;
   
   -- Product Service
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'product_service') THEN
      CREATE ROLE product_service LOGIN PASSWORD 'product_password';
   END IF;
   
   -- Proveedor Service
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'proveedor_service') THEN
      CREATE ROLE proveedor_service LOGIN PASSWORD 'proveedor_password';
   END IF;
   
   -- Pedidos Service
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pedidos_service') THEN
      CREATE ROLE pedidos_service LOGIN PASSWORD 'pedidos_password';
   END IF;
   
   -- Cliente Service
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cliente_service') THEN
      CREATE ROLE cliente_service LOGIN PASSWORD 'cliente_password';
   END IF;
   
   -- Visita Service (HU-MOV-003)
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'visita_service') THEN
      CREATE ROLE visita_service LOGIN PASSWORD 'visita_password';
   END IF;
   
   -- Visit Service (visit-service)
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'visit_service') THEN
      CREATE ROLE visit_service LOGIN PASSWORD 'visit_password';
   END IF;
END
$$;

-- Create databases conditionally
SELECT 'CREATE DATABASE user_db OWNER user_service'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'user_db')\gexec

SELECT 'CREATE DATABASE audit_db OWNER audit_service'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'audit_db')\gexec

SELECT 'CREATE DATABASE nit_db OWNER nit_service'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'nit_db')\gexec

SELECT 'CREATE DATABASE product_db OWNER product_service'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'product_db')\gexec

SELECT 'CREATE DATABASE proveedor_db OWNER proveedor_service'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'proveedor_db')\gexec

SELECT 'CREATE DATABASE pedidos_db OWNER pedidos_service'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pedidos_db')\gexec

SELECT 'CREATE DATABASE cliente_db OWNER cliente_service'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cliente_db')\gexec

SELECT 'CREATE DATABASE visita_db OWNER visita_service'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'visita_db')\gexec

SELECT 'CREATE DATABASE visit_db OWNER visit_service'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'visit_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE user_db TO user_service;
GRANT ALL PRIVILEGES ON DATABASE audit_db TO audit_service;
GRANT ALL PRIVILEGES ON DATABASE nit_db TO nit_service;
GRANT ALL PRIVILEGES ON DATABASE product_db TO product_service;
GRANT ALL PRIVILEGES ON DATABASE proveedor_db TO proveedor_service;
GRANT ALL PRIVILEGES ON DATABASE pedidos_db TO pedidos_service;
GRANT ALL PRIVILEGES ON DATABASE cliente_db TO cliente_service;
GRANT ALL PRIVILEGES ON DATABASE visita_db TO visita_service;
GRANT ALL PRIVILEGES ON DATABASE visit_db TO visit_service;


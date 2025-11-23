-- Script de inicialización para crear las bases de datos y usuarios
-- Este script se ejecuta automáticamente cuando se crea el contenedor de PostgreSQL

-- Crear usuarios para cada microservicio
CREATE USER user_service WITH PASSWORD 'user_password';
CREATE USER nit_service WITH PASSWORD 'nit_password';
CREATE USER audit_service WITH PASSWORD 'audit_password';

-- Crear las bases de datos
CREATE DATABASE user_db OWNER user_service;
CREATE DATABASE nit_db OWNER nit_service;
CREATE DATABASE audit_db OWNER audit_service;

-- Otorgar permisos completos a cada usuario en su respectiva base de datos
GRANT ALL PRIVILEGES ON DATABASE user_db TO user_service;
GRANT ALL PRIVILEGES ON DATABASE nit_db TO nit_service;
GRANT ALL PRIVILEGES ON DATABASE audit_db TO audit_service;

-- Conectar a cada base de datos y otorgar permisos en el esquema public
\c user_db;
GRANT ALL ON SCHEMA public TO user_service;

-- Crear la tabla Usuarios en la base de datos user_db
CREATE TABLE Usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    correo_electronico VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nit VARCHAR(20) NOT NULL,
    rol VARCHAR(50) DEFAULT 'usuario_institucional',
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- Otorgar permisos DESPUÉS de crear la tabla
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO user_service;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO user_service;

\c nit_db;
GRANT ALL ON SCHEMA public TO nit_service;

-- Crear la tabla instituciones_asociadas en la base de datos nit_db
CREATE TABLE instituciones_asociadas (
    nit VARCHAR(20) PRIMARY KEY,
    nombre_institucion VARCHAR(255) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- Crear índices para optimizar búsquedas
CREATE INDEX idx_pais_activo ON instituciones_asociadas(pais, activo);
CREATE INDEX idx_activo ON instituciones_asociadas(activo);

-- Insertar datos de prueba
INSERT INTO instituciones_asociadas (nit, nombre_institucion, pais, activo) VALUES
('901234567', 'Clínica Central', 'Colombia', true),
('800123456', 'Hospital Universitario', 'Colombia', true),
('900987654', 'Centro Médico Los Andes', 'Colombia', true),
('811234567', 'Fundación Cardiovascular', 'Colombia', true),
('123456789', 'Instituto Nacional de Salud', 'Colombia', true),
('555123456', 'Hospital General', 'Peru', true),
('666789012', 'Clínica San Pablo', 'Peru', true),
('777456123', 'Centro Médico ABC', 'Mexico', true),
('888321654', 'Hospital Siglo XXI', 'Mexico', true),
('999654321', 'Clínica Metropolitana', 'Ecuador', true);

-- Otorgar permisos DESPUÉS de crear la tabla
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nit_service;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nit_service;

\c audit_db;
GRANT ALL ON SCHEMA public TO audit_service;

-- Crear la tabla audit_logs en la base de datos audit_db
CREATE TABLE audit_logs (
    id VARCHAR(255) PRIMARY KEY,
    event VARCHAR(255) NOT NULL,
    request JSONB NOT NULL,
    outcome VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    auditid VARCHAR(255) UNIQUE NOT NULL
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX idx_audit_logs_event ON audit_logs(event);
CREATE INDEX idx_audit_logs_outcome ON audit_logs(outcome);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_auditid ON audit_logs(auditid);

-- Otorgar permisos DESPUÉS de crear la tabla
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO audit_service;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO audit_service;
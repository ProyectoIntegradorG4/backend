-- Script para crear gerentes de cuenta y asignar clientes
-- HU-MOV-002: Consulta de Clientes

-- ========================================
-- 1. CREAR GERENTES DE CUENTA (2 por país)
-- ========================================

-- COLOMBIA
-- Gerente 1: Ya existe (gerente.colombia@medisupply.com con ID 1)
-- Gerente 2: Nuevo gerente Colombia
INSERT INTO usuarios (nombre, correo_electronico, password_hash, nit, rol, activo)
VALUES 
    ('María Rodríguez Colombia', 'maria.rodriguez@medisupply.com', '$2b$12$KIXqP8xGVhDYr5YQN.J3xOYqZ5yQqH5zKqH5zKqH5zKqH5zKqH5zK', '111111111-1', 'gerente_cuenta', true)
ON CONFLICT (correo_electronico) DO NOTHING;

-- PERÚ
INSERT INTO usuarios (nombre, correo_electronico, password_hash, nit, rol, activo)
VALUES 
    ('Carlos Mendoza Perú', 'carlos.mendoza@medisupply.com', '$2b$12$KIXqP8xGVhDYr5YQN.J3xOYqZ5yQqH5zKqH5zKqH5zKqH5zKqH5zK', '111111111-3', 'gerente_cuenta', true),
    ('Ana Torres Perú', 'ana.torres@medisupply.com', '$2b$12$KIXqP8xGVhDYr5YQN.J3xOYqZ5yQqH5zKqH5zKqH5zKqH5zKqH5zK', '111111111-3', 'gerente_cuenta', true)
ON CONFLICT (correo_electronico) DO NOTHING;

-- MÉXICO
INSERT INTO usuarios (nombre, correo_electronico, password_hash, nit, rol, activo)
VALUES 
    ('Roberto Hernández México', 'roberto.hernandez@medisupply.com', '$2b$12$KIXqP8xGVhDYr5YQN.J3xOYqZ5yQqH5zKqH5zKqH5zKqH5zKqH5zK', '111111111-2', 'gerente_cuenta', true),
    ('Patricia López México', 'patricia.lopez@medisupply.com', '$2b$12$KIXqP8xGVhDYr5YQN.J3xOYqZ5yQqH5zKqH5zKqH5zKqH5zKqH5zK', '111111111-2', 'gerente_cuenta', true)
ON CONFLICT (correo_electronico) DO NOTHING;

-- ECUADOR
INSERT INTO usuarios (nombre, correo_electronico, password_hash, nit, rol, activo)
VALUES 
    ('Diego Salazar Ecuador', 'diego.salazar@medisupply.com', '$2b$12$KIXqP8xGVhDYr5YQN.J3xOYqZ5yQqH5zKqH5zKqH5zKqH5zKqH5zK', '111111111-4', 'gerente_cuenta', true),
    ('Sofía Morales Ecuador', 'sofia.morales@medisupply.com', '$2b$12$KIXqP8xGVhDYr5YQN.J3xOYqZ5yQqH5zKqH5zKqH5zKqH5zKqH5zK', '111111111-4', 'gerente_cuenta', true)
ON CONFLICT (correo_electronico) DO NOTHING;

-- Ver gerentes creados
SELECT id, nombre, correo_electronico, nit, rol, activo 
FROM usuarios 
WHERE rol = 'gerente_cuenta'
ORDER BY nit, id;


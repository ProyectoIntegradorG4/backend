-- Script SQL para insertar 50 productos médicos distribuidos en Colombia, Ecuador, Perú y México
-- MediSupply - Distribución de Productos Médicos

-- Productos para Colombia
INSERT INTO public.producto
("productoId", nombre, descripcion, "categoriaId", "formaFarmaceutica", "requierePrescripcion", "registroSanitario", sku, "location", ubicacion, stock, precio, estado_producto, actualizado_en, "fechaVencimiento")
VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Paracetamol 500mg Tabletas', 'Analgésico y antipirético para el alivio del dolor y la fiebre', 'CAT-ANL-001', 'Tableta', false, 'RS-COL-2024-001', 'SKU-COL-001', 'Bodega Bogotá', 'Colombia', 1500, 8500.00, 'activo', CURRENT_TIMESTAMP, '2026-12-31'),
('550e8400-e29b-41d4-a716-446655440002', 'Ibuprofeno 400mg Cápsulas', 'Antiinflamatorio no esteroideo para dolor e inflamación', 'CAT-ANL-001', 'Cápsula', false, 'RS-COL-2024-002', 'SKU-COL-002', 'Bodega Bogotá', 'Colombia', 1200, 12500.00, 'activo', CURRENT_TIMESTAMP, '2026-11-30'),
('550e8400-e29b-41d4-a716-446655440003', 'Vacuna Hepatitis B', 'Vacuna recombinante para prevención de hepatitis B', 'CAT-VAC-001', 'Inyectable', true, 'RS-COL-2024-003', 'SKU-COL-003', 'Bodega Bogotá', 'Colombia', 800, 45000.00, 'activo', CURRENT_TIMESTAMP, '2025-06-30'),
('550e8400-e29b-41d4-a716-446655440004', 'Vacuna Triple Viral', 'Vacuna contra sarampión, paperas y rubéola', 'CAT-VAC-001', 'Inyectable', true, 'RS-COL-2024-004', 'SKU-COL-004', 'Bodega Bogotá', 'Colombia', 950, 52000.00, 'activo', CURRENT_TIMESTAMP, '2025-08-15'),
('550e8400-e29b-41d4-a716-446655440005', 'Amoxicilina 500mg Cápsulas', 'Antibiótico de amplio espectro para infecciones bacterianas', 'CAT-MED-001', 'Cápsula', true, 'RS-COL-2024-005', 'SKU-COL-005', 'Bodega Medellín', 'Colombia', 2000, 9800.00, 'activo', CURRENT_TIMESTAMP, '2026-10-31'),
('550e8400-e29b-41d4-a716-446655440006', 'Monitor de Signos Vitales', 'Equipo multiparámetro para monitoreo continuo', 'CAT-EQU-001', 'Equipo', false, 'RS-COL-2024-006', 'SKU-COL-006', 'Bodega Cali', 'Colombia', 45, 2500000.00, 'activo', CURRENT_TIMESTAMP, NULL),
('550e8400-e29b-41d4-a716-446655440007', 'Jeringas Desechables 5ml', 'Jeringas estériles de un solo uso', 'CAT-INS-001', 'Insumo', false, 'RS-COL-2024-007', 'SKU-COL-007', 'Bodega Bogotá', 'Colombia', 5000, 3500.00, 'activo', CURRENT_TIMESTAMP, '2027-03-31'),
('550e8400-e29b-41d4-a716-446655440008', 'Guantes Quirúrgicos Estériles', 'Guantes de látex estériles tamaño medio', 'CAT-INS-001', 'Insumo', false, 'RS-COL-2024-008', 'SKU-COL-008', 'Bodega Medellín', 'Colombia', 3500, 12000.00, 'activo', CURRENT_TIMESTAMP, '2027-05-31'),
('550e8400-e29b-41d4-a716-446655440009', 'Gasas Estériles 10x10cm', 'Gasas de algodón estériles para curación', 'CAT-CON-001', 'Consumible', false, NULL, 'SKU-COL-009', 'Bodega Bogotá', 'Colombia', 8000, 2800.00, 'activo', CURRENT_TIMESTAMP, '2027-12-31'),
('550e8400-e29b-41d4-a716-446655440010', 'Oxímetro de Pulso Portátil', 'Dispositivo para medir saturación de oxígeno', 'CAT-EQU-001', 'Equipo', false, 'RS-COL-2024-010', 'SKU-COL-010', 'Bodega Cali', 'Colombia', 120, 180000.00, 'activo', CURRENT_TIMESTAMP, NULL),
('550e8400-e29b-41d4-a716-446655440011', 'Metformina 500mg Tabletas', 'Antidiabético oral para tratamiento de diabetes tipo 2', 'CAT-MED-001', 'Tableta', true, 'RS-COL-2024-011', 'SKU-COL-011', 'Bodega Medellín', 'Colombia', 1800, 7200.00, 'activo', CURRENT_TIMESTAMP, '2026-09-30'),
('550e8400-e29b-41d4-a716-446655440012', 'Suturas Quirúrgicas 3-0', 'Hilo de sutura absorbible para cirugía', 'CAT-INS-001', 'Insumo', false, 'RS-COL-2024-012', 'SKU-COL-012', 'Bodega Bogotá', 'Colombia', 600, 45000.00, 'activo', CURRENT_TIMESTAMP, '2027-08-31'),
('550e8400-e29b-41d4-a716-446655440013', 'Mascarillas N95', 'Mascarillas de protección respiratoria nivel N95', 'CAT-CON-001', 'Consumible', false, NULL, 'SKU-COL-013', 'Bodega Cali', 'Colombia', 4500, 8500.00, 'activo', CURRENT_TIMESTAMP, '2027-06-30');

-- Productos para Ecuador
INSERT INTO public.producto
("productoId", nombre, descripcion, "categoriaId", "formaFarmaceutica", "requierePrescripcion", "registroSanitario", sku, "location", ubicacion, stock, precio, estado_producto, actualizado_en, "fechaVencimiento")
VALUES
('550e8400-e29b-41d4-a716-446655440014', 'Paracetamol 500mg Tabletas', 'Analgésico y antipirético para el alivio del dolor y la fiebre', 'CAT-ANL-001', 'Tableta', false, 'RS-ECU-2024-001', 'SKU-ECU-001', 'Bodega Quito', 'Ecuador', 1400, 9200.00, 'activo', CURRENT_TIMESTAMP, '2026-12-31'),
('550e8400-e29b-41d4-a716-446655440015', 'Losartán 50mg Tabletas', 'Antihipertensivo para tratamiento de hipertensión arterial', 'CAT-MED-001', 'Tableta', true, 'RS-ECU-2024-002', 'SKU-ECU-002', 'Bodega Guayaquil', 'Ecuador', 1100, 15000.00, 'activo', CURRENT_TIMESTAMP, '2026-11-30'),
('550e8400-e29b-41d4-a716-446655440016', 'Vacuna Influenza', 'Vacuna antigripal tetravalente para temporada 2024-2025', 'CAT-VAC-001', 'Inyectable', true, 'RS-ECU-2024-003', 'SKU-ECU-003', 'Bodega Quito', 'Ecuador', 700, 48000.00, 'activo', CURRENT_TIMESTAMP, '2025-05-31'),
('550e8400-e29b-41d4-a716-446655440017', 'Vacuna COVID-19', 'Vacuna de refuerzo contra COVID-19', 'CAT-VAC-001', 'Inyectable', true, 'RS-ECU-2024-004', 'SKU-ECU-004', 'Bodega Quito', 'Ecuador', 600, 55000.00, 'activo', CURRENT_TIMESTAMP, '2025-07-31'),
('550e8400-e29b-41d4-a716-446655440018', 'Omeprazol 20mg Cápsulas', 'Inhibidor de bomba de protones para úlceras y reflujo', 'CAT-MED-001', 'Cápsula', false, 'RS-ECU-2024-005', 'SKU-ECU-005', 'Bodega Guayaquil', 'Ecuador', 1900, 10500.00, 'activo', CURRENT_TIMESTAMP, '2026-10-31'),
('550e8400-e29b-41d4-a716-446655440019', 'Desfibrilador Externo Automático', 'Equipo para reanimación cardiopulmonar', 'CAT-EQU-001', 'Equipo', false, 'RS-ECU-2024-006', 'SKU-ECU-006', 'Bodega Quito', 'Ecuador', 25, 3200000.00, 'activo', CURRENT_TIMESTAMP, NULL),
('550e8400-e29b-41d4-a716-446655440020', 'Agujas Desechables 21G', 'Agujas estériles para inyección intramuscular', 'CAT-INS-001', 'Insumo', false, 'RS-ECU-2024-007', 'SKU-ECU-007', 'Bodega Guayaquil', 'Ecuador', 4500, 2800.00, 'activo', CURRENT_TIMESTAMP, '2027-03-31'),
('550e8400-e29b-41d4-a716-446655440021', 'Mascarillas Quirúrgicas', 'Mascarillas desechables de tres capas', 'CAT-CON-001', 'Consumible', false, NULL, 'SKU-ECU-008', 'Bodega Quito', 'Ecuador', 6000, 4200.00, 'activo', CURRENT_TIMESTAMP, '2027-04-30'),
('550e8400-e29b-41d4-a716-446655440022', 'Termómetro Digital Infrarrojo', 'Termómetro sin contacto para medición de temperatura', 'CAT-EQU-001', 'Equipo', false, 'RS-ECU-2024-008', 'SKU-ECU-009', 'Bodega Guayaquil', 'Ecuador', 180, 95000.00, 'activo', CURRENT_TIMESTAMP, NULL),
('550e8400-e29b-41d4-a716-446655440023', 'Atorvastatina 20mg Tabletas', 'Estatinas para reducción de colesterol', 'CAT-MED-001', 'Tableta', true, 'RS-ECU-2024-009', 'SKU-ECU-010', 'Bodega Quito', 'Ecuador', 1600, 18000.00, 'activo', CURRENT_TIMESTAMP, '2026-09-30'),
('550e8400-e29b-41d4-a716-446655440024', 'Bisturí Desechable #11', 'Bisturíes estériles de un solo uso', 'CAT-INS-001', 'Insumo', false, 'RS-ECU-2024-010', 'SKU-ECU-011', 'Bodega Guayaquil', 'Ecuador', 800, 12000.00, 'activo', CURRENT_TIMESTAMP, '2027-08-31'),
('550e8400-e29b-41d4-a716-446655440025', 'Algodón Estéril', 'Algodón hidrófilo estéril para curaciones', 'CAT-CON-001', 'Consumible', false, NULL, 'SKU-ECU-012', 'Bodega Quito', 'Ecuador', 7500, 3500.00, 'activo', CURRENT_TIMESTAMP, '2027-12-31'),
('550e8400-e29b-41d4-a716-446655440026', 'Aspirina 100mg Tabletas', 'Antiagregante plaquetario para prevención cardiovascular', 'CAT-ANL-001', 'Tableta', false, 'RS-ECU-2024-011', 'SKU-ECU-013', 'Bodega Guayaquil', 'Ecuador', 2200, 6500.00, 'activo', CURRENT_TIMESTAMP, '2026-12-31');

-- Productos para Perú
INSERT INTO public.producto
("productoId", nombre, descripcion, "categoriaId", "formaFarmaceutica", "requierePrescripcion", "registroSanitario", sku, "location", ubicacion, stock, precio, estado_producto, actualizado_en, "fechaVencimiento")
VALUES
('550e8400-e29b-41d4-a716-446655440027', 'Paracetamol 500mg Tabletas', 'Analgésico y antipirético para el alivio del dolor y la fiebre', 'CAT-ANL-001', 'Tableta', false, 'RS-PER-2024-001', 'SKU-PER-001', 'Bodega Lima', 'Peru', 1600, 8800.00, 'activo', CURRENT_TIMESTAMP, '2026-12-31'),
('550e8400-e29b-41d4-a716-446655440028', 'Amlodipino 5mg Tabletas', 'Bloqueador de canales de calcio para hipertensión', 'CAT-MED-001', 'Tableta', true, 'RS-PER-2024-002', 'SKU-PER-002', 'Bodega Arequipa', 'Peru', 1300, 12500.00, 'activo', CURRENT_TIMESTAMP, '2026-11-30'),
('550e8400-e29b-41d4-a716-446655440029', 'Vacuna DPT', 'Vacuna contra difteria, tos ferina y tétanos', 'CAT-VAC-001', 'Inyectable', true, 'RS-PER-2024-003', 'SKU-PER-003', 'Bodega Lima', 'Peru', 850, 46000.00, 'activo', CURRENT_TIMESTAMP, '2025-06-30'),
('550e8400-e29b-41d4-a716-446655440030', 'Vacuna Neumocócica', 'Vacuna conjugada para prevención de neumonía', 'CAT-VAC-001', 'Inyectable', true, 'RS-PER-2024-004', 'SKU-PER-004', 'Bodega Lima', 'Peru', 750, 58000.00, 'activo', CURRENT_TIMESTAMP, '2025-08-15'),
('550e8400-e29b-41d4-a716-446655440031', 'Azitromicina 500mg Tabletas', 'Antibiótico macrólido para infecciones respiratorias', 'CAT-MED-001', 'Tableta', true, 'RS-PER-2024-005', 'SKU-PER-005', 'Bodega Arequipa', 'Peru', 1700, 22000.00, 'activo', CURRENT_TIMESTAMP, '2026-10-31'),
('550e8400-e29b-41d4-a716-446655440032', 'Ventilador Mecánico Portátil', 'Equipo de soporte ventilatorio para pacientes críticos', 'CAT-EQU-001', 'Equipo', false, 'RS-PER-2024-006', 'SKU-PER-006', 'Bodega Lima', 'Peru', 15, 4500000.00, 'activo', CURRENT_TIMESTAMP, NULL),
('550e8400-e29b-41d4-a716-446655440033', 'Catéter Intravenoso 18G', 'Catéteres para acceso venoso periférico', 'CAT-INS-001', 'Insumo', false, 'RS-PER-2024-007', 'SKU-PER-007', 'Bodega Arequipa', 'Peru', 3200, 18000.00, 'activo', CURRENT_TIMESTAMP, '2027-03-31'),
('550e8400-e29b-41d4-a716-446655440034', 'Antiséptico Yodado', 'Solución antiséptica con povidona yodada', 'CAT-CON-001', 'Consumible', false, NULL, 'SKU-PER-008', 'Bodega Lima', 'Peru', 2800, 15000.00, 'activo', CURRENT_TIMESTAMP, '2027-05-31'),
('550e8400-e29b-41d4-a716-446655440035', 'Electrocardiógrafo 12 Canales', 'Equipo para registro de actividad eléctrica del corazón', 'CAT-EQU-001', 'Equipo', false, 'RS-PER-2024-008', 'SKU-PER-009', 'Bodega Arequipa', 'Peru', 30, 1800000.00, 'activo', CURRENT_TIMESTAMP, NULL),
('550e8400-e29b-41d4-a716-446655440036', 'Metronidazol 500mg Tabletas', 'Antibiótico y antiparasitario de amplio espectro', 'CAT-MED-001', 'Tableta', true, 'RS-PER-2024-009', 'SKU-PER-010', 'Bodega Lima', 'Peru', 1500, 9500.00, 'activo', CURRENT_TIMESTAMP, '2026-09-30'),
('550e8400-e29b-41d4-a716-446655440037', 'Esparadrapo Hipoalergénico', 'Cinta adhesiva médica para fijación de apósitos', 'CAT-CON-001', 'Consumible', false, NULL, 'SKU-PER-011', 'Bodega Arequipa', 'Peru', 5000, 5500.00, 'activo', CURRENT_TIMESTAMP, '2027-12-31'),
('550e8400-e29b-41d4-a716-446655440038', 'Pinzas Quirúrgicas Estériles', 'Pinzas de disección para procedimientos quirúrgicos', 'CAT-INS-001', 'Insumo', false, 'RS-PER-2024-010', 'SKU-PER-012', 'Bodega Lima', 'Peru', 450, 85000.00, 'activo', CURRENT_TIMESTAMP, '2027-08-31'),
('550e8400-e29b-41d4-a716-446655440039', 'Acetaminofén Jarabe 120mg/5ml', 'Analgésico pediátrico en presentación líquida', 'CAT-ANL-001', 'Jarabe', false, 'RS-PER-2024-011', 'SKU-PER-013', 'Bodega Arequipa', 'Peru', 900, 12500.00, 'activo', CURRENT_TIMESTAMP, '2026-12-31');

-- Productos para México
INSERT INTO public.producto
("productoId", nombre, descripcion, "categoriaId", "formaFarmaceutica", "requierePrescripcion", "registroSanitario", sku, "location", ubicacion, stock, precio, estado_producto, actualizado_en, "fechaVencimiento")
VALUES
('550e8400-e29b-41d4-a716-446655440040', 'Paracetamol 500mg Tabletas', 'Analgésico y antipirético para el alivio del dolor y la fiebre', 'CAT-ANL-001', 'Tableta', false, 'RS-MEX-2024-001', 'SKU-MEX-001', 'Bodega Ciudad de México', 'Mexico', 1800, 9500.00, 'activo', CURRENT_TIMESTAMP, '2026-12-31'),
('550e8400-e29b-41d4-a716-446655440041', 'Enalapril 10mg Tabletas', 'Inhibidor de ECA para tratamiento de hipertensión', 'CAT-MED-001', 'Tableta', true, 'RS-MEX-2024-002', 'SKU-MEX-002', 'Bodega Guadalajara', 'Mexico', 1400, 13500.00, 'activo', CURRENT_TIMESTAMP, '2026-11-30'),
('550e8400-e29b-41d4-a716-446655440042', 'Vacuna VPH', 'Vacuna contra virus del papiloma humano', 'CAT-VAC-001', 'Inyectable', true, 'RS-MEX-2024-003', 'SKU-MEX-003', 'Bodega Ciudad de México', 'Mexico', 900, 65000.00, 'activo', CURRENT_TIMESTAMP, '2025-06-30'),
('550e8400-e29b-41d4-a716-446655440043', 'Vacuna Meningocócica', 'Vacuna conjugada para prevención de meningitis', 'CAT-VAC-001', 'Inyectable', true, 'RS-MEX-2024-004', 'SKU-MEX-004', 'Bodega Ciudad de México', 'Mexico', 800, 62000.00, 'activo', CURRENT_TIMESTAMP, '2025-08-15'),
('550e8400-e29b-41d4-a716-446655440044', 'Clopidogrel 75mg Tabletas', 'Antiagregante plaquetario para síndromes coronarios', 'CAT-MED-001', 'Tableta', true, 'RS-MEX-2024-005', 'SKU-MEX-005', 'Bodega Guadalajara', 'Mexico', 1200, 28000.00, 'activo', CURRENT_TIMESTAMP, '2026-10-31'),
('550e8400-e29b-41d4-a716-446655440045', 'Respirador Artificial', 'Equipo de ventilación mecánica para UCI', 'CAT-EQU-001', 'Equipo', false, 'RS-MEX-2024-006', 'SKU-MEX-006', 'Bodega Ciudad de México', 'Mexico', 20, 5200000.00, 'activo', CURRENT_TIMESTAMP, NULL),
('550e8400-e29b-41d4-a716-446655440046', 'Sonda Nasogástrica 16Fr', 'Sondas para alimentación enteral', 'CAT-INS-001', 'Insumo', false, 'RS-MEX-2024-007', 'SKU-MEX-007', 'Bodega Guadalajara', 'Mexico', 2800, 22000.00, 'activo', CURRENT_TIMESTAMP, '2027-03-31'),
('550e8400-e29b-41d4-a716-446655440047', 'Suero Fisiológico 500ml', 'Solución salina isotónica para hidratación', 'CAT-CON-001', 'Consumible', false, NULL, 'SKU-MEX-008', 'Bodega Ciudad de México', 'Mexico', 4000, 8500.00, 'activo', CURRENT_TIMESTAMP, '2027-04-30'),
('550e8400-e29b-41d4-a716-446655440048', 'Ultrasonido Portátil', 'Equipo de diagnóstico por imágenes portátil', 'CAT-EQU-001', 'Equipo', false, 'RS-MEX-2024-008', 'SKU-MEX-009', 'Bodega Guadalajara', 'Mexico', 35, 2800000.00, 'activo', CURRENT_TIMESTAMP, NULL),
('550e8400-e29b-41d4-a716-446655440049', 'Levofloxacino 500mg Tabletas', 'Antibiótico fluoroquinolona de amplio espectro', 'CAT-MED-001', 'Tableta', true, 'RS-MEX-2024-009', 'SKU-MEX-010', 'Bodega Ciudad de México', 'Mexico', 1100, 32000.00, 'activo', CURRENT_TIMESTAMP, '2026-09-30'),
('550e8400-e29b-41d4-a716-446655440050', 'Cánulas de Oxígeno', 'Cánulas nasales para administración de oxígeno', 'CAT-CON-001', 'Consumible', false, NULL, 'SKU-MEX-011', 'Bodega Guadalajara', 'Mexico', 5500, 6500.00, 'activo', CURRENT_TIMESTAMP, '2027-12-31'),
('550e8400-e29b-41d4-a716-446655440051', 'Escalpelo Quirúrgico #10', 'Cuchillas quirúrgicas estériles desechables', 'CAT-INS-001', 'Insumo', false, 'RS-MEX-2024-010', 'SKU-MEX-012', 'Bodega Ciudad de México', 'Mexico', 1000, 15000.00, 'activo', CURRENT_TIMESTAMP, '2027-08-31'),
('550e8400-e29b-41d4-a716-446655440052', 'Diclofenaco 50mg Tabletas', 'Antiinflamatorio no esteroideo para dolor articular', 'CAT-ANL-001', 'Tableta', false, 'RS-MEX-2024-011', 'SKU-MEX-013', 'Bodega Guadalajara', 'Mexico', 2000, 11000.00, 'activo', CURRENT_TIMESTAMP, '2026-12-31');

-- Verificación: Total de 52 productos insertados
-- Distribución por país:
-- Colombia: 13 productos
-- Ecuador: 13 productos  
-- Perú: 13 productos
-- México: 13 productos


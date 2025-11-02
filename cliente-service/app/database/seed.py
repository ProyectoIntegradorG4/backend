from sqlalchemy.orm import Session
from app.models.cliente import Cliente, GerenteClienteAsignacion, TipoInstitucion
from datetime import datetime, timezone
import logging

logger = logging.getLogger("uvicorn")


def seed_clientes(db: Session):
    """
    Seed de clientes de prueba para diferentes países
    """
    # Verificar si ya hay datos
    existing_count = db.query(Cliente).count()
    if existing_count > 0:
        logger.info(f"✅ Ya existen {existing_count} clientes en la base de datos, omitiendo seed")
        return

    clientes_data = [
        # COLOMBIA - 10 clientes
        {
            "nit": "800123456-1",
            "nombre_comercial": "Hospital San Juan",
            "razon_social": "Hospital San Juan de Dios SAS",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Colombia",
            "departamento": "Cundinamarca",
            "ciudad": "Bogotá",
            "direccion": "Calle 10 # 20-30",
            "telefono": "+57 1 234 5678",
            "email": "contacto@hospitalsanjuan.com",
            "contacto_principal": "Dr. Carlos Pérez",
            "cargo_contacto": "Director de Compras",
            "especialidad_medica": "General",
            "activo": True
        },
        {
            "nit": "800234567-2",
            "nombre_comercial": "Clínica del Rosario",
            "razon_social": "Clínica del Rosario Ltda",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Colombia",
            "departamento": "Antioquia",
            "ciudad": "Medellín",
            "direccion": "Carrera 50 # 30-20",
            "telefono": "+57 4 345 6789",
            "email": "compras@clinicarosario.com",
            "contacto_principal": "Dra. María González",
            "cargo_contacto": "Jefe de Suministros",
            "especialidad_medica": "Cardiología",
            "activo": True
        },
        {
            "nit": "800345678-3",
            "nombre_comercial": "IPS Salud Total",
            "razon_social": "IPS Salud Total SA",
            "tipo_institucion": TipoInstitucion.IPS.value,
            "pais": "Colombia",
            "departamento": "Valle del Cauca",
            "ciudad": "Cali",
            "direccion": "Avenida 3N # 12-45",
            "telefono": "+57 2 456 7890",
            "email": "administracion@saludtotal.com",
            "contacto_principal": "Lic. Juan Ramírez",
            "cargo_contacto": "Administrador",
            "especialidad_medica": "Atención Primaria",
            "activo": True
        },
        {
            "nit": "800456789-4",
            "nombre_comercial": "Hospital Universitario",
            "razon_social": "Hospital Universitario del Valle",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Colombia",
            "departamento": "Valle del Cauca",
            "ciudad": "Cali",
            "direccion": "Calle 5 # 36-08",
            "telefono": "+57 2 567 8901",
            "email": "suministros@huc.edu.co",
            "contacto_principal": "Dr. Roberto Silva",
            "cargo_contacto": "Director de Recursos",
            "especialidad_medica": "Docencia e Investigación",
            "activo": True
        },
        {
            "nit": "800567890-5",
            "nombre_comercial": "Centro de Salud Norte",
            "razon_social": "Centro de Salud Norte ESE",
            "tipo_institucion": TipoInstitucion.CENTRO_SALUD.value,
            "pais": "Colombia",
            "departamento": "Atlántico",
            "ciudad": "Barranquilla",
            "direccion": "Calle 72 # 46-83",
            "telefono": "+57 5 678 9012",
            "email": "centronorte@salud.gov.co",
            "contacto_principal": "Enf. Patricia Vargas",
            "cargo_contacto": "Coordinadora",
            "especialidad_medica": "Medicina General",
            "activo": True
        },
        {
            "nit": "800678901-6",
            "nombre_comercial": "Laboratorio Clínico Central",
            "razon_social": "Laboratorio Clínico Central SAS",
            "tipo_institucion": TipoInstitucion.LABORATORIO_CLINICO.value,
            "pais": "Colombia",
            "departamento": "Cundinamarca",
            "ciudad": "Bogotá",
            "direccion": "Carrera 7 # 40-62",
            "telefono": "+57 1 789 0123",
            "email": "gerencia@labcentral.com",
            "contacto_principal": "Dra. Laura Mendoza",
            "cargo_contacto": "Gerente General",
            "especialidad_medica": "Diagnóstico Clínico",
            "activo": True
        },
        {
            "nit": "800789012-7",
            "nombre_comercial": "Clínica La Esperanza",
            "razon_social": "Clínica La Esperanza SA",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Colombia",
            "departamento": "Santander",
            "ciudad": "Bucaramanga",
            "direccion": "Calle 35 # 20-15",
            "telefono": "+57 7 890 1234",
            "email": "compras@laesperanza.com",
            "contacto_principal": "Dr. Fernando Ruiz",
            "cargo_contacto": "Director Administrativo",
            "especialidad_medica": "Cirugía",
            "activo": True
        },
        {
            "nit": "800890123-8",
            "nombre_comercial": "Hospital Infantil",
            "razon_social": "Hospital Infantil Los Ángeles",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Colombia",
            "departamento": "Antioquia",
            "ciudad": "Medellín",
            "direccion": "Carrera 48 # 20-70",
            "telefono": "+57 4 901 2345",
            "email": "adquisiciones@infantil.com",
            "contacto_principal": "Dra. Sofía Castro",
            "cargo_contacto": "Jefe de Compras",
            "especialidad_medica": "Pediatría",
            "activo": True
        },
        {
            "nit": "800901234-9",
            "nombre_comercial": "IPS Vida Plena",
            "razon_social": "IPS Vida Plena Ltda",
            "tipo_institucion": TipoInstitucion.IPS.value,
            "pais": "Colombia",
            "departamento": "Cundinamarca",
            "ciudad": "Bogotá",
            "direccion": "Calle 100 # 15-20",
            "telefono": "+57 1 012 3456",
            "email": "suministros@vidaplena.com",
            "contacto_principal": "Lic. Andrea Torres",
            "cargo_contacto": "Coordinadora de Logística",
            "especialidad_medica": "Atención Integral",
            "activo": True
        },
        {
            "nit": "800012345-0",
            "nombre_comercial": "EPS Salud Vital",
            "razon_social": "EPS Salud Vital SA",
            "tipo_institucion": TipoInstitucion.EPS.value,
            "pais": "Colombia",
            "departamento": "Cundinamarca",
            "ciudad": "Bogotá",
            "direccion": "Avenida 68 # 80-50",
            "telefono": "+57 1 123 4567",
            "email": "contratacion@saludvital.com",
            "contacto_principal": "Dr. Miguel Ángel Soto",
            "cargo_contacto": "Director de Contratación",
            "especialidad_medica": "Aseguramiento",
            "activo": True
        },

        # PERÚ - 8 clientes
        {
            "nit": "20123456789",
            "nombre_comercial": "Hospital Nacional Dos de Mayo",
            "razon_social": "Hospital Nacional Dos de Mayo",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Grau 13, Cercado de Lima",
            "telefono": "+51 1 328 0028",
            "email": "logistica@hdm.gob.pe",
            "contacto_principal": "Dr. Luis Fernández",
            "cargo_contacto": "Jefe de Logística",
            "especialidad_medica": "General",
            "activo": True
        },
        {
            "nit": "20234567890",
            "nombre_comercial": "Clínica San Pablo",
            "razon_social": "Clínica San Pablo SAC",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. El Polo 789, Surco",
            "telefono": "+51 1 610 7070",
            "email": "compras@sanpablo.pe",
            "contacto_principal": "Lic. Carmen Flores",
            "cargo_contacto": "Gerente de Compras",
            "especialidad_medica": "Multiespecialidad",
            "activo": True
        },
        {
            "nit": "20345678901",
            "nombre_comercial": "Hospital Honorio Delgado",
            "razon_social": "Hospital Regional Honorio Delgado",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Peru",
            "departamento": "Arequipa",
            "ciudad": "Arequipa",
            "direccion": "Av. Daniel Alcides Carrión s/n",
            "telefono": "+51 54 231515",
            "email": "abastecimiento@hrhd.gob.pe",
            "contacto_principal": "Dr. Jorge Campos",
            "cargo_contacto": "Director de Abastecimiento",
            "especialidad_medica": "General",
            "activo": True
        },
        {
            "nit": "20456789012",
            "nombre_comercial": "Clínica Ricardo Palma",
            "razon_social": "Clínica Ricardo Palma SA",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Javier Prado Este 1066",
            "telefono": "+51 1 224 2224",
            "email": "proveedores@ricardopalma.pe",
            "contacto_principal": "Dra. Patricia Ramos",
            "cargo_contacto": "Jefe de Adquisiciones",
            "especialidad_medica": "Alta Complejidad",
            "activo": True
        },
        {
            "nit": "20567890123",
            "nombre_comercial": "IPS Lima Norte",
            "razon_social": "IPS Lima Norte SAC",
            "tipo_institucion": TipoInstitucion.IPS.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Túpac Amaru 1250",
            "telefono": "+51 1 537 2020",
            "email": "administracion@ipsnorte.pe",
            "contacto_principal": "Lic. Ricardo Vega",
            "cargo_contacto": "Administrador",
            "especialidad_medica": "Atención Primaria",
            "activo": True
        },
        {
            "nit": "20678901234",
            "nombre_comercial": "Laboratorio Roe",
            "razon_social": "Laboratorio ROE SAC",
            "tipo_institucion": TipoInstitucion.LABORATORIO_CLINICO.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Brasil 935, Jesús María",
            "telefono": "+51 1 471 2020",
            "email": "compras@roe.pe",
            "contacto_principal": "Dr. Alberto Salas",
            "cargo_contacto": "Gerente de Operaciones",
            "especialidad_medica": "Diagnóstico",
            "activo": True
        },
        {
            "nit": "20789012345",
            "nombre_comercial": "Centro de Salud Cusco",
            "razon_social": "Centro de Salud Wanchaq",
            "tipo_institucion": TipoInstitucion.CENTRO_SALUD.value,
            "pais": "Peru",
            "departamento": "Cusco",
            "ciudad": "Cusco",
            "direccion": "Av. De la Cultura 220",
            "telefono": "+51 84 233 030",
            "email": "cswanchaq@minsa.gob.pe",
            "contacto_principal": "Enf. María Huamán",
            "cargo_contacto": "Coordinadora",
            "especialidad_medica": "Medicina General",
            "activo": True
        },
        {
            "nit": "20890123456",
            "nombre_comercial": "Hospital Cayetano Heredia",
            "razon_social": "Hospital Nacional Cayetano Heredia",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Honorio Delgado 262",
            "telefono": "+51 1 482 0402",
            "email": "logistica@cayetano.gob.pe",
            "contacto_principal": "Dr. Pedro Quispe",
            "cargo_contacto": "Director de Logística",
            "especialidad_medica": "Docencia e Investigación",
            "activo": True
        },

        # MÉXICO - 7 clientes
        {
            "nit": "HEM850101AB1",
            "nombre_comercial": "Hospital Español de México",
            "razon_social": "Sociedad de Beneficencia Española AC",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Mexico",
            "departamento": "Ciudad de México",
            "ciudad": "Ciudad de México",
            "direccion": "Av. Ejército Nacional 613",
            "telefono": "+52 55 5255 9600",
            "email": "compras@hespanol.com",
            "contacto_principal": "Lic. Roberto Hernández",
            "cargo_contacto": "Gerente de Adquisiciones",
            "especialidad_medica": "General",
            "activo": True
        },
        {
            "nit": "CAM901201CD2",
            "nombre_comercial": "Clínica Angeles Metropolitano",
            "razon_social": "Hospitales Angeles Metropolitano SA de CV",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Mexico",
            "departamento": "Ciudad de México",
            "ciudad": "Ciudad de México",
            "direccion": "Tlacotalpan 59, Roma Sur",
            "telefono": "+52 55 5265 1800",
            "email": "proveedores@angeles.com.mx",
            "contacto_principal": "Dra. Gabriela Martínez",
            "cargo_contacto": "Directora de Compras",
            "especialidad_medica": "Alta Especialidad",
            "activo": True
        },
        {
            "nit": "HGE951015EF3",
            "nombre_comercial": "Hospital General de Guadalajara",
            "razon_social": "Hospital General de Guadalajara",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Mexico",
            "departamento": "Jalisco",
            "ciudad": "Guadalajara",
            "direccion": "Calle Hospital 315",
            "telefono": "+52 33 3614 5501",
            "email": "suministros@hgjalisco.gob.mx",
            "contacto_principal": "Dr. Francisco López",
            "cargo_contacto": "Jefe de Recursos Materiales",
            "especialidad_medica": "General",
            "activo": True
        },
        {
            "nit": "CSM960320GH4",
            "nombre_comercial": "Clínica Santa María",
            "razon_social": "Clínica Santa María SA de CV",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Mexico",
            "departamento": "Nuevo León",
            "ciudad": "Monterrey",
            "direccion": "Av. Gonzalitos 1313 Nte",
            "telefono": "+52 81 8333 3030",
            "email": "adquisiciones@santamaria.com.mx",
            "contacto_principal": "Lic. Ana García",
            "cargo_contacto": "Coordinadora de Compras",
            "especialidad_medica": "Multiespecialidad",
            "activo": True
        },
        {
            "nit": "LAB970825IJ5",
            "nombre_comercial": "Laboratorios Chopo",
            "razon_social": "Laboratorios Médicos Chopo SA de CV",
            "tipo_institucion": TipoInstitucion.LABORATORIO_CLINICO.value,
            "pais": "Mexico",
            "departamento": "Ciudad de México",
            "ciudad": "Ciudad de México",
            "direccion": "Av. Cuauhtémoc 462",
            "telefono": "+52 55 5395 3535",
            "email": "compras@grupochopo.com.mx",
            "contacto_principal": "Dr. Manuel Ochoa",
            "cargo_contacto": "Director de Compras",
            "especialidad_medica": "Diagnóstico",
            "activo": True
        },
        {
            "nit": "IPS980630KL6",
            "nombre_comercial": "IPS Salud Integral",
            "razon_social": "IPS Salud Integral SA de CV",
            "tipo_institucion": TipoInstitucion.IPS.value,
            "pais": "Mexico",
            "departamento": "Jalisco",
            "ciudad": "Guadalajara",
            "direccion": "Av. López Mateos 2375",
            "telefono": "+52 33 3817 0000",
            "email": "logistica@saludintegral.mx",
            "contacto_principal": "Lic. Sandra Morales",
            "cargo_contacto": "Jefe de Logística",
            "especialidad_medica": "Atención Ambulatoria",
            "activo": True
        },
        {
            "nit": "HIN991115MN7",
            "nombre_comercial": "Hospital Infantil de México",
            "razon_social": "Hospital Infantil de México Federico Gómez",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Mexico",
            "departamento": "Ciudad de México",
            "ciudad": "Ciudad de México",
            "direccion": "Dr. Márquez 162, Doctores",
            "telefono": "+52 55 5228 9917",
            "email": "recursos@himfg.edu.mx",
            "contacto_principal": "Dra. Elena Ramírez",
            "cargo_contacto": "Subdirectora de Recursos",
            "especialidad_medica": "Pediatría",
            "activo": True
        },

        # ECUADOR - 5 clientes
        {
            "nit": "1790123456001",
            "nombre_comercial": "Hospital Metropolitano",
            "razon_social": "Hospital Metropolitano SA",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Ecuador",
            "departamento": "Pichincha",
            "ciudad": "Quito",
            "direccion": "Av. Mariana de Jesús y Nicolás Arteta",
            "telefono": "+593 2 399 8000",
            "email": "compras@hospitalmetropolitano.org",
            "contacto_principal": "Lic. Diego Salazar",
            "cargo_contacto": "Gerente de Compras",
            "especialidad_medica": "General",
            "activo": True
        },
        {
            "nit": "1790234567001",
            "nombre_comercial": "Clínica Kennedy",
            "razon_social": "Clínica Kennedy SA",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Ecuador",
            "departamento": "Guayas",
            "ciudad": "Guayaquil",
            "direccion": "Av. del Periodista",
            "telefono": "+593 4 228 9666",
            "email": "adquisiciones@clinicakennedy.com",
            "contacto_principal": "Dra. María Vera",
            "cargo_contacto": "Directora de Adquisiciones",
            "especialidad_medica": "Multiespecialidad",
            "activo": True
        },
        {
            "nit": "1790345678001",
            "nombre_comercial": "Hospital Carlos Andrade Marín",
            "razon_social": "Hospital Carlos Andrade Marín IESS",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Ecuador",
            "departamento": "Pichincha",
            "ciudad": "Quito",
            "direccion": "Av. 18 de Septiembre y Ayacucho",
            "telefono": "+593 2 256 2296",
            "email": "logistica@hcam.iess.gob.ec",
            "contacto_principal": "Dr. Carlos Morales",
            "cargo_contacto": "Jefe de Logística",
            "especialidad_medica": "General",
            "activo": True
        },
        {
            "nit": "1790456789001",
            "nombre_comercial": "Centro de Salud Guayaquil",
            "razon_social": "Centro de Salud Tipo C Guayaquil",
            "tipo_institucion": TipoInstitucion.CENTRO_SALUD.value,
            "pais": "Ecuador",
            "departamento": "Guayas",
            "ciudad": "Guayaquil",
            "direccion": "Calle 25 y Av. Quito",
            "telefono": "+593 4 230 1212",
            "email": "csgye@msp.gob.ec",
            "contacto_principal": "Enf. Rosa Chávez",
            "cargo_contacto": "Coordinadora",
            "especialidad_medica": "Atención Primaria",
            "activo": True
        },
        {
            "nit": "1790567890001",
            "nombre_comercial": "Laboratorio Clínico Pasteur",
            "razon_social": "Laboratorio Clínico Pasteur Cía Ltda",
            "tipo_institucion": TipoInstitucion.LABORATORIO_CLINICO.value,
            "pais": "Ecuador",
            "departamento": "Pichincha",
            "ciudad": "Quito",
            "direccion": "Av. 6 de Diciembre N34-120",
            "telefono": "+593 2 246 7070",
            "email": "gerencia@labpasteur.com",
            "contacto_principal": "Dr. Andrés Jiménez",
            "cargo_contacto": "Gerente General",
            "especialidad_medica": "Diagnóstico",
            "activo": True
        },
    ]

    # Insertar clientes
    clientes = []
    for data in clientes_data:
        cliente = Cliente(**data)
        db.add(cliente)
        clientes.append(cliente)

    db.commit()
    logger.info(f"✅ Se insertaron {len(clientes)} clientes de prueba")


def seed_gerentes_cuenta(db: Session):
    """
    Seed de gerentes de cuenta en user_db.
    Crea 2 gerentes por país para pruebas.
    """
    try:
        from sqlalchemy import create_engine, text
        import os
        
        # Conexión a user_db
        USER_DB_URL = os.getenv(
            "USER_DATABASE_URL",
            "postgresql+psycopg://user_service:user_password@postgres-db:5432/user_db"
        )
        
        user_engine = create_engine(USER_DB_URL)
        
        # Hash de contraseña por defecto (Password123!)
        # Este es el hash de bcrypt para "Password123!"
        password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkIK1rGQ9."
        
        gerentes_data = [
            # Colombia
            ("Juan Gerente Colombia", "gerente.colombia@medisupply.com", "111111111-1"),
            ("María Rodríguez Colombia", "maria.rodriguez@medisupply.com", "111111111-1"),
            # Perú
            ("Carlos Mendoza Perú", "carlos.mendoza@medisupply.com", "111111111-3"),
            ("Ana Torres Perú", "ana.torres@medisupply.com", "111111111-3"),
            # México
            ("Roberto Hernández México", "roberto.hernandez@medisupply.com", "111111111-2"),
            ("Patricia López México", "patricia.lopez@medisupply.com", "111111111-2"),
            # Ecuador
            ("Diego Salazar Ecuador", "diego.salazar@medisupply.com", "111111111-4"),
            ("Sofía Morales Ecuador", "sofia.morales@medisupply.com", "111111111-4"),
        ]
        
        with user_engine.connect() as conn:
            for nombre, email, nit in gerentes_data:
                # Insertar si no existe
                query = text("""
                    INSERT INTO usuarios (nombre, correo_electronico, password_hash, nit, rol, activo)
                    VALUES (:nombre, :email, :password_hash, :nit, 'gerente_cuenta', true)
                    ON CONFLICT (correo_electronico) DO NOTHING
                """)
                conn.execute(query, {
                    "nombre": nombre,
                    "email": email,
                    "password_hash": password_hash,
                    "nit": nit
                })
            
            conn.commit()
        
        user_engine.dispose()
        logger.info("✅ Gerentes de cuenta verificados/creados en user_db")
        
    except Exception as e:
        logger.error(f"Error al crear gerentes de cuenta: {str(e)}")
        logger.info("⚠️  Continuando sin seed de gerentes. Créelos manualmente si es necesario.")


def seed_asignaciones(db: Session):
    """
    Seed de asignaciones de clientes a gerentes.
    Distribuye los clientes entre los gerentes de cada país.
    """
    from app.models.cliente import GerenteClienteAsignacion
    
    # Verificar si ya hay asignaciones
    existing_count = db.query(GerenteClienteAsignacion).count()
    if existing_count > 0:
        logger.info(f"✅ Ya existen {existing_count} asignaciones, omitiendo seed")
        return

    try:
        # Crear asignaciones: distribuir clientes entre gerentes por país
        # Gerentes IDs: Colombia(1,2), Peru(3,4), Mexico(5,6), Ecuador(7,8)
        
        asignaciones_config = [
            # Colombia - IDs impares al gerente 1, pares al gerente 2
            (1, "Colombia", "MOD(cliente_id, 2) = 1"),  # Gerente 1: impares
            (2, "Colombia", "MOD(cliente_id, 2) = 0"),  # Gerente 2: pares
            # Perú
            (3, "Peru", "MOD(cliente_id, 2) = 1"),      # Gerente 3: impares
            (4, "Peru", "MOD(cliente_id, 2) = 0"),      # Gerente 4: pares
            # México
            (5, "Mexico", "MOD(cliente_id, 2) = 1"),    # Gerente 5: impares
            (6, "Mexico", "MOD(cliente_id, 2) = 0"),    # Gerente 6: pares
            # Ecuador
            (7, "Ecuador", "MOD(cliente_id, 2) = 1"),   # Gerente 7: impares
            (8, "Ecuador", "MOD(cliente_id, 2) = 0"),   # Gerente 8: pares
        ]
        
        total_created = 0
        
        for gerente_id, pais, condicion in asignaciones_config:
            # Obtener clientes que cumplen la condición
            clientes = db.query(Cliente).filter(
                Cliente.pais == pais,
                text(condicion)
            ).all()
            
            for cliente in clientes:
                asignacion = GerenteClienteAsignacion(
                    gerente_id=gerente_id,
                    cliente_id=cliente.cliente_id,
                    pais=pais,
                    activo=True
                )
                db.add(asignacion)
                total_created += 1
        
        db.commit()
        logger.info(f"✅ Se crearon {total_created} asignaciones de clientes a gerentes")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear asignaciones: {str(e)}")
        logger.info("⚠️  Continuando sin asignaciones. Créelas manualmente si es necesario.")


def run_seeds(db: Session):
    """
    Ejecutar todos los seeds de forma automática.
    
    Orden de ejecución:
    1. Clientes (en cliente_db)
    2. Gerentes de cuenta (en user_db - cross-database)
    3. Asignaciones (en cliente_db, depende de gerentes)
    """
    logger.info("🌱 Iniciando seed de datos de prueba...")
    
    # 1. Seed de clientes
    seed_clientes(db)
    
    # 2. Seed de gerentes (en user_db)
    seed_gerentes_cuenta(db)
    
    # 3. Seed de asignaciones
    seed_asignaciones(db)
    
    logger.info("✅ Seed de datos completado")


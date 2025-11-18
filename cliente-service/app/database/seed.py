from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.cliente import Cliente, GerenteClienteAsignacion, TipoInstitucion
from datetime import datetime, timezone
import logging

logger = logging.getLogger("uvicorn")


def seed_clientes(db: Session):
    """
    Seed de clientes de prueba (sedes de instituciones asociadas).
    
    IMPORTANTE: Los NITs usados deben existir en la tabla instituciones_asociadas
    (en nit_db). Cada institución puede tener múltiples sedes en diferentes
    departamentos y ciudades del mismo país.
    """
    # Verificar si ya hay datos
    existing_count = db.query(Cliente).count()
    if existing_count > 0:
        logger.info(f"✅ Ya existen {existing_count} clientes en la base de datos, omitiendo seed")
        return

    # Datos de instituciones asociadas (NITs que existen en instituciones_asociadas)
    # Cada institución puede tener múltiples sedes
    clientes_data = [
        # COLOMBIA - Sedes de diferentes instituciones
        # Institución: Carter LLC (NIT: 17-767-0400)
        {
            "nit": "17-767-0400",
            "nombre_comercial": "Carter LLC - Sede Bogotá",
            "razon_social": "Carter LLC",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Colombia",
            "departamento": "Cundinamarca",
            "ciudad": "Bogotá",
            "direccion": "Calle 10 # 20-30",
            "telefono": "+57 1 234 5678",
            "email": "bogota@carterllc.com",
            "contacto_principal": "Dr. Carlos Pérez",
            "cargo_contacto": "Director de Compras",
            "especialidad_medica": "General",
            "activo": True
        },
        {
            "nit": "17-767-0400",
            "nombre_comercial": "Carter LLC - Sede Medellín",
            "razon_social": "Carter LLC",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Colombia",
            "departamento": "Antioquia",
            "ciudad": "Medellín",
            "direccion": "Carrera 50 # 30-20",
            "telefono": "+57 4 345 6789",
            "email": "medellin@carterllc.com",
            "contacto_principal": "Dra. María González",
            "cargo_contacto": "Jefe de Suministros",
            "especialidad_medica": "Cardiología",
            "activo": True
        },
        # Institución: Senger, Mraz and Conroy (NIT: 68-286-6298)
        {
            "nit": "68-286-6298",
            "nombre_comercial": "Clínica Senger - Sede Principal",
            "razon_social": "Senger, Mraz and Conroy",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Colombia",
            "departamento": "Valle del Cauca",
            "ciudad": "Cali",
            "direccion": "Avenida 3N # 12-45",
            "telefono": "+57 2 456 7890",
            "email": "cali@senger.com",
            "contacto_principal": "Lic. Juan Ramírez",
            "cargo_contacto": "Administrador",
            "especialidad_medica": "Atención Primaria",
            "activo": True
        },
        # Institución: Pouros-Terry (NIT: 94-974-6914)
        {
            "nit": "94-974-6914",
            "nombre_comercial": "Hospital Pouros-Terry",
            "razon_social": "Pouros-Terry",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Colombia",
            "departamento": "Valle del Cauca",
            "ciudad": "Cali",
            "direccion": "Calle 5 # 36-08",
            "telefono": "+57 2 567 8901",
            "email": "suministros@pouros.com",
            "contacto_principal": "Dr. Roberto Silva",
            "cargo_contacto": "Director de Recursos",
            "especialidad_medica": "Docencia e Investigación",
            "activo": True
        },
        {
            "nit": "94-974-6914",
            "nombre_comercial": "Hospital Pouros-Terry - Sede Barranquilla",
            "razon_social": "Pouros-Terry",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Colombia",
            "departamento": "Atlántico",
            "ciudad": "Barranquilla",
            "direccion": "Calle 72 # 46-83",
            "telefono": "+57 5 678 9012",
            "email": "barranquilla@pouros.com",
            "contacto_principal": "Enf. Patricia Vargas",
            "cargo_contacto": "Coordinadora",
            "especialidad_medica": "Medicina General",
            "activo": True
        },
        # Institución: Funk, Cassin and Kirlin (NIT: 36-923-6400)
        {
            "nit": "36-923-6400",
            "nombre_comercial": "Laboratorio Clínico Funk",
            "razon_social": "Funk, Cassin and Kirlin",
            "tipo_institucion": TipoInstitucion.LABORATORIO_CLINICO.value,
            "pais": "Colombia",
            "departamento": "Cundinamarca",
            "ciudad": "Bogotá",
            "direccion": "Carrera 7 # 40-62",
            "telefono": "+57 1 789 0123",
            "email": "gerencia@funklab.com",
            "contacto_principal": "Dra. Laura Mendoza",
            "cargo_contacto": "Gerente General",
            "especialidad_medica": "Diagnóstico Clínico",
            "activo": True
        },
        # Institución: Marvin-Dickinson (NIT: 60-803-9102)
        {
            "nit": "60-803-9102",
            "nombre_comercial": "Clínica Marvin",
            "razon_social": "Marvin-Dickinson",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Colombia",
            "departamento": "Santander",
            "ciudad": "Bucaramanga",
            "direccion": "Calle 35 # 20-15",
            "telefono": "+57 7 890 1234",
            "email": "compras@marvin.com",
            "contacto_principal": "Dr. Fernando Ruiz",
            "cargo_contacto": "Director Administrativo",
            "especialidad_medica": "Cirugía",
            "activo": True
        },
        # Institución: Hirthe Inc (NIT: 63-912-4938)
        {
            "nit": "63-912-4938",
            "nombre_comercial": "IPS Hirthe",
            "razon_social": "Hirthe Inc",
            "tipo_institucion": TipoInstitucion.IPS.value,
            "pais": "Colombia",
            "departamento": "Cundinamarca",
            "ciudad": "Bogotá",
            "direccion": "Calle 100 # 15-20",
            "telefono": "+57 1 012 3456",
            "email": "suministros@hirthe.com",
            "contacto_principal": "Lic. Andrea Torres",
            "cargo_contacto": "Coordinadora de Logística",
            "especialidad_medica": "Atención Integral",
            "activo": True
        },
        # Institución: Buckridge, Ward and Carroll (NIT: 47-141-4401)
        {
            "nit": "47-141-4401",
            "nombre_comercial": "EPS Buckridge",
            "razon_social": "Buckridge, Ward and Carroll",
            "tipo_institucion": TipoInstitucion.EPS.value,
            "pais": "Colombia",
            "departamento": "Cundinamarca",
            "ciudad": "Bogotá",
            "direccion": "Avenida 68 # 80-50",
            "telefono": "+57 1 123 4567",
            "email": "contratacion@buckridge.com",
            "contacto_principal": "Dr. Miguel Ángel Soto",
            "cargo_contacto": "Director de Contratación",
            "especialidad_medica": "Aseguramiento",
            "activo": True
        },
        {
            "nit": "47-141-4401",
            "nombre_comercial": "EPS Buckridge - Sede Medellín",
            "razon_social": "Buckridge, Ward and Carroll",
            "tipo_institucion": TipoInstitucion.EPS.value,
            "pais": "Colombia",
            "departamento": "Antioquia",
            "ciudad": "Medellín",
            "direccion": "Carrera 48 # 20-70",
            "telefono": "+57 4 901 2345",
            "email": "medellin@buckridge.com",
            "contacto_principal": "Dra. Sofía Castro",
            "cargo_contacto": "Jefe de Compras",
            "especialidad_medica": "Aseguramiento",
            "activo": True
        },
        # Institución: Jacobi-Lubowitz (NIT: 01-860-7439)
        {
            "nit": "01-860-7439",
            "nombre_comercial": "Centro de Salud Jacobi",
            "razon_social": "Jacobi-Lubowitz",
            "tipo_institucion": TipoInstitucion.CENTRO_SALUD.value,
            "pais": "Colombia",
            "departamento": "Cundinamarca",
            "ciudad": "Bogotá",
            "direccion": "Calle 50 # 15-30",
            "telefono": "+57 1 345 6789",
            "email": "contacto@jacobi.com",
            "contacto_principal": "Dr. Luis Martínez",
            "cargo_contacto": "Director",
            "especialidad_medica": "Atención Primaria",
            "activo": True
        },
        # PERÚ - Sedes de diferentes instituciones
        # Institución: Balistreri-Walsh (NIT: 61-362-0843)
        {
            "nit": "61-362-0843",
            "nombre_comercial": "Hospital Balistreri-Walsh - Sede Lima",
            "razon_social": "Balistreri-Walsh",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Grau 13, Cercado de Lima",
            "telefono": "+51 1 328 0028",
            "email": "lima@balistreri.com",
            "contacto_principal": "Dr. Luis Fernández",
            "cargo_contacto": "Jefe de Logística",
            "especialidad_medica": "General",
            "activo": True
        },
        {
            "nit": "61-362-0843",
            "nombre_comercial": "Hospital Balistreri-Walsh - Sede Arequipa",
            "razon_social": "Balistreri-Walsh",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Peru",
            "departamento": "Arequipa",
            "ciudad": "Arequipa",
            "direccion": "Av. Daniel Alcides Carrión s/n",
            "telefono": "+51 54 231515",
            "email": "arequipa@balistreri.com",
            "contacto_principal": "Dr. Jorge Campos",
            "cargo_contacto": "Director de Abastecimiento",
            "especialidad_medica": "General",
            "activo": True
        },
        # Institución: Walker and Sons (NIT: 89-078-5710)
        {
            "nit": "89-078-5710",
            "nombre_comercial": "Clínica Walker - Sede Principal",
            "razon_social": "Walker and Sons",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. El Polo 789, Surco",
            "telefono": "+51 1 610 7070",
            "email": "compras@walker.pe",
            "contacto_principal": "Lic. Carmen Flores",
            "cargo_contacto": "Gerente de Compras",
            "especialidad_medica": "Multiespecialidad",
            "activo": True
        },
        # Institución: Miller Group (NIT: 39-067-7505)
        {
            "nit": "39-067-7505",
            "nombre_comercial": "Clínica Miller - Sede Lima",
            "razon_social": "Miller Group",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Javier Prado Este 1066",
            "telefono": "+51 1 224 2224",
            "email": "proveedores@miller.pe",
            "contacto_principal": "Dra. Patricia Ramos",
            "cargo_contacto": "Jefe de Adquisiciones",
            "especialidad_medica": "Alta Complejidad",
            "activo": True
        },
        # Institución: Cormier, Ebert and Mann (NIT: 22-366-8556)
        {
            "nit": "22-366-8556",
            "nombre_comercial": "IPS Cormier",
            "razon_social": "Cormier, Ebert and Mann",
            "tipo_institucion": TipoInstitucion.IPS.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Túpac Amaru 1250",
            "telefono": "+51 1 537 2020",
            "email": "administracion@cormier.pe",
            "contacto_principal": "Lic. Ricardo Vega",
            "cargo_contacto": "Administrador",
            "especialidad_medica": "Atención Primaria",
            "activo": True
        },
        # Institución: Kihn Inc (NIT: 18-650-9284)
        {
            "nit": "18-650-9284",
            "nombre_comercial": "Laboratorio Kihn",
            "razon_social": "Kihn Inc",
            "tipo_institucion": TipoInstitucion.LABORATORIO_CLINICO.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Brasil 935, Jesús María",
            "telefono": "+51 1 471 2020",
            "email": "compras@kihn.pe",
            "contacto_principal": "Dr. Alberto Salas",
            "cargo_contacto": "Gerente de Operaciones",
            "especialidad_medica": "Diagnóstico",
            "activo": True
        },
        # Institución: Welch-Grady (NIT: 29-739-6036)
        {
            "nit": "29-739-6036",
            "nombre_comercial": "Centro de Salud Welch - Cusco",
            "razon_social": "Welch-Grady",
            "tipo_institucion": TipoInstitucion.CENTRO_SALUD.value,
            "pais": "Peru",
            "departamento": "Cusco",
            "ciudad": "Cusco",
            "direccion": "Av. De la Cultura 220",
            "telefono": "+51 84 233 030",
            "email": "cusco@welch.pe",
            "contacto_principal": "Enf. María Huamán",
            "cargo_contacto": "Coordinadora",
            "especialidad_medica": "Medicina General",
            "activo": True
        },
        # Institución: Skiles-Douglas (NIT: 89-809-8904)
        {
            "nit": "89-809-8904",
            "nombre_comercial": "Hospital Skiles-Douglas",
            "razon_social": "Skiles-Douglas",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Honorio Delgado 262",
            "telefono": "+51 1 482 0402",
            "email": "logistica@skiles.pe",
            "contacto_principal": "Dr. Pedro Quispe",
            "cargo_contacto": "Director de Logística",
            "especialidad_medica": "Docencia e Investigación",
            "activo": True
        },
        # Institución: Macejkovic, Spinka and Bartoletti (NIT: 61-635-3493)
        {
            "nit": "61-635-3493",
            "nombre_comercial": "Hospital Macejkovic",
            "razon_social": "Macejkovic, Spinka and Bartoletti",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Javier Prado 1500",
            "telefono": "+51 1 445 6789",
            "email": "compras@macejkovic.pe",
            "contacto_principal": "Dr. Carlos Mendoza",
            "cargo_contacto": "Jefe de Compras",
            "especialidad_medica": "General",
            "activo": True
        },
        # Institución: Goyette, Rowe and Hand (NIT: 84-424-9192)
        {
            "nit": "84-424-9192",
            "nombre_comercial": "Clínica Goyette",
            "razon_social": "Goyette, Rowe and Hand",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Arequipa 1234",
            "telefono": "+51 1 556 7890",
            "email": "contacto@goyette.pe",
            "contacto_principal": "Dra. Ana Torres",
            "cargo_contacto": "Directora",
            "especialidad_medica": "Multiespecialidad",
            "activo": True
        },
        # Institución: Hartmann, Terry and Hettinger (NIT: 22-686-5898)
        {
            "nit": "22-686-5898",
            "nombre_comercial": "IPS Hartmann",
            "razon_social": "Hartmann, Terry and Hettinger",
            "tipo_institucion": TipoInstitucion.IPS.value,
            "pais": "Peru",
            "departamento": "Lima",
            "ciudad": "Lima",
            "direccion": "Av. Brasil 456",
            "telefono": "+51 1 567 8901",
            "email": "info@hartmann.pe",
            "contacto_principal": "Lic. Roberto Vega",
            "cargo_contacto": "Administrador",
            "especialidad_medica": "Atención Primaria",
            "activo": True
        },

        # MÉXICO - Sedes de diferentes instituciones
        # Institución: Boyer, MacGyver and Smitham (NIT: 83-102-2959)
        {
            "nit": "83-102-2959",
            "nombre_comercial": "Hospital Boyer - Sede Ciudad de México",
            "razon_social": "Boyer, MacGyver and Smitham",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Mexico",
            "departamento": "Ciudad de México",
            "ciudad": "Ciudad de México",
            "direccion": "Av. Ejército Nacional 613",
            "telefono": "+52 55 5255 9600",
            "email": "cdmx@boyer.com.mx",
            "contacto_principal": "Lic. Roberto Hernández",
            "cargo_contacto": "Gerente de Adquisiciones",
            "especialidad_medica": "General",
            "activo": True
        },
        {
            "nit": "83-102-2959",
            "nombre_comercial": "Hospital Boyer - Sede Guadalajara",
            "razon_social": "Boyer, MacGyver and Smitham",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Mexico",
            "departamento": "Jalisco",
            "ciudad": "Guadalajara",
            "direccion": "Calle Hospital 315",
            "telefono": "+52 33 3614 5501",
            "email": "guadalajara@boyer.com.mx",
            "contacto_principal": "Dr. Francisco López",
            "cargo_contacto": "Jefe de Recursos Materiales",
            "especialidad_medica": "General",
            "activo": True
        },
        # Institución: Corwin, Haley and Mueller (NIT: 26-597-2054)
        {
            "nit": "26-597-2054",
            "nombre_comercial": "Clínica Corwin",
            "razon_social": "Corwin, Haley and Mueller",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Mexico",
            "departamento": "Ciudad de México",
            "ciudad": "Ciudad de México",
            "direccion": "Tlacotalpan 59, Roma Sur",
            "telefono": "+52 55 5265 1800",
            "email": "proveedores@corwin.com.mx",
            "contacto_principal": "Dra. Gabriela Martínez",
            "cargo_contacto": "Directora de Compras",
            "especialidad_medica": "Alta Especialidad",
            "activo": True
        },
        # Institución: Schinner LLC (NIT: 54-999-4764)
        {
            "nit": "54-999-4764",
            "nombre_comercial": "Clínica Schinner - Monterrey",
            "razon_social": "Schinner LLC",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Mexico",
            "departamento": "Nuevo León",
            "ciudad": "Monterrey",
            "direccion": "Av. Gonzalitos 1313 Nte",
            "telefono": "+52 81 8333 3030",
            "email": "adquisiciones@schinner.com.mx",
            "contacto_principal": "Lic. Ana García",
            "cargo_contacto": "Coordinadora de Compras",
            "especialidad_medica": "Multiespecialidad",
            "activo": True
        },
        # Institución: Streich, Medhurst and Bradtke (NIT: 22-962-8792)
        {
            "nit": "22-962-8792",
            "nombre_comercial": "Laboratorio Streich",
            "razon_social": "Streich, Medhurst and Bradtke",
            "tipo_institucion": TipoInstitucion.LABORATORIO_CLINICO.value,
            "pais": "Mexico",
            "departamento": "Ciudad de México",
            "ciudad": "Ciudad de México",
            "direccion": "Av. Cuauhtémoc 462",
            "telefono": "+52 55 5395 3535",
            "email": "compras@streich.com.mx",
            "contacto_principal": "Dr. Manuel Ochoa",
            "cargo_contacto": "Director de Compras",
            "especialidad_medica": "Diagnóstico",
            "activo": True
        },
        # Institución: Haag Group (NIT: 25-662-9858)
        {
            "nit": "25-662-9858",
            "nombre_comercial": "IPS Haag",
            "razon_social": "Haag Group",
            "tipo_institucion": TipoInstitucion.IPS.value,
            "pais": "Mexico",
            "departamento": "Jalisco",
            "ciudad": "Guadalajara",
            "direccion": "Av. López Mateos 2375",
            "telefono": "+52 33 3817 0000",
            "email": "logistica@haag.com.mx",
            "contacto_principal": "Lic. Sandra Morales",
            "cargo_contacto": "Jefe de Logística",
            "especialidad_medica": "Atención Ambulatoria",
            "activo": True
        },
        {
            "nit": "25-662-9858",
            "nombre_comercial": "IPS Haag - Sede Ciudad de México",
            "razon_social": "Haag Group",
            "tipo_institucion": TipoInstitucion.IPS.value,
            "pais": "Mexico",
            "departamento": "Ciudad de México",
            "ciudad": "Ciudad de México",
            "direccion": "Dr. Márquez 162, Doctores",
            "telefono": "+52 55 5228 9917",
            "email": "cdmx@haag.com.mx",
            "contacto_principal": "Dra. Elena Ramírez",
            "cargo_contacto": "Subdirectora de Recursos",
            "especialidad_medica": "Atención Ambulatoria",
            "activo": True
        },

        # ECUADOR - Sedes de diferentes instituciones
        # Institución: Baumbach LLC (NIT: 54-038-6594)
        {
            "nit": "54-038-6594",
            "nombre_comercial": "Hospital Baumbach - Quito",
            "razon_social": "Baumbach LLC",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Ecuador",
            "departamento": "Pichincha",
            "ciudad": "Quito",
            "direccion": "Av. Mariana de Jesús y Nicolás Arteta",
            "telefono": "+593 2 399 8000",
            "email": "quito@baumbach.com",
            "contacto_principal": "Lic. Diego Salazar",
            "cargo_contacto": "Gerente de Compras",
            "especialidad_medica": "General",
            "activo": True
        },
        {
            "nit": "54-038-6594",
            "nombre_comercial": "Hospital Baumbach - Guayaquil",
            "razon_social": "Baumbach LLC",
            "tipo_institucion": TipoInstitucion.HOSPITAL.value,
            "pais": "Ecuador",
            "departamento": "Guayas",
            "ciudad": "Guayaquil",
            "direccion": "Av. del Periodista",
            "telefono": "+593 4 228 9666",
            "email": "guayaquil@baumbach.com",
            "contacto_principal": "Dra. María Vera",
            "cargo_contacto": "Directora de Adquisiciones",
            "especialidad_medica": "General",
            "activo": True
        },
        # Institución: Wehner and Sons (NIT: 87-519-4367)
        {
            "nit": "87-519-4367",
            "nombre_comercial": "Clínica Wehner",
            "razon_social": "Wehner and Sons",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Ecuador",
            "departamento": "Pichincha",
            "ciudad": "Quito",
            "direccion": "Av. 18 de Septiembre y Ayacucho",
            "telefono": "+593 2 256 2296",
            "email": "logistica@wehner.com",
            "contacto_principal": "Dr. Carlos Morales",
            "cargo_contacto": "Jefe de Logística",
            "especialidad_medica": "Multiespecialidad",
            "activo": True
        },
        {
            "nit": "87-519-4367",
            "nombre_comercial": "Clínica Wehner - Sede Guayaquil",
            "razon_social": "Wehner and Sons",
            "tipo_institucion": TipoInstitucion.CLINICA.value,
            "pais": "Ecuador",
            "departamento": "Guayas",
            "ciudad": "Guayaquil",
            "direccion": "Calle 25 y Av. Quito",
            "telefono": "+593 4 230 1212",
            "email": "guayaquil@wehner.com",
            "contacto_principal": "Enf. Rosa Chávez",
            "cargo_contacto": "Coordinadora",
            "especialidad_medica": "Multiespecialidad",
            "activo": True
        },
        # Institución: Centro de Salud (usando Baumbach LLC) - Diferente ubicación para evitar duplicado
        {
            "nit": "54-038-6594",
            "nombre_comercial": "Centro de Salud Baumbach - Cuenca",
            "razon_social": "Baumbach LLC",
            "tipo_institucion": TipoInstitucion.CENTRO_SALUD.value,
            "pais": "Ecuador",
            "departamento": "Azuay",
            "ciudad": "Cuenca",
            "direccion": "Av. 12 de Abril y Av. Loja",
            "telefono": "+593 7 284 1234",
            "email": "cuenca@baumbach.com",
            "contacto_principal": "Dr. Andrés Jiménez",
            "cargo_contacto": "Gerente General",
            "especialidad_medica": "Atención Primaria",
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
        
        # Hash de contraseña por defecto (Admin@123)
        # Este es el hash de bcrypt para "Admin@123"
        password_hash = "$2b$10$V2ANvb20Gv22moKqFNWlG.rhTvhX7s7HHdchhU55fRKYOz.VW0UkK"
        
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
                text(condicion) # type: ignore
            ).all()
            
            for cliente in clientes:
                asignacion = GerenteClienteAsignacion(
                    gerente_id=gerente_id,
                    cliente_id=cliente.cliente_id,
                    nit=cliente.nit,  # Incluir el NIT del cliente (denormalizado)
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


"""
Script para cargar datos de ejemplo en la tabla de proveedores
"""
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importar el modelo
from app.models.proveedor import (
    Base, Proveedor, TipoProveedorEnum, PaisEnum, EstadoProveedorEnum
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://proveedor_service:proveedor_password@postgres-db:5432/proveedor_db"
)

# Crear engine y session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_database():
    """Crear todas las tablas"""
    Base.metadata.create_all(bind=engine)
    print("✓ Base de datos inicializada")

def load_sample_data():
    """Cargar datos de ejemplo"""
    session = SessionLocal()
    
    try:
        # Verificar si ya existen datos
        existing = session.query(Proveedor).first()
        if existing:
            print("✓ Base de datos ya contiene datos, omitiendo carga de ejemplo")
            return
        
        # Datos de ejemplo
        proveedores_ejemplo = [
            {
                "razon_social": "Farmacéutica Colombiana S.A.",
                "nit": "800123456-1",
                "tipo_proveedor": TipoProveedorEnum.LABORATORIO,
                "email": "info@farmacolombiana.com",
                "telefono": "+57-1-2345678",
                "direccion": "Cra. 7 # 32-15, Bogotá",
                "ciudad": "Bogotá",
                "pais": PaisEnum.COLOMBIA,
                "certificaciones": ["ISO 9001:2015", "ISO 13485:2016", "GMP"],
                "estado": EstadoProveedorEnum.ACTIVO,
                "calificacion": 4.5,
                "tiempo_entrega_promedio": 3,
            },
            {
                "razon_social": "Distribuidora Médica del Perú",
                "nit": "20123456789",
                "tipo_proveedor": TipoProveedorEnum.DISTRIBUIDOR,
                "email": "ventas@distribmedica.pe",
                "telefono": "+51-1-5551234",
                "direccion": "Av. Javier Prado Este 1234, Lima",
                "ciudad": "Lima",
                "pais": PaisEnum.PERU,
                "certificaciones": ["ISO 9001:2015"],
                "estado": EstadoProveedorEnum.ACTIVO,
                "calificacion": 4.2,
                "tiempo_entrega_promedio": 5,
            },
            {
                "razon_social": "Importadora Ecuatoriana de Fármacos",
                "nit": "0987654321",
                "tipo_proveedor": TipoProveedorEnum.IMPORTADOR,
                "email": "contacto@importfarmaeco.ec",
                "telefono": "+593-2-9876543",
                "direccion": "Calle 12 de Octubre 1500, Quito",
                "ciudad": "Quito",
                "pais": PaisEnum.ECUADOR,
                "certificaciones": ["ISO 13485:2016", "GMP"],
                "estado": EstadoProveedorEnum.ACTIVO,
                "calificacion": 3.8,
                "tiempo_entrega_promedio": 7,
            },
            {
                "razon_social": "Laboratorios Mexicanos S.A. de C.V.",
                "nit": "LAB123456XYZ",
                "tipo_proveedor": TipoProveedorEnum.LABORATORIO,
                "email": "sales@labmexicanos.com.mx",
                "telefono": "+52-55-12345678",
                "direccion": "Av. Paseo de la Reforma 505, México DF",
                "ciudad": "Mexico City",
                "pais": PaisEnum.MEXICO,
                "certificaciones": ["ISO 9001:2015", "ISO 13485:2016"],
                "estado": EstadoProveedorEnum.ACTIVO,
                "calificacion": 4.7,
                "tiempo_entrega_promedio": 2,
            },
            {
                "razon_social": "Distribuidora Especializada Colombia",
                "nit": "900234567-9",
                "tipo_proveedor": TipoProveedorEnum.DISTRIBUIDOR,
                "email": "soporte@distribespecializada.co",
                "telefono": "+57-1-3334444",
                "direccion": "Calle 80 # 15-45, Medellín",
                "ciudad": "Medellín",
                "pais": PaisEnum.COLOMBIA,
                "certificaciones": ["ISO 9001:2015"],
                "estado": EstadoProveedorEnum.INACTIVO,
                "calificacion": 3.5,
                "tiempo_entrega_promedio": 4,
            },
        ]
        
        # Crear instancias de Proveedor
        for prov_data in proveedores_ejemplo:
            proveedor = Proveedor(
                proveedor_id=uuid.uuid4(),
                **prov_data,
                version=0
            )
            session.add(proveedor)
        
        session.commit()
        print(f"✓ {len(proveedores_ejemplo)} proveedores de ejemplo cargados exitosamente")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error al cargar datos de ejemplo: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Inicializando base de datos de proveedores...")
    init_database()
    load_sample_data()
    print("✓ Inicialización completada")

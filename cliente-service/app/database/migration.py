"""
Módulo de migraciones para cliente-service
Ejecuta migraciones SQL automáticamente al iniciar el servicio
"""

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("uvicorn")


def run_migrations(db: Session) -> None:
    """
    Ejecutar migraciones pendientes de manera idempotente
    """
    logger.info("🔄 Verificando migraciones pendientes...")
    
    try:
        # Migración 001: Agregar columnas de geolocalización
        _migration_001_add_geolocation(db)
        
        logger.info("✅ Todas las migraciones completadas")
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando migraciones: {str(e)}")
        # No lanzar excepción para no bloquear el inicio del servicio
        # Las migraciones se pueden ejecutar manualmente si es necesario


def _migration_001_add_geolocation(db: Session) -> None:
    """
    Migración 001: Agregar columnas latitud y longitud a tabla clientes
    """
    try:
        # Verificar si la columna latitud ya existe
        check_query = text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'clientes' 
              AND column_name = 'latitud'
        """)
        
        result = db.execute(check_query).scalar()
        
        if result > 0:
            logger.info("⏭️  Migración 001: Columnas de geolocalización ya existen, saltando")
            return
        
        logger.info("🔄 Ejecutando Migración 001: Agregar columnas de geolocalización...")
        
        # Agregar columna latitud
        db.execute(text("""
            ALTER TABLE clientes 
            ADD COLUMN latitud NUMERIC(10, 8) NULL
        """))
        
        db.execute(text("""
            COMMENT ON COLUMN clientes.latitud 
            IS 'Latitud de la sede para geolocalización y optimización de rutas'
        """))
        
        # Agregar columna longitud
        db.execute(text("""
            ALTER TABLE clientes 
            ADD COLUMN longitud NUMERIC(11, 8) NULL
        """))
        
        db.execute(text("""
            COMMENT ON COLUMN clientes.longitud 
            IS 'Longitud de la sede para geolocalización y optimización de rutas'
        """))
        
        # Crear índice para búsquedas por coordenadas
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_clientes_geolocation 
            ON clientes (latitud, longitud) 
            WHERE latitud IS NOT NULL AND longitud IS NOT NULL
        """))
        
        db.commit()
        
        logger.info("✅ Migración 001: Columnas de geolocalización agregadas exitosamente")
        
    except Exception as e:
        db.rollback()
        logger.warning(f"⚠️  Migración 001: {str(e)} (puede que ya se haya ejecutado)")


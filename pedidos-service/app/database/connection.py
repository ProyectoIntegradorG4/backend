from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la base de datos PostgreSQL
# Se arma a partir de variables individuales si DATABASE_URL no está definida
DB_USER = os.getenv("PEDIDOS_DB_USER", "pedidos_service")
DB_PASSWORD = os.getenv("PEDIDOS_DB_PASSWORD", "pedidos_password")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres-db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("PEDIDOS_DB_NAME", "pedidos_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "PEDIDOS_DATABASE_URL",
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
)

# Configuración del engine con psycopg3
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Cambiar a True para debug SQL
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency para obtener la sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Inicializar la base de datos creando las tablas y aplicando migraciones."""
    try:
        # Importar modelos para asegurar su registro en el metadata
        from app.models import pedido as _pedido_models  # noqa: F401
        from app.models import entrega as _entrega_models  # noqa: F401
        from app.models import ruta as _ruta_models  # noqa: F401

        # Crear tablas si no existen
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Base de datos de pedidos inicializada correctamente")

        # Aplicar migraciones críticas para garantizar esquema correcto
        try:
            with engine.connect() as conn:
                # 1. Agregar columna cliente_id si no existe
                conn.execute(text("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS cliente_id INTEGER"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pedidos_cliente_id ON pedidos (cliente_id)"))
                
                # 2. Normalizar valores del enum estado a MAYÚSCULAS (compatibilidad con modelo)
                # La BD puede tener 'entregado' (minúsculas) pero el modelo espera 'ENTREGADO' (mayúsculas)
                conn.execute(text("""
                    UPDATE pedidos 
                    SET estado = UPPER(estado::text)::estadopedido 
                    WHERE estado::text != UPPER(estado::text)
                """))
                
                # 3. Verificar que el tipo enum tenga los valores correctos
                # Si hay discrepancia, esto ayudará a identificarla en logs
                result = conn.execute(text("""
                    SELECT enumlabel 
                    FROM pg_enum 
                    WHERE enumtypid = 'estadopedido'::regtype
                    ORDER BY enumsortorder
                """))
                enum_values = [row[0] for row in result]
                logger.info(f"📋 Valores del enum estadopedido en BD: {enum_values}")
                
                conn.commit()
                logger.info("✅ Migraciones de esquema completadas")
        except Exception as mig_err:
            logger.error(f"❌ Error aplicando migraciones: {mig_err}")
            # No lanzar excepción para no bloquear el startup si las migraciones fallan
            # (puede ser que ya estén aplicadas o que el esquema sea correcto)

    except Exception as e:
        logger.error(f"❌ Error inicializando la base de datos: {e}")
        raise

def test_db_connection():
    """Verificar conexión a la base de datos"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Error de conexión a la base de datos: {e}")
        return False

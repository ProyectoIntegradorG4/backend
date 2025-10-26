from sqlalchemy import create_engine
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
    "PEDIDOS_DATABASE_URL",
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
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
    """Inicializar la base de datos creando las tablas."""
    try:
        from app.models.pedido import Base as PedidoBase

        # Crear tablas si no existen
        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos de pedidos inicializada correctamente")

    except Exception as e:
        logger.error(f"Error inicializando la base de datos: {e}")
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

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
import redis
from contextlib import asynccontextmanager
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la base de datos PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg://nit_service:nit_password@localhost:5432/nit_db"
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

# Configuración de Redis para caché
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_TTL = int(os.getenv("REDIS_TTL", "3600"))  # TTL por defecto: 1 hora

def get_redis_client():
    """Obtener cliente Redis con manejo de errores"""
    try:
        client = redis.from_url(REDIS_URL, decode_responses=True)
        # Verificar conexión
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Error conectando a Redis: {e}")
        return None

def get_db() -> Generator[Session, None, None]:
    """Dependency para obtener la sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Inicializar la base de datos creando las tablas"""
    try:
        from app.models.institucion import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos inicializada correctamente")
        
        # Verificar conexión a Redis
        redis_client = get_redis_client()
        if redis_client:
            logger.info("Conexión a Redis establecida correctamente")
        else:
            logger.warning("No se pudo conectar a Redis - el caché no estará disponible")
            
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

def test_redis_connection():
    """Verificar conexión a Redis"""
    redis_client = get_redis_client()
    return redis_client is not None
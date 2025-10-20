from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
import redis
from contextlib import asynccontextmanager
import json
from datetime import datetime
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la base de datos PostgreSQL
# Se arma a partir de variables individuales si DATABASE_URL no está definida
DB_USER = os.getenv("POSTGRES_USER", "nit_service")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "nit_password")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres-db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "nit_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
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

# Configuración de Redis para caché
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-cache:6379/0")
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
    """Inicializar la base de datos creando las tablas y cargando datos de prueba si está vacío."""
    try:
        from app.models.institucion import Base, InstitucionAsociada

        # Crear tablas si no existen
        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos inicializada correctamente")

        # Seed de datos si la tabla está vacía
        session = SessionLocal()
        try:
            existing_count = session.query(InstitucionAsociada).count()
            if existing_count == 0:
                # Ubicar archivo JSON en la raíz del servicio
                service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                json_path = os.path.join(service_root, "NITValidationData.json")

                if os.path.exists(json_path):
                    logger.info("Cargando datos iniciales de instituciones desde NITValidationData.json")
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    inserted = 0
                    for item in data:
                        try:
                            fecha_registro = datetime.strptime(item["fecha_registro"], "%m/%d/%Y")
                            inst = InstitucionAsociada(
                                nit=item["nit"],
                                nombre_institucion=item["nombre_institucion"],
                                pais=item["pais"],
                                fecha_registro=fecha_registro,
                                activo=bool(item.get("activo", True))
                            )
                            session.add(inst)
                            inserted += 1
                        except Exception as e:
                            logger.warning(f"No se pudo insertar institución {item.get('nit')}: {e}")

                    session.commit()
                    logger.info(f"Seed completado. Instituciones insertadas: {inserted}")
                else:
                    logger.warning(f"Archivo de seed no encontrado: {json_path}")
            else:
                logger.info(f"Seed omitido: la tabla ya contiene {existing_count} registros")
        finally:
            session.close()

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
            from sqlalchemy import text
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Error de conexión a la base de datos: {e}")
        return False

def test_redis_connection():
    """Verificar conexión a Redis"""
    redis_client = get_redis_client()
    return redis_client is not None
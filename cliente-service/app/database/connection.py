import os
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError

logger = logging.getLogger("uvicorn")

# Configuración de la base de datos desde variables de entorno
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://cliente_service:cliente_password@postgres-db:5432/cliente_db"
)

def ensure_database_exists():
    """
    Asegurar que la base de datos existe, crearla si no existe.
    """
    try:
        # Extraer nombre de la base de datos de la URL
        db_name = DATABASE_URL.split('/')[-1].split('?')[0]

        # Si ya estamos usando la base de datos postgres, no es necesario crear
        if db_name == 'postgres':
            return True

        # Conectar a la base de datos postgres para crear la base de datos objetivo
        postgres_url = DATABASE_URL.rsplit('/', 1)[0] + '/postgres'
        temp_engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")

        with temp_engine.connect() as conn:
            # Verificar si la base de datos existe
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"))
            exists = result.fetchone() is not None

            if not exists:
                logger.info(f"Creando base de datos: {db_name}")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                logger.info(f"✅ Base de datos {db_name} creada exitosamente")
            else:
                logger.info(f"✅ Base de datos {db_name} ya existe")

        temp_engine.dispose()
        return True
    except Exception as e:
        logger.error(f"❌ Error al asegurar que la base de datos existe: {e}")
        return False


# Configuración optimizada del engine para alto rendimiento
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Desactivar logging SQL en producción
    poolclass=QueuePool,
    pool_size=20,              # Pool base para conexiones concurrentes
    max_overflow=40,           # Conexiones adicionales en picos de carga
    pool_pre_ping=True,        # Verificar conexiones antes de usarlas
    pool_recycle=1800,         # Reciclar conexiones cada 30 minutos
    pool_timeout=30,           # Timeout para obtener conexión del pool
    connect_args={
        "connect_timeout": 10,
        "sslmode": os.getenv("DB_SSL_MODE", "prefer"),  # prefer for compatibility, require for production
        "options": "-c jit=off -c application_name=cliente_service"
    }
)

# Session maker optimizado
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False     # Evita queries adicionales después de commit
)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener la sesión de base de datos
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Crear las tablas en la base de datos.
    Importa los modelos para que queden registrados en Base.metadata.
    """
    from app.models.cliente import Base
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tablas creadas exitosamente")


def test_db_connection() -> bool:
    """
    Probar la conexión a la base de datos
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"❌ Error al conectar a la base de datos: {e}")
        return False


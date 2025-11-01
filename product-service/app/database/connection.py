import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError

logger = logging.getLogger("uvicorn")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:grupo4@postgres-db:5432/postgres"
)

def ensure_database_exists():
    """Ensure the target database exists, create if it doesn't."""
    try:
        # Extract database name from URL
        db_name = DATABASE_URL.split('/')[-1].split('?')[0]

        # If already using postgres database, no need to create
        if db_name == 'postgres':
            return True

        # Connect to postgres database to create the target database
        postgres_url = DATABASE_URL.rsplit('/', 1)[0] + '/postgres'
        temp_engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")

        with temp_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"))
            exists = result.fetchone() is not None

            if not exists:
                logger.info(f"Creating database: {db_name}")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                logger.info(f"✅ Database {db_name} created successfully")
            else:
                logger.info(f"✅ Database {db_name} already exists")

        temp_engine.dispose()
        return True
    except Exception as e:
        logger.error(f"❌ Error ensuring database exists: {e}")
        return False

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # necesario para SQLite + threads
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()
# Alias esperado por algunos archivos existentes
EntitiesBase = Base

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """
    Crea las tablas. Importa modelos para que queden registradas en Base.metadata.
    """
    # Importar modelos para registrar mapeos antes del create_all
    from app.models import product, category  # noqa: F401
    Base.metadata.create_all(bind=engine)

def test_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False

# app/database/connection.py
import os
import logging
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.engine.url import make_url, URL

logger = logging.getLogger("uvicorn")

# URL principal de la app (rol de aplicación)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://product_service:product_password@postgres-db:5432/product_db"
)

# Opcionales: credenciales admin para crear/verificar la BD
ADMIN_DATABASE_URL = os.getenv("ADMIN_DATABASE_URL")  # p.ej. postgresql+psycopg://postgres:postgres_pwd@postgres-db:5432/postgres
POSTGRES_ADMIN_USER = os.getenv("POSTGRES_ADMIN_USER", "postgres")
POSTGRES_ADMIN_PASSWORD = os.getenv("POSTGRES_ADMIN_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres-db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

def _safe_make_admin_url(target_db: str = "postgres") -> Optional[str]:
    if ADMIN_DATABASE_URL:
        try:
            url = make_url(ADMIN_DATABASE_URL)
            # Forzamos que la DB admin sea la indicada (normalmente 'postgres')
            url = url.set(database=target_db)
            return str(url)
        except Exception as e:
            logger.warning(f"ADMIN_DATABASE_URL inválida: {e}")

    if not POSTGRES_ADMIN_PASSWORD:
        # No hay forma segura de conectar como admin; devolvemos None
        return None

    # Construimos un URL admin con psycopg3
    url = URL.create(
        drivername="postgresql+psycopg",
        username=POSTGRES_ADMIN_USER,
        password=POSTGRES_ADMIN_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=target_db
    )
    return str(url)

def ensure_database_exists() -> bool:
    try:
        app_url = make_url(DATABASE_URL)
        db_name = app_url.database or "postgres"

        # Si ya estamos apuntando a 'postgres', no intentamos crear nada
        if db_name == "postgres":
            return True

        admin_url = _safe_make_admin_url(target_db="postgres")
        if not admin_url:
            logger.info("Sin credenciales admin; omitiendo creación de BD y continuando.")
            return True

        temp_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
        with temp_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db"),
                {"db": db_name}
            ).fetchone() is not None

            if not exists:
                logger.info(f"Creando base de datos: {db_name}")
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                logger.info(f"Base de datos {db_name} creada correctamente")
            else:
                logger.info(f"La base de datos {db_name} ya existe")

        temp_engine.dispose()
        return True

    except Exception as e:
        logger.error(f"Error asegurando existencia de la BD: {e}")
        # No bloqueamos el arranque si falla esta verificación
        return False

# --- Engine y session ---
url = make_url(DATABASE_URL)
connect_args = {}
if url.get_backend_name() == "sqlite":
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # evita conexiones rotas en el pool
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()
# Alias conservado
EntitiesBase = Base

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    # Importa modelos antes de create_all
    from app.models import product, category  # noqa: F401
    from app.models.warehouse import Bodega  # noqa: F401
    from app.models.inventory import InventarioLote  # noqa: F401
    Base.metadata.create_all(bind=engine)

def test_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Test de conexión a BD falló: {e}")
        return False

import os
import logging
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.engine.url import make_url, URL

logger = logging.getLogger("uvicorn")

# ---------------------------------------------------------------------------
# 1. DATABASES: principal (vendedor) y secundaria (user)
# ---------------------------------------------------------------------------

# --- Base de datos principal (Vendedor Service) ---
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://vendedor_service:vendedor_password@postgres-db:5432/vendedor_db"
)

# --- Base de datos secundaria: USER SERVICE ---
USER_DATABASE_URL = os.getenv(
    "USER_DATABASE_URL",
    "postgresql+psycopg://user_service:user_password@postgres-db:5432/user_db"
)

# --- Credenciales admin (solo para crear vendedor_db, NO user_db) ---
ADMIN_DATABASE_URL = os.getenv("ADMIN_DATABASE_URL")  # opcional
POSTGRES_ADMIN_USER = os.getenv("POSTGRES_ADMIN_USER", "postgres")
POSTGRES_ADMIN_PASSWORD = os.getenv("POSTGRES_ADMIN_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres-db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

# ---------------------------------------------------------------------------
# 2. Helper: construir conexión admin segura
# ---------------------------------------------------------------------------

def _safe_make_admin_url(target_db: str = "postgres") -> Optional[str]:
    if ADMIN_DATABASE_URL:
        try:
            url = make_url(ADMIN_DATABASE_URL)
            url = url.set(database=target_db)
            return str(url)
        except Exception as e:
            logger.warning(f"ADMIN_DATABASE_URL inválida: {e}")

    if not POSTGRES_ADMIN_PASSWORD:
        return None

    url = URL.create(
        drivername="postgresql+psycopg",
        username=POSTGRES_ADMIN_USER,
        password=POSTGRES_ADMIN_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=target_db
    )
    return str(url)

# ---------------------------------------------------------------------------
# 3. Crear BD vendedor si no existe (NO aplica para user_db)
# ---------------------------------------------------------------------------

def ensure_database_exists() -> bool:
    try:
        app_url = make_url(DATABASE_URL)
        db_name = app_url.database or "postgres"

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
        return False

# ---------------------------------------------------------------------------
# 4. Engines / Sessions
# ---------------------------------------------------------------------------

# --- Engine principal (vendedores) ---
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Engine secundario (users) ---
user_engine = create_engine(USER_DATABASE_URL, pool_pre_ping=True)
UserSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=user_engine)

# Base ORM del servicio
Base = declarative_base()
EntitiesBase = Base

# ---------------------------------------------------------------------------
# 5. Session providers
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """BD principal (vendedores)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_db() -> Generator[Session, None, None]:
    """BD externa (users) - NO create_all"""
    db = UserSessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# 6. Init models (solo vendedor)
# ---------------------------------------------------------------------------

def init_db() -> None:
    from app.models.vendedor import Vendedor  # noqa: F401
    Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# 7. Test de conexión
# ---------------------------------------------------------------------------

def test_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception as e:
        logger.warning(f"Test de conexión a BD falló: {e}")
        return False

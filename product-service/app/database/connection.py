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

# Ensure database exists before creating engine
ensure_database_exists()

engine = create_engine(
    DATABASE_URL,
    echo=False,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
    connect_args={"connect_timeout": 10},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
EntitiesBase = declarative_base()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False

async def init_db():
    from app.models import Producto, CategoriaProducto  # registra mapeos
    from app.database.seed import seed_categories       # opcional: seed en startup
    EntitiesBase.metadata.create_all(bind=engine)

# app/database/connection.py
from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

# Engine/Session
SQLALCHEMY_DATABASE_URL = "sqlite:///./products.db"
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

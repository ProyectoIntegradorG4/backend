import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no está definido.")
    return url

def get_engine(url: Optional[str] = None):
    url = url or get_database_url()
    return create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    )

def get_sessionmaker(engine=None):
    if engine is None:
        engine = get_engine()
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

# Instancias por defecto para runtime (producción/desarrollo)
engine = get_engine()
SessionLocal = get_sessionmaker(engine)


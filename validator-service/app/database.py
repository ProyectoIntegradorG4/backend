from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from sqlalchemy.orm import sessionmaker
import os

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:grupo4@postgres-db:5432/postgres")
    # Asegurar que use psycopg2 si la URL tiene psycopg (psycopg3)
    # porque estos servicios tienen psycopg2-binary instalado
    if url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql+psycopg2://")
    return url

DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


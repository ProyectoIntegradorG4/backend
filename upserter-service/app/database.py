from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no está definido.")
    # Asegurar que use psycopg2 si la URL tiene psycopg (psycopg3)
    # porque estos servicios tienen psycopg2-binary instalado
    if url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql+psycopg2://")
    return url

DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

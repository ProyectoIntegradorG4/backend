# app/database/session.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Acepta cualquiera de las dos vars de entorno (primero VISIT_DATABASE_URL)
DATABASE_URL = os.getenv("VISIT_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("VISIT_DATABASE_URL/DATABASE_URL no está definida en el entorno.")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


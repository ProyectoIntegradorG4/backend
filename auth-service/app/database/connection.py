from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import os

# Configuración de la base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg://user_service:user_password@postgres-db:5432/user_db"
)

# Configuración optimizada del engine para alto rendimiento
engine = create_engine(
    DATABASE_URL,
    echo=False,
    poolclass=QueuePool,
    pool_size=20,              # Incrementado para mayor concurrencia
    max_overflow=40,           # Más conexiones en picos de carga
    pool_pre_ping=True,
    pool_recycle=1800,         # Reciclar conexiones más frecuentemente
    pool_timeout=30,           # Timeout para obtener conexión del pool
    connect_args={
        "connect_timeout": 10,
        "options": "-c jit=off -c application_name=auth_service_optimized"
    }
)

# Session maker optimizado
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False     # Evita queries adicionales después de commit
)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency para obtener la sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Inicializar la base de datos"""
    from app.models.user import Base
    Base.metadata.create_all(bind=engine)

# app/models/territorio.py
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base


class Territorio(Base):
    __tablename__ = "territorios"

    territorio_id = Column(String(50), primary_key=True)
    nombre = Column(String(255), nullable=False)
    codigo = Column(String(20), unique=True, nullable=False)
    pais = Column(String(100), nullable=False, default='Colombia')
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

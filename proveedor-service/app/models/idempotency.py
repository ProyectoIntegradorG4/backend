"""
Modelo para manejo de idempotencia
"""
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone, timedelta

Base = declarative_base()

class IdempotencyKey(Base):
    """Modelo para almacenar claves de idempotencia y sus respuestas"""
    __tablename__ = "idempotency_keys"

    key = Column(String(64), primary_key=True)
    response = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    @staticmethod
    def calculate_expiry(minutes: int = 30) -> datetime:
        """Calcular fecha de expiración (por defecto 30 minutos)"""
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)
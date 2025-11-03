from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timezone
from app.database.connection import Base

class User(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    correo_electronico = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nit = Column(String(20), nullable=False)
    rol = Column(String(50), default='gerente_cuenta')
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    activo = Column(Boolean, default=True)

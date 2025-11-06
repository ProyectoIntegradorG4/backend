from sqlalchemy import Column, String, DateTime, Boolean, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime
from app.database.connection import Base  # usa tu Base compartida

class InstitucionAsociada(Base):
    __tablename__ = "instituciones_asociadas"

    nit = Column(String(20), primary_key=True)
    nombre_institucion = Column(String(255), nullable=False)
    pais = Column(String(100), nullable=False)
    fecha_registro = Column(DateTime, nullable=False, default=datetime.now)
    activo = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index('idx_pais_activo', 'pais', 'activo'),
        Index('idx_activo', 'activo'),
    )

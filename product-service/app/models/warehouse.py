from sqlalchemy import Column, String
from app.database.connection import Base

class Bodega(Base):
    __tablename__ = "bodega"

    bodegaId = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    pais = Column(String, nullable=False) 
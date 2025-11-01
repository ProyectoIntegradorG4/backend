from sqlalchemy import Column, String, Boolean
from app.database.connection import Base

class CategoriaProducto(Base):
    __tablename__ = "categoria_producto"

    categoriaId = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    requiereCadenaFrio = Column(Boolean, default=False)
    requiereRegistroSanitario = Column(Boolean, default=False)

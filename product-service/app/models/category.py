from sqlalchemy import Column, String, Boolean
from app.database.connection import EntitiesBase

class CategoriaProducto(EntitiesBase):
    __tablename__ = "categoria_producto"

    categoriaId = Column(String(50), primary_key=True, nullable=False)
    nombre = Column(String(120), nullable=False)
    requiereCadenaFrio = Column(Boolean, nullable=False, default=False)
    # Si la categoría requiere registro sanitario por regulación
    requiereRegistroSanitario = Column(Boolean, nullable=False, default=False)

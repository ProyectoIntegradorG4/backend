import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database.connection import EntitiesBase

class Producto(EntitiesBase):
    __tablename__ = "producto"

    productoId = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Básicos
    nombre = Column(String(200), nullable=False)
    descripcion = Column(String(2000), nullable=False)
    categoriaId = Column(String(50), nullable=False)
    subcategoria = Column(String(100))
    formaFarmaceutica = Column(String(100), nullable=False)
    registroSanitario = Column(String(120))
    requierePrescripcion = Column(Boolean, nullable=False)

    # Técnicos
    laboratorio = Column(String(120))         # fabricante referencial
    principioActivo = Column(String(200))
    concentracion = Column(String(100))
    codigoBarras = Column(String(18))         # opcional si viene

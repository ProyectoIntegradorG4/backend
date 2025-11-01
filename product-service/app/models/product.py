# app/models/product.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from pydantic import BaseModel

from app.database.connection import Base  # tu Base de SQLAlchemy (declarative_base)


# ---------------------------
# ORM: Tabla producto
# ---------------------------
class Producto(Base):
    __tablename__ = "producto"

    productoId = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)

    # FK a categoria_producto (definida en app/models/category.py)
    categoriaId = Column(String, ForeignKey("categoria_producto.categoriaId"), nullable=False)

    formaFarmaceutica = Column(String, nullable=True)
    requierePrescripcion = Column(Boolean, default=False)
    registroSanitario = Column(String, nullable=True)

    # Stock and location fields
    sku = Column(String, nullable=True, index=True)
    location = Column(String, nullable=True)
    ubicacion = Column(String, nullable=True)
    stock = Column(String, nullable=True)

    # estado como texto para tests ("activo"/"inactivo")
    estado_producto = Column(String, default="activo")

    # timestamp para ordenamiento
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relación hacia CategoriaProducto (la clase está en category.py)
    categoria = relationship("CategoriaProducto", backref="productos")


# ---------------------------
# Pydantic Schemas usados por los tests y el service
# ---------------------------
class ProductoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, min_length=1, max_length=500)
    categoriaId: Optional[str] = Field(None, min_length=1, max_length=50)
    formaFarmaceutica: Optional[str] = Field(None, min_length=1, max_length=100)
    requierePrescripcion: bool = False
    registroSanitario: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    ubicacion: Optional[str] = Field(None, max_length=200)
    stock: Optional[str] = Field(None, max_length=50)


class ProductoOut(BaseModel):
    productoId: str
    nombre: str
    categoria: str
    formaFarmaceutica: Optional[str] = None
    requierePrescripcion: bool
    registroSanitario: Optional[str] = None
    estado_producto: str
    actualizado_en: Optional[datetime] = None
    sku: Optional[str] = None
    location: Optional[str] = None
    ubicacion: Optional[str] = None
    stock: Optional[str] = None


class ProductosResponse(BaseModel):
    total: int
    items: List[ProductoOut]
    page: int
    page_size: int

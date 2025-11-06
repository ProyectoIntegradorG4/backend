# app/models/product.py
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from pydantic import BaseModel as PydBaseModel

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Date, Integer, Float
from sqlalchemy.orm import relationship

from pydantic import BaseModel

from sqlalchemy.orm import relationship

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
    stock = Column(Integer, nullable=True)
    precio = Column(Float, nullable=True, default=0.0, comment="Precio unitario del producto")

    # estado como texto para tests ("activo"/"inactivo")
    estado_producto = Column(String, default="activo")

    # timestamp para ordenamiento
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relación hacia CategoriaProducto (la clase está en category.py)
    categoria = relationship("CategoriaProducto", backref="productos")

    #fecha vencimiento
    fechaVencimiento = Column(Date, nullable=True)



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
    stock: Optional[int] = None
    precio: Optional[float] = Field(None, ge=0.0, description="Precio unitario del producto")
    fechaVencimiento: Optional[date] = None


    @field_validator("fechaVencimiento", mode="before")
    @classmethod
    def _parse_fecha(cls, v):
        # Permite None, date, o string ISO
        if v is None or isinstance(v, date):
            return v
        if isinstance(v, str) and v.strip():
            # Acepta 'YYYY-MM-DD'
            return date.fromisoformat(v.strip())
        return None


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
    stock: Optional[int] = None
    precio: Optional[float] = None
    fechaVencimiento: Optional[date] = None

    model_config = {
      "from_attributes": True  
      }



class ProductosResponse(BaseModel):
    total: int
    items: List[ProductoOut]
    page: int
    page_size: int


# Relación con lotes
Producto.lotes = relationship(
    "InventarioLote",
    back_populates="producto",
    cascade="all, delete-orphan",
    lazy="selectin"  # carga eficiente para listados
)

# ---- Nuevos DTOs de salida compatibles ----
class LoteOut(PydBaseModel):
    loteId: str
    bodegaId: str
    bodega: str
    pais: str
    stock: int
    fechaVencimiento: Optional[date] = None

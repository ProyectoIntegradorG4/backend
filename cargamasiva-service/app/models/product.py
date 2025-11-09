# app/models/product.py
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Date, Integer, Float
from sqlalchemy.orm import relationship

from app.database.session import Base

class Producto(Base):
    __tablename__ = "producto"

    productoId = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)

    categoriaId = Column(String, ForeignKey("categoria_producto.categoriaId"), nullable=False)

    formaFarmaceutica = Column(String, nullable=True)
    requierePrescripcion = Column(Boolean, default=False)
    registroSanitario = Column(String, nullable=True)

    sku = Column(String, nullable=True, index=True)
    location = Column(String, nullable=True)
    ubicacion = Column(String, nullable=True)
    stock = Column(Integer, nullable=True)
    precio = Column(Float, nullable=True, default=0.0)

    estado_producto = Column(String, default="activo")
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fechaVencimiento = Column(Date, nullable=True)

    # relación: referencia por nombre de clase, que está en category.py
    categoria = relationship("CategoriaProducto", backref="productos")

# --------- Pydantic usado por la carga masiva ----------
class ProductoCSVIn(BaseModel):
    productoId: str = Field(..., min_length=1, max_length=64)
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    categoriaId: str = Field(..., min_length=1, max_length=50)
    formaFarmaceutica: Optional[str] = Field(None, max_length=100)
    requierePrescripcion: bool = False
    registroSanitario: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    ubicacion: Optional[str] = Field(None, max_length=200)
    stock: Optional[int] = None
    precio: Optional[float] = Field(None, ge=0.0)
    estado_producto: str = Field(..., min_length=1, max_length=50)
    actualizado_en: Optional[datetime] = None
    fechaVencimiento: Optional[date] = None

    @field_validator("fechaVencimiento", mode="before")
    @classmethod
    def _parse_fecha(cls, v):
        if v is None or isinstance(v, date): return v
        if isinstance(v, str) and v.strip(): return date.fromisoformat(v.strip())
        return None

    @field_validator("actualizado_en", mode="before")
    @classmethod
    def _parse_dt(cls, v):
        if v is None or isinstance(v, datetime): return v
        if isinstance(v, str) and v.strip(): return datetime.fromisoformat(v.strip().replace("Z", "+00:00"))
        return None

    @field_validator("estado_producto")
    @classmethod
    def validar_estado(cls, v: str):
        allowed = {"ACTIVO", "INACTIVO", "SUSPENDIDO"}
        norm = v.upper()
        if norm not in allowed:
            raise ValueError(f"estado_producto inválido ({'|'.join(allowed)})")
        return norm

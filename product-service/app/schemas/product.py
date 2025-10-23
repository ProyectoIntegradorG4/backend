from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Request de creación (HU)
class ProductoCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    descripcion: str = Field(..., min_length=2, max_length=2000)
    categoriaId: str = Field(..., max_length=50)
    subcategoria: Optional[str] = Field(None, max_length=100)
    laboratorio: Optional[str] = Field(None, max_length=120)
    principioActivo: Optional[str] = Field(None, max_length=200)
    concentracion: Optional[str] = Field(None, max_length=100)
    formaFarmaceutica: str = Field(..., max_length=100)
    registroSanitario: Optional[str] = Field(None, max_length=120)
    requierePrescripcion: bool
    codigoBarras: Optional[str] = Field(None, max_length=18)

# Response 201 (HU)
class ProductoCreatedResponse(BaseModel):
    productoId: UUID
    sku_visible: str
    nombre: str
    categoriaId: str
    requiereCadenaFrio: bool
    registroSanitario: Optional[str]
    requierePrescripcion: bool

# Listar productos
class ProductoOut(BaseModel):
    productoId: UUID
    nombre: str
    categoria: str
    formaFarmaceutica: str
    requierePrescripcion: bool
    registroSanitario: Optional[str]
    estado_producto: str
    actualizado_en: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)


class ProductosResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[ProductoOut]   


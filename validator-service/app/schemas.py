from pydantic import BaseModel
from typing import Optional
from datetime import date

class ProductoTemporalCreate(BaseModel):
    sku: str
    nombre: str
    fecha_vencimiento: Optional[date]
    lote: Optional[str]
    error: Optional[str]

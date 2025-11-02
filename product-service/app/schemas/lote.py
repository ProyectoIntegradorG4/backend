# app/schemas/lote.py
from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class LoteItem(BaseModel):
    loteId: str
    productoId: str
    productoNombre: str
    categoriaId: Optional[str] = None
    bodegaId: str
    bodegaNombre: str
    fechaVencimiento: Optional[date] = None
    stock: int
    diasRestantes: Optional[int] = None   # días a hoy; negativo si vencido
    estado: str                           # "VENCIDO" | "PROXIMO" | "OK" | "SIN_FECHA"

class LoteListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[LoteItem]

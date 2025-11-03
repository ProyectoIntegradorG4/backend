from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class VendedorCreate(BaseModel):
    nombres: str = Field(..., min_length=1, max_length=120)
    apellidos: str = Field(..., min_length=1, max_length=120)
    tipoDocumento: str = Field(..., min_length=1, max_length=6)  # CC/CE/PAS...
    numeroDocumento: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    telefono: Optional[str] = Field(None, max_length=30)
    pais: str = Field(..., min_length=2, max_length=100)
    territorioId: str = Field(..., min_length=1, max_length=100)

    # opcional: si UI ya lo sabe, lo puede mandar y nos ahorramos ambigüedad
    nitInstitucion: Optional[str] = Field(None, min_length=8, max_length=20)

class VendedorCreatedResponse(BaseModel):
    vendedorId: str
    usuarioId: int
    estado: str
    rol: str
    territorioId: str
    password_generada: bool

class VendedorListItem(BaseModel):
    vendedorId: str
    nombres: str
    apellidos: str
    tipoDocumento: str
    numeroDocumento: str
    email: EmailStr
    pais: str
    territorio: Optional[str] = None
    territorioId: str
    estado: str
    actualizado_en: Optional[datetime] = None

class VendedoresResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[VendedorListItem]

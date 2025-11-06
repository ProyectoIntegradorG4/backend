from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    correo_electronico: EmailStr
    password_plano: str = Field(..., min_length=8, max_length=64)
    rol: str = Field(default="gerente_cuenta")
    nit: str = Field(..., min_length=8, max_length=20)
    activo: bool = True


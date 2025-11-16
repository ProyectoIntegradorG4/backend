# app/schemas/plan_venta.py
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from decimal import Decimal


# ==================== Schemas de entrada ====================

class MetaCreate(BaseModel):
    productoId: str = Field(..., min_length=1, max_length=255)
    territorioId: str = Field(..., min_length=1, max_length=50)
    vendedorId: int = Field(..., gt=0)
    objetivo_cantidad: int = Field(default=0, ge=0)
    objetivo_valor: Optional[Decimal] = Field(default=None, ge=0)
    nota: Optional[str] = Field(None, max_length=500)

    @field_validator('objetivo_cantidad', 'objetivo_valor')
    @classmethod
    def validate_at_least_one_objective(cls, v, info):
        # Validación completa se hace en el servicio para tener acceso a ambos campos
        return v


class PlanVentaCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    periodo: dict = Field(..., description="Objeto con 'desde' y 'hasta' en formato YYYY-MM-DD")
    territorios: List[str] = Field(..., min_items=1, description="Lista de IDs de territorios")
    metas: List[MetaCreate] = Field(..., min_items=1, description="Lista de metas del plan")

    @field_validator('periodo')
    @classmethod
    def validate_periodo(cls, v):
        if not isinstance(v, dict):
            raise ValueError("periodo debe ser un objeto con 'desde' y 'hasta'")
        if 'desde' not in v or 'hasta' not in v:
            raise ValueError("periodo debe contener 'desde' y 'hasta'")
        
        try:
            desde = date.fromisoformat(v['desde']) if isinstance(v['desde'], str) else v['desde']
            hasta = date.fromisoformat(v['hasta']) if isinstance(v['hasta'], str) else v['hasta']
            
            if hasta < desde:
                raise ValueError("La fecha 'hasta' debe ser mayor o igual a 'desde'")
            
            v['desde'] = desde
            v['hasta'] = hasta
        except (ValueError, TypeError) as e:
            raise ValueError(f"Formato de fecha inválido: {str(e)}")
        
        return v


# ==================== Schemas de salida ====================

class MetaOut(BaseModel):
    meta_id: UUID
    producto_id: str
    territorio_id: str
    vendedor_id: int
    objetivo_cantidad: int
    objetivo_valor: Optional[Decimal]
    nota: Optional[str]

    model_config = {"from_attributes": True}


class TerritorioOut(BaseModel):
    territorio_id: str
    nombre: str
    codigo: str
    pais: str
    activo: bool

    model_config = {"from_attributes": True}


class PlanVentaOut(BaseModel):
    plan_id: UUID
    nombre: str
    periodo_desde: date
    periodo_hasta: date
    estado: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metas_count: int = 0
    territorios_count: int = 0

    model_config = {"from_attributes": True}


class PlanVentaListItem(BaseModel):
    """Schema para item en listado de planes (HU-WEB-009)"""
    planId: str
    nombre: str
    periodo: dict  # {"desde": "YYYY-MM-DD", "hasta": "YYYY-MM-DD"}
    estado: str
    territorios_count: int
    metas_count: int
    actualizado_en: Optional[str] = None

    model_config = {"from_attributes": True}


class PlanVentaDetailOut(BaseModel):
    plan_id: UUID
    nombre: str
    periodo_desde: date
    periodo_hasta: date
    estado: str
    created_at: Optional[str] = None
    territorios: List[TerritorioOut]
    metas: List[MetaOut]

    model_config = {"from_attributes": True}


class PlanVentaCreateResponse(BaseModel):
    planId: str
    estado: str
    metas_creadas: int
    mensaje: str = "Plan de venta creado exitosamente"

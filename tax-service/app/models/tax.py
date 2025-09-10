from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

Base = declarative_base()

class Tax(Base):
    __tablename__ = "taxes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    rate = Column(Numeric(5, 4))  # Ejemplo: 0.1900 para 19%
    tax_type = Column(String)  # IVA, Renta, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TaxCalculation(Base):
    __tablename__ = "tax_calculations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # Referencia al usuario
    tax_id = Column(Integer, ForeignKey("taxes.id"))
    base_amount = Column(Numeric(12, 2))
    tax_amount = Column(Numeric(12, 2))
    total_amount = Column(Numeric(12, 2))
    calculation_date = Column(DateTime, default=datetime.utcnow)

    tax = relationship("Tax")

# Pydantic models para validación
class TaxBase(BaseModel):
    name: str
    description: str
    rate: Decimal
    tax_type: str

class TaxCreate(TaxBase):
    pass

class TaxUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rate: Optional[Decimal] = None
    tax_type: Optional[str] = None
    is_active: Optional[bool] = None

class TaxResponse(TaxBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaxCalculationRequest(BaseModel):
    user_id: int
    tax_id: int
    base_amount: Decimal

class TaxCalculationResponse(BaseModel):
    id: int
    user_id: int
    tax_id: int
    base_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    calculation_date: datetime
    tax: TaxResponse

    class Config:
        from_attributes = True
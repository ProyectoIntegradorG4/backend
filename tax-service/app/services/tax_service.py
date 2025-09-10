from sqlalchemy.orm import Session
from app.models.tax import Tax, TaxCalculation, TaxCreate, TaxUpdate, TaxCalculationRequest
from typing import List, Optional
from decimal import Decimal

class TaxService:
    def __init__(self, db: Session):
        self.db = db

    async def create_tax(self, tax: TaxCreate) -> Tax:
        db_tax = Tax(
            name=tax.name,
            description=tax.description,
            rate=tax.rate,
            tax_type=tax.tax_type
        )
        
        self.db.add(db_tax)
        self.db.commit()
        self.db.refresh(db_tax)
        return db_tax

    async def get_tax(self, tax_id: int) -> Optional[Tax]:
        return self.db.query(Tax).filter(Tax.id == tax_id, Tax.is_active == True).first()

    async def get_taxes(self, skip: int = 0, limit: int = 100) -> List[Tax]:
        return self.db.query(Tax).filter(Tax.is_active == True).offset(skip).limit(limit).all()

    async def update_tax(self, tax_id: int, tax_update: TaxUpdate) -> Optional[Tax]:
        db_tax = self.db.query(Tax).filter(Tax.id == tax_id).first()
        if not db_tax:
            return None

        update_data = tax_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tax, field, value)

        self.db.commit()
        self.db.refresh(db_tax)
        return db_tax

    async def delete_tax(self, tax_id: int) -> bool:
        db_tax = self.db.query(Tax).filter(Tax.id == tax_id).first()
        if not db_tax:
            return False

        # Soft delete
        db_tax.is_active = False
        self.db.commit()
        return True

    async def calculate_tax(self, calculation_request: TaxCalculationRequest) -> Optional[TaxCalculation]:
        # Obtener el impuesto
        tax = await self.get_tax(calculation_request.tax_id)
        if not tax:
            return None

        # Calcular el impuesto
        tax_amount = calculation_request.base_amount * tax.rate
        total_amount = calculation_request.base_amount + tax_amount

        # Guardar el cálculo
        db_calculation = TaxCalculation(
            user_id=calculation_request.user_id,
            tax_id=calculation_request.tax_id,
            base_amount=calculation_request.base_amount,
            tax_amount=tax_amount,
            total_amount=total_amount
        )

        self.db.add(db_calculation)
        self.db.commit()
        self.db.refresh(db_calculation)
        return db_calculation

    async def get_user_calculations(self, user_id: int) -> List[TaxCalculation]:
        return self.db.query(TaxCalculation).filter(
            TaxCalculation.user_id == user_id
        ).order_by(TaxCalculation.calculation_date.desc()).all()
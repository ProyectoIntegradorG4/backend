from pydantic import BaseModel
from typing import Optional
from datetime import date

class ProductIn(BaseModel):
    sku: str
    name: str
    description: Optional[str]
    category: Optional[str]
    manufacturer: Optional[str]
    storage_type: Optional[str]
    min_shelf_life_months: Optional[int]
    expiration_date: Optional[date]
    batch_number: Optional[str]
    cold_chain_required: Optional[bool] = False
    certifications: Optional[str]
    commercialization_auth: Optional[str]
    country_regulations: Optional[str]
    unit_price: Optional[float]
    purchase_conditions: Optional[str]
    delivery_time_hours: Optional[int]
    external_code: Optional[str]
    created_by: str


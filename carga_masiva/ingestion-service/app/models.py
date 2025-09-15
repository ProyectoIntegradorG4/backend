from sqlalchemy import Column, Integer, Numeric, String, Text, Boolean, DECIMAL, Date, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import datetime
import uuid

Base = declarative_base()

class ProductStaging(Base):
    __tablename__ = "products_stg"

    product_id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    manufacturer = Column(String(255))
    storage_type = Column(String(50))
    min_shelf_life_months = Column(Integer)
    expiration_date = Column(Date)
    batch_number = Column(String(50))
    cold_chain_required = Column(Boolean, default=False)
    certifications = Column(Text)
    commercialization_auth = Column(String(100))
    country_regulations = Column(Text)
    unit_price = Column(DECIMAL(12,2), nullable=True)
    purchase_conditions = Column(Text)
    delivery_time_hours = Column(Integer)
    external_code = Column(String(100))
    import_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)    
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    created_by = Column(String(50))
    validation_status = Column(String(10), default="PENDING")
    validation_errors = Column(Text, nullable=True)
    validated_at = Column(TIMESTAMP, nullable=True)
    processed = Column(Boolean, default=False) 

from sqlalchemy import Column, Integer, Numeric, String, Text, Boolean, Date, DECIMAL, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID

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
    import_id = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(50))
    validation_status = Column(String(10), default="PENDING")  # PENDING / VALID / ERROR
    validation_errors = Column(Text, default=None)
    validated_at = Column(DateTime, default=None)
    processed = Column(Boolean, default=False) 


class Products(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    manufacturer = Column(String(255))
    storage_type = Column(String(50))
    expiration_date = Column(Date)
    batch_number = Column(String(50))
    unit_price = Column(DECIMAL(12,2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

from sqlalchemy import Column, Integer, String, Text, DECIMAL, Date, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Product(Base):
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
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

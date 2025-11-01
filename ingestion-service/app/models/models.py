import uuid
import datetime
from sqlalchemy import Column, Integer, Numeric, String, Text, Boolean, DECIMAL, Date, TIMESTAMP
# 👇 cambia este import obsoleto:
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator, CHAR

Base = declarative_base()

# 👇 Tipo portable para UUID (Postgres/SQLite)
class GUID(TypeDecorator):
    """
    Almacena UUID como CHAR(36) en motores sin soporte nativo (SQLite)
    y usa UUID nativo en Postgres.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(value)

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
    unit_price = Column(DECIMAL(12, 2), nullable=True)
    purchase_conditions = Column(Text)
    delivery_time_hours = Column(Integer)
    external_code = Column(String(100))
    # 👇 aquí el cambio clave
    import_id = Column(GUID(), default=uuid.uuid4, nullable=False)

    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    created_by = Column(String(50))
    validation_status = Column(String(10), default="PENDING")
    validation_errors = Column(Text, nullable=True)
    validated_at = Column(TIMESTAMP, nullable=True)
    processed = Column(Boolean, default=False)

from sqlalchemy import Column, String
from app.database.connection import Base

class Territorio(Base):
    __tablename__ = "territorio"
    territorioId = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)

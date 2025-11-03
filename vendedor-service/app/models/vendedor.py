# app/models/vendedor.py
from sqlalchemy import Column, String, DateTime, func, UniqueConstraint
from app.database.connection import Base

class Vendedor(Base):
    __tablename__ = "vendedor"

    vendedorId       = Column(String(20), primary_key=True, index=True)
    nombres          = Column(String(120), nullable=False)
    apellidos        = Column(String(120), nullable=False)
    tipoDocumento    = Column(String(6),   nullable=False)
    numeroDocumento  = Column(String(30),  nullable=False, index=True)
    email            = Column(String(255), nullable=False, index=True)
    telefono         = Column(String(30),  nullable=True)
    pais             = Column(String(100), nullable=False)
    territorioId     = Column(String(100), nullable=False)
    estado           = Column(String(20),  nullable=False, default="ACTIVO")

    creado_en        = Column(DateTime, server_default=func.now(), nullable=False)
    actualizado_en   = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("numeroDocumento", name="uq_vendedor_numdoc"),
        UniqueConstraint("email",           name="uq_vendedor_email"),
    )

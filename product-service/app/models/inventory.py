from sqlalchemy import Column, String, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

class InventarioLote(Base):
    __tablename__ = "inventario_lote"

    loteId = Column(String, primary_key=True, index=True)  # UUID en string
    productoId = Column(String, ForeignKey("producto.productoId"), nullable=False)
    bodegaId = Column(String, ForeignKey("bodega.bodegaId"), nullable=False)

    # redundamos país en el lote por trazabilidad/regulatorio por país
    pais = Column(String, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    fechaVencimiento = Column(Date, nullable=True)

    # Relaciones
    producto = relationship("Producto", back_populates="lotes")
    bodega = relationship("Bodega", backref="lotes")

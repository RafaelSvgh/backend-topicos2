"""
Modelo para promociones.
"""
from sqlalchemy import Column, Integer, String, DECIMAL
from .base import Base

class Promocion(Base):
    __tablename__ = 'promocion'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50))
    descuento = Column(DECIMAL(10, 2)) 
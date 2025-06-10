"""
Modelo para intereses de usuarios.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, func
from .base import Base

class Interes(Base):
    __tablename__ = 'interes'

    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, nullable=False, default=func.now())
    producto_codigo = Column(String(20), ForeignKey('producto.codigo'), nullable=True)
    subcategoria_id = Column(Integer, ForeignKey('subcategoria.id'), nullable=True)
    categoria_id = Column(Integer, ForeignKey('categoria.id'), nullable=True)
    promocion_id = Column(Integer, ForeignKey('promocion.id'), nullable=True)
    chat_id = Column(Integer, ForeignKey('chat.id'), nullable=True)
    correo_html = Column(Text, nullable=True)
    enviado = Column(Boolean, default=False) 
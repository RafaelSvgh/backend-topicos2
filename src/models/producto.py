"""
Modelos relacionados con productos, categorías y subcategorías.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Categoria(Base):
    __tablename__ = 'categoria'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(40), nullable=False)

    subcategorias = relationship("Subcategoria", back_populates="categoria")


class Subcategoria(Base):
    __tablename__ = 'subcategoria'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(40), nullable=False)
    categoria_id = Column(Integer, ForeignKey('categoria.id'))

    categoria = relationship("Categoria", back_populates="subcategorias")
    productos = relationship("Producto", back_populates="subcategoria")


class Producto(Base):
    __tablename__ = 'producto'
    
    codigo = Column(String(20), primary_key=True)
    nombre = Column(String(50))
    marca = Column(String(50))
    talla = Column(String(5))
    color = Column(String(20))
    subcategoria_id = Column(Integer, ForeignKey('subcategoria.id'))

    subcategoria = relationship("Subcategoria", back_populates="productos") 
"""
Módulo de modelos de la aplicación.
Exporta todos los modelos para facilitar su importación.
"""
from .base import Base, engine, Session, session
from .producto import Categoria, Subcategoria, Producto
from .promocion import Promocion
from .chat import Usuario, Chat, Mensaje
from .interes import Interes

__all__ = [
    'Base',
    'engine',
    'Session',
    'session',
    'Categoria',
    'Subcategoria',
    'Producto',
    'Promocion',
    'Usuario',
    'Chat',
    'Mensaje',
    'Interes'
] 
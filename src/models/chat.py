"""
Modelos relacionados con usuarios, chats y mensajes.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Usuario(Base):
    __tablename__ = 'usuario'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(70))
    correo = Column(String(70))
    telefono = Column(String(15))
    
    chats = relationship("Chat", back_populates="usuario")


class Chat(Base):
    __tablename__ = 'chat'
    
    id = Column(Integer, primary_key=True)
    fecha_ini = Column(DateTime)
    fecha_fin = Column(DateTime, nullable=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id'))
    
    usuario = relationship("Usuario", back_populates="chats")
    mensajes = relationship("Mensaje", back_populates="chat")


class Mensaje(Base):
    __tablename__ = 'mensaje'
    
    id = Column(Integer, primary_key=True)
    texto = Column(String(2000))  # Aumentado a 2000 caracteres
    fecha = Column(DateTime)
    enviado = Column(String(1))
    chat_id = Column(Integer, ForeignKey('chat.id'))
    
    chat = relationship("Chat", back_populates="mensajes") 
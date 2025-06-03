from langchain.schema import Document
from sqlalchemy import create_engine, text,Boolean, Text, func, Column, Integer, String, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import json

connection_string = "mssql+pyodbc://sa:rafa0134@localhost\\MSSQLSERVER2,1433/negocio?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes"
engine = create_engine(connection_string)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Definición de modelos
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


class Promocion(Base):
    __tablename__ = 'promocion'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50))
    descuento = Column(DECIMAL(10, 2))


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
    

# Modelo de Interes
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

# Función para obtener o crear un chat
def obtener_o_crear_chat(usuario_id):
    chat = session.query(Chat).filter_by(usuario_id=usuario_id, fecha_fin=None).first()
    if not chat:
        chat = Chat(fecha_ini=datetime.now(), usuario_id=usuario_id)
        session.add(chat)
        session.commit()
    return chat

# Función para agregar un mensaje
def agregar_mensaje(usuario_id, texto, enviado="S"):
    chat = obtener_o_crear_chat(usuario_id)
    mensaje = Mensaje(texto=texto, fecha=datetime.now(), enviado=enviado, chat_id=chat.id)
    session.add(mensaje)
    session.commit()
    print(f"Mensaje agregado al chat {chat.id}")

# Función para agregar un mensaje
def recibir_mensaje(usuario_id, texto, enviado="N"):
    chat = obtener_o_crear_chat(usuario_id)
    mensaje = Mensaje(texto=texto, fecha=datetime.now(), enviado=enviado, chat_id=chat.id)
    session.add(mensaje)
    session.commit()
    print(f"Mensaje agregado al chat {chat.id}")

# Consulta con joins completos
query = """
SELECT 
    p.codigo,
    p.nombre AS producto_nombre,
    p.marca,
    p.talla,
    p.color,
    sc.nombre AS subcategoria_nombre,
    c.nombre AS categoria_nombre,
    lp.precio,
    lp.descripcion AS tipo_precio
FROM producto p
JOIN subcategoria sc ON p.subcategoria_id = sc.id
JOIN categoria c ON sc.categoria_id = c.id
LEFT JOIN producto_precio pp ON p.codigo = pp.producto_codigo
LEFT JOIN lista_precio lp ON pp.lista_precio_id = lp.id
"""
query_categorias = """
SELECT
    c.id AS categoria_id,
    c.nombre AS categoria_nombre,
    COUNT(p.codigo) AS total_productos,
    STRING_AGG(p.nombre, ', ') AS productos
FROM categoria c
JOIN subcategoria sc ON sc.categoria_id = c.id
JOIN producto p ON p.subcategoria_id = sc.id
GROUP BY c.id, c.nombre
"""
query_subcategorias = """
SELECT 
    sc.id AS subcategoria_id,
    sc.nombre AS subcategoria_nombre,
    c.nombre AS categoria_nombre,
    COUNT(p.codigo) AS total_productos,
    STRING_AGG(p.nombre, ', ') AS productos
FROM subcategoria sc
JOIN categoria c ON sc.categoria_id = c.id
JOIN producto p ON p.subcategoria_id = sc.id
GROUP BY sc.id, sc.nombre, c.nombre
"""

query_tallas_por_subcategoria = """
SELECT 
    subcategoria_nombre,
    STRING_AGG(talla, ', ') AS tallas_disponibles
FROM (
    SELECT DISTINCT sc.nombre AS subcategoria_nombre, p.talla
    FROM producto p
    JOIN subcategoria sc ON p.subcategoria_id = sc.id
    WHERE p.talla IS NOT NULL
) AS tallas_unicas
GROUP BY subcategoria_nombre
"""

query_tallas_por_categoria = """
SELECT 
    categoria_nombre,
    STRING_AGG(talla, ', ') AS tallas_disponibles
FROM (
    SELECT DISTINCT c.nombre AS categoria_nombre, p.talla
    FROM producto p
    JOIN subcategoria sc ON p.subcategoria_id = sc.id
    JOIN categoria c ON sc.categoria_id = c.id
    WHERE p.talla IS NOT NULL
) AS tallas_unicas
GROUP BY categoria_nombre
"""
query_promociones = """
SELECT 
    nombre AS promocion_nombre,
    descuento
FROM promocion
"""
query_productos_por_promocion = """
SELECT 
    pr.nombre AS promocion_nombre,
    STRING_AGG(p.nombre, ', ') AS productos
FROM producto_promocion pp
JOIN producto p ON pp.producto_codigo = p.codigo
JOIN promocion pr ON pp.promocion_id = pr.id
GROUP BY pr.nombre
"""

query_cat = """
SELECT id, nombre FROM categoria
"""

query_subcat = """
SELECT id, nombre, categoria_id FROM subcategoria
"""

query_prod = """
SELECT 
    codigo, nombre, marca, talla, color, subcategoria_id 
FROM producto
"""

query_prom = """
SELECT id, nombre, descuento FROM promocion
"""

def construir_estructura_simple():
    estructura = {
        "categoria": [],
        "subcategoria": [],
        "producto": [],
        "promocion": []
    }

    with engine.connect() as conn:
        # Categorías
        res_cat = conn.execute(text(query_cat))
        for row in res_cat.fetchall():
            estructura["categoria"].append({
                "id": row.id,
                "nombre": row.nombre
            })

        # Subcategorías
        res_sub = conn.execute(text(query_subcat))
        for row in res_sub.fetchall():
            estructura["subcategoria"].append({
                "id": row.id,
                "nombre": row.nombre
            })

        # Productos
        res_prod = conn.execute(text(query_prod))
        for row in res_prod.fetchall():
            estructura["producto"].append({
                "codigo": row.codigo,
                "nombre": row.nombre
            })

        # Promociones
        res_promo = conn.execute(text(query_prom))
        for row in res_promo.fetchall():
            estructura["promocion"].append({
                "id": row.id,
                "nombre": row.nombre
            })

    return estructura



def procesar_tallas_por_categoria():
    docs = []
    with engine.connect() as conn:
        result = conn.execute(text(query_tallas_por_categoria))
        rows = result.fetchall()
        for row in rows:
            content = f"""Los productos de la categoría "{row.categoria_nombre}" están disponibles en las siguientes tallas: {row.tallas_disponibles}."""
            docs.append(Document(page_content=content, metadata={"categoria": row.categoria_nombre}))
    return docs

def procesar_promociones():
    docs = []
    with engine.connect() as conn:
        result = conn.execute(text(query_promociones))
        rows = result.fetchall()
        for row in rows:
            content = f"""La promoción "{row.promocion_nombre}" ofrece un descuento del {row.descuento:.0f}%."""
            docs.append(Document(page_content=content, metadata={"promocion": row.promocion_nombre}))
    return docs

def procesar_productos_por_promocion():
    docs = []
    with engine.connect() as conn:
        result = conn.execute(text(query_productos_por_promocion))
        rows = result.fetchall()
        for row in rows:
            content = f"""La promoción "{row.promocion_nombre}" aplica a los siguientes productos: {row.productos}."""
            docs.append(Document(page_content=content, metadata={"promocion": row.promocion_nombre}))
    return docs

def procesar_tallas_por_subcategoria():
    docs = []
    with engine.connect() as conn:
        result = conn.execute(text(query_tallas_por_subcategoria))
        rows = result.fetchall()
        for row in rows:
            content = f"""Los productos de la subcategoría "{row.subcategoria_nombre}" están disponibles en las siguientes tallas: {row.tallas_disponibles}."""
            docs.append(Document(page_content=content, metadata={"subcategoria": row.subcategoria_nombre}))
    return docs

def procesar_categoria_o_subcategoria(query, tipo='categoria'):
    docs = []
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()

        for row in rows:
            if tipo == 'categoria':
                content = f"""
La categoría "{row.categoria_nombre}" contiene {row.total_productos} productos.
Algunos de estos son: {row.productos}.
                """.strip()
                docs.append(Document(page_content=content, metadata={"categoria_id": row.categoria_id}))
            else:  # subcategoria
                content = f"""
La subcategoría "{row.subcategoria_nombre}", que pertenece a la categoría "{row.categoria_nombre}", contiene {row.total_productos} productos.
Algunos de estos productos son: {row.productos}.
                """.strip()
                docs.append(Document(page_content=content, metadata={"subcategoria_id": row.subcategoria_id}))
    return docs

def procesar_productos():
    with engine.connect() as conn:
        documents = []
        result = conn.execute(text(query))
        rows = result.fetchall()
        for row in rows:
            content = f"""
    El producto "{row.producto_nombre}" (código: {row.codigo}), de la marca {row.marca}, talla {row.talla}, color {row.color},
    pertenece a la subcategoría "{row.subcategoria_nombre}", dentro de la categoría "{row.categoria_nombre}".
    Tiene un precio de {row.precio} ({row.tipo_precio}).
            """.strip()
            documents.append(Document(page_content=content, metadata={"codigo": row.codigo}))
    
    return documents

def obtener_mensajes_por_rango(fecha_inicio: datetime, fecha_fin: datetime):
    resultados = (
        session.query(Mensaje, Usuario)
        .join(Mensaje.chat)
        .join(Chat.usuario)
        .filter(Mensaje.fecha.between(fecha_inicio, fecha_fin))
        .all()
    )

    mensajes_por_usuario = {}
    for mensaje, usuario in resultados:
        if usuario.nombre not in mensajes_por_usuario:
            mensajes_por_usuario[usuario.nombre] = []
        mensajes_por_usuario[usuario.nombre].append(mensaje.texto)

    return json.dumps(mensajes_por_usuario, indent=4, ensure_ascii=False)

# def obtener_mensajes_por_rango(fecha_inicio: datetime, fecha_fin: datetime):
#     resultados = (
#         session.query(Mensaje, Usuario)
#         .join(Mensaje.chat)
#         .join(Chat.usuario)
#         .filter(Mensaje.fecha.between(fecha_inicio, fecha_fin))
#         .all()
#     )

#     mensajes_por_usuario = {}
#     for mensaje, usuario in resultados:
#         if usuario.nombre not in mensajes_por_usuario:
#             mensajes_por_usuario[usuario.nombre] = []
#         mensajes_por_usuario[usuario.nombre].append({
#             "texto": mensaje.texto,
#         })

#     return json.dumps(mensajes_por_usuario, indent=4, ensure_ascii=False)

def obtener_chat_id_por_nombre_usuario(nombre_usuario: str) -> int | None:
    # Buscar el usuario por nombre
    usuario = session.query(Usuario).filter_by(nombre=nombre_usuario).first()
    
    if not usuario:
        return None  # No existe un usuario con ese nombre

    # Obtener el último chat por fecha_ini (puedes cambiar lógica si prefieres otro criterio)
    chat = session.query(Chat)\
                 .filter_by(usuario_id=usuario.id)\
                 .order_by(Chat.fecha_ini.desc())\
                 .first()
    
    if not chat:
        return None  # No tiene chats

    return chat.id

def insertar_intereses(datos_intereses: dict):
    for nombre_usuario, interes_info in datos_intereses.items():
        chat_id = obtener_chat_id_por_nombre_usuario(nombre_usuario)
        if chat_id is None:
            print(f"No se encontró chat para {nombre_usuario}, se omite.")
            continue

        tipo = interes_info['tipo']
        valor_id = interes_info['id']

        # Crear nueva instancia de Interes
        nuevo_interes = Interes(
            fecha=datetime.now(),
            chat_id=chat_id,
            producto_codigo=valor_id if tipo == 'producto' else None,
            subcategoria_id=valor_id if tipo == 'subcategoria' else None,
            categoria_id=valor_id if tipo == 'categoria' else None,
            promocion_id=valor_id if tipo == 'promocion' else None,
            correo_html=""
            # 'enviado' se deja como False por defecto
        )

        session.add(nuevo_interes)
        print(f"Interés insertado para {nombre_usuario} con tipo {tipo} e id {valor_id}")

    session.commit()
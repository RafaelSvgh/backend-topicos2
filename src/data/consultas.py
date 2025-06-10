import os
import json
import logging
from datetime import datetime
from langchain.schema import Document
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text
from .sql_queries import *
from src.models import (engine, Session, session,
    Usuario, Chat, Mensaje, Interes
)

# Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def obtener_o_crear_chat(usuario_id):
    chat = session.query(Chat).filter_by(usuario_id=usuario_id, fecha_fin=None).first()
    print(chat)
    if not chat:
        chat = Chat(fecha_ini=datetime.now(), usuario_id=usuario_id)
        session.add(chat)
        session.commit()
    return chat

def agregar_mensaje(usuario_id, texto, enviado="S"):
    chat = obtener_o_crear_chat(usuario_id)
    mensaje = Mensaje(texto=texto, fecha=datetime.now(), enviado=enviado, chat_id=chat.id)
    session.add(mensaje)
    session.commit()
    print(f"Mensaje agregado al chat {chat.id}")

def recibir_mensaje(usuario_id, texto, enviado="N"):
    chat = obtener_o_crear_chat(usuario_id)
    mensaje = Mensaje(texto=texto, fecha=datetime.now(), enviado=enviado, chat_id=chat.id)
    session.add(mensaje)
    session.commit()
    print(f"Mensaje agregado al chat {chat.id}")

def construir_estructura_simple():
    estructura = {
        "categoria": [],
        "subcategoria": [],
        "producto": [],
        "promocion": []
    }
    with engine.connect() as conn:
        res_cat = conn.execute(text(QUERY_CATEGORIAS_SIMPLE))
        for row in res_cat.fetchall():
            estructura["categoria"].append({
                "id": row.id,
                "nombre": row.nombre
            })
        res_sub = conn.execute(text(QUERY_SUBCATEGORIAS_SIMPLE))
        for row in res_sub.fetchall():
            estructura["subcategoria"].append({
                "id": row.id,
                "nombre": row.nombre
            })
        res_prod = conn.execute(text(QUERY_PRODUCTOS_SIMPLE))
        for row in res_prod.fetchall():
            estructura["producto"].append({
                "codigo": row.codigo,
                "nombre": row.nombre
            })
        res_promo = conn.execute(text(QUERY_PROMOCIONES_SIMPLE))
        for row in res_promo.fetchall():
            estructura["promocion"].append({
                "id": row.id,
                "nombre": row.nombre
            })
    return estructura

def procesar_tallas_por_categoria():
    docs = []
    with engine.connect() as conn:
        result = conn.execute(text(QUERY_TALLAS_POR_CATEGORIA))
        rows = result.fetchall()
        for row in rows:
            content = f"""Los productos de la categoría "{row.categoria_nombre}" están disponibles en las siguientes tallas: {row.tallas_disponibles}."""
            docs.append(Document(page_content=content, metadata={"categoria": row.categoria_nombre}))
    return docs

def procesar_promociones():
    docs = []
    with engine.connect() as conn:
        result = conn.execute(text(QUERY_PROMOCIONES))
        rows = result.fetchall()
        for row in rows:
            content = f"""La promoción "{row.promocion_nombre}" ofrece un descuento del {row.descuento:.0f}%."""
            docs.append(Document(page_content=content, metadata={"promocion": row.promocion_nombre}))
    return docs

def procesar_productos_por_promocion():
    docs = []
    with engine.connect() as conn:
        result = conn.execute(text(QUERY_PRODUCTOS_POR_PROMOCION))
        rows = result.fetchall()
        for row in rows:
            content = f"""La promoción "{row.promocion_nombre}" aplica a los siguientes productos: {row.productos}."""
            docs.append(Document(page_content=content, metadata={"promocion": row.promocion_nombre}))
    return docs

def procesar_tallas_por_subcategoria():
    docs = []
    with engine.connect() as conn:
        result = conn.execute(text(QUERY_TALLAS_POR_SUBCATEGORIA))
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
        result = conn.execute(text(QUERY_PRODUCTOS))
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

def obtener_chat_id_por_nombre_usuario(nombre_usuario: str) -> int | None:
    usuario = session.query(Usuario).filter_by(nombre=nombre_usuario).first()
    if not usuario:
        return None
    chat = session.query(Chat)\
                 .filter_by(usuario_id=usuario.id)\
                 .order_by(Chat.fecha_ini.desc())\
                 .first()
    if not chat:
        return None
    return chat.id

def guardar_html_interes_cat(chat_id, categoria_id, html):
    with Session() as session:
        session.execute(text(QUERY_GUARDAR_HTML_INTERES_CAT), {
            "html": html,
            "chat_id": chat_id,
            "categoria_id": categoria_id
        })
        session.commit()

def generar_correo_categoria(categoria_id: int, chat_id: str = None):
    with Session() as session:
        productos = session.execute(text(QUERY_PRODUCTOS_CATEGORIA), {"categoria_id": categoria_id}).fetchall()

        if not productos:
            print(f"No se encontraron productos para la categoría {categoria_id}.")
            return

        categoria_nombre = productos[0].categoria_nombre
        session.commit()
        lista_productos = [
            {
                "nombre": row.nombre,
                "marca": row.marca,
                "precio": row.precio,
                "imagen_url": row.imagen_url,
                "subcategoria": row.subcategoria_nombre
            } for row in productos
        ]

    contexto = {
        "categoria_nombre": categoria_nombre,
        "productos": lista_productos
    }

    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "templates"))

    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("categoria_template.html")
    html_final = template.render(contexto)

    if chat_id:
        guardar_html_interes_cat(chat_id, categoria_id, html_final)
        print(f"✅ HTML guardado para categoría {categoria_id}, chat_id={chat_id}")
    else:
        archivo_salida = f"correo_categoria_{categoria_id}.html"
        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(html_final)
        print(f"✅ Correo generado: {archivo_salida}")

def guardar_html_interes_prod(chat_id, codigo_producto, html):
    with Session() as session:
        session.execute(text("""
            UPDATE interes
            SET correo_html = :html, enviado = 0
            WHERE chat_id = :chat_id AND producto_codigo = :codigo
        """), {
            "html": html,
            "chat_id": chat_id,
            "codigo": codigo_producto
        })
        session.commit()

def generar_correo_html(codigo_producto: str, chat_id: str = None):
    with Session() as session:
        datos = session.execute(text(QUERY_DATOS_PRODUCTO), {"codigo": codigo_producto}).fetchone()

        if not datos:
            print(f"Producto con código '{codigo_producto}' no encontrado.")
            return

        imagenes_bd = session.execute(
            text(QUERY_IMAGENES_PRODUCTO),
            {"codigo": codigo_producto}
        ).fetchall()

        session.commit()

        imagenes_list = []
        for row in imagenes_bd:
            try:
                url = row['url']  
            except (TypeError, KeyError):
                url = row[0] if len(row) > 0 else None
            if url:
                imagenes_list.append({"url": url})

        textos_fijos = [
            {"titulo": "Vista frontal", "descripcion": "Tela suave, ideal para el día a día."},
            {"titulo": "Vista trasera", "descripcion": "Diseño ergonómico y moderno."},
            {"titulo": "Diseño", "descripcion": "Destaca por su comodidad y estilo, ideal para cualquier día."},
            {"titulo": "Comodidad", "descripcion": "Permite total libertad de movimiento sin perder estilo."}
        ]

        imagenes = [
            {
                "url": img["url"],
                "titulo": textos_fijos[i]["titulo"],
                "descripcion": textos_fijos[i]["descripcion"]
            }
            for i, img in enumerate(imagenes_list[:4])
        ]

    contexto = {
        "nombre": datos.nombre,
        "marca": datos.marca,
        "precio": datos.precio,
        "imagenes": imagenes,
        "tallas": ["S", "M", "L", "XL"],
    }

    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "templates"))

    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("producto_template.html")
    html_final = template.render(contexto)

    if chat_id:
        guardar_html_interes_prod(chat_id, codigo_producto, html_final)
        print(f"✅ HTML guardado en la base de datos para chat_id={chat_id}")
    else:
        archivo_salida = f"correo_{codigo_producto}.html"
        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(html_final)
        print(f"✅ Correo generado: {archivo_salida}")

def guardar_html_interes_prom(chat_id, promocion_id, html):
    with Session() as session:
        session.execute(text("""
            UPDATE interes
            SET correo_html = :html, enviado = 0
            WHERE chat_id = :chat_id AND promocion_id = :promocion_id
        """), {
            "html": html,
            "chat_id": chat_id,
            "promocion_id": promocion_id
        })
        session.commit()

def generar_correo_promocion(promocion_id: int, chat_id: str = None):
    with Session() as session:
        productos = session.execute(text(QUERY_PRODUCTOS_PROMOCION), {"promocion_id": promocion_id}).fetchall()

        if not productos:
            print(f"No se encontraron productos para la promoción {promocion_id}.")
            return

        promocion_nombre = productos[0].promocion_nombre
        session.commit()
        lista_productos = [
            {
                "codigo": row.codigo,
                "nombre": row.nombre,
                "marca": row.marca,
                "precio": float(row.precio),
                "precio_promocional": float(row.precio) * (1 - float(row.promocion_descuento) / 100),
                "imagen_url": row.imagen_url or "https://via.placeholder.com/150"
            }
            for row in productos
        ]

    contexto = {
        "promocion_nombre": promocion_nombre,
        "productos": lista_productos
    }

    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "templates"))

    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("promocion_template.html")
    html_final = template.render(contexto)

    if chat_id:
        guardar_html_interes_prom(chat_id, promocion_id, html_final)
        print(f"✅ HTML guardado para promoción {promocion_id}, chat_id={chat_id}")
    else:
        archivo_salida = f"correo_promocion_{promocion_id}.html"
        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(html_final)
        print(f"✅ Correo generado: {archivo_salida}")

def guardar_html_interes_sub(chat_id, subcategoria_id, html):
    with Session() as session:
        session.execute(text("""
            UPDATE interes
            SET correo_html = :html, enviado = 0
            WHERE chat_id = :chat_id AND subcategoria_id = :subcategoria_id
        """), {
            "html": html,
            "chat_id": chat_id,
            "subcategoria_id": subcategoria_id
        })
        session.commit()

def generar_correo_subcategoria(subcategoria_id: int, chat_id: str = None):
    with Session() as session:
        productos = session.execute(text(QUERY_PRODUCTOS_SUBCATEGORIA), {"subcategoria_id": subcategoria_id}).fetchall()

        if not productos:
            print(f"❌ No se encontraron productos para la subcategoría {subcategoria_id}.")
            return

        subcategoria_nombre = productos[0].subcategoria_nombre
        session.commit()
        lista_productos = [
            {
                "nombre": row.nombre,
                "marca": row.marca,
                "precio": row.precio,
                "imagen_url": row.imagen_url
            } for row in productos
        ]

    contexto = {
        "subcategoria_nombre": subcategoria_nombre,
        "productos": lista_productos
    }

    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "templates"))

    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("subcategoria_template.html")
    html_final = template.render(contexto)

    if chat_id:
        guardar_html_interes_sub(chat_id, subcategoria_id, html_final)
        print(f"✅ HTML guardado para subcategoría {subcategoria_id}, chat_id={chat_id}")
    else:
        archivo_salida = f"correo_subcategoria_{subcategoria_id}.html"
        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(html_final)
        print(f"✅ Correo generado: {archivo_salida}")

def insertar_intereses(datos_intereses: dict):
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Iniciando inserción de intereses para {len(datos_intereses)} usuarios")
        
        for nombre_usuario, interes_info in datos_intereses.items():
            try:
                logger.info(f"Procesando usuario: {nombre_usuario}")
                
                chat_id = obtener_chat_id_por_nombre_usuario(nombre_usuario)
                if chat_id is None:
                    logger.warning(f"No se encontró chat para {nombre_usuario}, se omite.")
                    continue

                tipo = interes_info['tipo']
                valor_id = interes_info['id']

                # Skip if valor_id is None
                if valor_id is None:
                    logger.warning(f"valor_id es None para {nombre_usuario}, se omite.")
                    continue
                
                logger.info(f"Creando nuevo interés en la base de datos para tipo: {tipo}, id: {valor_id}")
                
                # Crear el interés
                nuevo_interes = Interes(
                    fecha=datetime.now(),
                    chat_id=chat_id,
                    correo_html="",  # Se actualizará después con el HTML
                    producto_codigo=valor_id if tipo == "producto" else None,
                    subcategoria_id=valor_id if tipo == "subcategoria" else None,
                    categoria_id=valor_id if tipo == "categoria" else None,
                    promocion_id=valor_id if tipo == "promocion" else None,
                )

                session.add(nuevo_interes)
                session.commit()
                logger.info(f"Interés insertado para {nombre_usuario}")

                try:
                    if tipo == 'producto':
                        generar_correo_html(valor_id, chat_id)
                    elif tipo == 'subcategoria':
                        generar_correo_subcategoria(valor_id, chat_id)
                    elif tipo == 'categoria':
                        generar_correo_categoria(valor_id, chat_id)
                    elif tipo == 'promocion':
                        generar_correo_promocion(valor_id, chat_id)
                    logger.info(f"HTML generado y guardado para {tipo} {valor_id}")
                except Exception as e:
                    logger.error(f"Error generando HTML: {str(e)}")
                    continue
                
            except Exception as e:
                logger.error(f"Error procesando usuario {nombre_usuario}: {str(e)}")
                session.rollback()
                continue

        logger.info("Proceso de inserción de intereses completado")
        
    except Exception as e:
        logger.error(f"Error general en insertar_intereses: {str(e)}")
        session.rollback()
        raise
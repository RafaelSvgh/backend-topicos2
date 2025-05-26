from sqlalchemy import create_engine, text
from langchain.schema import Document

connection_string = "mssql+pyodbc://sa:rafa0134@localhost\\MSSQLSERVER2,1433/negocio?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes"
engine = create_engine(connection_string)

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
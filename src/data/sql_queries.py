"""
Consultas SQL para la aplicación.
Este módulo contiene todas las consultas SQL utilizadas en la aplicación.
"""

# Consulta con joins completos para productos
QUERY_PRODUCTOS = '''
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
'''

# Consulta para categorías
QUERY_CATEGORIAS = '''
SELECT
    c.id AS categoria_id,
    c.nombre AS categoria_nombre,
    COUNT(p.codigo) AS total_productos,
    STRING_AGG(p.nombre, ', ') AS productos
FROM categoria c
JOIN subcategoria sc ON sc.categoria_id = c.id
JOIN producto p ON p.subcategoria_id = sc.id
GROUP BY c.id, c.nombre
'''

# Consulta para subcategorías
QUERY_SUBCATEGORIAS = '''
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
'''

# Consulta para tallas por subcategoría
QUERY_TALLAS_POR_SUBCATEGORIA = '''
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
'''

# Consulta para tallas por categoría
QUERY_TALLAS_POR_CATEGORIA = '''
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
'''

# Consulta para promociones
QUERY_PROMOCIONES = '''
SELECT 
    nombre AS promocion_nombre,
    descuento
FROM promocion
'''

# Consulta para productos por promoción
QUERY_PRODUCTOS_POR_PROMOCION = '''
SELECT 
    pr.nombre AS promocion_nombre,
    STRING_AGG(p.nombre, ', ') AS productos
FROM producto_promocion pp
JOIN producto p ON pp.producto_codigo = p.codigo
JOIN promocion pr ON pp.promocion_id = pr.id
GROUP BY pr.nombre
'''

# Consultas simples
QUERY_CATEGORIAS_SIMPLE = '''
SELECT id, nombre FROM categoria
'''

QUERY_SUBCATEGORIAS_SIMPLE = '''
SELECT id, nombre, categoria_id FROM subcategoria
'''

QUERY_PRODUCTOS_SIMPLE = '''
SELECT 
    codigo, nombre, marca, talla, color, subcategoria_id 
FROM producto
'''

QUERY_PROMOCIONES_SIMPLE = '''
SELECT id, nombre, descuento FROM promocion
'''

# Consulta para guardar HTML de interés en categoría
QUERY_GUARDAR_HTML_INTERES_CAT = '''
UPDATE interes
SET correo_html = :html, enviado = 0
WHERE chat_id = :chat_id AND categoria_id = :categoria_id
'''

# Consulta para productos de una categoría
QUERY_PRODUCTOS_CATEGORIA = '''
SELECT
    prod.codigo,
    prod.nombre,
    prod.marca,
    prod.precio,
    prod.url AS imagen_url,
    c.nombre AS categoria_nombre,
    s.nombre AS subcategoria_nombre
FROM subcategoria s
JOIN categoria c ON s.categoria_id = c.id
OUTER APPLY (
    SELECT TOP 1
        p.codigo, p.nombre, p.marca,
        lp.precio,
        i.url
    FROM producto p
    JOIN producto_precio pp ON pp.producto_codigo = p.codigo
    JOIN lista_precio lp ON lp.id = pp.lista_precio_id
    JOIN (
        SELECT producto_codigo, MIN(id) AS primera_imagen_id
        FROM imagen
        GROUP BY producto_codigo
    ) img_min ON img_min.producto_codigo = p.codigo
    JOIN imagen i ON i.id = img_min.primera_imagen_id
    WHERE p.subcategoria_id = s.id
    ORDER BY p.nombre
) AS prod
WHERE c.id = :categoria_id AND prod.codigo IS NOT NULL
'''

# Consulta para datos de un producto específico
QUERY_DATOS_PRODUCTO = '''
SELECT 
    p.nombre, p.marca, p.color, p.talla,
    lp.precio
FROM producto p
JOIN producto_precio pp ON p.codigo = pp.producto_codigo
JOIN lista_precio lp ON pp.lista_precio_id = lp.id
WHERE p.codigo = :codigo
'''

# Consulta para imágenes de un producto
QUERY_IMAGENES_PRODUCTO = '''
SELECT url FROM imagen WHERE producto_codigo = :codigo
'''

# Consulta para productos de una promoción
QUERY_PRODUCTOS_PROMOCION = '''
SELECT
    p.codigo,
    p.nombre,
    p.marca,
    lp.precio,
    pr.nombre AS promocion_nombre,
    pr.descuento AS promocion_descuento,
    i.url AS imagen_url
FROM promocion pr
JOIN producto_promocion pp ON pr.id = pp.promocion_id
JOIN producto p ON pp.producto_codigo = p.codigo
JOIN producto_precio ppr ON ppr.producto_codigo = p.codigo
JOIN lista_precio lp ON lp.id = ppr.lista_precio_id
JOIN (
    SELECT producto_codigo, MIN(id) AS primera_imagen_id
    FROM imagen
    GROUP BY producto_codigo
) img_min ON img_min.producto_codigo = p.codigo
JOIN imagen i ON i.id = img_min.primera_imagen_id
WHERE pr.id = :promocion_id
  AND lp.descripcion = 'Precio regular'  -- filtra solo precios regulares
ORDER BY p.nombre
'''

# Consulta para productos de una subcategoría
QUERY_PRODUCTOS_SUBCATEGORIA = '''
SELECT
    p.codigo,
    p.nombre,
    p.marca,
    precios.precio,
    i.url AS imagen_url,
    s.nombre AS subcategoria_nombre
FROM producto p
JOIN subcategoria s ON s.id = p.subcategoria_id
JOIN (
    SELECT pp.producto_codigo, lp.precio
    FROM producto_precio pp
    JOIN lista_precio lp ON lp.id = pp.lista_precio_id
    WHERE pp.id IN (
        SELECT MIN(id)
        FROM producto_precio
        GROUP BY producto_codigo
    )
) precios ON precios.producto_codigo = p.codigo
JOIN (
    SELECT producto_codigo, MIN(id) AS primera_imagen_id
    FROM imagen
    GROUP BY producto_codigo
) img_min ON img_min.producto_codigo = p.codigo
JOIN imagen i ON i.id = img_min.primera_imagen_id
WHERE p.subcategoria_id = :subcategoria_id
ORDER BY p.nombre
''' 
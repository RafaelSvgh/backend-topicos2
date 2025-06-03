from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text, create_engine
import sys

connection_string = "mssql+pyodbc://@localhost/negocio?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

engine = create_engine(connection_string)

# Probar la conexión
with engine.connect() as conn:
    print("Conexión exitosa")

def guardar_html_interes(chat_id, categoria_id, html):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE interes
            SET correo_html = :html, enviado = 0
            WHERE chat_id = :chat_id AND categoria_id = :categoria_id
        """), {
            "html": html,
            "chat_id": chat_id,
            "categoria_id": categoria_id
        })

def generar_correo_categoria(categoria_id: int, chat_id: str = None):
    with engine.connect() as conn:
        productos = conn.execute(text("""
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

        """), {"categoria_id": categoria_id}).fetchall()

        if not productos:
            print(f"No se encontraron productos para la categoría {categoria_id}.")
            return

        categoria_nombre = productos[0].categoria_nombre

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

    env = Environment(loader=FileSystemLoader('../../templates'))
    template = env.get_template("categoria_template.html")
    html_final = template.render(contexto)

    if chat_id:
        guardar_html_interes(chat_id, categoria_id, html_final)
        print(f"✅ HTML guardado para categoría {categoria_id}, chat_id={chat_id}")
    else:
        archivo_salida = f"correo_categoria_{categoria_id}.html"
        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(html_final)
        print(f"✅ Correo generado: {archivo_salida}")

# Ejecutar desde terminal: python categoria_email.py 1 [CHAT_ID]
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Debes proporcionar el ID de la categoría. Ejemplo:")
        print("   python categoria_email.py 1 [CHAT_ID]")
    else:
        categoria_id = int(sys.argv[1])
        chat_id = sys.argv[2] if len(sys.argv) > 2 else None
        generar_correo_categoria(categoria_id, chat_id)
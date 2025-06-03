from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text, create_engine
import sys

# Conexión a la base de datos
connection_string = "mssql+pyodbc://@localhost/negocio?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
engine = create_engine(connection_string)

def guardar_html_interes(chat_id, subcategoria_id, html):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE interes
            SET correo_html = :html, enviado = 0
            WHERE chat_id = :chat_id AND subcategoria_id = :subcategoria_id
        """), {
            "html": html,
            "chat_id": chat_id,
            "subcategoria_id": subcategoria_id
        })

def generar_correo_subcategoria(subcategoria_id: int, chat_id: str = None):
    with engine.connect() as conn:
        productos = conn.execute(text("""
SELECT
    p.codigo,
    p.nombre,
    p.marca,
    precios.precio,
    i.url AS imagen_url,
    s.nombre AS subcategoria_nombre
FROM producto p
JOIN subcategoria s ON s.id = p.subcategoria_id

-- Traer el primer precio registrado por producto
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

-- Traer la primera imagen registrada por producto
JOIN (
    SELECT producto_codigo, MIN(id) AS primera_imagen_id
    FROM imagen
    GROUP BY producto_codigo
) img_min ON img_min.producto_codigo = p.codigo
JOIN imagen i ON i.id = img_min.primera_imagen_id

WHERE p.subcategoria_id = :subcategoria_id
ORDER BY p.nombre


        """), {"subcategoria_id": subcategoria_id}).fetchall()

        if not productos:
            print(f"❌ No se encontraron productos para la subcategoría {subcategoria_id}.")
            return

        subcategoria_nombre = productos[0].subcategoria_nombre

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

    env = Environment(loader=FileSystemLoader('../../templates'))
    template = env.get_template("subcategoria_template.html")
    html_final = template.render(contexto)

    if chat_id:
        guardar_html_interes(chat_id, subcategoria_id, html_final)
        print(f"✅ HTML guardado para subcategoría {subcategoria_id}, chat_id={chat_id}")
    else:
        archivo_salida = f"correo_subcategoria_{subcategoria_id}.html"
        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(html_final)
        print(f"✅ Correo generado: {archivo_salida}")

# Ejecutar desde terminal
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Debes proporcionar el ID de la subcategoría. Ejemplo:")
        print("   python subcategoria_email.py 3 [CHAT_ID]")
    else:
        subcategoria_id = int(sys.argv[1])
        chat_id = sys.argv[2] if len(sys.argv) > 2 else None
        generar_correo_subcategoria(subcategoria_id, chat_id)

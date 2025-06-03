from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text, create_engine
import sys

connection_string = "mssql+pyodbc://@localhost/negocio?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
engine = create_engine(connection_string)

def guardar_html_interes(chat_id, promocion_id, html):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE interes
            SET correo_html = :html, enviado = 0
            WHERE chat_id = :chat_id AND promocion_id = :promocion_id
        """), {
            "html": html,
            "chat_id": chat_id,
            "promocion_id": promocion_id
        })

def generar_correo_promocion(promocion_id: int, chat_id: str = None):
    with engine.connect() as conn:
        productos = conn.execute(text("""
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
        """), {"promocion_id": promocion_id}).fetchall()

        if not productos:
            print(f"No se encontraron productos para la promoción {promocion_id}.")
            return

        promocion_nombre = productos[0].promocion_nombre

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

    env = Environment(loader=FileSystemLoader('../../templates'))
    template = env.get_template("promocion_template.html")
    html_final = template.render(contexto)

    if chat_id:
        guardar_html_interes(chat_id, promocion_id, html_final)
        print(f"✅ HTML guardado para promoción {promocion_id}, chat_id={chat_id}")
    else:
        archivo_salida = f"correo_promocion_{promocion_id}.html"
        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(html_final)
        print(f"✅ Correo generado: {archivo_salida}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Debes proporcionar el ID de la promoción. Ejemplo:")
        print("   python promocion_email.py 1 [CHAT_ID]")
    else:
        promocion_id = int(sys.argv[1])
        chat_id = sys.argv[2] if len(sys.argv) > 2 else None
        generar_correo_promocion(promocion_id, chat_id)

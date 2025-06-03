from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text, create_engine
import sys

connection_string = "mssql+pyodbc://@localhost/negocio?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

engine = create_engine(connection_string)

# Probar la conexión
with engine.connect() as conn:
    print("Conexión exitosa")

def guardar_html_interes(chat_id, codigo_producto, html):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE interes
            SET correo_html = :html, enviado = 0
            WHERE chat_id = :chat_id AND producto_codigo = :codigo
        """), {
            "html": html,
            "chat_id": chat_id,
            "codigo": codigo_producto
        })

def generar_correo_html(codigo_producto: str, chat_id: str = None):
    with engine.connect() as conn:
        datos = conn.execute(text("""
            SELECT 
                p.nombre, p.marca, p.color, p.talla,
                lp.precio
            FROM producto p
            JOIN producto_precio pp ON p.codigo = pp.producto_codigo
            JOIN lista_precio lp ON pp.lista_precio_id = lp.id
            WHERE p.codigo = :codigo
        """), {"codigo": codigo_producto}).fetchone()

        if not datos:
            print(f"Producto con código '{codigo_producto}' no encontrado.")
            return

        # Convierte a lista de diccionarios con solo la URL
        imagenes_bd = conn.execute(
            text("SELECT url FROM imagen WHERE producto_codigo = :codigo"),
            {"codigo": codigo_producto}
        ).fetchall()

        imagenes_list = []
        for row in imagenes_bd:
            try:
                url = row['url']  # si el row soporta claves
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

    env = Environment(loader=FileSystemLoader('../../templates'))
    template = env.get_template("producto_template.html")
    html_final = template.render(contexto)

    if chat_id:
        guardar_html_interes(chat_id, codigo_producto, html_final)
        print(f"✅ HTML guardado en la base de datos para chat_id={chat_id}")
    else:
        archivo_salida = f"correo_{codigo_producto}.html"
        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(html_final)
        print(f"✅ Correo generado: {archivo_salida}")

# Ejecutar desde terminal: python producto_template.py P012 [CHAT_ID]
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Debes proporcionar el código del producto. Ejemplo:")
        print("   python producto_template.py P012 [CHAT_ID]")
    else:
        codigo = sys.argv[1]
        chat_id = sys.argv[2] if len(sys.argv) > 2 else None
        generar_correo_html(codigo, chat_id)
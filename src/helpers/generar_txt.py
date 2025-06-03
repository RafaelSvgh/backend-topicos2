from sqlalchemy import create_engine, text
from langchain.schema import Document  # Asegúrate de tener langchain instalado
from src.data.consultas import (  # Asumiendo que tus funciones están en consultas.py
    procesar_tallas_por_categoria,
    procesar_tallas_por_subcategoria,
    procesar_promociones,
    procesar_productos_por_promocion,
    procesar_categoria_o_subcategoria,
    procesar_productos,
    query_categorias,
    query_subcategorias
)

def generar_txt_desde_consultas(output_path="datos_vectoriales.txt"):
    docs = []

    # Ejecutar cada función de extracción
    docs += procesar_tallas_por_categoria()
    print("Tallas por categoría procesadas.")
    docs += procesar_tallas_por_subcategoria()
    print("Tallas por subcategoría procesadas.")
    docs += procesar_promociones()
    print("Promociones procesadas.")
    docs += procesar_productos_por_promocion()
    print("Productos por promoción procesados.")
    docs += procesar_categoria_o_subcategoria(query_categorias, tipo='categoria')
    print("Categorías procesadas.")
    docs += procesar_categoria_o_subcategoria(query_subcategorias, tipo='subcategoria')
    print("Subcategorías procesadas.")
    docs += procesar_productos()
    print("Productos procesados.")

    # Guardar en un archivo txt
    with open(output_path, "w", encoding="utf-8") as file:
        for doc in docs:
            file.write(doc.page_content.strip() + "\n\n")  # Espaciado entre entradas

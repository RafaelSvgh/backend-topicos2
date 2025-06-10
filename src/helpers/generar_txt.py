import os
from src.data.sql_queries import (
    QUERY_CATEGORIAS,
    QUERY_SUBCATEGORIAS
)
from src.data.consultas import (  
    procesar_tallas_por_categoria,
    procesar_tallas_por_subcategoria,
    procesar_promociones,
    procesar_productos_por_promocion,
    procesar_categoria_o_subcategoria,
    procesar_productos,
)

def generar_txt_desde_consultas(output_path="datos_vectoriales.txt"):
    if os.path.exists(output_path):
        print(f"✅ El archivo {output_path} ya existe, no es necesario regenerarlo.")
        return

    print(f"🔄 Generando archivo {output_path}...")
    docs = []
    docs += procesar_tallas_por_categoria()
    docs += procesar_tallas_por_subcategoria()
    docs += procesar_promociones()
    docs += procesar_productos_por_promocion()
    docs += procesar_categoria_o_subcategoria(QUERY_CATEGORIAS, tipo='categoria')
    docs += procesar_categoria_o_subcategoria(QUERY_SUBCATEGORIAS, tipo='subcategoria')
    docs += procesar_productos()

    with open(output_path, "w", encoding="utf-8") as file:
        for doc in docs:
            file.write(doc.page_content.strip() + "\n\n")
    
    print(f"✅ Archivo {output_path} generado exitosamente.")

import json

def cargar_sinonimos(archivo="filtros.json"):
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Advertencia: No se encontró el archivo {archivo}")
        return {}
    except json.JSONDecodeError:
        print(f"Error: El archivo {archivo} no es un JSON válido")
        return {}

def reemplazar_sinonimos(texto, sinonimos):
    if not sinonimos:
        return texto
    palabras = texto.lower().split()
    texto_reemplazado = []
    for palabra in palabras:
        reemplazada = False
        for palabra_principal, alternativas in sinonimos.items():
            if palabra in alternativas or palabra == palabra_principal:
                texto_reemplazado.append(palabra_principal)
                reemplazada = True
                break
        if not reemplazada:
            texto_reemplazado.append(palabra)
    return " ".join(texto_reemplazado)
import json

from src.helpers.qa_chain import setup_simple_qa_chain

def detectar_intereses(conversaciones_json):
    qa_chain = setup_simple_qa_chain()

    # 👇 Convertir string JSON a dict (solo si no es ya un dict)
    if isinstance(conversaciones_json, str):
        conversaciones = json.loads(conversaciones_json)
    else:
        conversaciones = conversaciones_json

    intereses_por_usuario = {}

    for usuario, mensajes in conversaciones.items():
        intereses = set()
        for mensaje in mensajes:
            try:
                respuesta = qa_chain.invoke({"question": mensaje})
                if respuesta.strip().lower() != "sin interés":
                    intereses.add(respuesta.strip())
            except Exception as e:
                print(f"Error con mensaje '{mensaje}': {e}")
        intereses_por_usuario[usuario] = list(intereses)

    return intereses_por_usuario

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from src.data.consultas import construir_estructura_simple

def setup_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    template = """No te pases de 255 caracteres, Eres un vendedor de una tienda de ropa virtual. 
    Responde a la pregunta del usuario basándote en el siguiente contexto y en el historial de conversación.
    Si no sabes la respuesta, simplemente di que no lo sabes, no intentes inventar una respuesta, nome respondas utilizando la letra ñ Ñ.

    Contexto: {context}
    
    Pregunta: {question}"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    qa_chain = (
        {
            "context": lambda x: format_docs(retriever.invoke(x["question"])),
            "question": lambda x: x["question"],
            "chat_history": lambda x: x["chat_history"]
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return qa_chain

def setup_simple_qa_chain():
    # Definir el prompt directo
    template = """Eres un asistente virtual para una tienda de ropa.
Analiza el mensaje del cliente y responde solamente con el nombre del producto o promoción de interés, si lo hay.
Si no hay un interés claro, responde: "Sin interés.

Pregunta: {question}"""

    # Crear plantilla del prompt
    prompt = ChatPromptTemplate.from_template(template)

    # Definir el modelo LLM
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)

    # Cadena de procesamiento
    qa_chain = (
        prompt
        | llm
        | StrOutputParser()
    )

    return qa_chain

def obtener_interes_principal_por_usuario(intereses_por_usuario: dict) -> dict:
    # Inicializar el modelo LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    datos = construir_estructura_simple()
    # Prompt para seleccionar el interés principal
    prompt = ChatPromptTemplate.from_template(
        """Eres un asistente de ventas. A continuación te presento una lista de intereses expresados por un cliente.
        Debes analizar los elementos y devolver el más importante o representativo según la intención del usuario, si no existe responde "sin interés".

        Lista de intereses del usuario:
        {intereses}

        Devuelve solo el interés principal, no des mas texto ni rodeos, responde directamente el interes del usuario."""
    )

    resultado_final = {}

    # Iterar sobre los usuarios y procesar sus intereses
    for usuario, intereses in intereses_por_usuario.items():
        if not intereses or intereses == ["Sin interés."]:
            resultado_final[usuario] = "Sin interés"
            continue

        # Formatear el prompt e invocar el modelo
        prompt_input = prompt.format(intereses=", ".join(intereses))
        respuesta = llm.invoke(prompt_input)

        resultado_final[usuario] = respuesta.content.strip()

    return resultado_final

def obtener_match_por_usuario_con_llm(intereses_por_usuario: dict) -> dict:
    # Inicializar el modelo LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # Obtener datos
    datos = construir_estructura_simple()

    # Aplanar los elementos con tipo e ID
    elementos = []
    for promo in datos['promocion']:
        elementos.append({'tipo': 'promocion', 'nombre': promo['nombre'], 'id': promo['id']})
    for prod in datos['producto']:
        elementos.append({'tipo': 'producto', 'nombre': prod['nombre'], 'id': prod['codigo']})
    for subcat in datos['subcategoria']:
        elementos.append({'tipo': 'subcategoria', 'nombre': subcat['nombre'], 'id': subcat['id']})
    for cat in datos['categoria']:
        elementos.append({'tipo': 'categoria', 'nombre': cat['nombre'], 'id': cat['id']})

    # Definir el prompt
    prompt = ChatPromptTemplate.from_template(
        """Eres un asistente experto en ventas que ayuda a identificar el elemento más relevante del catálogo según el interés expresado por un usuario.

Interés del usuario:
"{interes}"

Lista de elementos disponibles:
{elementos}

Tu tarea es identificar cuál es el elemento del catálogo que más se relaciona con el interés del usuario. Devuelve únicamente un JSON en el siguiente formato:
{{
  "tipo": "producto" | "subcategoria" | "categoria" | "promocion" | "sin coincidencia",
  "id": "ID o código correspondiente, o null si no hay coincidencia"
}}

No expliques tu elección. No agregues texto adicional.
"""
    )

    resultado_final = {}

    for usuario, interes in intereses_por_usuario.items():
        if not interes:
            resultado_final[usuario] = {"tipo": "sin coincidencia", "id": None}
            continue

        prompt_input = prompt.format(
            interes=interes,
            elementos=[{"tipo": e["tipo"], "nombre": e["nombre"], "id": e["id"]} for e in elementos]
        )

        respuesta = llm.invoke(prompt_input)

        try:
            respuesta_json = eval(respuesta.content.strip())
        except Exception:
            respuesta_json = {"tipo": "error", "id": None}

        resultado_final[usuario] = respuesta_json

    return resultado_final


import os

from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_core.messages import AIMessage, HumanMessage

from src.helpers.generar_txt import generar_txt_desde_consultas
from src.helpers.sinonimos import cargar_sinonimos, reemplazar_sinonimos
from src.helpers.embeddings import load_and_process_document, create_vector_store
from src.helpers.qa_chain import obtener_interes_principal_por_usuario, obtener_match_por_usuario_con_llm, setup_qa_chain

from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

from langchain_community.llms import OpenAI
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

from src.data.consultas import agregar_mensaje, construir_estructura_simple, insertar_intereses, obtener_mensajes_por_rango, recibir_mensaje
from datetime import datetime
from src.helpers.generar_interes import detectar_intereses

app = Flask(__name__)
CORS(app)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")
TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
generar_txt_desde_consultas()

sinonimos = cargar_sinonimos()
file_path = "datos_vectoriales.txt"
splits = load_and_process_document(file_path)
vectorstore = create_vector_store(splits)
qa_chain = setup_qa_chain(vectorstore)
chat_history = []

fecha_ini = datetime(2024, 1, 1)
fecha_fin = datetime(2025, 12, 31)

chats = obtener_mensajes_por_rango(fecha_ini, fecha_fin)

intereses = detectar_intereses(chats)

interes_principal = obtener_interes_principal_por_usuario(intereses)

# print(interes_principal)
filtro_interes = obtener_match_por_usuario_con_llm(interes_principal)
insertar_intereses(filtro_interes)
# print(interes_principal)
# print(resultadoo)
@app.route('/whatsapp-response', methods=['POST'])
def qa():
    data = request.get_json()
    # question = request.values.get('Body', '')
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "No se proporcionó una pregunta"}), 400
    # prompt_normalizado = reemplazar_sinonimos(question, sinonimos)
    agregar_mensaje("1", question)
    response = qa_chain.invoke({
        "question": question,
        "chat_history": chat_history
    })
    recibir_mensaje("1", response)
    # print(response)
    chat_history.append(HumanMessage(content=question))
    chat_history.append(AIMessage(content=response))
    return jsonify({"response": response})
    # resp = MessagingResponse()
    # msg = resp.message()
    # msg.body(response["result"])
    # return str(resp)

@app.route('/whatsapp-response', methods=['POST'])
def whatsapp():
    mensaje_usuario = request.values.get('Body', '')
    # result = db_chain.invoke({"query": mensaje_usuario})
    # resp = MessagingResponse()
    # msg = resp.message()
    # msg.body(result["result"])
    # return str(resp)


@app.route('/send-message', methods=['POST'])
def send_message():
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body="Hola, Bienvenido a nuestra tienda virtual, ¿En qué puedo ayudarte?",
        from_=TWILIO_WHATSAPP_FROM,
        to=TWILIO_WHATSAPP_TO
    )
    return jsonify({"status": "success"})
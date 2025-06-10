import os

from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_core.messages import AIMessage, HumanMessage

from src.helpers.generar_txt import generar_txt_desde_consultas
from src.helpers.embeddings import load_and_process_document, create_vector_store
from src.helpers.qa_chain import obtener_interes_principal_por_usuario, obtener_match_por_usuario_con_llm, setup_qa_chain

from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

from src.data.consultas import agregar_mensaje, insertar_intereses, obtener_mensajes_por_rango, recibir_mensaje
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
file_path = "datos_vectoriales.txt"
splits = load_and_process_document(file_path)
vectorstore = create_vector_store(splits)
qa_chain = setup_qa_chain(vectorstore)
chat_history = []

@app.route('/insertar-intereses', methods=['POST'])
def insertar_intereses_route():
    try:
        data = request.get_json()
        fecha_ini_str = data.get('fecha_inicio', '01-01-2024')
        fecha_fin_str = data.get('fecha_fin', '31-12-2025')
        try:
            fecha_ini = datetime.strptime(fecha_ini_str, '%d-%m-%Y')
            fecha_fin = datetime.strptime(fecha_fin_str, '%d-%m-%Y')
            print(fecha_fin)
        except ValueError as e:
            return jsonify({
                "status": "error",
                "message": "Formato de fecha inválido. Use DD-MM-YYYY (ejemplo: 30-05-2025)",
                "error": str(e)
            }), 400

        if fecha_ini > fecha_fin:
            return jsonify({
                "status": "error",
                "message": "La fecha de inicio debe ser menor que la fecha de fin"
            }), 400

        chats = obtener_mensajes_por_rango(fecha_ini, fecha_fin)
        intereses = detectar_intereses(chats)
        interes_principal = obtener_interes_principal_por_usuario(intereses)
        filtro_interes = obtener_match_por_usuario_con_llm(interes_principal)
        print(filtro_interes)
        insertar_intereses(filtro_interes)
        
        return jsonify({
            "status": "success",
            "data": {
                "fecha_inicio": fecha_ini_str,
                "fecha_fin": fecha_fin_str,
                "total_intereses": len(filtro_interes)
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Error al procesar la solicitud",
            "error": str(e)
        }), 500

@app.route('/whatsapp-response', methods=['POST'])
def qa():
    if request.form:
            question = request.form.get('Body', '')
    else:
        data = request.get_json(silent=True)
        question = data.get('Body', '') if data else ''
    if not question:
        return jsonify({"error": "No se proporcionó una pregunta"}), 400
    agregar_mensaje("4", question)
    response = qa_chain.invoke({
        "question": question,
        "chat_history": chat_history
    })
    recibir_mensaje("4", response)
    chat_history.append(HumanMessage(content=question))
    chat_history.append(AIMessage(content=response))
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(response)
    print(response)
    return str(resp)


@app.route('/send-message', methods=['POST'])
def send_message():
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body="Hola, Bienvenido a nuestra tienda virtual, ¿En qué puedo ayudarte?",
        from_=TWILIO_WHATSAPP_FROM,
        to=TWILIO_WHATSAPP_TO
    )
    return jsonify({"status": "success"})
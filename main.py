import os
from langchain.schema import Document
from dotenv import load_dotenv
from flask_cors import CORS
from twilio.rest import Client
from langchain_openai import ChatOpenAI
from flask import Flask, request, jsonify
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from twilio.twiml.messaging_response import MessagingResponse
from src.utils.generar_txt import generar_txt_desde_consultas
load_dotenv()

app = Flask(__name__)
CORS(app)

# Variables de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

DATABASE_URI = os.getenv("DATABASE_URI")
# db = SQLDatabase.from_uri(DATABASE_URI)
# 1. Conexión a la base de datos
# Tu cadena de conexión
generar_txt_desde_consultas()

# # Mostrar ejemplo
# print(f"{len(documents)} documentos creados. Ejemplo:\n")
# Modelo LLM
llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0, verbose=True)

# db_chain = SQLDatabaseChain.from_llm(
#     llm,
#     db,
#     verbose=True,
# )

# Twilio
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")
TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO")


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
    # message = client.messages.create(
    #     body="Hola, Bienvenido a nuestra tienda virtual, ¿En qué puedo ayudarte?",
    #     from_=TWILIO_WHATSAPP_FROM,
    #     to=TWILIO_WHATSAPP_TO
    # )
    # return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0", debug=True)

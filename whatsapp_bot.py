#!/usr/bin/env python3
"""
WhatsApp Bot — Claude via Twilio
Recibe mensajes de WhatsApp y responde con Claude
"""

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import anthropic
import os
from dotenv import load_dotenv

load_dotenv("/Users/fedehaas/.env_whatsapp")

app = Flask(__name__)

# Clientes
claude  = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
twilio  = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])

# Historial de conversación por número (en memoria)
conversations = {}

SYSTEM_PROMPT = """Sos un asistente personal inteligente que responde por WhatsApp.
Respondés siempre en español, de forma clara y concisa.
Sos amable, directo y útil. Si te preguntan sobre finanzas o inversiones,
respondés con conocimiento pero aclarás que no es asesoría formal.
Máximo 3-4 párrafos por respuesta para que sea legible en WhatsApp."""

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").strip()
    from_number  = request.values.get("From", "")

    print(f"📩 Mensaje de {from_number}: {incoming_msg}")

    # Historial del usuario
    if from_number not in conversations:
        conversations[from_number] = []

    conversations[from_number].append({
        "role": "user",
        "content": incoming_msg
    })

    # Limitar historial a últimos 10 mensajes
    history = conversations[from_number][-10:]

    try:
        response = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history
        )
        reply = response.content[0].text

        # Guardar respuesta en historial
        conversations[from_number].append({
            "role": "assistant",
            "content": reply
        })

    except Exception as e:
        reply = f"Error al procesar tu mensaje: {str(e)}"

    print(f"🤖 Respuesta: {reply[:80]}...")

    # Responder vía Twilio
    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)

@app.route("/", methods=["GET"])
def health():
    return "✅ WhatsApp Bot activo", 200

if __name__ == "__main__":
    print("🤖 Bot iniciado en http://localhost:5000")
    print("   Webhook URL: http://localhost:5000/webhook")
    app.run(debug=False, port=5001, host="0.0.0.0")

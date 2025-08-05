"""
Agente WhatsApp - Aplicação Principal
Sistema modular para automação de mensagens WhatsApp via Evolution API
"""
import logging
from flask import Flask, request, jsonify
from datetime import datetime

# Importa módulos do core
from core import WhatsAppClient, MessageHandler

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Inicializa aplicação Flask
app = Flask(__name__)

# Inicializa componentes do agente
whatsapp_client = WhatsAppClient()
message_handler = MessageHandler(whatsapp_client)

logger = logging.getLogger(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Endpoint webhook - Recebe mensagens da Evolution API
    """
    try:
        webhook_data = request.json
        logger.info("📨 Webhook recebido")
        
        # Processa mensagens
        if message_handler.process_webhook_data(webhook_data):
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "no_messages"})
            
    except Exception as e:
        logger.error(f"💥 Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/send", methods=["POST"])
def send_message():
    """
    Endpoint para envio manual de mensagens
    
    Body JSON:
    {
        "number": "5511999999999",
        "message": "Sua mensagem aqui"
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "JSON inválido"}), 400
        
        number = data.get("number")
        message = data.get("message")
        
        if not number or not message:
            return jsonify({"error": "Campos 'number' e 'message' são obrigatórios"}), 400
        
        # Envia mensagem
        if whatsapp_client.send_message(number, message):
            return jsonify({
                "status": "success",
                "message": "Mensagem enviada com sucesso",
                "to": number
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Falha ao enviar mensagem"
            }), 500
            
    except Exception as e:
        logger.error(f"Erro no envio manual: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    """
    Endpoint de status - Verifica saúde do agente
    """
    try:
        is_connected = whatsapp_client.is_connected()
        
        return jsonify({
            "status": "online",
            "whatsapp_connected": is_connected,
            "instance": whatsapp_client.instance,
            "api_url": whatsapp_client.api_url,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/", methods=["GET"])
def home():
    """
    Endpoint raiz - Informações básicas
    """
    return jsonify({
        "name": "WhatsApp Agent",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "webhook": "/webhook (POST)",
            "send": "/send (POST)",
            "status": "/status (GET)"
        }
    })

def setup_webhook():
    """
    Configura webhook na Evolution API
    """
    import requests
    import os
    
    api_url = whatsapp_client.api_url
    instance = whatsapp_client.instance
    api_key = whatsapp_client.api_key
    
    endpoint = f"{api_url}/webhook/set/{instance}"
    payload = {
        "url": "http://localhost:5000/webhook",
        "webhook_by_events": False,
        "webhook_base64": False,
        "events": ["MESSAGES_UPSERT"]
    }
    headers = {
        "Content-Type": "application/json",
        "apikey": api_key
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            logger.info("✅ Webhook configurado com sucesso")
            return True
        else:
            logger.warning(f"⚠️ Falha ao configurar webhook: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao configurar webhook: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando Agente WhatsApp")
    logger.info(f"📡 API URL: {whatsapp_client.api_url}")
    logger.info(f"🏷️ Instância: {whatsapp_client.instance}")
    
    # Aguarda Evolution API estar pronta
    import time
    time.sleep(2)
    
    # Configura webhook
    logger.info("🔧 Configurando webhook...")
    setup_webhook()
    
    logger.info("✅ Agente WhatsApp pronto!")
    logger.info("📱 Acesse http://localhost:8090/manager para conectar WhatsApp")
    logger.info("🌐 API rodando em http://localhost:5000")
    
    # Inicia servidor Flask
    app.run(host="0.0.0.0", port=5000, debug=False)
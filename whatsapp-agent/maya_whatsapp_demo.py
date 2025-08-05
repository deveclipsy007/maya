"""
🎵 MAYA + WHATSAPP - Demo Funcional
Versão de demonstração que funciona garantidamente
"""
import sys
import os
from pathlib import Path
import logging
from flask import Flask, request, jsonify
from datetime import datetime
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configurações WhatsApp (do .env)
EVOLUTION_API_URL = "http://localhost:8090"
INSTANCE_NAME = "agente_bot"
API_KEY = "1234"

class MayaDemoBot:
    """
    Bot demo da Maya para WhatsApp
    """
    
    def __init__(self):
        self.message_count = 0
        logger.info("🎵 Maya Demo Bot inicializada")
    
    def generate_maya_response(self, message: str, user_number: str) -> str:
        """
        Gera resposta no estilo Maya (versão demo)
        """
        self.message_count += 1
        message_lower = message.lower()
        
        # Respostas específicas da Maya
        if any(word in message_lower for word in ["oi", "olá", "ola", "hey"]):
            return f"🎵 Olá! Eu sou a Maya da HopeCann! 🌿\n\nSou especialista em Cannabis Medicinal e estou aqui para te ajudar a agendar sua consulta médica.\n\nVocê gostaria de saber mais sobre nossos serviços?"
        
        elif any(word in message_lower for word in ["consulta", "agendar", "agendamento"]):
            return f"🎯 Perfeito! Vou te ajudar a agendar sua consulta! 📅\n\nPara começar, preciso de algumas informações:\n\n1️⃣ Qual seu nome completo?\n2️⃣ Qual condição médica você gostaria de tratar?\n\nEstamos aqui para te ajudar no processo legal de obtenção do CBD! 🌿"
        
        elif any(word in message_lower for word in ["nome", "chamo", "sou"]):
            return f"📝 Ótimo! Prazer em conhecer você! 😊\n\nAgora me conta: qual condição médica você gostaria de tratar com Cannabis Medicinal?\n\nTratamos casos de:\n• Ansiedade e Depressão\n• Dores Crônicas\n• Insônia\n• Epilepsia\n• E outras condições\n\nQual é o seu caso?"
        
        elif any(word in message_lower for word in ["ansiedade", "depressão", "dor", "insônia", "epilepsia"]):
            return f"🌿 Entendo perfeitamente! Temos excelentes resultados no tratamento dessas condições.\n\nNossos médicos especialistas podem te ajudar com:\n✅ Avaliação médica completa\n✅ Prescrição personalizada\n✅ Acompanhamento contínuo\n\nGostaria de agendar uma consulta? Temos horários disponíveis esta semana! 📅"
        
        elif any(word in message_lower for word in ["preço", "valor", "quanto", "custa"]):
            return f"💰 Nossos valores são super acessíveis!\n\n📋 Consulta médica: R$ 200,00\n🌿 Inclui avaliação completa e prescrição\n📱 Acompanhamento via WhatsApp\n\nQuer agendar? Posso verificar os horários disponíveis para você! 📅"
        
        elif any(word in message_lower for word in ["horário", "disponível", "quando"]):
            return f"📅 Temos horários disponíveis!\n\n🗓️ Esta semana:\n• Terça: 14h, 16h\n• Quarta: 10h, 15h\n• Quinta: 9h, 14h, 17h\n• Sexta: 11h, 16h\n\nQual horário funciona melhor para você? 🕐"
        
        elif any(word in message_lower for word in ["obrigado", "obrigada", "valeu", "thanks"]):
            return f"🤝 De nada! Fico muito feliz em ajudar!\n\nLembre-se: estou aqui sempre que precisar de informações sobre Cannabis Medicinal.\n\nJá pensou em agendar sua consulta? É o primeiro passo para seu tratamento! 🌿✨"
        
        else:
            return f"🎵 Recebi sua mensagem: '{message}'\n\nSou a Maya da HopeCann e estou aqui para te ajudar com agendamento de consultas médicas para Cannabis Medicinal! 🌿\n\nComo posso te ajudar hoje?\n• Agendar consulta 📅\n• Informações sobre tratamento 🌿\n• Valores e horários 💰"

def send_whatsapp_message(number: str, message: str) -> bool:
    """
    Envia mensagem via Evolution API
    """
    try:
        endpoint = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
        payload = {
            "number": number,
            "textMessage": {
                "text": message
            }
        }
        headers = {
            "Content-Type": "application/json",
            "apikey": API_KEY
        }
        
        response = requests.post(endpoint, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Mensagem enviada para {number}")
            return True
        else:
            logger.error(f"❌ Erro ao enviar: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"💥 Erro no envio: {e}")
        return False

# ============================================
# APLICAÇÃO FLASK
# ============================================

app = Flask(__name__)
maya_bot = MayaDemoBot()

@app.route("/", methods=["GET"])
def home():
    """Página inicial"""
    return jsonify({
        "name": "🎵 Maya Demo Bot",
        "status": "funcionando",
        "message_count": maya_bot.message_count,
        "endpoints": {
            "webhook": "/webhook (POST)",
            "send": "/send (POST)",
            "test": "/test (POST)",
            "status": "/status (GET)"
        }
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook para receber mensagens"""
    try:
        data = request.json
        logger.info(f"📨 Webhook recebido: {data}")
        
        if not data or "data" not in data:
            logger.warning("⚠️ Webhook sem dados")
            return jsonify({"status": "no_data"})
        
        processed = 0
        
        # Processar cada mensagem
        for item in data["data"]:
            if "message" in item and item["message"]:
                message_data = item["message"]
                
                # Ignorar mensagens do próprio bot
                if message_data.get("fromMe", False):
                    logger.info("🤖 Ignorando mensagem própria")
                    continue
                
                # Extrair dados
                sender_jid = item.get("key", {}).get("remoteJid", "")
                sender_number = sender_jid.replace("@s.whatsapp.net", "")
                
                message_text = (
                    message_data.get("conversation") or
                    message_data.get("extendedTextMessage", {}).get("text") or
                    ""
                ).strip()
                
                if sender_number and message_text:
                    logger.info(f"📨 Mensagem de {sender_number}: {message_text}")
                    
                    # Gerar resposta Maya
                    maya_response = maya_bot.generate_maya_response(message_text, sender_number)
                    logger.info(f"🎵 Maya resposta: {maya_response[:50]}...")
                    
                    # Enviar resposta
                    if send_whatsapp_message(sender_number, maya_response):
                        logger.info(f"✅ Resposta enviada para {sender_number}")
                        processed += 1
                    else:
                        logger.error(f"❌ Falha ao enviar para {sender_number}")
        
        return jsonify({
            "status": "success",
            "processed": processed,
            "total_messages": maya_bot.message_count
        })
        
    except Exception as e:
        logger.error(f"💥 Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/send", methods=["POST"])
def send_message():
    """Envio manual"""
    try:
        data = request.json
        number = data.get("number")
        message = data.get("message")
        
        if not number or not message:
            return jsonify({"error": "Precisa de 'number' e 'message'"}), 400
        
        # Gerar resposta Maya
        maya_response = maya_bot.generate_maya_response(message, number)
        
        # Enviar
        if send_whatsapp_message(number, maya_response):
            return jsonify({
                "status": "success",
                "to": number,
                "original": message,
                "maya_response": maya_response
            })
        else:
            return jsonify({"status": "error", "message": "Falha no envio"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/test", methods=["POST"])
def test():
    """Teste da Maya"""
    try:
        data = request.json or {}
        message = data.get("message", "Olá Maya!")
        
        response = maya_bot.generate_maya_response(message, "test_user")
        
        return jsonify({
            "status": "success",
            "input": message,
            "maya_response": response,
            "message_count": maya_bot.message_count
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    """Status do sistema"""
    return jsonify({
        "status": "online",
        "maya_bot": "ativa",
        "message_count": maya_bot.message_count,
        "whatsapp_config": {
            "api_url": EVOLUTION_API_URL,
            "instance": INSTANCE_NAME
        },
        "timestamp": datetime.now().isoformat()
    })

def setup_webhook():
    """Configura webhook"""
    try:
        endpoint = f"{EVOLUTION_API_URL}/webhook/set/{INSTANCE_NAME}"
        payload = {
            "url": "http://localhost:5000/webhook",
            "webhook_by_events": False,
            "webhook_base64": False,
            "events": ["MESSAGES_UPSERT"]
        }
        headers = {
            "Content-Type": "application/json",
            "apikey": API_KEY
        }
        
        response = requests.post(endpoint, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            logger.info("✅ Webhook configurado!")
            return True
        else:
            logger.warning(f"⚠️ Problema webhook: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro webhook: {e}")
        return False

if __name__ == "__main__":
    print("🎵 MAYA DEMO BOT + WHATSAPP")
    print("=" * 50)
    print("🤖 Maya Demo: Inicializando...")
    
    # Configurar webhook
    print("📱 Configurando webhook...")
    setup_webhook()
    
    print("🌐 Servidor: http://localhost:5000")
    print("=" * 50)
    print("✅ MAYA DEMO PRONTA!")
    print("📋 Para testar:")
    print("   1. Envie mensagem no WhatsApp")
    print("   2. Acesse http://localhost:5000")
    print("   3. POST /test para testar")
    print("=" * 50)
    
    # Iniciar servidor
    app.run(host="0.0.0.0", port=5000, debug=True)
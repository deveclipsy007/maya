"""
🎵 MAYA + WHATSAPP - Versão Corrigida com Evolution API v1.7.4
Baseado na documentação oficial: https://doc.evolution-api.com
"""
import requests
import json
from flask import Flask, request, jsonify
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Configurações Evolution API
EVOLUTION_API_URL = "http://localhost:8080"
INSTANCE_NAME = "agente_bot"
API_KEY = "1234"

def send_whatsapp_message(number: str, message: str) -> bool:
    """Envia mensagem via Evolution API - Endpoint correto"""
    try:
        # Endpoint correto baseado na documentação
        url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
        
        # Payload correto para Evolution API v1.7.4
        payload = {
            "number": number,
            "text": message
        }
        
        headers = {
            "Content-Type": "application/json",
            "apikey": API_KEY
        }
        
        logger.info(f"📤 Enviando para {number}: {message[:50]}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Mensagem enviada para {number}")
            return True
        else:
            logger.error(f"❌ Erro envio ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"💥 Erro no envio: {e}")
        return False

def generate_maya_response(message: str) -> str:
    """Gera resposta da Maya HopeCann"""
    msg = message.lower().strip()
    
    if any(word in msg for word in ["oi", "olá", "ola", "hey", "bom dia", "boa tarde", "boa noite"]):
        return """🎵 Olá! Eu sou a Maya da HopeCann! 🌿

Sou especialista em Cannabis Medicinal e estou aqui para te ajudar a agendar sua consulta médica.

Como posso te ajudar hoje?
• 📅 Agendar consulta
• 🌿 Informações sobre tratamento
• 💰 Valores e horários"""

    elif any(word in msg for word in ["consulta", "agendar", "agendamento", "marcar"]):
        return """🎯 Perfeito! Vou te ajudar a agendar sua consulta! 📅

Para começar, preciso de algumas informações:

1️⃣ Qual seu nome completo?
2️⃣ Qual condição médica você gostaria de tratar?

Tratamos:
• Ansiedade e Depressão
• Dores Crônicas  
• Insônia
• Epilepsia
• Outras condições

Estamos aqui para te ajudar no processo legal de obtenção do CBD! 🌿"""

    elif any(word in msg for word in ["preço", "valor", "quanto", "custa", "custo"]):
        return """💰 Nossos valores são super acessíveis!

📋 Consulta médica: R$ 200,00
🌿 Inclui:
• Avaliação médica completa
• Prescrição personalizada
• Acompanhamento via WhatsApp
• Orientações sobre uso

Quer agendar? Posso verificar os horários disponíveis! 📅"""

    elif any(word in msg for word in ["horário", "disponível", "quando", "agenda"]):
        return """📅 Temos horários disponíveis esta semana!

🗓️ Disponibilidade:
• Terça: 14h, 16h
• Quarta: 10h, 15h  
• Quinta: 9h, 14h, 17h
• Sexta: 11h, 16h

Qual horário funciona melhor para você? 🕐

Para confirmar, preciso do seu nome completo."""

    elif any(word in msg for word in ["ansiedade", "depressão", "dor", "insônia", "epilepsia", "stress"]):
        return """🌿 Entendo perfeitamente! Temos excelentes resultados no tratamento dessas condições.

Nossos médicos especialistas podem te ajudar com:
✅ Avaliação médica completa
✅ Prescrição personalizada de CBD
✅ Acompanhamento contínuo
✅ Orientações sobre dosagem

A Cannabis Medicinal tem ajudado milhares de pessoas!

Gostaria de agendar uma consulta? Temos horários disponíveis esta semana! 📅"""

    elif any(word in msg for word in ["obrigado", "obrigada", "valeu", "thanks"]):
        return """🤝 De nada! Fico muito feliz em ajudar!

Lembre-se: estou aqui sempre que precisar de informações sobre Cannabis Medicinal.

Já pensou em agendar sua consulta? É o primeiro passo para seu tratamento! 🌿✨

Como posso te ajudar mais?"""

    else:
        return f"""🎵 Recebi sua mensagem: "{message}"

Sou a Maya da HopeCann e estou aqui para te ajudar com agendamento de consultas médicas para Cannabis Medicinal! 🌿

Como posso te ajudar hoje?
• 📅 Agendar consulta
• 🌿 Informações sobre tratamento  
• 💰 Valores e horários
• 🩺 Condições que tratamos"""

def check_instance_status():
    """Verifica status da instância"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/connectionState/{INSTANCE_NAME}"
        headers = {"apikey": API_KEY}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            state = data.get("instance", {}).get("state", "unknown")
            logger.info(f"📱 Status da instância: {state}")
            return state == "open"
        else:
            logger.warning(f"⚠️ Erro ao verificar instância: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro verificação: {e}")
        return False

# ============================================
# FLASK APP
# ============================================

app = Flask(__name__)
message_count = 0

@app.route("/", methods=["GET"])
def home():
    """Página inicial"""
    return jsonify({
        "name": "🎵 Maya HopeCann Bot",
        "status": "funcionando",
        "messages_processed": message_count,
        "version": "1.0",
        "evolution_api": "v1.7.4",
        "instance": INSTANCE_NAME
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook para receber mensagens - Formato Evolution API v1.7.4"""
    global message_count
    
    try:
        data = request.json
        logger.info(f"📨 Webhook recebido: {json.dumps(data, indent=2)}")
        
        if not data:
            logger.warning("⚠️ Webhook vazio")
            return jsonify({"status": "no_data"})
        
        processed = 0
        
        # Formato Evolution API v1.7.4 - pode vir como array ou objeto
        messages_data = data if isinstance(data, list) else [data]
        
        for item in messages_data:
            # Verificar se é mensagem válida
            if "key" in item and "message" in item:
                message_data = item["message"]
                
                # Ignorar mensagens próprias
                if message_data.get("fromMe", False):
                    logger.info("🤖 Ignorando mensagem própria")
                    continue
                
                # Extrair dados
                key_data = item.get("key", {})
                sender_jid = key_data.get("remoteJid", "")
                sender_number = sender_jid.replace("@s.whatsapp.net", "")
                
                # Extrair texto da mensagem
                message_text = ""
                if "conversation" in message_data:
                    message_text = message_data["conversation"]
                elif "extendedTextMessage" in message_data:
                    message_text = message_data["extendedTextMessage"].get("text", "")
                elif "text" in message_data:
                    message_text = message_data["text"]
                
                message_text = message_text.strip()
                
                if sender_number and message_text:
                    logger.info(f"📨 Mensagem de {sender_number}: {message_text}")
                    
                    # Gerar resposta Maya
                    maya_response = generate_maya_response(message_text)
                    logger.info(f"🎵 Maya responde: {maya_response[:50]}...")
                    
                    # Enviar resposta
                    if send_whatsapp_message(sender_number, maya_response):
                        message_count += 1
                        processed += 1
                        logger.info(f"✅ Resposta #{message_count} enviada para {sender_number}!")
                    else:
                        logger.error(f"❌ Falha ao enviar para {sender_number}")
                else:
                    logger.warning(f"⚠️ Dados incompletos - Number: {sender_number}, Text: {message_text}")
        
        return jsonify({
            "status": "success",
            "processed": processed,
            "total_messages": message_count
        })
        
    except Exception as e:
        logger.error(f"💥 Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/test", methods=["GET", "POST"])
def test():
    """Teste da Maya"""
    try:
        if request.method == "POST":
            data = request.json or {}
            message = data.get("message", "Olá Maya!")
        else:
            message = request.args.get("message", "Olá Maya!")
        
        response = generate_maya_response(message)
        
        return jsonify({
            "status": "success",
            "input": message,
            "maya_response": response,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/send", methods=["POST"])
def send():
    """Envio manual via Maya"""
    try:
        data = request.json
        number = data.get("number")
        message = data.get("message")
        
        if not number or not message:
            return jsonify({"error": "Campos 'number' e 'message' obrigatórios"}), 400
        
        maya_response = generate_maya_response(message)
        
        if send_whatsapp_message(number, maya_response):
            return jsonify({
                "status": "success",
                "to": number,
                "original_message": message,
                "maya_response": maya_response
            })
        else:
            return jsonify({"status": "error", "message": "Falha no envio"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    """Status do sistema"""
    try:
        instance_connected = check_instance_status()
        
        return jsonify({
            "status": "online",
            "maya_bot": "ativa",
            "messages_processed": message_count,
            "whatsapp_instance": {
                "name": INSTANCE_NAME,
                "connected": instance_connected,
                "api_url": EVOLUTION_API_URL
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def setup_webhook():
    """Configura webhook - Evolution API v1.7.4"""
    try:
        # Endpoint correto para configurar webhook
        url = f"{EVOLUTION_API_URL}/webhook/set/{INSTANCE_NAME}"
        
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
        
        logger.info("🔧 Configurando webhook...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            logger.info("✅ Webhook configurado com sucesso!")
            return True
        else:
            logger.error(f"❌ Erro webhook ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"💥 Erro ao configurar webhook: {e}")
        return False

if __name__ == "__main__":
    print("🎵 MAYA HOPECANN BOT - Evolution API v1.7.4")
    print("=" * 50)
    print("🤖 Inicializando Maya...")
    
    # Verificar status da instância
    if check_instance_status():
        print("✅ Instância WhatsApp conectada!")
    else:
        print("⚠️ Instância pode não estar conectada")
    
    # Configurar webhook
    if setup_webhook():
        print("✅ Webhook configurado!")
    else:
        print("⚠️ Problema na configuração do webhook")
    
    print("🌐 Servidor: http://localhost:5000")
    print("📱 Envie mensagem no WhatsApp para testar!")
    print("🧪 Teste direto: http://localhost:5000/test")
    print("=" * 50)
    
    # Iniciar servidor Flask
    app.run(host="0.0.0.0", port=5000, debug=False)
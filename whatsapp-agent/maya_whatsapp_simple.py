"""
🎵 MAYA + WHATSAPP - Versão Simplificada
Integração direta da Maya com WhatsApp (sem dependências extras)
"""
import sys
import os
from pathlib import Path
import logging
from flask import Flask, request, jsonify
from datetime import datetime

# Adicionar caminho do projeto principal
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Importar módulos WhatsApp
from core import WhatsAppClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MayaWhatsAppSimple:
    """
    Integração simplificada Maya + WhatsApp
    """
    
    def __init__(self):
        self.whatsapp_client = WhatsAppClient()
        self.maya_instance = None
        self.user_sessions = {}
        
        # Tentar importar Maya
        try:
            from maya_optimized import get_maya
            self.maya_instance = get_maya()
            logger.info("✅ Maya carregada com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar Maya: {e}")
            self.maya_instance = None
    
    def process_message(self, sender_number: str, message_text: str) -> bool:
        """
        Processa mensagem com Maya
        """
        try:
            logger.info(f"🎵 Processando mensagem de {sender_number}: {message_text}")
            
            if not self.maya_instance:
                # Fallback se Maya não carregou
                fallback_response = "🎵 Olá! Sou a Maya da HopeCann. No momento estou com problemas técnicos, mas em breve estarei funcionando perfeitamente para te ajudar com agendamento de consultas!"
                return self.whatsapp_client.send_message(sender_number, fallback_response)
            
            # Processar com Maya
            maya_response = self.maya_instance.run(message_text)
            
            if maya_response and maya_response.content:
                # Enviar resposta
                success = self.whatsapp_client.send_message(sender_number, maya_response.content)
                
                if success:
                    logger.info(f"✅ Resposta Maya enviada para {sender_number}")
                    
                    # Verificar áudio (se disponível)
                    if hasattr(maya_response, 'response_audio') and maya_response.response_audio:
                        logger.info(f"🎵 Áudio gerado ({len(maya_response.response_audio.content)} bytes)")
                        # Por enquanto apenas loga, futuramente pode enviar áudio
                    
                    return True
                else:
                    logger.error("❌ Falha ao enviar resposta")
                    return False
            else:
                logger.warning("⚠️ Maya não gerou resposta")
                return False
                
        except Exception as e:
            logger.error(f"💥 Erro ao processar mensagem: {e}")
            
            # Enviar mensagem de erro amigável
            error_msg = "🎵 Desculpe, tive um probleminha. Pode repetir sua mensagem?"
            self.whatsapp_client.send_message(sender_number, error_msg)
            return False
    
    def test_maya(self, message: str) -> dict:
        """
        Testa Maya diretamente
        """
        try:
            if not self.maya_instance:
                return {
                    "status": "error",
                    "message": "Maya não está carregada"
                }
            
            response = self.maya_instance.run(message)
            
            return {
                "status": "success",
                "input": message,
                "maya_response": response.content if response else "Sem resposta",
                "has_audio": bool(hasattr(response, 'response_audio') and response.response_audio),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

# ============================================
# APLICAÇÃO FLASK
# ============================================

app = Flask(__name__)
maya_bridge = MayaWhatsAppSimple()

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Webhook para receber mensagens WhatsApp
    """
    try:
        webhook_data = request.json
        logger.info("📨 Webhook recebido")
        
        if not webhook_data or "data" not in webhook_data:
            return jsonify({"status": "no_data"})
        
        # Processar cada mensagem
        processed = False
        for item in webhook_data["data"]:
            if "message" in item and item["message"]:
                message_data = item["message"]
                
                # Ignorar mensagens do próprio bot
                if message_data.get("fromMe", False):
                    continue
                
                # Extrair dados
                sender_number = item.get("key", {}).get("remoteJid", "").replace("@s.whatsapp.net", "")
                message_text = (
                    message_data.get("conversation") or
                    message_data.get("extendedTextMessage", {}).get("text") or
                    ""
                ).strip()
                
                if sender_number and message_text:
                    logger.info(f"📨 Mensagem de {sender_number}: {message_text}")
                    maya_bridge.process_message(sender_number, message_text)
                    processed = True
        
        return jsonify({
            "status": "success" if processed else "no_messages",
            "processed_by": "maya"
        })
        
    except Exception as e:
        logger.error(f"💥 Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/send", methods=["POST"])
def send_message():
    """
    Envio manual via Maya
    """
    try:
        data = request.json
        number = data.get("number")
        message = data.get("message")
        
        if not number or not message:
            return jsonify({"error": "Campos 'number' e 'message' obrigatórios"}), 400
        
        # Processar com Maya
        success = maya_bridge.process_message(number, message)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Mensagem processada pela Maya",
                "to": number
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Falha no processamento"
            }), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/maya/test", methods=["POST"])
def test_maya():
    """
    Teste direto da Maya
    """
    try:
        data = request.json
        message = data.get("message", "Olá Maya!")
        
        result = maya_bridge.test_maya(message)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    """
    Status da integração
    """
    try:
        whatsapp_connected = maya_bridge.whatsapp_client.is_connected()
        maya_loaded = maya_bridge.maya_instance is not None
        
        return jsonify({
            "status": "online",
            "maya": {
                "loaded": maya_loaded,
                "status": "ativa" if maya_loaded else "erro",
                "name": "Maya HopeCann"
            },
            "whatsapp": {
                "connected": whatsapp_connected,
                "instance": maya_bridge.whatsapp_client.instance
            },
            "integration": "maya + whatsapp",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    """
    Informações da API
    """
    return jsonify({
        "name": "🎵 Maya + WhatsApp (Simplificada)",
        "version": "1.0.0",
        "description": "Maya HopeCann integrada com WhatsApp",
        "features": [
            "Agendamento de consultas",
            "Respostas inteligentes",
            "Integração WhatsApp"
        ],
        "endpoints": {
            "webhook": "/webhook (POST) - Recebe mensagens",
            "send": "/send (POST) - Envia via Maya",
            "maya_test": "/maya/test (POST) - Testa Maya",
            "status": "/status (GET) - Status"
        },
        "como_testar": {
            "1": "POST /maya/test com {'message': 'Quero consulta'}",
            "2": "POST /send com {'number': '5511999999999', 'message': 'Olá'}",
            "3": "Envie mensagem no WhatsApp"
        }
    })

def setup_webhook():
    """
    Configura webhook
    """
    import requests
    
    whatsapp_client = maya_bridge.whatsapp_client
    
    endpoint = f"{whatsapp_client.api_url}/webhook/set/{whatsapp_client.instance}"
    payload = {
        "url": "http://localhost:5000/webhook",
        "webhook_by_events": False,
        "webhook_base64": False,
        "events": ["MESSAGES_UPSERT"]
    }
    headers = {
        "Content-Type": "application/json",
        "apikey": whatsapp_client.api_key
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            logger.info("✅ Webhook configurado!")
        else:
            logger.warning(f"⚠️ Problema webhook: {response.text}")
    except Exception as e:
        logger.error(f"❌ Erro webhook: {e}")

if __name__ == "__main__":
    print("🎵 MAYA + WHATSAPP (SIMPLIFICADA)")
    print("=" * 50)
    
    # Verificar se Maya carregou
    if maya_bridge.maya_instance:
        print("✅ Maya carregada com sucesso!")
    else:
        print("⚠️ Maya não carregou - usando fallback")
        print("💡 Instale dependências: pip install agno")
    
    print("📱 Configurando WhatsApp...")
    setup_webhook()
    
    print("🌐 API: http://localhost:5000")
    print("=" * 50)
    print("✅ INTEGRAÇÃO PRONTA!")
    print("📋 Para testar:")
    print("   1. python test_maya.py")
    print("   2. Envie mensagem no WhatsApp")
    print("=" * 50)
    
    # Iniciar servidor
    app.run(host="0.0.0.0", port=5000, debug=False)
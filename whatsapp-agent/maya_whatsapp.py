"""
🎵 MAYA + WHATSAPP - Integração Completa
Maya otimizada integrada com WhatsApp via Evolution API
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

# Importar Maya otimizada
from maya_optimized import MayaOptimized, get_maya

# Importar módulos WhatsApp
from core import WhatsAppClient
from core.agno_integration import AgnoMessageHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MayaWhatsAppBridge:
    """
    Ponte entre Maya e WhatsApp com funcionalidades especiais
    """
    
    def __init__(self):
        self.maya = get_maya()
        self.whatsapp_client = WhatsAppClient()
        self.user_sessions = {}  # Controle de sessões por usuário
        
        logger.info("🎵 Maya WhatsApp Bridge inicializada")
    
    def process_message(self, sender_number: str, message_text: str) -> bool:
        """
        Processa mensagem com Maya e envia resposta
        """
        try:
            logger.info(f"🎵 Maya processando de {sender_number}: {message_text}")
            
            # Atualizar sessão do usuário
            self._update_user_session(sender_number, message_text)
            
            # Processar com Maya
            maya_response = self.maya.run(message_text)
            
            if maya_response and maya_response.content:
                # Enviar resposta de texto
                text_sent = self.whatsapp_client.send_message(
                    sender_number, 
                    maya_response.content
                )
                
                if text_sent:
                    logger.info(f"✅ Resposta Maya enviada para {sender_number}")
                    
                    # Verificar se há áudio para enviar
                    if hasattr(maya_response, 'response_audio') and maya_response.response_audio:
                        self._handle_audio_response(sender_number, maya_response.response_audio)
                    
                    return True
                else:
                    logger.error(f"❌ Falha ao enviar resposta Maya")
                    return False
            else:
                logger.warning("⚠️ Maya não gerou resposta")
                return False
                
        except Exception as e:
            logger.error(f"💥 Erro na ponte Maya-WhatsApp: {e}")
            
            # Enviar mensagem de erro amigável
            error_message = "🎵 Desculpe, tive um probleminha técnico. Pode repetir sua mensagem?"
            self.whatsapp_client.send_message(sender_number, error_message)
            return False
    
    def _update_user_session(self, user_id: str, message: str):
        """
        Atualiza sessão do usuário
        """
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'first_contact': datetime.now().isoformat(),
                'message_count': 0,
                'last_message': None
            }
        
        self.user_sessions[user_id]['message_count'] += 1
        self.user_sessions[user_id]['last_message'] = message
        self.user_sessions[user_id]['last_contact'] = datetime.now().isoformat()
    
    def _handle_audio_response(self, sender_number: str, audio_data):
        """
        Processa resposta de áudio (futura implementação)
        """
        try:
            logger.info(f"🎵 Áudio gerado para {sender_number} ({len(audio_data.content)} bytes)")
            
            # Por enquanto, apenas salva o áudio localmente
            # No futuro, pode enviar como mensagem de áudio no WhatsApp
            audio_filename = f"tmp/maya_whatsapp_{sender_number}_{int(datetime.now().timestamp())}.wav"
            
            from agno.utils.audio import write_audio_to_file
            write_audio_to_file(
                audio=audio_data.content,
                filename=audio_filename
            )
            
            logger.info(f"💾 Áudio salvo: {audio_filename}")
            
            # Enviar notificação sobre áudio
            audio_notification = "🎵 Geriei uma resposta em áudio para você! (Em breve disponível no WhatsApp)"
            self.whatsapp_client.send_message(sender_number, audio_notification)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar áudio: {e}")
    
    def get_user_stats(self, user_id: str) -> dict:
        """
        Obtém estatísticas do usuário
        """
        return self.user_sessions.get(user_id, {})

class MayaWhatsAppHandler:
    """
    Handler especializado para Maya + WhatsApp
    """
    
    def __init__(self):
        self.bridge = MayaWhatsAppBridge()
        self.logger = logging.getLogger(__name__)
    
    def process_webhook_data(self, webhook_data: dict) -> bool:
        """
        Processa webhook com Maya
        """
        try:
            if not webhook_data or "data" not in webhook_data:
                return False
            
            # Processa cada mensagem
            for item in webhook_data["data"]:
                if self._is_valid_message(item):
                    self._handle_message_with_maya(item)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao processar webhook com Maya: {e}")
            return False
    
    def _is_valid_message(self, item: dict) -> bool:
        """
        Verifica se é mensagem válida
        """
        if "message" not in item or not item["message"]:
            return False
        
        # Ignora mensagens do próprio bot
        if item["message"].get("fromMe", False):
            return False
        
        return True
    
    def _handle_message_with_maya(self, item: dict) -> None:
        """
        Processa mensagem com Maya
        """
        try:
            sender_number = self._extract_sender_number(item)
            message_text = self._extract_message_text(item["message"])
            
            if sender_number and message_text:
                self.logger.info(f"📨 Mensagem para Maya de {sender_number}: {message_text}")
                self.bridge.process_message(sender_number, message_text)
        
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem com Maya: {e}")
    
    def _extract_sender_number(self, item: dict) -> str:
        """
        Extrai número do remetente
        """
        try:
            remote_jid = item.get("key", {}).get("remoteJid", "")
            return remote_jid.replace("@s.whatsapp.net", "") if remote_jid else None
        except:
            return None
    
    def _extract_message_text(self, message_data: dict) -> str:
        """
        Extrai texto da mensagem
        """
        try:
            text = (
                message_data.get("conversation") or
                message_data.get("extendedTextMessage", {}).get("text") or
                message_data.get("text") or
                ""
            )
            return text.strip() if text else None
        except:
            return None

# ============================================
# APLICAÇÃO FLASK
# ============================================

app = Flask(__name__)
maya_handler = MayaWhatsAppHandler()

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Webhook que processa mensagens com Maya
    """
    try:
        webhook_data = request.json
        logger.info("📨 Webhook recebido - processando com Maya")
        
        if maya_handler.process_webhook_data(webhook_data):
            return jsonify({"status": "success", "processed_by": "maya"})
        else:
            return jsonify({"status": "no_messages"})
            
    except Exception as e:
        logger.error(f"💥 Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/send", methods=["POST"])
def send_message():
    """
    Envio manual processado pela Maya
    """
    try:
        data = request.json
        number = data.get("number")
        message = data.get("message")
        
        if not number or not message:
            return jsonify({"error": "Campos 'number' e 'message' obrigatórios"}), 400
        
        # Processa com Maya
        success = maya_handler.bridge.process_message(number, message)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Mensagem processada pela Maya e enviada",
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
    Testa Maya diretamente
    """
    try:
        data = request.json
        message = data.get("message", "Olá Maya!")
        
        # Testa Maya
        maya = get_maya()
        response = maya.run(message)
        
        result = {
            "status": "success",
            "input": message,
            "maya_response": response.content if response else "Sem resposta",
            "has_audio": bool(hasattr(response, 'response_audio') and response.response_audio),
            "timestamp": datetime.now().isoformat()
        }
        
        if hasattr(response, 'response_audio') and response.response_audio:
            result["audio_size"] = len(response.response_audio.content)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/maya/stats/<user_id>", methods=["GET"])
def user_stats(user_id):
    """
    Estatísticas de um usuário
    """
    try:
        stats = maya_handler.bridge.get_user_stats(user_id)
        return jsonify({
            "user_id": user_id,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/maya/reset", methods=["POST"])
def reset_maya():
    """
    Reseta contador de áudio da Maya
    """
    try:
        maya = get_maya()
        maya.reset_counter()
        return jsonify({
            "status": "success",
            "message": "Contador de áudio resetado"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    """
    Status da integração Maya + WhatsApp
    """
    try:
        whatsapp_connected = maya_handler.bridge.whatsapp_client.is_connected()
        
        return jsonify({
            "status": "online",
            "maya": {
                "name": "Maya - HopeCann Áudio",
                "status": "ativa",
                "audio_support": True,
                "message_counter": maya_handler.bridge.maya.message_counter
            },
            "whatsapp": {
                "connected": whatsapp_connected,
                "instance": maya_handler.bridge.whatsapp_client.instance
            },
            "integration": "maya + whatsapp",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    """
    Informações da API Maya + WhatsApp
    """
    return jsonify({
        "name": "🎵 Maya + WhatsApp Integration",
        "version": "1.0.0",
        "description": "Maya HopeCann integrada com WhatsApp via Evolution API",
        "features": [
            "Agendamento de consultas",
            "Respostas com áudio inteligente",
            "Contexto de conversa",
            "Integração WhatsApp completa"
        ],
        "endpoints": {
            "webhook": "/webhook (POST) - Recebe mensagens WhatsApp",
            "send": "/send (POST) - Envia via Maya",
            "maya_test": "/maya/test (POST) - Testa Maya",
            "maya_stats": "/maya/stats/<user_id> (GET) - Stats usuário",
            "maya_reset": "/maya/reset (POST) - Reset contador áudio",
            "status": "/status (GET) - Status integração"
        },
        "como_testar": {
            "1": "POST /maya/test com {'message': 'Quero agendar consulta'}",
            "2": "POST /send com {'number': '5511999999999', 'message': 'Olá Maya'}",
            "3": "Envie mensagem no WhatsApp conectado"
        }
    })

def setup_webhook():
    """
    Configura webhook automaticamente
    """
    import requests
    
    whatsapp_client = maya_handler.bridge.whatsapp_client
    
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
            logger.info("✅ Webhook configurado para Maya!")
        else:
            logger.warning(f"⚠️ Problema no webhook: {response.text}")
    except Exception as e:
        logger.error(f"❌ Erro webhook: {e}")

if __name__ == "__main__":
    print("🎵 INICIANDO MAYA + WHATSAPP")
    print("=" * 50)
    print("🤖 Maya: Carregando...")
    
    try:
        # Inicializar Maya
        maya = get_maya()
        print("✅ Maya carregada com sucesso!")
        
        print("📱 WhatsApp: Configurando...")
        setup_webhook()
        
        print("🌐 API: http://localhost:5000")
        print("=" * 50)
        print("✅ MAYA + WHATSAPP PRONTA!")
        print("📋 Para testar:")
        print("   1. Acesse http://localhost:5000")
        print("   2. POST /maya/test para testar Maya")
        print("   3. Envie mensagem no WhatsApp")
        print("=" * 50)
        
        # Inicia servidor
        app.run(host="0.0.0.0", port=5000, debug=False)
        
    except Exception as e:
        print(f"❌ Erro ao inicializar: {e}")
        sys.exit(1)
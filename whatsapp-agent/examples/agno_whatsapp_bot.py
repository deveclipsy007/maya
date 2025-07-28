"""
Exemplo: Como integrar seu agente Agno com WhatsApp
"""
import logging
from flask import Flask, request, jsonify
from datetime import datetime

# Importa módulos da nossa estrutura
from core import WhatsAppClient
from core.agno_integration import AgnoMessageHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# AQUI VOCÊ IMPORTA E CONFIGURA SEU AGENTE AGNO
# ============================================

# Exemplo de como seria (adapte para seu caso):
class MeuAgenteAgno:
    """
    SUBSTITUA ESTA CLASSE PELO SEU AGENTE AGNO REAL
    """
    def __init__(self):
        # Configurações do seu agente
        self.name = "Assistente Agno"
        self.version = "1.0"
    
    def process(self, message: str, user_id: str = None, context: dict = None) -> str:
        """
        ADAPTE ESTE MÉTODO PARA SEU AGENTE AGNO
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário (número WhatsApp)
            context: Contexto da conversa
            
        Returns:
            str: Resposta do agente
        """
        # Exemplo de lógica - substitua pela sua
        if "preço" in message.lower():
            return f"🏷️ Para informações sobre preços, nossa equipe comercial entrará em contato!\n\nUsuário: {user_id}"
        
        elif "suporte" in message.lower():
            return f"🔧 Nosso suporte técnico está disponível 24/7!\n\nComo posso ajudar com seu problema?"
        
        elif "produto" in message.lower():
            return f"📦 Temos diversos produtos disponíveis!\n\nQue tipo de produto você procura?"
        
        else:
            return f"🤖 Olá! Sou o {self.name}.\n\nRecebi sua mensagem: '{message}'\n\nComo posso ajudar você hoje?"

# ============================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================

# Inicializa componentes
app = Flask(__name__)
whatsapp_client = WhatsAppClient()

# AQUI VOCÊ INICIALIZA SEU AGENTE AGNO REAL
# Exemplo: meu_agente = MeuFrameworkAgno.load_agent("caminho/para/agente")
meu_agente_agno = MeuAgenteAgno()

# Cria handler especializado para Agno
agno_handler = AgnoMessageHandler(meu_agente_agno, whatsapp_client)

# ============================================
# ENDPOINTS DA API
# ============================================

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Webhook que usa seu agente Agno para responder
    """
    try:
        webhook_data = request.json
        logger.info("📨 Webhook recebido - processando com Agno")
        
        # Processa com agente Agno
        if agno_handler.process_webhook_data(webhook_data):
            return jsonify({"status": "success", "processed_by": "agno"})
        else:
            return jsonify({"status": "no_messages"})
            
    except Exception as e:
        logger.error(f"💥 Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/send", methods=["POST"])
def send_message():
    """
    Envio manual - pode usar Agno ou envio direto
    """
    try:
        data = request.json
        number = data.get("number")
        message = data.get("message")
        use_agno = data.get("use_agno", False)  # Opcional: usar Agno para processar
        
        if not number or not message:
            return jsonify({"error": "Campos 'number' e 'message' obrigatórios"}), 400
        
        if use_agno:
            # Processa mensagem com Agno antes de enviar
            agno_response = meu_agente_agno.process(message, user_id=number)
            success = whatsapp_client.send_message(number, agno_response)
            response_text = agno_response
        else:
            # Envio direto
            success = whatsapp_client.send_message(number, message)
            response_text = message
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Mensagem enviada",
                "to": number,
                "text": response_text,
                "processed_by": "agno" if use_agno else "direct"
            })
        else:
            return jsonify({"status": "error", "message": "Falha no envio"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/agno/test", methods=["POST"])
def test_agno():
    """
    Endpoint para testar seu agente Agno diretamente
    """
    try:
        data = request.json
        message = data.get("message", "Olá!")
        user_id = data.get("user_id", "test_user")
        
        # Testa agente Agno
        response = meu_agente_agno.process(message, user_id=user_id)
        
        return jsonify({
            "status": "success",
            "input": message,
            "output": response,
            "agent": "agno",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    """
    Status da aplicação com informações do Agno
    """
    try:
        whatsapp_connected = whatsapp_client.is_connected()
        
        return jsonify({
            "status": "online",
            "whatsapp_connected": whatsapp_connected,
            "agno_agent": {
                "name": getattr(meu_agente_agno, 'name', 'Agno Agent'),
                "version": getattr(meu_agente_agno, 'version', '1.0'),
                "status": "active"
            },
            "instance": whatsapp_client.instance,
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
        "name": "WhatsApp + Agno Integration",
        "version": "1.0.0",
        "description": "Integração entre Framework Agno e WhatsApp via Evolution API",
        "endpoints": {
            "webhook": "/webhook (POST) - Recebe mensagens e processa com Agno",
            "send": "/send (POST) - Envia mensagens (com opção Agno)",
            "agno_test": "/agno/test (POST) - Testa agente Agno",
            "status": "/status (GET) - Status da aplicação"
        }
    })

# ============================================
# CONFIGURAÇÃO E INICIALIZAÇÃO
# ============================================

def setup_webhook():
    """
    Configura webhook na Evolution API
    """
    import requests
    
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
            logger.info("✅ Webhook configurado para Agno")
            return True
        else:
            logger.warning(f"⚠️ Falha ao configurar webhook: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao configurar webhook: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando WhatsApp + Agno Integration")
    logger.info(f"🧠 Agente Agno: {getattr(meu_agente_agno, 'name', 'Agno Agent')}")
    logger.info(f"📱 WhatsApp Instance: {whatsapp_client.instance}")
    
    # Configura webhook
    setup_webhook()
    
    logger.info("✅ Integração Agno + WhatsApp pronta!")
    logger.info("🌐 API rodando em http://localhost:5000")
    logger.info("📚 Teste o agente em: POST /agno/test")
    
    # Inicia servidor
    app.run(host="0.0.0.0", port=5000, debug=False)
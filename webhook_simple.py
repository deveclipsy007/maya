#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook simplificado para Evolution API com resposta automática
Integra seus scripts funcionais (texto.py, imagem.py, enquete.py) diretamente
"""
import os
import json
import time
import requests
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify
import logging

# Importar agente IA
try:
    from agents.agent_whatsapp.agent_whatsapp.ai_whatsapp_agent import AIWhatsAppAgent
    from agents.agno_core.agno_core.interfaces import AgnoInput, MessageType, EventType
    AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Agente IA não disponível: {e}")
    AI_AVAILABLE = False

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações da Evolution API (baseadas nos seus scripts)
EVOLUTION_URL = "http://localhost:8080"
API_KEY = "1234"
INSTANCE_NAME = "agente_bot"

# Headers padrão (dos seus scripts)
HEADERS = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

# Pasta para salvar mensagens
MESSAGES_FOLDER = "mensagens_recebidas"
os.makedirs(MESSAGES_FOLDER, exist_ok=True)

# Inicializar agente IA
ai_agent = None
if AI_AVAILABLE:
    try:
        ai_agent = AIWhatsAppAgent()
        asyncio.create_task(ai_agent.initialize())
        logger.info("🤖 Agente IA inicializado com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar agente IA: {e}")
        ai_agent = None

def send_text_message(number, text):
    """
    Envia mensagem de texto - baseado no seu texto.py
    """
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
    
    payload = {
        "number": number,
        "textMessage": {"text": text}
    }
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)
        logger.info(f"Mensagem enviada para {number}: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {str(e)}")
        return False

def send_poll_message(number, poll_name, options):
    """
    Envia enquete - baseado no seu enquete.py
    """
    url = f"{EVOLUTION_URL}/message/sendPoll/{INSTANCE_NAME}"
    
    payload = {
        "number": number,
        "options": {
            "delay": 123,
            "presence": "composing"
        },
        "pollMessage": {
            "name": poll_name,
            "selectableCount": 1,
            "values": options
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)
        logger.info(f"Enquete enviada para {number}: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Erro ao enviar enquete: {str(e)}")
        return False

async def generate_ai_response(text_content, from_number):
    """
    Gera resposta usando IA quando disponível
    """
    if ai_agent and AI_AVAILABLE:
        try:
            # Criar input para o agente IA
            agno_input = AgnoInput(
                instance_name="agente_bot",
                event_type=EventType.MESSAGES_UPSERT,
                message_type=MessageType.TEXT,
                from_number=from_number,
                to_number="agente_bot",
                message_id=f"webhook_{int(time.time())}",
                timestamp=int(time.time()),
                text_content=text_content,
                is_from_me=False
            )
            
            # Processar com IA
            if await ai_agent.can_handle(agno_input):
                output = await ai_agent.run(agno_input)
                logger.info("🧠 Resposta gerada com IA!")
                return output.text_content
        except Exception as e:
            logger.error(f"Erro na IA: {e}")
    
    # Fallback para resposta simples
    return generate_simple_response(text_content)

def generate_simple_response(text_content):
    """
    Gera resposta simples quando IA não está disponível
    """
    text_lower = text_content.lower().strip()
    
    # Comandos de enquete
    if any(cmd in text_lower for cmd in ["/enquete", "/poll", "criar enquete"]):
        return handle_poll_command(text_content)
    
    # Saudações
    elif any(greeting in text_lower for greeting in ["oi", "olá", "ola", "hey", "hello", "bom dia", "boa tarde", "boa noite"]):
        return "Olá! Como posso ajudá-lo hoje? 😊\n\nDigite 'ajuda' para ver o que posso fazer!"
    
    # Despedidas
    elif any(bye in text_lower for bye in ["tchau", "bye", "até logo", "falou", "até mais"]):
        return "Até logo! Foi um prazer conversar com você! 👋\n\nVolte sempre que precisar!"
    
    # Agradecimentos
    elif any(thanks in text_lower for thanks in ["obrigado", "obrigada", "valeu", "thanks", "brigado"]):
        return "De nada! Fico feliz em ajudar! 🙂\n\nPrecisa de mais alguma coisa?"
    
    # Ajuda
    elif any(help_cmd in text_lower for help_cmd in ["ajuda", "help", "menu", "comandos"]):
        return """🤖 *Agno WhatsApp Assistant*

Posso ajudá-lo com:

📝 *Conversas gerais*
• Respondo perguntas
• Converso sobre diversos assuntos
• Dou informações úteis

📊 *Enquetes e pesquisas*
• `/enquete Pergunta? Opção1, Opção2, Opção3`
• Exemplo: `/enquete Qual sua cor favorita? Azul, Verde, Vermelho`

🆘 *Comandos úteis*
• `ajuda` - Este menu
• `sobre` - Informações sobre mim
• `status` - Status do sistema

Digite qualquer coisa e vamos conversar! 💬"""
    
    # Sobre o bot
    elif any(about in text_lower for about in ["sobre", "quem é você", "o que é você", "bot"]):
        return """🤖 *Sobre o Agno Assistant*

Sou um assistente inteligente para WhatsApp!

✨ *Características:*
• Sistema modular e escalável
• Respostas inteligentes
• Criação de enquetes
• Integração com Evolution API

🔧 *Tecnologia:*
• Python + Flask
• Arquitetura modular
• Processamento em tempo real

Desenvolvido com ❤️ para facilitar sua comunicação!"""
    
    # Como está
    elif any(how in text_lower for how in ["como você está", "como vai", "tudo bem"]):
        return "Estou funcionando perfeitamente! 🚀\n\nTodos os sistemas operacionais e pronto para ajudar. E você, como está?"
    
    # Status do sistema
    elif "status" in text_lower:
        return """📊 *Status do Sistema*

🟢 Webhook: Online
🟢 Evolution API: Conectada
🟢 Agentes: Ativos
🟢 Processamento: Normal

⚡ Tempo de resposta: < 1s
📈 Mensagens processadas hoje: Funcionando!

Sistema 100% operacional! ✅"""
    
    # Resposta padrão inteligente
    else:
        return f"Interessante! Você disse: '{text_content[:100]}{'...' if len(text_content) > 100 else ''}'\n\n🤔 Posso ajudá-lo com mais alguma coisa?\n\nDigite 'ajuda' para ver minhas funcionalidades!"

def handle_poll_command(text):
    """
    Processa comando de enquete
    """
    # Remover comando inicial
    text_clean = text.lower()
    for cmd in ["/enquete", "/poll", "criar enquete"]:
        if cmd in text_clean:
            text = text_clean.replace(cmd, "").strip()
            break
    
    if not text:
        return """📊 *Como criar enquetes:*

*Formato:*
`/enquete Pergunta? Opção1, Opção2, Opção3`

*Exemplos:*
• `/enquete Qual sua cor favorita? Azul, Verde, Vermelho`
• `/enquete Você gosta de pizza? Sim, Não, Talvez`
• `/enquete Melhor horário para reunião? Manhã, Tarde, Noite`

💡 *Dica:* Use vírgulas para separar as opções!"""
    
    # Tentar extrair pergunta e opções
    if "?" in text:
        parts = text.split("?", 1)
        question = parts[0].strip() + "?"
        
        if len(parts) > 1 and parts[1].strip():
            options_text = parts[1].strip()
            options = [opt.strip() for opt in options_text.split(",") if opt.strip()]
            
            if len(options) >= 2:
                return {
                    "type": "poll",
                    "question": question,
                    "options": options
                }
    
    # Se chegou aqui, formato inválido
    return """❌ *Formato de enquete inválido*

Use o formato correto:
`/enquete Pergunta? Opção1, Opção2, Opção3`

Exemplo:
`/enquete Qual sua cor favorita? Azul, Verde, Vermelho`"""

async def process_webhook_message(webhook_data):
    """
    Processa mensagem do webhook e envia resposta automática com IA
    """
    try:
        # Extrair dados da mensagem
        event_type = webhook_data.get('event', '')
        data = webhook_data.get('data', {})
        
        # Processar apenas mensagens recebidas
        if event_type != 'messages.upsert':
            return False
        
        key = data.get('key', {})
        message = data.get('message', {})
        
        # Ignorar mensagens próprias
        if key.get('fromMe', False):
            logger.info("Ignorando mensagem própria")
            return False
        
        # Extrair número do remetente
        remote_jid = key.get('remoteJid', '')
        from_number = remote_jid.replace('@s.whatsapp.net', '').replace('@g.us', '')
        
        # Extrair conteúdo da mensagem
        text_content = None
        if 'conversation' in message:
            text_content = message['conversation']
        elif 'extendedTextMessage' in message:
            text_content = message['extendedTextMessage'].get('text', '')
        
        if not text_content:
            logger.info("Mensagem sem conteúdo de texto")
            return False
        
        logger.info(f"Processando mensagem de {from_number}: {text_content[:50]}...")
        
        # Gerar resposta com IA
        response = await generate_ai_response(text_content, from_number)
        
        # Verificar se é enquete
        if isinstance(response, dict) and response.get('type') == 'poll':
            # Enviar enquete
            success = send_poll_message(
                from_number, 
                response['question'], 
                response['options']
            )
            if success:
                logger.info(f"Enquete enviada para {from_number}")
            return success
        else:
            # Enviar mensagem de texto
            success = send_text_message(from_number, response)
            if success:
                logger.info(f"Resposta enviada para {from_number}: {response[:50]}...")
            return success
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        return False

@app.route("/", methods=["GET"])
def index():
    """Endpoint raiz"""
    return jsonify({
        "status": "online",
        "message": "Agno WhatsApp Webhook está funcionando!",
        "version": "2.0.0 - Simplificado",
        "features": ["Resposta automática", "Enquetes", "Conversação inteligente"]
    })

@app.route("/webhook", methods=["POST"])
@app.route("/webhook/messages-upsert", methods=["POST"])
def webhook():
    """Endpoint principal do webhook - aceita /webhook e /webhook/messages-upsert"""
    try:
        # Log da requisição
        endpoint = request.endpoint or request.path
        logger.info(f"Webhook recebido em: {endpoint}")
        
        # Obter dados
        data = None
        if request.is_json:
            data = request.json
        else:
            try:
                data = json.loads(request.data)
            except:
                data = None
        
        if not data:
            logger.warning("Webhook sem dados válidos")
            return jsonify({"status": "warning", "message": "No valid data"})
        
        # Salvar mensagem
        timestamp = int(time.time())
        filename = f"{MESSAGES_FOLDER}/{timestamp}_webhook.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Processar e responder automaticamente
        try:
            response_sent = asyncio.run(process_webhook_message(data))
            if response_sent:
                logger.info("✅ Resposta automática enviada com sucesso!")
            else:
                logger.info("ℹ️ Mensagem processada, mas sem resposta necessária")
        except Exception as e:
            logger.error(f"Erro no processamento automático: {str(e)}")
        
        return jsonify({"status": "success", "message": "Webhook processed"})
        
    except Exception as e:
        logger.error(f"Erro crítico no webhook: {str(e)}")
        return jsonify({"status": "error", "message": "Internal error"})

@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "evolution_api": EVOLUTION_URL,
        "instance": INSTANCE_NAME
    })

@app.route("/mensagens", methods=["GET"])
def mensagens():
    """Lista mensagens recentes"""
    try:
        files = []
        for filename in os.listdir(MESSAGES_FOLDER):
            if filename.endswith('.json'):
                filepath = os.path.join(MESSAGES_FOLDER, filename)
                files.append({
                    "filename": filename,
                    "size": os.path.getsize(filepath),
                    "modified": os.path.getmtime(filepath)
                })
        
        # Ordenar por data de modificação (mais recente primeiro)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            "status": "success",
            "total": len(files),
            "messages": files[:10]  # Últimas 10
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

if __name__ == "__main__":
    print("🚀 Iniciando Agno WhatsApp Webhook Simplificado...")
    print(f"📡 Evolution API: {EVOLUTION_URL}")
    print(f"🤖 Instância: {INSTANCE_NAME}")
    print("💬 Resposta automática: ATIVADA")
    print("="*50)
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

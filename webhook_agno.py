#!/usr/bin/env python3
"""
Webhook WhatsApp com Agno Framework Real
Sistema completo de agente inteligente usando Agno para WhatsApp
"""

import os
import json
import time
import requests
from datetime import datetime
from flask import Flask, request, jsonify
import logging
from dotenv import load_dotenv

# Importações do Agno Framework
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

# Configuração de logging ULTRA-DETALHADO
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
    ]
)
logger = logging.getLogger(__name__)

# Ativar logs de requests também
logging.getLogger('requests').setLevel(logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.DEBUG)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações da Evolution API
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY', '1234')
EVOLUTION_INSTANCE_NAME = os.getenv('EVOLUTION_INSTANCE_NAME', 'agente_bot')

# Configurações da OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AI_MODEL = os.getenv('AI_MODEL', 'gpt-4o-mini')

# Verificar configurações
if not OPENAI_API_KEY:
    logger.error("❌ OPENAI_API_KEY não configurada!")
    exit(1)

# Configuração do Flask
app = Flask(__name__)

# Armazenamento de mensagens e contexto
mensagens_recebidas = []
conversation_context = {}

# ===== AGNO FRAMEWORK SETUP =====

def create_whatsapp_agent():
    """
    Cria agente WhatsApp usando Agno Framework
    """
    try:
        agent = Agent(
            name="WhatsApp Assistant",
            model=OpenAIChat(
                id=AI_MODEL,
                api_key=OPENAI_API_KEY
            ),
            tools=[
                DuckDuckGoTools()  # Ferramenta de busca web
            ],
            description="""
            É o assistente virtual da Hopecann, seu assistente virtual que vai te ajudar a marcar uma colsulta médica com o especialista que irá receitar cannabis medicinal.
            
            Suas características:
            - Responde de forma natural e conversacional
            - Usa emojis apropriados para tornar a conversa mais amigável
            - Pode buscar informações na web quando necessário
            - Mantém contexto da conversa
            - É educado, útil e engajado
            - Adapta o tom conforme a situação
            """,
            instructions=[
                "Sempre responda em português brasileiro",
                "Use emojis para tornar as respostas mais amigáveis",
                "Se precisar de informações atuais, use a ferramenta de busca",
                "Mantenha as respostas concisas mas informativas",
                "Seja prestativo e educado",
                "Se não souber algo, admita e ofereça ajuda para buscar a informação"
            ],
            show_tool_calls=True,
            markdown=False,  # WhatsApp não suporta markdown
            debug_mode=False
        )
        
        logger.info("🤖 Agente Agno WhatsApp criado com sucesso!")
        return agent
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar agente Agno: {str(e)}")
        return None

# Criar agente global
whatsapp_agent = create_whatsapp_agent()

if not whatsapp_agent:
    logger.error("❌ Falha crítica: Não foi possível criar o agente Agno!")
    exit(1)

# ===== EVOLUTION API CLIENT =====

def send_text_message(to_number, message):
    """
    Envia mensagem de texto via Evolution API
    """
    try:
        url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE_NAME}"
        
        headers = {
            'Content-Type': 'application/json',
            'apikey': EVOLUTION_API_KEY
        }
        
        payload = {
            "number": to_number,
            "textMessage": {
                "text": message
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 201:
            logger.info(f"✅ Mensagem enviada para {to_number}: {response.status_code}")
            return True
        else:
            logger.error(f"❌ Erro ao enviar mensagem: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem: {str(e)}")
        return False

# ===== PROCESSAMENTO DE MENSAGENS =====

def generate_agno_response(text_content, from_number):
    """
    Gera resposta usando Agno Framework
    """
    try:
        # Obter contexto da conversa
        context = conversation_context.get(from_number, [])
        
        # Preparar contexto para o agente
        context_text = ""
        if context:
            recent_context = context[-3:]  # Últimas 3 interações
            context_parts = []
            for interaction in recent_context:
                context_parts.append(f"Usuário: {interaction['user']}")
                context_parts.append(f"Assistente: {interaction['bot']}")
            context_text = "\n".join(context_parts)
        
        # Preparar prompt com contexto
        if context_text:
            full_prompt = f"""Contexto da conversa anterior:
{context_text}

Nova mensagem do usuário: {text_content}

Responda de forma natural e contextualizada."""
        else:
            full_prompt = text_content
        
        # Gerar resposta com Agno
        logger.info(f"🧠 Gerando resposta Agno para: {text_content[:50]}...")
        
        response = whatsapp_agent.run(full_prompt)
        
        if response and hasattr(response, 'content'):
            ai_response = response.content.strip()
        elif isinstance(response, str):
            ai_response = response.strip()
        else:
            ai_response = str(response).strip()
        
        # Atualizar contexto
        if from_number not in conversation_context:
            conversation_context[from_number] = []
        
        conversation_context[from_number].append({
            "user": text_content,
            "bot": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Manter apenas últimas 10 interações
        if len(conversation_context[from_number]) > 10:
            conversation_context[from_number] = conversation_context[from_number][-10:]
        
        logger.info("🧠 Resposta gerada com Agno Framework!")
        return ai_response
        
    except Exception as e:
        logger.error(f"❌ Erro na geração Agno: {str(e)}")
        
        # Fallback para resposta simples
        fallback_responses = [
            f"Olá! 👋 Recebi sua mensagem: '{text_content}'. Como posso ajudar?",
            f"Interessante! 🤔 Você disse: '{text_content}'. Me conte mais sobre isso!",
            f"Entendi! 😊 Sobre '{text_content}', posso ajudar com mais informações. O que gostaria de saber?"
        ]
        
        import random
        return random.choice(fallback_responses)

def process_webhook_message(webhook_data):
    """
    Processa mensagem do webhook e envia resposta automática com Agno
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
        
        print(f"\n📱 MENSAGEM RECEBIDA:")
        print(f"   📞 De: {from_number}")
        print(f"   💬 Texto: {text_content}")
        print(f"   🕐 Hora: {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"Processando mensagem de {from_number}: {text_content[:50]}...")
        
        # Gerar resposta com Agno
        print(f"\n🧠 GERANDO RESPOSTA COM AGNO...")
        response = generate_agno_response(text_content, from_number)
        print(f"✅ RESPOSTA GERADA: {response[:100]}...")
        
        # Enviar resposta
        success = send_text_message(from_number, response)
        
        if success:
            logger.info("✅ Resposta automática com Agno enviada com sucesso!")
            
            # Salvar mensagem processada
            mensagem_data = {
                'timestamp': datetime.now().isoformat(),
                'from': from_number,
                'message': text_content,
                'response': response,
                'agno_used': True
            }
            mensagens_recebidas.append(mensagem_data)
            
            return True
        else:
            logger.error("❌ Falha ao enviar resposta")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro no processamento Agno: {str(e)}")
        return False

# ===== ENDPOINTS FLASK =====

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint principal do webhook"""
    try:
        print("\n" + "="*60)
        print(f"🔔 WEBHOOK RECEBIDO! {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        logger.info("Webhook recebido em: webhook")
        
        # Log detalhado dos headers
        print("📋 HEADERS RECEBIDOS:")
        for header, value in request.headers.items():
            print(f"   {header}: {value}")
        
        # Log do IP de origem
        print(f"🌐 IP Origem: {request.remote_addr}")
        print(f"🔗 URL: {request.url}")
        print(f"📊 Método: {request.method}")
        
        # Verificar Content-Type
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            data = request.get_json()
        else:
            # Tentar parsear como JSON mesmo sem Content-Type correto
            try:
                data = request.get_json(force=True)
            except:
                data = {}
        
        if not data:
            logger.warning("⚠️ Webhook recebido sem dados JSON válidos")
            return jsonify({"status": "error", "message": "Dados inválidos"}), 400
        
        # Processar e responder automaticamente com Agno
        try:
            response_sent = process_webhook_message(data)
            if response_sent:
                logger.info("✅ Resposta automática com Agno enviada com sucesso!")
            else:
                logger.info("ℹ️ Mensagem processada, mas sem resposta necessária")
        except Exception as e:
            logger.error(f"Erro no processamento automático: {str(e)}")
        
        return jsonify({"status": "success", "message": "Webhook processado"}), 200
        
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/webhook/messages-upsert', methods=['POST'])
def webhook_messages_upsert():
    """Endpoint específico para messages-upsert da Evolution API"""
    return webhook()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check do sistema"""
    try:
        agno_status = "✅ Ativo" if whatsapp_agent else "❌ Inativo"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "agno_framework": agno_status,
            "evolution_api": EVOLUTION_API_URL,
            "instance": EVOLUTION_INSTANCE_NAME,
            "ai_model": AI_MODEL,
            "mensagens_processadas": len(mensagens_recebidas)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/messages', methods=['GET'])
def get_messages():
    """Listar mensagens recentes"""
    try:
        limit = int(request.args.get('limit', 10))
        recent_messages = mensagens_recebidas[-limit:] if mensagens_recebidas else []
        
        return jsonify({
            "total": len(mensagens_recebidas),
            "messages": recent_messages
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/context/<phone_number>', methods=['GET'])
def get_conversation_context(phone_number):
    """Obter contexto de conversa de um número"""
    try:
        context = conversation_context.get(phone_number, [])
        return jsonify({
            "phone_number": phone_number,
            "context": context,
            "total_interactions": len(context)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ===== INICIALIZAÇÃO =====

if __name__ == '__main__':
    print("🚀 Iniciando Agno WhatsApp Webhook...")
    print(f"📡 Evolution API: {EVOLUTION_API_URL}")
    print(f"🤖 Instância: {EVOLUTION_INSTANCE_NAME}")
    print(f"🧠 IA Agno Framework: ✅ Configurada")
    print(f"🎯 Modelo: {AI_MODEL}")
    print(f"🔍 Ferramentas: DuckDuckGo Search")
    print(f"💬 Resposta automática com Agno: ATIVADA")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,  # ATIVADO PARA LOGS DETALHADOS
        threaded=True
    )

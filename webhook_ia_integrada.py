#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook com IA integrada diretamente
Solução simples e funcional para resposta automática com OpenAI
"""
import os
import json
import time
import requests
import asyncio
import httpx
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from flask import Flask, request, jsonify
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações da Evolution API
EVOLUTION_URL = "http://localhost:8080"
API_KEY = "1234"
INSTANCE_NAME = "agente_bot"

# Configurações de IA
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gpt-3.5-turbo")

# Headers padrão
HEADERS = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

# Pasta para salvar mensagens
MESSAGES_FOLDER = "mensagens_recebidas"
os.makedirs(MESSAGES_FOLDER, exist_ok=True)

# Cliente HTTP para IA
http_client = None

# Contexto de conversas
conversation_context = {}

# Personalidade do agente IA
SYSTEM_PROMPT = """Você é um assistente inteligente para WhatsApp chamado Agno.

PERSONALIDADE:
- Amigável, prestativo e conversacional
- Responde em português brasileiro
- Usa emojis apropriados
- Mantém conversas naturais
- É conciso mas informativo

CAPACIDADES:
- Conversar sobre qualquer assunto
- Responder perguntas
- Dar conselhos e sugestões
- Ajudar com tarefas
- Criar enquetes (quando solicitado)

LIMITAÇÕES:
- Não pode acessar internet em tempo real
- Não pode fazer ligações ou enviar SMS
- Não pode acessar dados pessoais sem permissão

ESTILO DE RESPOSTA:
- Máximo 2000 caracteres
- Use quebras de linha para organizar
- Seja direto mas amigável
- Adapte o tom à conversa"""

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

def call_openai_api(messages):
    """
    Chama API da OpenAI para gerar resposta inteligente (versão síncrona)
    """
    if not OPENAI_API_KEY:
        raise Exception("Chave OpenAI não configurada")
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.7,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"Erro na chamada OpenAI: {str(e)}")
        raise

def generate_ai_response(text_content, from_number):
    """
    Gera resposta usando IA OpenAI (versão síncrona)
    """
    try:
        # Obter contexto da conversa
        context = conversation_context.get(from_number, [])
        
        # Preparar mensagens para IA
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Adicionar histórico (últimas 5 interações)
        for interaction in context[-5:]:
            messages.append({"role": "user", "content": interaction["user"]})
            messages.append({"role": "assistant", "content": interaction["bot"]})
        
        # Adicionar mensagem atual
        messages.append({"role": "user", "content": text_content})
        
        # Chamar OpenAI
        ai_response = call_openai_api(messages)
        
        # Atualizar contexto
        if from_number not in conversation_context:
            conversation_context[from_number] = []
        
        conversation_context[from_number].append({
            "user": text_content,
            "bot": ai_response,
            "timestamp": time.time()
        })
        
        # Manter apenas últimas 10 interações
        if len(conversation_context[from_number]) > 10:
            conversation_context[from_number].pop(0)
        
        logger.info("🧠 Resposta gerada com IA OpenAI!")
        return ai_response
        
    except Exception as e:
        logger.error(f"Erro na IA: {str(e)}")
        # Fallback para resposta simples
        return generate_fallback_response(text_content)

def generate_fallback_response(text_content):
    """
    Resposta de fallback quando IA não está disponível
    """
    text_lower = text_content.lower().strip()
    
    if any(greeting in text_lower for greeting in ["oi", "olá", "ola", "hey", "hello", "bom dia", "boa tarde", "boa noite"]):
        return "Olá! 👋 Como posso ajudá-lo hoje?\n\n💡 *Dica:* Configure OPENAI_API_KEY para respostas com IA!"
    
    elif any(thanks in text_lower for thanks in ["obrigado", "obrigada", "valeu", "thanks", "brigado"]):
        return "De nada! 😊 Fico feliz em ajudar!\n\nPrecisa de mais alguma coisa?"
    
    elif any(bye in text_lower for bye in ["tchau", "bye", "até logo", "falou", "até mais"]):
        return "Até logo! 👋 Foi um prazer conversar com você!\n\nVolte sempre que precisar! 😊"
    
    elif "como você está" in text_lower or "como vai" in text_lower:
        return "Estou funcionando perfeitamente! 🚀\n\nTodos os sistemas operacionais e pronto para ajudar. E você, como está?"
    
    elif any(help_cmd in text_lower for help_cmd in ["ajuda", "help", "menu", "comandos"]):
        ai_status = "🟢 Configurada" if OPENAI_API_KEY else "🟡 Não configurada"
        return f"""🤖 *Agno AI Assistant*

*Funcionalidades:*

💬 *Conversação Inteligente*
• Respondo perguntas com IA
• Converso sobre diversos assuntos
• Dou conselhos e sugestões

🧠 *Status da IA:* {ai_status}
• Modelo: {AI_MODEL}
• OpenAI: {'✅' if OPENAI_API_KEY else '❌'}

📊 *Comandos:*
• `ajuda` - Este menu
• `sobre` - Informações do sistema
• `status` - Status da IA

Digite qualquer coisa e vamos conversar! 🚀"""
    
    elif "sobre" in text_lower:
        return """🤖 *Sobre o Agno AI Assistant*

Sou um assistente inteligente para WhatsApp!

✨ *Características:*
• IA conversacional com OpenAI
• Memória de conversas
• Respostas contextuais
• Processamento em tempo real

🧠 *Tecnologia:*
• GPT-3.5/GPT-4 (OpenAI)
• Python assíncrono
• Integração Evolution API

Desenvolvido para ser seu assistente pessoal! 💪"""
    
    elif "status" in text_lower:
        ai_status = "🟢 Online" if OPENAI_API_KEY else "🟡 Offline"
        return f"""📊 *Status do Sistema*

🤖 *Agente:* Online
🧠 *IA OpenAI:* {ai_status}
📡 *Webhook:* Conectado
⚡ *Processamento:* Tempo real

🔧 *Configuração:*
• Modelo: {AI_MODEL}
• Chave OpenAI: {'✅' if OPENAI_API_KEY else '❌'}

💬 *Conversas Ativas:* {len(conversation_context)}

Sistema operacional! 🚀"""
    
    else:
        return f"""🤔 Interessante! Você disse: "{text_content[:150]}{'...' if len(text_content) > 150 else ''}"

💡 *Para respostas com IA:*
Configure OPENAI_API_KEY no arquivo .env

Enquanto isso, posso ajudá-lo com:
• Conversas básicas
• Informações sobre o sistema
• Comandos especiais

Digite 'ajuda' para ver todas as opções! 😊"""

def process_webhook_message(webhook_data):
    """
    Processa mensagem do webhook e envia resposta automática com IA (versão síncrona)
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
        message_type = ""
        
        # Verificar se é uma mensagem de texto normal
        if 'conversation' in message:
            text_content = message['conversation']
            message_type = "texto"
        elif 'extendedTextMessage' in message:
            text_content = message['extendedTextMessage'].get('text', '')
            message_type = "texto_estendido"
        
        # Verificar se é áudio com transcrição automática (speechToText)
        elif 'audioMessage' in message:
            # Verificar se temos a transcrição via speechToText
            if 'speechToText' in message:
                text_content = message['speechToText']
                message_type = "audio_transcrito"
                logger.info(f"🎤 Áudio transcrito automaticamente pela Evolution API: {text_content[:50]}...")
        
        if not text_content:
            logger.info("Mensagem sem conteúdo de texto ou transcrição")
            return False
        
        logger.info(f"Processando mensagem de {from_number}: {text_content[:50]}...")
        
        # Gerar resposta com IA
        response = generate_ai_response(text_content, from_number)
        
        # Enviar resposta
        success = send_text_message(from_number, response)
        
        if success:
            logger.info(f"✅ Resposta enviada para {from_number}")
        
        return success
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        return False

@app.route("/", methods=["GET"])
def index():
    """Endpoint raiz"""
    ai_status = "Configurada" if OPENAI_API_KEY else "Não configurada"
    return jsonify({
        "status": "online",
        "message": "Agno WhatsApp Webhook com IA integrada!",
        "version": "3.0.0 - IA Integrada",
        "features": ["Resposta automática", "IA OpenAI", "Conversação inteligente"],
        "ai_status": ai_status,
        "model": AI_MODEL
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
        
        # Processar e responder automaticamente com IA
        try:
            response_sent = process_webhook_message(data)
            if response_sent:
                logger.info("✅ Resposta automática com IA enviada com sucesso!")
            else:
                logger.info("ℹ️ Mensagem processada, mas sem resposta necessária")
        except Exception as e:
            logger.error(f"Erro no processamento automático: {str(e)}")
        
        return jsonify({"status": "success", "message": "Webhook processed with AI"})
        
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
        "instance": INSTANCE_NAME,
        "ai_configured": bool(OPENAI_API_KEY),
        "ai_model": AI_MODEL
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
    print("🚀 Iniciando Agno WhatsApp Webhook com IA Integrada...")
    print(f"📡 Evolution API: {EVOLUTION_URL}")
    print(f"🤖 Instância: {INSTANCE_NAME}")
    print(f"🧠 IA OpenAI: {'✅ Configurada' if OPENAI_API_KEY else '❌ Não configurada'}")
    print(f"🎯 Modelo: {AI_MODEL}")
    print("💬 Resposta automática com IA: ATIVADA")
    print("="*50)
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

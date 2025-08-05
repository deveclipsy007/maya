#!/usr/bin/env python3
"""
Script para configurar o agente OpenAI na Evolution API para a Maya HopeCann
"""

import os
import json
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Variáveis de configuração
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8090')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY', '1234')  # Valor padrão conforme docker-compose
EVOLUTION_INSTANCE = os.getenv('EVOLUTION_INSTANCE_NAME', 'agente_bot')  # Nome da instância conforme .env
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Verificar se as credenciais estão presentes
if not OPENAI_API_KEY:
    print("⚠️ Chave OpenAI não encontrada! Defina a variável OPENAI_API_KEY no arquivo .env")
    exit(1)

print(f"🚀 Configurando agente OpenAI para Maya HopeCann na Evolution API ({EVOLUTION_API_URL})")

def create_openai_credentials():
    """Cria credenciais OpenAI na Evolution API"""
    
    url = f"{EVOLUTION_API_URL}/openai/credentials/{EVOLUTION_INSTANCE}"
    headers = {
        'Content-Type': 'application/json',
        'apikey': EVOLUTION_API_KEY
    }
    
    payload = {
        "id": "maya_hopecann",
        "name": "Maya HopeCann Credentials",
        "apiKey": OPENAI_API_KEY,
        "organization": "",
        "model": "gpt-4o",
        "maxTokens": 2000,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        creds_id = response.json().get('credentials', {}).get('id')
        if creds_id:
            print(f"✅ Credenciais OpenAI criadas com sucesso! ID: {creds_id}")
            return creds_id
        else:
            print(f"⚠️ Resposta sem ID de credencial: {response.text}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao criar credenciais OpenAI: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Detalhes: {e.response.text}")
        return None

def create_maya_bot(creds_id):
    """Cria o bot da Maya HopeCann usando as credenciais OpenAI"""
    
    if not creds_id:
        print("❌ Não foi possível criar o bot sem credenciais OpenAI válidas")
        return False
    
    url = f"{EVOLUTION_API_URL}/openai/create/{EVOLUTION_INSTANCE}"
    headers = {
        'Content-Type': 'application/json',
        'apikey': EVOLUTION_API_KEY
    }
    
    # Configuração da Maya HopeCann como um chatbot GPT-4o
    payload = {
        "enabled": True,
        "openaiCredsId": creds_id,
        "botType": "chatCompletion",
        "model": "gpt-4o",
        "systemMessages": [
            "Você é Maya, a assistente virtual da clínica HopeCann especializada em cannabis medicinal.",
            "Seu papel é auxiliar pacientes, fornecendo informações básicas sobre cannabis medicinal, produtos disponíveis e agendamento de consultas.",
            "Mantenha um tom amigável, profissional e empático, evitando repetir sua apresentação em cada mensagem.",
            "Seja concisa e direta em suas respostas, personalizando-as com o nome do paciente quando disponível.",
            "Ao receber pedidos de agendamento, consulte os horários disponíveis no sistema e ajude o paciente a marcar uma consulta.",
            "Você pode transcrever áudios enviados pelo paciente para entender melhor suas necessidades.",
            "Mantenha a confidencialidade das informações dos pacientes e explique que detalhes médicos específicos devem ser tratados durante a consulta."
        ],
        "assistantMessages": [
            "Olá! Sou a Maya, assistente virtual da clínica HopeCann. Como posso ajudar você hoje?"
        ],
        "userMessages": [
            "Quero marcar uma consulta",
            "Preciso de informações sobre cannabis medicinal",
            "Como funciona o tratamento?"
        ],
        "maxTokens": 2000,
        "triggerType": "all",
        "triggerOperator": "none",
        "triggerValue": "",
        "expire": 60,
        "keywordFinish": "#fim",
        "delayMessage": 1500,
        "unknownMessage": "Desculpe, não entendi sua solicitação. Poderia explicar de outra forma?",
        "listeningFromMe": False,
        "stopBotFromMe": False,
        "keepOpen": True,
        "debounceTime": 3,
        "ignoreJids": []
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        print("✅ Bot da Maya HopeCann criado com sucesso!")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao criar bot da Maya: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Detalhes: {e.response.text}")
        return False

def configure_webhook_speech_to_text(creds_id):
    """Configura webhook com speechToText ativado"""
    
    url = f"{EVOLUTION_API_URL}/openai/settings/{EVOLUTION_INSTANCE}"
    headers = {
        'Content-Type': 'application/json',
        'apikey': EVOLUTION_API_KEY
    }
    
    payload = {
        "openaiCredsId": creds_id,
        "expire": 60,
        "keywordFinish": "#fim",
        "delayMessage": 1500,
        "unknownMessage": "Desculpe, não entendi. Poderia repetir?",
        "listeningFromMe": False,
        "stopBotFromMe": False,
        "keepOpen": True,
        "debounceTime": 3,
        "ignoreJids": [],
        "openaiIdFallback": creds_id,
        "speechToText": True  # Ativar transcrição automática de áudio
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        print("✅ Configuração de webhook com speechToText ativada!")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao configurar webhook: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Detalhes: {e.response.text}")
        return False

def main():
    """Função principal"""
    
    print("\n📋 PASSO 1: Criando credenciais OpenAI...")
    creds_id = create_openai_credentials()
    
    if not creds_id:
        print("❌ Não foi possível prosseguir sem credenciais OpenAI")
        return
    
    print("\n📋 PASSO 2: Criando bot da Maya HopeCann...")
    bot_success = create_maya_bot(creds_id)
    
    if not bot_success:
        print("❌ Falha ao criar bot da Maya HopeCann")
        return
    
    print("\n📋 PASSO 3: Configurando webhook com speechToText...")
    webhook_success = configure_webhook_speech_to_text(creds_id)
    
    if not webhook_success:
        print("❌ Falha ao configurar webhook com speechToText")
        return
    
    print("\n🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
    print("A Maya HopeCann está agora pronta para atender com transcrição automática de áudio!")
    print("\nPróximos passos:")
    print("1. Certifique-se de que o webhook da Evolution API aponta para seu servidor")
    print("2. Verifique se a instância da Maya está conectada no WhatsApp")
    print("3. Teste enviando uma mensagem ou áudio para o número configurado")

if __name__ == "__main__":
    main()

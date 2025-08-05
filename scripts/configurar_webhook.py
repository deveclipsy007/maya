#!/usr/bin/env python3
"""
Script para configurar o webhook na Evolution API
Este é provavelmente o motivo do agente não estar respondendo!
"""
import requests
import json

def configure_webhook():
    """Configura o webhook na Evolution API"""
    print("🔧 CONFIGURANDO WEBHOOK NA EVOLUTION API")
    print("=" * 50)
    
    # Configurações
    evolution_url = "http://localhost:8080"
    api_key = "1234"
    instance_name = "agente_bot"
    webhook_url = "http://localhost:5000/webhook"
    
    # Headers
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }
    
    # Dados do webhook
    webhook_data = {
        "url": webhook_url,
        "events": [
            "MESSAGES_UPSERT",
            "MESSAGES_UPDATE", 
            "MESSAGES_DELETE",
            "SEND_MESSAGE"
        ],
        "webhook_by_events": False
    }
    
    print(f"📡 Configurando webhook para instância: {instance_name}")
    print(f"🔗 URL do webhook: {webhook_url}")
    print(f"📋 Eventos: {', '.join(webhook_data['events'])}")
    
    try:
        # URL para configurar webhook
        config_url = f"{evolution_url}/webhook/set/{instance_name}"
        
        # Fazer requisição
        response = requests.post(
            config_url,
            json=webhook_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ WEBHOOK CONFIGURADO COM SUCESSO!")
            result = response.json()
            print(f"   Status: {result}")
            return True
        else:
            print(f"❌ Falha na configuração: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao configurar webhook: {str(e)}")
        return False

def verify_webhook_config():
    """Verifica se o webhook foi configurado corretamente"""
    print("\n🔍 VERIFICANDO CONFIGURAÇÃO DO WEBHOOK")
    print("=" * 50)
    
    evolution_url = "http://localhost:8080"
    api_key = "1234"
    instance_name = "agente_bot"
    
    headers = {"apikey": api_key}
    
    try:
        # URL para verificar webhook
        verify_url = f"{evolution_url}/webhook/find/{instance_name}"
        
        response = requests.get(verify_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            config = response.json()
            print("✅ Configuração encontrada:")
            print(f"   URL: {config.get('url', 'N/A')}")
            print(f"   Eventos: {config.get('events', 'N/A')}")
            print(f"   Ativo: {config.get('enabled', 'N/A')}")
            return True
        else:
            print(f"⚠️  Configuração não encontrada: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar: {str(e)}")
        return False

def test_webhook_after_config():
    """Testa o webhook após configuração"""
    print("\n🧪 TESTANDO WEBHOOK APÓS CONFIGURAÇÃO")
    print("=" * 50)
    
    # Enviar mensagem de teste diretamente
    evolution_url = "http://localhost:8080"
    api_key = "1234"
    instance_name = "agente_bot"
    
    url = f"{evolution_url}/message/sendText/{instance_name}"
    
    payload = {
        "number": "5562998550007",
        "textMessage": {"text": "🎉 WEBHOOK CONFIGURADO! Agora o agente deve responder automaticamente. Envie 'oi' para testar!"}
    }
    
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ Mensagem de teste enviada!")
            print("📱 Você deve ter recebido uma mensagem confirmando a configuração.")
            print("\n💡 PRÓXIMO PASSO:")
            print("   Envie 'oi' pelo WhatsApp e veja se o agente responde automaticamente!")
            return True
        else:
            print(f"❌ Falha no teste: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return False

def main():
    """Executa configuração completa do webhook"""
    print("🚀 CONFIGURAÇÃO COMPLETA DO WEBHOOK")
    print("=" * 60)
    print("Este script vai configurar o webhook na Evolution API")
    print("para que o agente responda automaticamente!")
    print()
    
    # Passo 1: Configurar webhook
    config_success = configure_webhook()
    
    if not config_success:
        print("\n❌ FALHA NA CONFIGURAÇÃO!")
        print("Verifique se:")
        print("1. Evolution API está rodando (docker-compose up -d)")
        print("2. Instância 'agente_bot' existe")
        print("3. API key '1234' está correta")
        return
    
    # Passo 2: Verificar configuração
    verify_success = verify_webhook_config()
    
    # Passo 3: Teste final
    test_success = test_webhook_after_config()
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DA CONFIGURAÇÃO:")
    print("=" * 60)
    
    results = [
        ("Configuração do webhook", config_success),
        ("Verificação da config", verify_success),
        ("Teste de funcionamento", test_success)
    ]
    
    for step, success in results:
        status = "✅ OK" if success else "❌ FALHA"
        print(f"{step:<25}: {status}")
    
    if all(result[1] for result in results):
        print("\n🎉 CONFIGURAÇÃO COMPLETA!")
        print("🤖 O agente agora deve responder automaticamente!")
        print("\n📱 TESTE AGORA:")
        print("1. Envie 'oi' pelo WhatsApp")
        print("2. O agente deve responder automaticamente")
        print("3. Teste outros comandos como 'ajuda' ou '/enquete'")
    else:
        print("\n⚠️  PROBLEMAS NA CONFIGURAÇÃO")
        print("Verifique os erros acima e tente novamente.")

if __name__ == "__main__":
    main()

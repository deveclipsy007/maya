"""
🔧 CORREÇÃO DO WEBHOOK - Evolution API
Diagnostica e corrige problemas de webhook
"""
import requests
import json
import time

# Configurações
EVOLUTION_API_URL = "http://localhost:8090"
INSTANCE_NAME = "agente_bot"
API_KEY = "1234"
WEBHOOK_URL = "http://localhost:5000/webhook"

EVOLUTION_API_URL = "http://localhost:8090"  # This line is already correct

def check_evolution_api():
    """Verifica se Evolution API está funcionando"""
    print("🔍 Verificando Evolution API...")
    try:
        response = requests.get(f"{EVOLUTION_API_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Evolution API funcionando - Versão: {data.get('version', 'N/A')}")
            return True
        else:
            print(f"❌ Evolution API retornou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Evolution API não acessível: {e}")
        return False

def check_instance():
    """Verifica status da instância"""
    print(f"\n🔍 Verificando instância '{INSTANCE_NAME}'...")
    try:
        # Verificar se instância existe
        response = requests.get(
            f"{EVOLUTION_API_URL}/instance/fetchInstances",
            headers={"apikey": API_KEY}
        )
        
        if response.status_code == 200:
            data = response.json()
            instances = data if isinstance(data, list) else [data]
            instance_found = False
            
            for item in instances:
                instance = item.get('instance', item)  # Pode vir como 'instance' ou direto
                if instance.get('instanceName') == INSTANCE_NAME:
                    instance_found = True
                    print(f"✅ Instância encontrada:")
                    print(f"   Nome: {instance.get('instanceName')}")
                    print(f"   Status: {instance.get('connectionStatus', 'N/A')}")
                    print(f"   Número: {instance.get('owner', 'N/A')}")
                    break
            
            if not instance_found:
                print(f"❌ Instância '{INSTANCE_NAME}' não encontrada!")
                return False
            
            return True
        else:
            print(f"❌ Erro ao verificar instâncias: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def check_current_webhook():
    """Verifica webhook atual"""
    print(f"\n🔍 Verificando webhook atual...")
    try:
        response = requests.get(
            f"{EVOLUTION_API_URL}/webhook/find/{INSTANCE_NAME}",
            headers={"apikey": API_KEY}
        )
        
        if response.status_code == 200:
            webhook_data = response.json()
            print(f"✅ Webhook atual:")
            print(f"   URL: {webhook_data.get('url', 'N/A')}")
            print(f"   Events: {webhook_data.get('events', 'N/A')}")
            print(f"   Enabled: {webhook_data.get('enabled', 'N/A')}")
            return webhook_data
        else:
            print(f"❌ Erro ao verificar webhook: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def delete_webhook():
    """Remove webhook atual"""
    print(f"\n🗑️ Removendo webhook atual...")
    try:
        response = requests.delete(
            f"{EVOLUTION_API_URL}/webhook/{INSTANCE_NAME}",
            headers={"apikey": API_KEY}
        )
        
        if response.status_code in [200, 204]:
            print("✅ Webhook removido!")
            return True
        else:
            print(f"⚠️ Resposta ao remover: {response.status_code} - {response.text}")
            return True  # Pode não existir, tudo bem
            
    except Exception as e:
        print(f"❌ Erro ao remover: {e}")
        return False

def create_webhook():
    """Cria novo webhook"""
    print(f"\n🔧 Criando novo webhook...")
    try:
        payload = {
            "url": WEBHOOK_URL,
            "webhook_by_events": False,
            "webhook_base64": False,
            "events": ["MESSAGES_UPSERT"]
        }
        
        response = requests.post(
            f"{EVOLUTION_API_URL}/webhook/set/{INSTANCE_NAME}",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "apikey": API_KEY
            }
        )
        
        if response.status_code in [200, 201]:
            print("✅ Webhook criado com sucesso!")
            print(f"   URL: {WEBHOOK_URL}")
            print(f"   Events: MESSAGES_UPSERT")
            return True
        else:
            print(f"❌ Erro ao criar webhook: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_webhook_endpoint():
    """Testa se o endpoint do webhook está acessível"""
    print(f"\n🧪 Testando endpoint do webhook...")
    try:
        response = requests.get("http://localhost:5000/", timeout=3)
        if response.status_code == 200:
            print("✅ Endpoint do webhook acessível!")
            return True
        else:
            print(f"❌ Endpoint retornou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Endpoint não acessível: {e}")
        print("💡 Certifique-se de que o servidor Flask está rodando!")
        return False

def send_test_message():
    """Envia mensagem de teste"""
    print(f"\n📤 Enviando mensagem de teste...")
    
    numero = input("Digite o número para teste (ex: 5562998550007): ").strip()
    if not numero:
        print("❌ Número não informado")
        return False
    
    try:
        payload = {
            "number": numero,
            "textMessage": {
                "text": "🧪 TESTE WEBHOOK CORRIGIDO: Responda esta mensagem para testar!"
            }
        }
        
        response = requests.post(
            f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "apikey": API_KEY
            }
        )
        
        if response.status_code in [200, 201]:
            print("✅ Mensagem de teste enviada!")
            print("📱 Responda no WhatsApp e observe os logs do servidor")
            return True
        else:
            print(f"❌ Erro no envio: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("🔧 CORREÇÃO COMPLETA DO WEBHOOK")
    print("=" * 50)
    
    # 1. Verificar Evolution API
    if not check_evolution_api():
        print("❌ Evolution API não está funcionando!")
        return
    
    # 2. Verificar instância
    if not check_instance():
        print("❌ Problema com a instância!")
        return
    
    # 3. Verificar endpoint do webhook
    if not test_webhook_endpoint():
        print("❌ Servidor Flask não está rodando!")
        print("💡 Execute: python debug_webhook.py")
        return
    
    # 4. Verificar webhook atual
    current_webhook = check_current_webhook()
    
    # 5. Remover webhook atual
    delete_webhook()
    
    # 6. Aguardar um pouco
    print("\n⏳ Aguardando 2 segundos...")
    time.sleep(2)
    
    # 7. Criar novo webhook
    if not create_webhook():
        print("❌ Falha ao criar webhook!")
        return
    
    # 8. Verificar se foi criado
    print("\n🔍 Verificando webhook criado...")
    new_webhook = check_current_webhook()
    
    if new_webhook:
        print("✅ Webhook configurado corretamente!")
    
    # 9. Teste final
    print("\n" + "=" * 50)
    test_msg = input("Enviar mensagem de teste? (s/n): ").lower()
    if test_msg == 's':
        send_test_message()
    
    print("\n✅ CORREÇÃO COMPLETA!")
    print("📋 Próximos passos:")
    print("   1. Certifique-se que o servidor Flask está rodando")
    print("   2. Envie mensagem no WhatsApp")
    print("   3. Observe os logs do servidor")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Corrige a URL do webhook para o IP correto
O problema é que a Evolution API está usando 192.168.15.8 ao invés de localhost
"""
import requests
import json

def fix_webhook_url():
    """Corrige a URL do webhook para o IP correto"""
    print("🔧 CORRIGINDO URL DO WEBHOOK")
    print("=" * 40)
    
    # Configurações
    evolution_url = "http://localhost:8080"
    api_key = "1234"
    instance_name = "agente_bot"
    
    # Nova URL correta (usando o IP que a Evolution API está esperando)
    webhook_url = "http://192.168.15.8:5000/webhook"
    
    # Headers
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }
    
    # Dados do webhook corrigidos
    webhook_data = {
        "url": webhook_url,
        "events": ["MESSAGES_UPSERT"],
        "webhook_by_events": True,
        "webhook_base64": True
    }
    
    print(f"🔗 Nova URL: {webhook_url}")
    print(f"📋 Eventos: {webhook_data['events']}")
    
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
        
        if response.status_code in [200, 201]:
            print("✅ URL DO WEBHOOK CORRIGIDA!")
            result = response.json()
            print(f"   Resposta: {response.status_code}")
            return True
        else:
            print(f"❌ Falha na correção: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao corrigir URL: {str(e)}")
        return False

def verify_fix():
    """Verifica se a correção funcionou"""
    print("\n🔍 VERIFICANDO CORREÇÃO")
    print("=" * 40)
    
    try:
        response = requests.get(
            "http://localhost:8080/webhook/find/agente_bot",
            headers={"apikey": "1234"},
            timeout=10
        )
        
        if response.status_code == 200:
            config = response.json()
            print("✅ Configuração atual:")
            print(f"   URL: {config.get('url')}")
            print(f"   Eventos: {config.get('events')}")
            print(f"   Ativo: {config.get('enabled')}")
            
            # Verificar se a URL está correta
            if "192.168.15.8:5000" in config.get('url', ''):
                print("✅ URL corrigida com sucesso!")
                return True
            else:
                print("⚠️  URL ainda não está correta")
                return False
        else:
            print(f"❌ Erro na verificação: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def test_message_processing():
    """Testa se o processamento de mensagens está funcionando"""
    print("\n🧪 TESTANDO PROCESSAMENTO DE MENSAGENS")
    print("=" * 40)
    
    # Verificar se há mensagens na pasta
    import os
    messages_folder = "mensagens_recebidas"
    
    if os.path.exists(messages_folder):
        files = [f for f in os.listdir(messages_folder) if f.endswith('.json')]
        print(f"📁 Mensagens salvas: {len(files)}")
        
        if files:
            # Mostrar a mensagem mais recente
            latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(messages_folder, f)))
            print(f"📄 Última mensagem: {latest_file}")
            
            # Ler conteúdo
            try:
                with open(os.path.join(messages_folder, latest_file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extrair informações da mensagem
                event = data.get('event', '')
                message_data = data.get('data', {})
                
                print(f"   Evento: {event}")
                
                if 'message' in message_data:
                    msg = message_data['message']
                    if 'conversation' in msg:
                        print(f"   Conteúdo: {msg['conversation']}")
                    elif 'extendedTextMessage' in msg:
                        print(f"   Conteúdo: {msg['extendedTextMessage'].get('text', 'N/A')}")
                
                return True
                
            except Exception as e:
                print(f"   ❌ Erro ao ler mensagem: {str(e)}")
                return False
        else:
            print("   ⚠️  Nenhuma mensagem encontrada")
            return False
    else:
        print("   ❌ Pasta de mensagens não existe")
        return False

def main():
    """Executa correção completa"""
    print("🚀 CORREÇÃO COMPLETA DO WEBHOOK")
    print("=" * 50)
    print("Corrigindo URL e testando funcionamento...")
    print()
    
    # Passo 1: Corrigir URL
    fix_success = fix_webhook_url()
    
    if not fix_success:
        print("\n❌ FALHA NA CORREÇÃO!")
        return
    
    # Passo 2: Verificar correção
    verify_success = verify_fix()
    
    # Passo 3: Testar processamento
    processing_success = test_message_processing()
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DA CORREÇÃO:")
    print("=" * 50)
    
    results = [
        ("Correção da URL", fix_success),
        ("Verificação", verify_success),
        ("Processamento", processing_success)
    ]
    
    for step, success in results:
        status = "✅ OK" if success else "❌ FALHA"
        print(f"{step:<20}: {status}")
    
    if all(result[1] for result in results):
        print("\n🎉 CORREÇÃO COMPLETA!")
        print("🤖 O agente deve estar funcionando agora!")
        print("\n📱 TESTE:")
        print("Envie 'oi' pelo WhatsApp e veja se responde!")
    else:
        print("\n⚠️  Ainda há problemas")
        print("Verifique se o webhook_simple.py está rodando")

if __name__ == "__main__":
    main()

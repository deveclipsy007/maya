"""
Quick Start - Inicia o agente rapidamente
"""
import os
import time
import requests
import webbrowser
from core import WhatsAppClient

def check_evolution_api():
    """Verifica se Evolution API está rodando"""
    try:
        response = requests.get("http://localhost:8090", timeout=3)
        return response.status_code == 200
    except:
        return False

def open_manager():
    """Abre o manager no navegador"""
    try:
        webbrowser.open("http://localhost:8090/manager")
        return True
    except:
        return False

def send_test_message():
    """Envia mensagem de teste"""
    client = WhatsAppClient()
    
    print("\n📱 TESTE DE ENVIO")
    print("=" * 30)
    
    number = input("Digite o número para teste (ex: 5511999999999): ").strip()
    
    if not number:
        print("❌ Número não informado")
        return
    
    message = "🤖 Teste do Agente WhatsApp!\n\nSe você recebeu esta mensagem, tudo está funcionando perfeitamente!\n\nResponda qualquer coisa para testar o sistema automático."
    
    print(f"Enviando para {number}...")
    
    if client.send_message(number, message):
        print("✅ Mensagem enviada! Verifique o WhatsApp.")
        print("💬 Responda a mensagem para testar o webhook")
    else:
        print("❌ Falha no envio")

def main():
    print("🚀 QUICK START - AGENTE WHATSAPP")
    print("=" * 40)
    
    # 1. Verificar Evolution API
    print("🔍 Verificando Evolution API...")
    if not check_evolution_api():
        print("❌ Evolution API não está rodando!")
        print("💡 Execute: docker-compose up -d")
        return
    
    print("✅ Evolution API está rodando!")
    
    # 2. Abrir manager
    print("\n📱 Abrindo Evolution Manager...")
    if open_manager():
        print("✅ Manager aberto no navegador")
        print("📋 Escaneie o QR Code para conectar o WhatsApp")
    
    # 3. Aguardar conexão
    print("\n⏳ Aguarde conectar o WhatsApp e pressione Enter...")
    input()
    
    # 4. Verificar conexão
    client = WhatsAppClient()
    if client.is_connected():
        print("✅ WhatsApp conectado!")
    else:
        print("⚠️ WhatsApp pode não estar conectado ainda")
    
    # 5. Teste opcional
    test = input("\n🧪 Deseja fazer um teste de envio? (s/n): ").lower()
    if test == 's':
        send_test_message()
    
    # 6. Iniciar agente
    print("\n🚀 Para iniciar o agente, execute:")
    print("python app.py")
    
    start_now = input("\nIniciar agora? (s/n): ").lower()
    if start_now == 's':
        print("\n" + "=" * 40)
        print("🤖 INICIANDO AGENTE...")
        os.system("python app.py")

if __name__ == "__main__":
    main()
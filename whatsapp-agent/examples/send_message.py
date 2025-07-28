"""
Exemplo: Como enviar mensagens programaticamente
"""
from core import WhatsAppClient

# Inicializa cliente
client = WhatsAppClient()

def send_welcome_message(number: str):
    """Envia mensagem de boas-vindas"""
    message = """
🤖 Olá! Bem-vindo ao nosso atendimento automatizado!

Posso te ajudar com:
• Informações sobre produtos
• Suporte técnico
• Dúvidas gerais

Como posso te ajudar hoje?
    """.strip()
    
    return client.send_message(number, message)

def send_promotional_message(number: str):
    """Envia mensagem promocional"""
    message = """
🎉 OFERTA ESPECIAL! 

Aproveite nossa promoção:
• 50% de desconto
• Frete grátis
• Garantia estendida

Válido até o final do mês! 
Não perca essa oportunidade! 🛒
    """.strip()
    
    return client.send_message(number, message)

# Exemplo de uso
if __name__ == "__main__":
    # Substitua pelo número desejado
    test_number = "5511999999999"
    
    print("Enviando mensagem de teste...")
    
    if client.send_message(test_number, "🧪 Teste do sistema - Tudo funcionando!"):
        print("✅ Mensagem enviada com sucesso!")
    else:
        print("❌ Falha no envio")
"""
Exemplo: Como personalizar respostas do agente
"""
from core import ResponseGenerator

# Cria gerador de respostas
response_gen = ResponseGenerator()

# Adiciona padrões personalizados
response_gen.add_custom_pattern(
    category="vendas",
    patterns=["preço", "valor", "quanto custa", "orçamento"],
    responses=[
        "Para informações sobre preços, entre em contato com nossa equipe comercial! 💰",
        "Temos várias opções de preços. Que tipo de serviço você procura? 🛒"
    ]
)

response_gen.add_custom_pattern(
    category="suporte",
    patterns=["problema", "erro", "não funciona", "bug"],
    responses=[
        "Vou te ajudar com esse problema! Pode me dar mais detalhes? 🔧",
        "Entendi que você está com dificuldades. Vamos resolver isso juntos! 💪"
    ]
)

# Teste as respostas
if __name__ == "__main__":
    test_messages = [
        "Oi, tudo bem?",
        "Quanto custa o serviço?",
        "Estou com um problema",
        "Obrigado pela ajuda",
        "Mensagem aleatória"
    ]
    
    for msg in test_messages:
        response = response_gen.generate_response(msg)
        print(f"Mensagem: {msg}")
        print(f"Resposta: {response}")
        print("-" * 50)
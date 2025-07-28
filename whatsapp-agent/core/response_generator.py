"""
Gerador de Respostas - Lógica para gerar respostas automáticas
"""
import re
from typing import Optional

class ResponseGenerator:
    def __init__(self):
        # Padrões de resposta configuráveis
        self.response_patterns = {
            "saudacoes": {
                "patterns": ["oi", "olá", "ola", "hey", "e aí", "eai", "bom dia", "boa tarde", "boa noite"],
                "responses": [
                    "Olá! Tudo bem? Como posso te ajudar? 😊",
                    "Oi! Seja bem-vindo! Em que posso ajudar? 👋",
                    "Olá! Prazer em conversar com você! 🤝"
                ]
            },
            "despedidas": {
                "patterns": ["tchau", "bye", "até", "falou", "até mais", "até logo"],
                "responses": [
                    "Até logo! Foi um prazer conversar com você! 👋",
                    "Tchau! Volte sempre que precisar! 😊",
                    "Até mais! Estarei aqui quando precisar! 🤝"
                ]
            },
            "agradecimentos": {
                "patterns": ["obrigado", "obrigada", "valeu", "thanks", "brigado"],
                "responses": [
                    "De nada! Estou aqui para ajudar sempre que precisar! 🤝",
                    "Por nada! Foi um prazer ajudar! 😊",
                    "Disponha! Sempre à disposição! 👍"
                ]
            },
            "ajuda": {
                "patterns": ["ajuda", "help", "socorro", "não sei", "como"],
                "responses": [
                    "Posso te ajudar com:\n• Responder suas mensagens\n• Conversar sobre assuntos gerais\n• Fornecer informações básicas\n\nO que você gostaria de saber? 💡"
                ]
            },
            "sobre_bot": {
                "patterns": ["quem é você", "o que você faz", "bot", "robô", "você é"],
                "responses": [
                    "Eu sou um agente WhatsApp automatizado! 🤖\nPosso responder suas mensagens e ajudar com informações básicas.\nComo posso te ajudar hoje?"
                ]
            }
        }
    
    def generate_response(self, message_text: str, sender_number: str = None) -> Optional[str]:
        """
        Gera resposta baseada no texto da mensagem
        
        Args:
            message_text: Texto da mensagem recebida
            sender_number: Número do remetente (opcional)
            
        Returns:
            str: Resposta gerada ou None
        """
        if not message_text:
            return None
        
        text_lower = message_text.lower().strip()
        
        # Verifica padrões de resposta
        for category, config in self.response_patterns.items():
            if self._matches_pattern(text_lower, config["patterns"]):
                return self._get_response(config["responses"])
        
        # Resposta padrão personalizada
        return self._generate_default_response(message_text)
    
    def _matches_pattern(self, text: str, patterns: list) -> bool:
        """
        Verifica se o texto corresponde a algum padrão
        """
        for pattern in patterns:
            if pattern in text:
                return True
        return False
    
    def _get_response(self, responses: list) -> str:
        """
        Retorna uma resposta da lista (pode ser aleatória no futuro)
        """
        import random
        return random.choice(responses)
    
    def _generate_default_response(self, original_message: str) -> str:
        """
        Gera resposta padrão quando não há padrão específico
        """
        responses = [
            f"Recebi sua mensagem: '{original_message}'\n\nObrigado por entrar em contato! Como posso ajudar? 📱",
            f"Vi que você disse: '{original_message}'\n\nInteressante! Conte-me mais sobre isso. 🤔",
            f"Entendi sua mensagem: '{original_message}'\n\nEstou aqui para conversar! O que mais gostaria de saber? 💬"
        ]
        
        import random
        return random.choice(responses)
    
    def add_custom_pattern(self, category: str, patterns: list, responses: list):
        """
        Adiciona padrão personalizado de resposta
        
        Args:
            category: Nome da categoria
            patterns: Lista de padrões para detectar
            responses: Lista de possíveis respostas
        """
        self.response_patterns[category] = {
            "patterns": patterns,
            "responses": responses
        }
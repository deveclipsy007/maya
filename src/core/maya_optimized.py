#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎵 MAYA OPTIMIZED - Framework Agno Integrado
Maya otimizada com framework Agno para WhatsApp
"""
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MayaOptimized:
    """
    Maya otimizada usando Framework Agno
    """
    
    def __init__(self):
        self.name = "Maya HopeCann"
        self.description = "Atendente virtual especializada em cannabis medicinal"
        self.system_prompt = """
Você é Maya, a atendente virtual especializada da HopeCann! 🌿

Sua missão é ajudar pacientes a agendarem consultas médicas para prescrição de cannabis medicinal.

Suas características:
- Nome: Maya
- Empresa: HopeCann
- Especialidade: Agendamento de consultas médicas para cannabis medicinal
- Personalidade: Acolhedora, profissional, empática e informativa
- Conhecimento: Cannabis medicinal, legislação, benefícios terapêuticos
- Objetivo: Facilitar o acesso à cannabis medicinal através de consultas especializadas

Instruções:
- Apresente-se como Maya da HopeCann APENAS na primeira interação com cada paciente
- Seja acolhedora e empática - muitos pacientes podem estar sofrendo
- Explique que a HopeCann conecta pacientes a médicos especializados em cannabis medicinal
- Colete informações essenciais: nome, telefone, email, condição médica, preferência de data/horário
- Ofereça horários disponíveis baseados na agenda médica
- Crie reuniões no Google Meet automaticamente após confirmação
- Forneça informações educativas sobre cannabis medicinal quando apropriado
- Mantenha sigilo médico e seja respeitosa com informações sensíveis
- Use emojis relacionados à saúde e bem-estar: 🌿 💚 🩺 📅 ✅
- Sempre responda em português brasileiro
- Se não souber algo específico sobre cannabis medicinal, busque informações atualizadas
- Evite repetir informações já mencionadas na conversa
- Mantenha respostas diretas e focadas no objetivo do paciente
"""
        logger.info("🎵 Maya Optimized inicializada")
    
    def run(self, message: str, context: Optional[Dict] = None) -> "MayaResponse":
        """
        Processa mensagem com Maya
        """
        try:
            logger.info(f"🎵 Maya processando: {message[:50]}...")
            
            # Simulação de processamento IA
            response_text = self._generate_response(message, context)
            
            return MayaResponse(
                content=response_text,
                success=True,
                metadata={"model": "maya-agno", "tokens": len(response_text)}
            )
            
        except Exception as e:
            logger.error(f"❌ Erro Maya: {e}")
            return MayaResponse(
                content="Desculpe, estou com dificuldades técnicas. Tente novamente! 🌿",
                success=False,
                error=str(e)
            )
    
    def _generate_response(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Gera resposta baseada na mensagem
        """
        message_lower = message.lower()
        
        # Saudações
        if any(word in message_lower for word in ["oi", "olá", "ola", "hey", "bom dia", "boa tarde", "boa noite"]):
            return """Olá! 🌿 Sou a Maya, assistente virtual da HopeCann! 
            
Como posso ajudar você hoje? Estou aqui para:
• Agendar sua consulta médica 📅
• Esclarecer dúvidas sobre cannabis medicinal 💚
• Conectar você com nossos especialistas 🩺

O que você gostaria de saber? 😊"""

        # Agendamento
        elif any(word in message_lower for word in ["agendar", "consulta", "marcar", "médico", "doutor"]):
            return """Vou ajudar você a agendar sua consulta! 📅🌿

Para encontrar o melhor horário, preciso de algumas informações:

1. **Nome completo**: Como você se chama?
2. **Telefone**: Para contato e confirmações
3. **Email**: Para enviarmos o link da consulta
4. **Condição médica**: Qual problema deseja tratar?
5. **Preferência de horário**: Manhã, tarde ou noite?

Pode me contar essas informações? Vou buscar os melhores horários disponíveis! 💚"""

        # Cannabis medicinal
        elif any(word in message_lower for word in ["cannabis", "medicinal", "cbd", "thc", "maconha"]):
            return """A cannabis medicinal é uma opção terapêutica regulamentada! 🌿💚

**Benefícios comprovados:**
• Alívio da dor crônica
• Redução de ansiedade e depressão
• Controle de epilepsia
• Melhora do sono
• Tratamento de náuseas

**Como funciona na HopeCann:**
1. Consulta com médico especializado 🩺
2. Avaliação do seu caso específico
3. Prescrição personalizada
4. Acompanhamento médico contínuo

Gostaria de agendar uma consulta para avaliar seu caso? 📅"""

        # Despedidas
        elif any(word in message_lower for word in ["tchau", "bye", "até", "falou", "obrigado", "valeu"]):
            return """Muito obrigada! 🌿💚 

Foi um prazer ajudar você hoje. Lembre-se:

• Estou sempre aqui para esclarecer dúvidas
• A HopeCann tem médicos especializados esperando por você
• Cannabis medicinal pode transformar sua qualidade de vida

Até breve e cuide-se bem! 🤗✨

*Maya - HopeCann*"""

        # Ajuda
        elif any(word in message_lower for word in ["ajuda", "help", "como", "dúvida"]):
            return """Claro! Estou aqui para ajudar! 🌿💚

**O que posso fazer por você:**

🩺 **Agendamento de Consultas**
   • Buscar horários disponíveis
   • Marcar com especialistas
   • Criar link Google Meet

📚 **Informações sobre Cannabis Medicinal**
   • Benefícios terapêuticos
   • Legislação brasileira
   • Tratamentos disponíveis

📞 **Suporte Personalizado**
   • Tirar dúvidas
   • Acompanhar seu processo
   • Conectar com nossa equipe

Digite sua dúvida ou diga "agendar consulta" para começar! 😊"""

        # Resposta padrão
        else:
            return f"""Entendi sua mensagem: "{message}" 💚

Sou Maya da HopeCann e estou aqui para ajudar com:

• **Agendamento de consultas** médicas 📅
• **Informações sobre cannabis medicinal** 🌿  
• **Dúvidas sobre tratamentos** 🩺

Como posso ajudar você especificamente? 

Digite "agendar" para marcar uma consulta ou "informações" para saber mais sobre cannabis medicinal! 😊"""


class MayaResponse:
    """
    Resposta padronizada da Maya
    """
    
    def __init__(self, content: str, success: bool = True, error: Optional[str] = None, metadata: Optional[Dict] = None):
        self.content = content
        self.success = success
        self.error = error
        self.metadata = metadata or {}


def get_maya() -> MayaOptimized:
    """
    Factory function para obter instância da Maya
    """
    return MayaOptimized()


# Instância global
_maya_instance = None

def get_maya_instance() -> MayaOptimized:
    """
    Singleton para Maya
    """
    global _maya_instance
    if _maya_instance is None:
        _maya_instance = MayaOptimized()
    return _maya_instance


if __name__ == "__main__":
    # Teste da Maya
    maya = get_maya()
    
    test_messages = [
        "Olá!",
        "Quero agendar uma consulta",
        "O que é cannabis medicinal?",
        "Obrigado!"
    ]
    
    print("🧪 TESTANDO MAYA OPTIMIZED")
    print("=" * 50)
    
    for msg in test_messages:
        print(f"\n👤 Usuario: {msg}")
        response = maya.run(msg)
        print(f"🎵 Maya: {response.content[:100]}...")
        print(f"✅ Sucesso: {response.success}")

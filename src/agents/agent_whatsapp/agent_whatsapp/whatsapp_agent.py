"""
Agente WhatsApp para processamento de mensagens de texto
Implementa interface do Agno Core para processar mensagens de texto do WhatsApp
"""
import asyncio
import os
from typing import Optional
import structlog
from agno_core.interfaces import Agent, AgnoInput, AgnoOutput, MessageType, EventType

logger = structlog.get_logger(__name__)


class WhatsAppAgent(Agent):
    """
    Agente especializado em processar mensagens de texto do WhatsApp
    """
    
    def __init__(self):
        super().__init__(
            name="whatsapp",
            description="Processa mensagens de texto do WhatsApp com IA conversacional"
        )
        self.logger = logger.bind(agent="WhatsAppAgent")
        
        # Configurações do agente
        self.max_response_length = 2000  # Limite do WhatsApp
        self.response_delay = 1  # Delay em segundos para parecer mais humano
        
        # Contexto de conversa (em produção, usar banco de dados)
        self.conversation_context = {}
    
    async def can_handle(self, input_data: AgnoInput) -> bool:
        """
        Verifica se pode processar a entrada
        
        Args:
            input_data: Dados de entrada
            
        Returns:
            bool: True se for mensagem de texto
        """
        # Processar apenas mensagens de texto recebidas
        can_process = (
            input_data.message_type == MessageType.TEXT and
            input_data.event_type == EventType.MESSAGES_UPSERT and
            not input_data.is_from_me and  # Não processar mensagens próprias
            input_data.text_content is not None and
            len(input_data.text_content.strip()) > 0
        )
        
        self.logger.info(
            "Verificação de capacidade de processamento",
            can_handle=can_process,
            message_type=input_data.message_type.value,
            event_type=input_data.event_type.value,
            is_from_me=input_data.is_from_me,
            has_text=input_data.text_content is not None
        )
        
        return can_process
    
    async def run(self, input_data: AgnoInput) -> AgnoOutput:
        """
        Processa mensagem de texto e gera resposta
        
        Args:
            input_data: Dados de entrada
            
        Returns:
            AgnoOutput: Resposta processada
        """
        self.logger.info(
            "Iniciando processamento de mensagem",
            from_number=input_data.from_number,
            message_length=len(input_data.text_content or ""),
            is_group=input_data.is_group
        )
        
        try:
            # Obter contexto da conversa
            context = self._get_conversation_context(input_data.from_number)
            
            # Processar mensagem
            response_text = await self._process_text_message(
                input_data.text_content,
                context,
                input_data
            )
            
            # Atualizar contexto
            self._update_conversation_context(
                input_data.from_number,
                input_data.text_content,
                response_text
            )
            
            # Criar resposta
            output = AgnoOutput(
                to_number=input_data.from_number,
                message_type=MessageType.TEXT,
                text_content=response_text,
                delay_seconds=self.response_delay,
                quote_message_id=input_data.message_id,
                metadata={
                    "agent": self.name,
                    "processed_at": input_data.timestamp,
                    "context_length": len(context)
                }
            )
            
            self.logger.info(
                "Mensagem processada com sucesso",
                response_length=len(response_text),
                delay=self.response_delay
            )
            
            return output
            
        except Exception as e:
            self.logger.error(
                "Erro no processamento da mensagem",
                error=str(e),
                from_number=input_data.from_number
            )
            
            # Resposta de fallback
            return AgnoOutput(
                to_number=input_data.from_number,
                message_type=MessageType.TEXT,
                text_content="Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.",
                delay_seconds=1,
                metadata={"agent": self.name, "error": str(e)}
            )
    
    async def _process_text_message(
        self, 
        text: str, 
        context: list, 
        input_data: AgnoInput
    ) -> str:
        """
        Processa mensagem de texto usando IA
        
        Args:
            text: Texto da mensagem
            context: Contexto da conversa
            input_data: Dados completos da entrada
            
        Returns:
            str: Resposta gerada
        """
        # Por enquanto, implementação simples
        # Em produção, integrar com OpenAI, Anthropic, etc.
        
        text_lower = text.lower().strip()
        
        # Respostas básicas
        if any(greeting in text_lower for greeting in ["oi", "olá", "ola", "hey", "hello"]):
            return f"Olá! Como posso ajudá-lo hoje? 😊"
        
        elif any(thanks in text_lower for thanks in ["obrigado", "obrigada", "valeu", "thanks"]):
            return "De nada! Fico feliz em ajudar! 🙂"
        
        elif any(bye in text_lower for bye in ["tchau", "bye", "até", "falou"]):
            return "Até logo! Foi um prazer conversar com você! 👋"
        
        elif "como você está" in text_lower or "como vai" in text_lower:
            return "Estou bem, obrigado por perguntar! E você, como está?"
        
        elif "ajuda" in text_lower or "help" in text_lower:
            return """🤖 *Agno WhatsApp Assistant*

Posso ajudá-lo com:
• Conversas gerais
• Responder perguntas
• Processar imagens (em breve)
• Criar enquetes (em breve)

Digite qualquer coisa e vamos conversar!"""
        
        else:
            # Resposta padrão inteligente
            return f"Interessante! Você disse: '{text[:100]}...' \n\nPosso ajudá-lo com mais alguma coisa? 🤔"
    
    def _get_conversation_context(self, phone_number: str) -> list:
        """
        Obtém contexto da conversa para um número
        
        Args:
            phone_number: Número do telefone
            
        Returns:
            list: Histórico da conversa
        """
        return self.conversation_context.get(phone_number, [])
    
    def _update_conversation_context(
        self, 
        phone_number: str, 
        user_message: str, 
        bot_response: str
    ) -> None:
        """
        Atualiza contexto da conversa
        
        Args:
            phone_number: Número do telefone
            user_message: Mensagem do usuário
            bot_response: Resposta do bot
        """
        if phone_number not in self.conversation_context:
            self.conversation_context[phone_number] = []
        
        context = self.conversation_context[phone_number]
        
        # Adicionar nova interação
        context.append({
            "user": user_message,
            "bot": bot_response,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Manter apenas últimas 10 interações
        if len(context) > 10:
            context.pop(0)
    
    async def initialize(self) -> None:
        """
        Inicializa o agente
        """
        await super().initialize()
        
        self.logger.info("WhatsAppAgent inicializado com sucesso")
        
        # Em produção, carregar modelos de IA aqui
        # await self._load_ai_models()
    
    async def cleanup(self) -> None:
        """
        Limpa recursos do agente
        """
        self.logger.info("Limpando recursos do WhatsAppAgent")
        
        # Limpar contexto de conversas
        self.conversation_context.clear()
        
        await super().cleanup()

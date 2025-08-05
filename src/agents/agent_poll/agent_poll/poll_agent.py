"""
Agente Poll para gerenciamento de enquetes e pesquisas no WhatsApp
Implementa interface do Agno Core para processar e criar enquetes
"""
import asyncio
import json
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import structlog
from agno_core.interfaces import Agent, AgnoInput, AgnoOutput, MessageType, EventType

logger = structlog.get_logger(__name__)


class PollAgent(Agent):
    """
    Agente especializado em criar e gerenciar enquetes no WhatsApp
    """
    
    def __init__(self):
        super().__init__(
            name="poll",
            description="Cria e gerencia enquetes interativas no WhatsApp"
        )
        self.logger = logger.bind(agent="PollAgent")
        
        # Armazenamento de enquetes ativas (em produção, usar banco de dados)
        self.active_polls: Dict[str, Dict[str, Any]] = {}
        self.poll_responses: Dict[str, List[Dict[str, Any]]] = {}
        
        # Comandos para criar enquetes
        self.poll_triggers = [
            "/enquete", "/poll", "criar enquete", "nova enquete",
            "fazer pesquisa", "/pesquisa"
        ]
    
    async def can_handle(self, input_data: AgnoInput) -> bool:
        """
        Verifica se pode processar a entrada
        
        Args:
            input_data: Dados de entrada
            
        Returns:
            bool: True se for comando de enquete ou resposta a enquete
        """
        if not input_data.text_content:
            return False
        
        text_lower = input_data.text_content.lower().strip()
        
        # Verificar se é comando para criar enquete
        is_poll_command = any(trigger in text_lower for trigger in self.poll_triggers)
        
        # Verificar se é resposta a enquete existente
        is_poll_response = self._is_poll_response(input_data)
        
        can_process = (
            input_data.message_type == MessageType.TEXT and
            input_data.event_type == EventType.MESSAGES_UPSERT and
            not input_data.is_from_me and
            (is_poll_command or is_poll_response)
        )
        
        self.logger.info(
            "Verificação de capacidade de processamento",
            can_handle=can_process,
            is_poll_command=is_poll_command,
            is_poll_response=is_poll_response,
            text_preview=text_lower[:50]
        )
        
        return can_process
    
    async def run(self, input_data: AgnoInput) -> AgnoOutput:
        """
        Processa comando de enquete ou resposta
        
        Args:
            input_data: Dados de entrada
            
        Returns:
            AgnoOutput: Resposta processada
        """
        self.logger.info(
            "Iniciando processamento de enquete",
            from_number=input_data.from_number,
            is_group=input_data.is_group
        )
        
        try:
            text_lower = input_data.text_content.lower().strip()
            
            # Verificar se é comando para criar enquete
            if any(trigger in text_lower for trigger in self.poll_triggers):
                return await self._handle_poll_creation(input_data)
            
            # Verificar se é resposta a enquete
            elif self._is_poll_response(input_data):
                return await self._handle_poll_response(input_data)
            
            else:
                # Fallback - não deveria chegar aqui
                return await self._create_help_response(input_data)
                
        except Exception as e:
            self.logger.error(
                "Erro no processamento da enquete",
                error=str(e),
                from_number=input_data.from_number
            )
            
            return AgnoOutput(
                to_number=input_data.from_number,
                message_type=MessageType.TEXT,
                text_content="Desculpe, ocorreu um erro ao processar sua enquete. Tente novamente.",
                delay_seconds=1,
                metadata={"agent": self.name, "error": str(e)}
            )
    
    async def _handle_poll_creation(self, input_data: AgnoInput) -> AgnoOutput:
        """
        Processa comando para criar enquete
        
        Args:
            input_data: Dados de entrada
            
        Returns:
            AgnoOutput: Enquete criada
        """
        text = input_data.text_content.strip()
        
        # Extrair pergunta e opções do texto
        poll_data = self._parse_poll_command(text)
        
        if not poll_data:
            return await self._create_poll_help_response(input_data)
        
        # Criar enquete
        poll_id = f"poll_{input_data.from_number}_{input_data.timestamp}"
        
        # Armazenar enquete
        self.active_polls[poll_id] = {
            "id": poll_id,
            "creator": input_data.from_number,
            "question": poll_data["question"],
            "options": poll_data["options"],
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "is_group": input_data.is_group,
            "group_id": input_data.group_id
        }
        
        self.poll_responses[poll_id] = []
        
        # Criar texto da enquete
        poll_text = self._format_poll_message(poll_data["question"], poll_data["options"], poll_id)
        
        self.logger.info(
            "Enquete criada com sucesso",
            poll_id=poll_id,
            question=poll_data["question"],
            options_count=len(poll_data["options"])
        )
        
        return AgnoOutput(
            to_number=input_data.from_number,
            message_type=MessageType.TEXT,
            text_content=poll_text,
            delay_seconds=1,
            metadata={
                "agent": self.name,
                "poll_id": poll_id,
                "action": "poll_created"
            }
        )
    
    async def _handle_poll_response(self, input_data: AgnoInput) -> AgnoOutput:
        """
        Processa resposta a enquete
        
        Args:
            input_data: Dados de entrada
            
        Returns:
            AgnoOutput: Confirmação da resposta
        """
        # Implementar lógica de resposta a enquetes
        # Por enquanto, resposta simples
        return AgnoOutput(
            to_number=input_data.from_number,
            message_type=MessageType.TEXT,
            text_content="Obrigado pela sua resposta! 📊",
            delay_seconds=1,
            metadata={"agent": self.name, "action": "poll_response"}
        )
    
    def _parse_poll_command(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extrai pergunta e opções do comando de enquete
        
        Args:
            text: Texto do comando
            
        Returns:
            Dict com pergunta e opções ou None se inválido
        """
        # Remover comando inicial
        for trigger in self.poll_triggers:
            if trigger in text.lower():
                text = text.lower().replace(trigger, "").strip()
                break
        
        if not text:
            return None
        
        # Tentar diferentes formatos
        # Formato 1: "Pergunta? opção1, opção2, opção3"
        if "?" in text:
            parts = text.split("?", 1)
            question = parts[0].strip() + "?"
            
            if len(parts) > 1 and parts[1].strip():
                options_text = parts[1].strip()
                options = [opt.strip() for opt in options_text.split(",") if opt.strip()]
                
                if len(options) >= 2:
                    return {"question": question, "options": options}
        
        # Formato 2: Apenas pergunta (gerar opções padrão)
        if text.endswith("?"):
            return {
                "question": text,
                "options": ["Sim", "Não", "Talvez"]
            }
        
        return None
    
    def _format_poll_message(self, question: str, options: List[str], poll_id: str) -> str:
        """
        Formata mensagem da enquete
        
        Args:
            question: Pergunta da enquete
            options: Lista de opções
            poll_id: ID da enquete
            
        Returns:
            str: Mensagem formatada
        """
        message = f"📊 *ENQUETE*\n\n"
        message += f"*{question}*\n\n"
        
        for i, option in enumerate(options, 1):
            message += f"{i}️⃣ {option}\n"
        
        message += f"\n💬 Responda com o número da sua escolha!"
        message += f"\n⏰ Enquete válida por 24h"
        
        return message
    
    def _is_poll_response(self, input_data: AgnoInput) -> bool:
        """
        Verifica se é resposta a enquete ativa
        
        Args:
            input_data: Dados de entrada
            
        Returns:
            bool: True se for resposta a enquete
        """
        # Implementar lógica para detectar respostas
        # Por enquanto, retorna False
        return False
    
    async def _create_help_response(self, input_data: AgnoInput) -> AgnoOutput:
        """
        Cria resposta de ajuda
        """
        return await self._create_poll_help_response(input_data)
    
    async def _create_poll_help_response(self, input_data: AgnoInput) -> AgnoOutput:
        """
        Cria resposta de ajuda para enquetes
        
        Args:
            input_data: Dados de entrada
            
        Returns:
            AgnoOutput: Mensagem de ajuda
        """
        help_text = """📊 *Como criar enquetes:*

*Formato 1:*
`/enquete Qual sua cor favorita? Azul, Verde, Vermelho`

*Formato 2:*
`/enquete Você gosta de pizza?`
(Gera opções: Sim, Não, Talvez)

*Comandos disponíveis:*
• `/enquete` ou `/poll`
• `criar enquete`
• `nova enquete`
• `fazer pesquisa`

💡 *Dica:* Use vírgulas para separar as opções!"""
        
        return AgnoOutput(
            to_number=input_data.from_number,
            message_type=MessageType.TEXT,
            text_content=help_text,
            delay_seconds=1,
            metadata={"agent": self.name, "action": "help"}
        )
    
    async def initialize(self) -> None:
        """
        Inicializa o agente
        """
        await super().initialize()
        
        self.logger.info("PollAgent inicializado com sucesso")
        
        # Em produção, carregar enquetes ativas do banco de dados
        # await self._load_active_polls()
    
    async def cleanup(self) -> None:
        """
        Limpa recursos do agente
        """
        self.logger.info("Limpando recursos do PollAgent")
        
        # Salvar enquetes ativas no banco de dados
        # await self._save_active_polls()
        
        # Limpar cache
        self.active_polls.clear()
        self.poll_responses.clear()
        
        await super().cleanup()

"""
Interfaces principais do Agno Core
Baseado na documentação oficial do Agno Framework
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import asyncio


class MessageType(Enum):
    """Tipos de mensagem suportados pelo sistema"""
    TEXT = "text"
    IMAGE = "image" 
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    POLL = "poll"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"


class EventType(Enum):
    """Tipos de evento do Evolution API"""
    MESSAGES_UPSERT = "MESSAGES_UPSERT"
    MESSAGES_UPDATE = "MESSAGES_UPDATE"
    MESSAGES_DELETE = "MESSAGES_DELETE"
    SEND_MESSAGE = "SEND_MESSAGE"
    CONNECTION_UPDATE = "CONNECTION_UPDATE"
    QRCODE_UPDATED = "QRCODE_UPDATED"
    TYPEBOT_START = "TYPEBOT_START"
    TYPEBOT_CHANGE_STATUS = "TYPEBOT_CHANGE_STATUS"


@dataclass
class AgnoInput:
    """
    Entrada padronizada para o sistema Agno
    Baseada nos eventos da Evolution API
    """
    # Identificação
    instance_name: str
    event_type: EventType
    message_type: MessageType
    
    # Dados da mensagem
    from_number: str
    to_number: str
    message_id: str
    timestamp: int
    
    # Conteúdo
    text_content: Optional[str] = None
    media_url: Optional[str] = None
    media_base64: Optional[str] = None
    media_mimetype: Optional[str] = None
    
    # Metadados
    is_from_me: bool = False
    is_group: bool = False
    group_id: Optional[str] = None
    participant: Optional[str] = None
    
    # Dados brutos originais
    raw_data: Optional[Dict[str, Any]] = None


@dataclass 
class AgnoOutput:
    """
    Saída padronizada do sistema Agno
    """
    # Identificação
    to_number: str
    message_type: MessageType
    
    # Conteúdo da resposta
    text_content: Optional[str] = None
    media_url: Optional[str] = None
    media_base64: Optional[str] = None
    media_mimetype: Optional[str] = None
    
    # Configurações de envio
    delay_seconds: int = 0
    quote_message_id: Optional[str] = None
    
    # Metadados
    metadata: Optional[Dict[str, Any]] = None


class Agent(ABC):
    """
    Interface base para todos os agentes do sistema
    Seguindo padrões do Agno Framework
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._initialized = False
    
    @abstractmethod
    async def can_handle(self, input_data: AgnoInput) -> bool:
        """
        Verifica se este agente pode processar a entrada
        
        Args:
            input_data: Dados de entrada padronizados
            
        Returns:
            bool: True se pode processar, False caso contrário
        """
        pass
    
    @abstractmethod
    async def run(self, input_data: AgnoInput) -> AgnoOutput:
        """
        Processa a entrada e retorna uma saída
        
        Args:
            input_data: Dados de entrada padronizados
            
        Returns:
            AgnoOutput: Resposta processada
        """
        pass
    
    async def initialize(self) -> None:
        """
        Inicializa o agente (carregamento de modelos, configurações, etc.)
        """
        self._initialized = True
    
    async def cleanup(self) -> None:
        """
        Limpa recursos do agente
        """
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Verifica se o agente foi inicializado"""
        return self._initialized


class Tool(ABC):
    """
    Interface base para ferramentas que podem ser usadas pelos agentes
    Baseada no padrão de Tools do Agno Framework
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Executa a ferramenta
        
        Args:
            **kwargs: Parâmetros específicos da ferramenta
            
        Returns:
            Any: Resultado da execução
        """
        pass


class AgentRegistry:
    """
    Registro de agentes disponíveis no sistema
    Implementa descoberta automática via entry points
    """
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._tools: Dict[str, Tool] = {}
    
    def register_agent(self, agent: Agent) -> None:
        """Registra um agente no sistema"""
        self._agents[agent.name] = agent
    
    def register_tool(self, tool: Tool) -> None:
        """Registra uma ferramenta no sistema"""
        self._tools[tool.name] = tool
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Obtém um agente pelo nome"""
        return self._agents.get(name)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Obtém uma ferramenta pelo nome"""
        return self._tools.get(name)
    
    def list_agents(self) -> List[str]:
        """Lista nomes de todos os agentes registrados"""
        return list(self._agents.keys())
    
    def list_tools(self) -> List[str]:
        """Lista nomes de todas as ferramentas registradas"""
        return list(self._tools.keys())


# Instância global do registro
registry = AgentRegistry()

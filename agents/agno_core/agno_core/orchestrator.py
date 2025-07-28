"""
Orquestrador central do sistema Agno
Gerencia descoberta de plugins e roteamento de mensagens
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
import pkg_resources
from .interfaces import Agent, AgnoInput, AgnoOutput, AgentRegistry, registry
import structlog

logger = structlog.get_logger(__name__)


class AgentManager:
    """
    Gerenciador central de agentes
    Implementa descoberta automática via entry points e roteamento inteligente
    """
    
    def __init__(self):
        self.registry = registry
        self._initialized = False
        self.logger = logger.bind(component="AgentManager")
    
    async def load_plugins(self) -> None:
        """
        Carrega plugins automaticamente via setuptools entry points
        Baseado no padrão de descoberta do Agno Framework
        """
        self.logger.info("Iniciando carregamento de plugins...")
        
        try:
            # Descobrir agentes via entry points
            for entry_point in pkg_resources.iter_entry_points('agno_agents'):
                try:
                    self.logger.info(f"Carregando agente: {entry_point.name}")
                    
                    # Carregar classe do agente
                    agent_class = entry_point.load()
                    
                    # Instanciar agente
                    agent_instance = agent_class()
                    
                    # Registrar no sistema
                    self.registry.register_agent(agent_instance)
                    
                    # Inicializar agente
                    await agent_instance.initialize()
                    
                    self.logger.info(
                        f"Agente carregado com sucesso",
                        agent_name=entry_point.name,
                        agent_class=agent_class.__name__
                    )
                    
                except Exception as e:
                    self.logger.error(
                        f"Erro ao carregar agente {entry_point.name}: {str(e)}",
                        error=str(e),
                        agent_name=entry_point.name
                    )
                    continue
            
            self._initialized = True
            self.logger.info(
                "Carregamento de plugins concluído",
                total_agents=len(self.registry.list_agents())
            )
            
        except Exception as e:
            self.logger.error(f"Erro crítico no carregamento de plugins: {str(e)}")
            raise
    
    async def dispatch(self, input_data: AgnoInput) -> Optional[AgnoOutput]:
        """
        Roteia a entrada para o agente apropriado
        
        Args:
            input_data: Dados de entrada padronizados
            
        Returns:
            AgnoOutput: Resposta processada ou None se nenhum agente puder processar
        """
        if not self._initialized:
            await self.load_plugins()
        
        self.logger.info(
            "Iniciando dispatch de mensagem",
            message_type=input_data.message_type.value,
            event_type=input_data.event_type.value,
            from_number=input_data.from_number
        )
        
        # Encontrar agentes que podem processar a entrada
        capable_agents = []
        
        for agent_name in self.registry.list_agents():
            agent = self.registry.get_agent(agent_name)
            if agent and await agent.can_handle(input_data):
                capable_agents.append(agent)
        
        if not capable_agents:
            self.logger.warning(
                "Nenhum agente encontrado para processar a mensagem",
                message_type=input_data.message_type.value,
                event_type=input_data.event_type.value
            )
            return None
        
        # Por enquanto, usar o primeiro agente capaz
        # TODO: Implementar lógica de priorização/seleção mais sofisticada
        selected_agent = capable_agents[0]
        
        self.logger.info(
            "Agente selecionado para processamento",
            agent_name=selected_agent.name,
            total_capable=len(capable_agents)
        )
        
        try:
            # Processar com o agente selecionado
            output = await selected_agent.run(input_data)
            
            self.logger.info(
                "Mensagem processada com sucesso",
                agent_name=selected_agent.name,
                output_type=output.message_type.value if output else None
            )
            
            return output
            
        except Exception as e:
            self.logger.error(
                "Erro no processamento da mensagem",
                agent_name=selected_agent.name,
                error=str(e)
            )
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica a saúde do sistema
        
        Returns:
            Dict com informações de status
        """
        agents_status = {}
        
        for agent_name in self.registry.list_agents():
            agent = self.registry.get_agent(agent_name)
            agents_status[agent_name] = {
                "initialized": agent.is_initialized if agent else False,
                "description": agent.description if agent else "N/A"
            }
        
        return {
            "manager_initialized": self._initialized,
            "total_agents": len(self.registry.list_agents()),
            "total_tools": len(self.registry.list_tools()),
            "agents": agents_status
        }
    
    async def shutdown(self) -> None:
        """
        Desliga o gerenciador e limpa recursos
        """
        self.logger.info("Iniciando shutdown do AgentManager...")
        
        # Limpar todos os agentes
        for agent_name in self.registry.list_agents():
            agent = self.registry.get_agent(agent_name)
            if agent:
                try:
                    await agent.cleanup()
                    self.logger.info(f"Agente {agent_name} finalizado com sucesso")
                except Exception as e:
                    self.logger.error(f"Erro ao finalizar agente {agent_name}: {str(e)}")
        
        self._initialized = False
        self.logger.info("Shutdown concluído")


# Instância global do gerenciador
manager = AgentManager()

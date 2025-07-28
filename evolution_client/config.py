"""
Configuração do Evolution API Client
Carrega configurações do ambiente (.env)
"""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()


@dataclass
class EvolutionConfig:
    """
    Configurações da Evolution API
    """
    base_url: str
    api_key: str
    instance_name: str
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        instance_name: Optional[str] = None
    ):
        self.base_url = base_url or os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
        self.api_key = api_key or os.getenv("EVOLUTION_API_KEY", "1234")
        self.instance_name = instance_name or os.getenv("EVOLUTION_INSTANCE_NAME", "agente_bot")
        
        # Validar configurações obrigatórias
        if not self.base_url:
            raise ValueError("EVOLUTION_API_URL é obrigatório")
        if not self.api_key:
            raise ValueError("EVOLUTION_API_KEY é obrigatório")
        if not self.instance_name:
            raise ValueError("EVOLUTION_INSTANCE_NAME é obrigatório")
    
    @property
    def webhook_url(self) -> str:
        """URL do webhook configurada"""
        return os.getenv("WEBHOOK_URL", "http://localhost:5000/webhook")
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em produção"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"

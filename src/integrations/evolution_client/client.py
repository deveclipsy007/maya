"""
Cliente para Evolution API
Implementa métodos para envio de mensagens via WhatsApp
Baseado na documentação oficial da Evolution API
"""
import asyncio
import base64
import json
from typing import Optional, Dict, Any, List
import requests
import structlog
from .config import EvolutionConfig

logger = structlog.get_logger(__name__)


class EvolutionClient:
    """
    Cliente para interagir com a Evolution API
    """
    
    def __init__(self, config: Optional[EvolutionConfig] = None):
        self.config = config or EvolutionConfig()
        self.logger = logger.bind(component="EvolutionClient")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.cleanup()
    
    async def initialize(self) -> None:
        """
        Inicializa o cliente
        """
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "Content-Type": "application/json",
                "apikey": self.config.api_key
            }
        )
        
        self.logger.info(
            "EvolutionClient inicializado",
            base_url=self.config.base_url,
            instance_name=self.config.instance_name
        )
    
    async def cleanup(self) -> None:
        """
        Limpa recursos do cliente
        """
        if self.session:
            await self.session.close()
            self.session = None
        
        self.logger.info("EvolutionClient finalizado")
    
    async def send_text(
        self, 
        to: str, 
        text: str, 
        quote_message_id: Optional[str] = None,
        delay_seconds: int = 0
    ) -> Dict[str, Any]:
        """
        Envia mensagem de texto
        
        Args:
            to: Número de destino
            text: Texto da mensagem
            quote_message_id: ID da mensagem para citar
            delay_seconds: Delay antes do envio
            
        Returns:
            Dict: Resposta da API
        """
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        
        payload = {
            "number": to,
            "text": text
        }
        
        if quote_message_id:
            payload["quoted"] = {
                "key": {
                    "id": quote_message_id
                }
            }
        
        url = f"{self.config.base_url}/message/sendText/{self.config.instance_name}"
        
        self.logger.info(
            "Enviando mensagem de texto",
            to=to,
            text_length=len(text),
            has_quote=quote_message_id is not None,
            delay=delay_seconds
        )
        
        try:
            async with self.session.post(url, json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    self.logger.info(
                        "Mensagem de texto enviada com sucesso",
                        to=to,
                        message_id=result.get("key", {}).get("id")
                    )
                else:
                    self.logger.error(
                        "Erro ao enviar mensagem de texto",
                        to=to,
                        status=response.status,
                        error=result
                    )
                
                return result
                
        except Exception as e:
            self.logger.error(
                "Exceção ao enviar mensagem de texto",
                to=to,
                error=str(e)
            )
            raise
    
    async def send_image(
        self, 
        to: str, 
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        caption: Optional[str] = None,
        filename: str = "image.jpg"
    ) -> Dict[str, Any]:
        """
        Envia imagem
        
        Args:
            to: Número de destino
            image_url: URL da imagem
            image_base64: Imagem em base64
            caption: Legenda da imagem
            filename: Nome do arquivo
            
        Returns:
            Dict: Resposta da API
        """
        if not image_url and not image_base64:
            raise ValueError("É necessário fornecer image_url ou image_base64")
        
        media_message = {
            "mediatype": "image",
            "fileName": filename
        }
        
        if image_url:
            media_message["media"] = image_url
        elif image_base64:
            media_message["media"] = image_base64
        
        if caption:
            media_message["caption"] = caption
        
        payload = {
            "number": to,
            "mediaMessage": media_message
        }
        
        url = f"{self.config.base_url}/message/sendMedia/{self.config.instance_name}"
        
        self.logger.info(
            "Enviando imagem",
            to=to,
            has_url=image_url is not None,
            has_base64=image_base64 is not None,
            has_caption=caption is not None,
            filename=filename
        )
        
        try:
            async with self.session.post(url, json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    self.logger.info(
                        "Imagem enviada com sucesso",
                        to=to,
                        message_id=result.get("key", {}).get("id")
                    )
                else:
                    self.logger.error(
                        "Erro ao enviar imagem",
                        to=to,
                        status=response.status,
                        error=result
                    )
                
                return result
                
        except Exception as e:
            self.logger.error(
                "Exceção ao enviar imagem",
                to=to,
                error=str(e)
            )
            raise
    
    async def send_poll(
        self, 
        to: str, 
        poll_name: str,
        poll_options: List[str],
        selectable_count: int = 1
    ) -> Dict[str, Any]:
        """
        Envia enquete
        
        Args:
            to: Número de destino
            poll_name: Nome/pergunta da enquete
            poll_options: Lista de opções
            selectable_count: Número de opções selecionáveis
            
        Returns:
            Dict: Resposta da API
        """
        payload = {
            "number": to,
            "pollMessage": {
                "name": poll_name,
                "selectableCount": selectable_count,
                "values": poll_options
            }
        }
        
        url = f"{self.config.base_url}/message/sendPoll/{self.config.instance_name}"
        
        self.logger.info(
            "Enviando enquete",
            to=to,
            poll_name=poll_name,
            options_count=len(poll_options),
            selectable_count=selectable_count
        )
        
        try:
            async with self.session.post(url, json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    self.logger.info(
                        "Enquete enviada com sucesso",
                        to=to,
                        message_id=result.get("key", {}).get("id")
                    )
                else:
                    self.logger.error(
                        "Erro ao enviar enquete",
                        to=to,
                        status=response.status,
                        error=result
                    )
                
                return result
                
        except Exception as e:
            self.logger.error(
                "Exceção ao enviar enquete",
                to=to,
                error=str(e)
            )
            raise
    
    async def get_instance_info(self) -> Dict[str, Any]:
        """
        Obtém informações da instância
        
        Returns:
            Dict: Informações da instância
        """
        url = f"{self.config.base_url}/instance/fetchInstances"
        
        try:
            async with self.session.get(url) as response:
                result = await response.json()
                
                self.logger.info(
                    "Informações da instância obtidas",
                    status=response.status
                )
                
                return result
                
        except Exception as e:
            self.logger.error(
                "Erro ao obter informações da instância",
                error=str(e)
            )
            raise
    
    async def set_webhook(
        self, 
        webhook_url: str,
        events: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Configura webhook da instância
        
        Args:
            webhook_url: URL do webhook
            events: Lista de eventos para escutar
            
        Returns:
            Dict: Resposta da API
        """
        if events is None:
            events = [
                "MESSAGES_UPSERT",
                "MESSAGES_UPDATE", 
                "MESSAGES_DELETE",
                "SEND_MESSAGE",
                "CONNECTION_UPDATE",
                "QRCODE_UPDATED"
            ]
        
        payload = {
            "url": webhook_url,
            "webhook_by_events": False,
            "webhook_base64": False,
            "events": events
        }
        
        url = f"{self.config.base_url}/webhook/set/{self.config.instance_name}"
        
        self.logger.info(
            "Configurando webhook",
            webhook_url=webhook_url,
            events_count=len(events)
        )
        
        try:
            async with self.session.post(url, json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    self.logger.info("Webhook configurado com sucesso")
                else:
                    self.logger.error(
                        "Erro ao configurar webhook",
                        status=response.status,
                        error=result
                    )
                
                return result
                
        except Exception as e:
            self.logger.error(
                "Exceção ao configurar webhook",
                error=str(e)
            )
            raise

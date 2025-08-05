"""
Cliente Evolution API simplificado baseado nos scripts funcionais do usuário
"""
import requests
import base64
import json
import structlog
from .config import EvolutionConfig

logger = structlog.get_logger(__name__)


class SimpleEvolutionClient:
    """
    Cliente simplificado para Evolution API usando requests (síncrono)
    Baseado nos scripts funcionais: texto.py, imagem.py, enquete.py, audio.py
    """
    
    def __init__(self, config: EvolutionConfig = None):
        self.config = config or EvolutionConfig()
        self.logger = logger.bind(component="SimpleEvolutionClient")
        
        # Headers padrão baseados nos scripts funcionais
        self.headers = {
            "apikey": self.config.api_key,
            "Content-Type": "application/json"
        }
        
        self.logger.info(
            "SimpleEvolutionClient inicializado",
            base_url=self.config.base_url,
            instance_name=self.config.instance_name
        )
    
    def send_text(self, number: str, text: str) -> dict:
        """
        Envia mensagem de texto - baseado em texto.py
        """
        url = f"{self.config.base_url}/message/sendText/{self.config.instance_name}"
        
        payload = {
            "number": number,
            "textMessage": {"text": text}
        }
        
        self.logger.info("Enviando mensagem de texto", to=number, text_length=len(text))
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            result = response.json() if response.content else {}
            
            if response.status_code == 200:
                self.logger.info("Mensagem enviada com sucesso", to=number)
            else:
                self.logger.error("Erro ao enviar mensagem", to=number, status=response.status_code)
            
            return result
            
        except Exception as e:
            self.logger.error("Exceção ao enviar mensagem", to=number, error=str(e))
            return {"error": str(e)}
    
    def send_image(self, number: str, image_base64: str, caption: str = "", filename: str = "image.png") -> dict:
        """
        Envia imagem - baseado em imagem.py
        """
        url = f"{self.config.base_url}/message/sendMedia/{self.config.instance_name}"
        
        payload = {
            "number": number,
            "options": {
                "delay": 123,
                "presence": "composing"
            },
            "mediaMessage": {
                "mediatype": "image",
                "fileName": filename,
                "caption": caption,
                "media": image_base64
            }
        }
        
        self.logger.info("Enviando imagem", to=number, filename=filename)
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=60)
            result = response.json() if response.content else {}
            
            if response.status_code == 200:
                self.logger.info("Imagem enviada com sucesso", to=number)
            else:
                self.logger.error("Erro ao enviar imagem", to=number, status=response.status_code)
            
            return result
            
        except Exception as e:
            self.logger.error("Exceção ao enviar imagem", to=number, error=str(e))
            return {"error": str(e)}
    
    def send_poll(self, number: str, poll_name: str, options: list, selectable_count: int = 1) -> dict:
        """
        Envia enquete - baseado em enquete.py
        """
        url = f"{self.config.base_url}/message/sendPoll/{self.config.instance_name}"
        
        payload = {
            "number": number,
            "options": {
                "delay": 123,
                "presence": "composing"
            },
            "pollMessage": {
                "name": poll_name,
                "selectableCount": selectable_count,
                "values": options
            }
        }
        
        self.logger.info("Enviando enquete", to=number, poll_name=poll_name)
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            result = response.json() if response.content else {}
            
            if response.status_code == 200:
                self.logger.info("Enquete enviada com sucesso", to=number)
            else:
                self.logger.error("Erro ao enviar enquete", to=number, status=response.status_code)
            
            return result
            
        except Exception as e:
            self.logger.error("Exceção ao enviar enquete", to=number, error=str(e))
            return {"error": str(e)}

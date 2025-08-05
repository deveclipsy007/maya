"""
Cliente WhatsApp - Módulo principal para comunicação com Evolution API
"""
import os
import requests
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class WhatsAppClient:
    def __init__(self):
        self.api_url = os.getenv("EVOLUTION_API_URL", "http://localhost:8090")
        self.instance = os.getenv("INSTANCE_NAME", "agente_bot")
        self.api_key = os.getenv("API_KEY", "1234")
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def send_message(self, number: str, message: str) -> bool:
        """
        Envia mensagem para um número
        
        Args:
            number: Número do destinatário (ex: 5511999999999)
            message: Texto da mensagem
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        endpoint = f"{self.api_url}/message/sendText/{self.instance}"
        
        payload = {
            "number": number,
            "textMessage": {
                "text": message
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                self.logger.info(f"✅ Mensagem enviada para {number}")
                return True
            else:
                self.logger.error(f"❌ Erro ao enviar para {number}: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"💥 Exceção ao enviar mensagem: {e}")
            return False
    
    def get_instance_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtém informações da instância
        
        Returns:
            dict: Informações da instância ou None se erro
        """
        endpoint = f"{self.api_url}/instance/fetchInstances"
        headers = {"apikey": self.api_key}
        
        try:
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                instances = response.json()
                for instance in instances:
                    if instance.get('name') == self.instance:
                        return instance
            return None
        except Exception as e:
            self.logger.error(f"Erro ao obter info da instância: {e}")
            return None
    
    def is_connected(self) -> bool:
        """
        Verifica se a instância está conectada
        
        Returns:
            bool: True se conectada, False caso contrário
        """
        endpoint = f"{self.api_url}/instance/connectionState/{self.instance}"
        headers = {"apikey": self.api_key}
        
        try:
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                data = response.json()
                state = data.get("instance", {}).get("state", "")
                return state == "open"
            return False
        except Exception as e:
            self.logger.error(f"Erro ao verificar conexão: {e}")
            return False
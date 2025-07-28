"""
Manipulador de Mensagens - Processa mensagens recebidas e gera respostas
"""
import logging
from typing import Optional, Dict, Any
from .response_generator import ResponseGenerator

class MessageHandler:
    def __init__(self, whatsapp_client):
        self.whatsapp_client = whatsapp_client
        self.response_generator = ResponseGenerator()
        self.logger = logging.getLogger(__name__)
    
    def process_webhook_data(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Processa dados recebidos do webhook
        
        Args:
            webhook_data: Dados do webhook da Evolution API
            
        Returns:
            bool: True se processado com sucesso
        """
        try:
            if not webhook_data or "data" not in webhook_data:
                return False
            
            # Processa cada mensagem no webhook
            for item in webhook_data["data"]:
                if self._is_valid_message(item):
                    self._handle_message(item)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao processar webhook: {e}")
            return False
    
    def _is_valid_message(self, item: Dict[str, Any]) -> bool:
        """
        Verifica se o item é uma mensagem válida para processar
        """
        if "message" not in item or not item["message"]:
            return False
        
        # Ignora mensagens enviadas pelo próprio bot
        if item["message"].get("fromMe", False):
            return False
        
        return True
    
    def _handle_message(self, item: Dict[str, Any]) -> None:
        """
        Processa uma mensagem individual
        """
        try:
            message_data = item["message"]
            sender_number = self._extract_sender_number(item)
            message_text = self._extract_message_text(message_data)
            
            if not sender_number or not message_text:
                return
            
            self.logger.info(f"📨 Mensagem de {sender_number}: {message_text}")
            
            # Gera resposta
            response = self.response_generator.generate_response(message_text, sender_number)
            
            if response:
                self.logger.info(f"🤖 Resposta: {response}")
                
                # Envia resposta
                if self.whatsapp_client.send_message(sender_number, response):
                    self.logger.info(f"✅ Resposta enviada para {sender_number}")
                else:
                    self.logger.error(f"❌ Falha ao enviar resposta para {sender_number}")
        
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem: {e}")
    
    def _extract_sender_number(self, item: Dict[str, Any]) -> Optional[str]:
        """
        Extrai o número do remetente
        """
        try:
            remote_jid = item.get("key", {}).get("remoteJid", "")
            if remote_jid:
                # Remove @s.whatsapp.net se presente
                return remote_jid.replace("@s.whatsapp.net", "")
            return None
        except:
            return None
    
    def _extract_message_text(self, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Extrai o texto da mensagem
        """
        try:
            # Tenta diferentes formatos de mensagem
            text = (
                message_data.get("conversation") or
                message_data.get("extendedTextMessage", {}).get("text") or
                message_data.get("text") or
                ""
            )
            return text.strip() if text else None
        except:
            return None
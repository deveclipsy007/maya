"""
Adapter para converter eventos da Evolution API em formato Agno
"""
from typing import Optional, Dict, Any
import structlog
from agno_core.interfaces import AgnoInput, MessageType, EventType
from ..schemas.webhook_schemas import WebhookEvent, WhatsAppMessage

logger = structlog.get_logger(__name__)


class EvolutionAdapter:
    """
    Converte eventos da Evolution API para o formato Agno
    """
    
    def __init__(self):
        self.logger = logger.bind(component="EvolutionAdapter")
    
    def parse_webhook_event(self, data: Dict[str, Any]) -> Optional[WebhookEvent]:
        """
        Converte dados brutos do webhook em WebhookEvent
        
        Args:
            data: Dados brutos do webhook
            
        Returns:
            WebhookEvent ou None se inválido
        """
        try:
            webhook_event = WebhookEvent(**data)
            
            self.logger.info(
                "Evento webhook parseado",
                event_type=webhook_event.event,
                instance=webhook_event.instance
            )
            
            return webhook_event
            
        except Exception as e:
            self.logger.error(
                "Erro ao parsear evento webhook",
                error=str(e),
                data_keys=list(data.keys()) if isinstance(data, dict) else "not_dict"
            )
            return None
    
    def to_agno_input(self, webhook_event: WebhookEvent) -> Optional[AgnoInput]:
        """
        Converte WebhookEvent em AgnoInput
        
        Args:
            webhook_event: Evento do webhook
            
        Returns:
            AgnoInput ou None se não processável
        """
        try:
            # Apenas processar eventos de mensagens
            if webhook_event.event_type != EventType.MESSAGES_UPSERT:
                self.logger.debug(
                    "Evento não é de mensagem, ignorando",
                    event_type=webhook_event.event
                )
                return None
            
            # Extrair mensagens do evento
            messages = webhook_event.get_messages()
            
            if not messages:
                self.logger.debug("Nenhuma mensagem encontrada no evento")
                return None
            
            # Processar primeira mensagem (por enquanto)
            message = messages[0]
            
            # Ignorar mensagens próprias
            if message.is_from_me:
                self.logger.debug("Ignorando mensagem própria")
                return None
            
            # Determinar tipo da mensagem
            agno_message_type = self._map_message_type(message)
            
            if not agno_message_type:
                self.logger.debug(
                    "Tipo de mensagem não suportado",
                    whatsapp_type=message.message_type
                )
                return None
            
            # Criar AgnoInput
            agno_input = AgnoInput(
                instance_name=webhook_event.instance,
                event_type=EventType.MESSAGES_UPSERT,
                message_type=agno_message_type,
                from_number=message.from_number,
                to_number=webhook_event.instance,  # Nome da instância como destino
                message_id=message.key.id,
                timestamp=message.messageTimestamp,
                text_content=message.text_content,
                is_from_me=message.is_from_me,
                is_group=message.is_group,
                group_id=message.group_id,
                participant=message.participant,
                raw_data=webhook_event.data
            )
            
            self.logger.info(
                "AgnoInput criado com sucesso",
                message_type=agno_message_type.value,
                from_number=message.from_number,
                has_text=agno_input.text_content is not None,
                is_group=message.is_group
            )
            
            return agno_input
            
        except Exception as e:
            self.logger.error(
                "Erro ao converter para AgnoInput",
                error=str(e),
                event_type=webhook_event.event
            )
            return None
    
    def _map_message_type(self, message: WhatsAppMessage) -> Optional[MessageType]:
        """
        Mapeia tipo de mensagem WhatsApp para MessageType do Agno
        
        Args:
            message: Mensagem do WhatsApp
            
        Returns:
            MessageType correspondente ou None
        """
        whatsapp_type = message.message_type
        
        if not whatsapp_type:
            return None
        
        # Mapeamento de tipos
        type_mapping = {
            "conversation": MessageType.TEXT,
            "extendedTextMessage": MessageType.TEXT,
            "imageMessage": MessageType.IMAGE,
            "videoMessage": MessageType.VIDEO,
            "audioMessage": MessageType.AUDIO,
            "documentMessage": MessageType.DOCUMENT,
            "stickerMessage": MessageType.STICKER,
            "locationMessage": MessageType.LOCATION,
            "contactMessage": MessageType.CONTACT,
            "pollCreationMessage": MessageType.POLL,
            "pollUpdateMessage": MessageType.POLL
        }
        
        return type_mapping.get(whatsapp_type)

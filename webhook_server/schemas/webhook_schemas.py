"""
Schemas Pydantic para validação de eventos webhook da Evolution API
Baseado na documentação oficial da Evolution API
"""
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Tipos de evento suportados pela Evolution API"""
    MESSAGES_UPSERT = "messages.upsert"
    MESSAGES_UPDATE = "messages.update"
    MESSAGES_DELETE = "messages.delete"
    SEND_MESSAGE = "send.message"
    CONNECTION_UPDATE = "connection.update"
    QRCODE_UPDATED = "qrcode.updated"
    TYPEBOT_START = "typebot_start"
    TYPEBOT_CHANGE_STATUS = "typebot_change_status"


class MessageType(str, Enum):
    """Tipos de mensagem do WhatsApp"""
    CONVERSATION = "conversation"
    EXTENDED_TEXT_MESSAGE = "extendedTextMessage"
    IMAGE_MESSAGE = "imageMessage"
    VIDEO_MESSAGE = "videoMessage"
    AUDIO_MESSAGE = "audioMessage"
    DOCUMENT_MESSAGE = "documentMessage"
    STICKER_MESSAGE = "stickerMessage"
    LOCATION_MESSAGE = "locationMessage"
    CONTACT_MESSAGE = "contactMessage"
    POLL_CREATION_MESSAGE = "pollCreationMessage"
    POLL_UPDATE_MESSAGE = "pollUpdateMessage"


class MessageKey(BaseModel):
    """Chave identificadora da mensagem"""
    id: str
    fromMe: bool
    remoteJid: str


class MessageInfo(BaseModel):
    """Informações da mensagem"""
    key: MessageKey
    messageTimestamp: int
    pushName: Optional[str] = None
    participant: Optional[str] = None


class TextMessage(BaseModel):
    """Mensagem de texto"""
    text: str


class MediaMessage(BaseModel):
    """Mensagem de mídia (imagem, vídeo, etc.)"""
    url: Optional[str] = None
    mimetype: Optional[str] = None
    caption: Optional[str] = None
    fileSha256: Optional[str] = None
    fileLength: Optional[int] = None
    height: Optional[int] = None
    width: Optional[int] = None


class PollOption(BaseModel):
    """Opção de enquete"""
    optionName: str


class PollMessage(BaseModel):
    """Mensagem de enquete"""
    name: str
    options: List[PollOption]
    selectableOptionsCount: int = 1


class MessageContent(BaseModel):
    """Conteúdo da mensagem"""
    conversation: Optional[str] = None
    extendedTextMessage: Optional[Dict[str, Any]] = None
    imageMessage: Optional[MediaMessage] = None
    videoMessage: Optional[MediaMessage] = None
    audioMessage: Optional[MediaMessage] = None
    documentMessage: Optional[MediaMessage] = None
    stickerMessage: Optional[MediaMessage] = None
    locationMessage: Optional[Dict[str, Any]] = None
    contactMessage: Optional[Dict[str, Any]] = None
    pollCreationMessage: Optional[PollMessage] = None
    pollUpdateMessage: Optional[Dict[str, Any]] = None


class WhatsAppMessage(BaseModel):
    """Mensagem completa do WhatsApp"""
    key: MessageKey
    messageTimestamp: int
    pushName: Optional[str] = None
    participant: Optional[str] = None
    message: Optional[MessageContent] = None
    
    @property
    def message_type(self) -> Optional[str]:
        """Determina o tipo da mensagem"""
        if not self.message:
            return None
        
        for field_name, field_value in self.message.dict().items():
            if field_value is not None:
                return field_name
        
        return None
    
    @property
    def text_content(self) -> Optional[str]:
        """Extrai conteúdo de texto da mensagem"""
        if not self.message:
            return None
        
        # Mensagem de texto simples
        if self.message.conversation:
            return self.message.conversation
        
        # Mensagem de texto estendida
        if self.message.extendedTextMessage:
            return self.message.extendedTextMessage.get("text")
        
        # Caption de mídia
        for media_field in ["imageMessage", "videoMessage", "audioMessage", "documentMessage"]:
            media_msg = getattr(self.message, media_field, None)
            if media_msg and hasattr(media_msg, 'caption') and media_msg.caption:
                return media_msg.caption
        
        return None
    
    @property
    def is_from_me(self) -> bool:
        """Verifica se a mensagem é própria"""
        return self.key.fromMe
    
    @property
    def is_group(self) -> bool:
        """Verifica se é mensagem de grupo"""
        return "@g.us" in self.key.remoteJid
    
    @property
    def from_number(self) -> str:
        """Número do remetente"""
        if self.is_group and self.participant:
            return self.participant.replace("@s.whatsapp.net", "")
        return self.key.remoteJid.replace("@s.whatsapp.net", "").replace("@g.us", "")
    
    @property
    def group_id(self) -> Optional[str]:
        """ID do grupo (se aplicável)"""
        if self.is_group:
            return self.key.remoteJid
        return None


class InstanceInfo(BaseModel):
    """Informações da instância"""
    instanceName: str
    instanceId: Optional[str] = None
    status: Optional[str] = None


class WebhookEvent(BaseModel):
    """Evento completo do webhook"""
    event: str
    instance: str
    data: Dict[str, Any]
    destination: Optional[str] = None
    date_time: Optional[str] = None
    sender: Optional[str] = None
    server_url: Optional[str] = None
    apikey: Optional[str] = None
    
    @property
    def event_type(self) -> Optional[EventType]:
        """Converte evento para enum"""
        try:
            return EventType(self.event)
        except ValueError:
            return None
    
    def get_messages(self) -> List[WhatsAppMessage]:
        """Extrai mensagens do evento"""
        messages = []
        
        # Diferentes estruturas dependendo do evento
        if "messages" in self.data:
            for msg_data in self.data["messages"]:
                try:
                    messages.append(WhatsAppMessage(**msg_data))
                except Exception as e:
                    # Log do erro mas continue processando outras mensagens
                    continue
        
        elif "message" in self.data:
            try:
                messages.append(WhatsAppMessage(**self.data["message"]))
            except Exception:
                pass
        
        return messages


class WebhookResponse(BaseModel):
    """Resposta padrão do webhook"""
    status: str = "success"
    message: str = "Webhook processed successfully"
    timestamp: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

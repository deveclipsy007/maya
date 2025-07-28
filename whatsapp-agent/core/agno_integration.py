"""
Integração com Framework Agno
Permite usar agentes do Agno com WhatsApp via Evolution API
"""
import logging
from typing import Optional, Dict, Any

class AgnoWhatsAppBridge:
    """
    Ponte entre o Framework Agno e WhatsApp
    """
    
    def __init__(self, agno_agent, whatsapp_client):
        """
        Inicializa a ponte Agno-WhatsApp
        
        Args:
            agno_agent: Instância do seu agente Agno
            whatsapp_client: Cliente WhatsApp da nossa estrutura
        """
        self.agno_agent = agno_agent
        self.whatsapp_client = whatsapp_client
        self.logger = logging.getLogger(__name__)
        
        # Configurações opcionais
        self.enable_context = True  # Manter contexto da conversa
        self.user_contexts = {}     # Armazena contexto por usuário
    
    def process_message(self, sender_number: str, message_text: str) -> bool:
        """
        Processa mensagem usando o agente Agno
        
        Args:
            sender_number: Número do remetente
            message_text: Texto da mensagem
            
        Returns:
            bool: True se processado com sucesso
        """
        try:
            self.logger.info(f"🧠 Processando com Agno: {message_text}")
            
            # Prepara contexto do usuário
            user_context = self._get_user_context(sender_number)
            
            # Chama o agente Agno
            agno_response = self._call_agno_agent(
                message=message_text,
                user_id=sender_number,
                context=user_context
            )
            
            if agno_response:
                # Atualiza contexto se habilitado
                if self.enable_context:
                    self._update_user_context(sender_number, message_text, agno_response)
                
                # Envia resposta via WhatsApp
                success = self.whatsapp_client.send_message(sender_number, agno_response)
                
                if success:
                    self.logger.info(f"✅ Resposta Agno enviada para {sender_number}")
                    return True
                else:
                    self.logger.error(f"❌ Falha ao enviar resposta Agno")
                    return False
            else:
                self.logger.warning("⚠️ Agno não gerou resposta")
                return False
                
        except Exception as e:
            self.logger.error(f"💥 Erro na integração Agno: {e}")
            return False
    
    def _call_agno_agent(self, message: str, user_id: str, context: Dict = None) -> Optional[str]:
        """
        Chama o agente Agno - ADAPTE ESTE MÉTODO PARA SEU AGENTE
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário
            context: Contexto da conversa
            
        Returns:
            str: Resposta do agente Agno
        """
        try:
            # EXEMPLO - Adapte para sua implementação do Agno
            
            # Opção 1: Se seu agente tem método 'process' ou 'chat'
            if hasattr(self.agno_agent, 'process'):
                return self.agno_agent.process(message, user_id=user_id, context=context)
            
            # Opção 2: Se seu agente tem método 'generate_response'
            elif hasattr(self.agno_agent, 'generate_response'):
                return self.agno_agent.generate_response(message, context=context)
            
            # Opção 3: Se seu agente tem método 'chat'
            elif hasattr(self.agno_agent, 'chat'):
                return self.agno_agent.chat(message, user_id=user_id)
            
            # Opção 4: Se seu agente é callable
            elif callable(self.agno_agent):
                return self.agno_agent(message, user_id=user_id, context=context)
            
            else:
                self.logger.error("❌ Método do agente Agno não encontrado")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao chamar agente Agno: {e}")
            return None
    
    def _get_user_context(self, user_id: str) -> Dict:
        """
        Obtém contexto do usuário
        """
        if not self.enable_context:
            return {}
        
        return self.user_contexts.get(user_id, {
            'messages': [],
            'user_id': user_id,
            'session_start': None
        })
    
    def _update_user_context(self, user_id: str, user_message: str, agent_response: str):
        """
        Atualiza contexto do usuário
        """
        if not self.enable_context:
            return
        
        if user_id not in self.user_contexts:
            from datetime import datetime
            self.user_contexts[user_id] = {
                'messages': [],
                'user_id': user_id,
                'session_start': datetime.now().isoformat()
            }
        
        # Adiciona mensagens ao contexto
        self.user_contexts[user_id]['messages'].extend([
            {'role': 'user', 'content': user_message},
            {'role': 'assistant', 'content': agent_response}
        ])
        
        # Limita histórico (últimas 20 mensagens)
        if len(self.user_contexts[user_id]['messages']) > 20:
            self.user_contexts[user_id]['messages'] = self.user_contexts[user_id]['messages'][-20:]
    
    def clear_user_context(self, user_id: str):
        """
        Limpa contexto de um usuário
        """
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
            self.logger.info(f"🗑️ Contexto limpo para {user_id}")
    
    def set_context_enabled(self, enabled: bool):
        """
        Habilita/desabilita manutenção de contexto
        """
        self.enable_context = enabled
        self.logger.info(f"📝 Contexto {'habilitado' if enabled else 'desabilitado'}")


class AgnoMessageHandler:
    """
    Handler de mensagens especializado para Agno
    """
    
    def __init__(self, agno_agent, whatsapp_client):
        self.bridge = AgnoWhatsAppBridge(agno_agent, whatsapp_client)
        self.logger = logging.getLogger(__name__)
    
    def process_webhook_data(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Processa webhook usando agente Agno
        """
        try:
            if not webhook_data or "data" not in webhook_data:
                return False
            
            # Processa cada mensagem
            for item in webhook_data["data"]:
                if self._is_valid_message(item):
                    self._handle_message_with_agno(item)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao processar webhook com Agno: {e}")
            return False
    
    def _is_valid_message(self, item: Dict[str, Any]) -> bool:
        """
        Verifica se é mensagem válida
        """
        if "message" not in item or not item["message"]:
            return False
        
        # Ignora mensagens do próprio bot
        if item["message"].get("fromMe", False):
            return False
        
        return True
    
    def _handle_message_with_agno(self, item: Dict[str, Any]) -> None:
        """
        Processa mensagem com agente Agno
        """
        try:
            sender_number = self._extract_sender_number(item)
            message_text = self._extract_message_text(item["message"])
            
            if sender_number and message_text:
                self.logger.info(f"📨 Mensagem para Agno de {sender_number}: {message_text}")
                self.bridge.process_message(sender_number, message_text)
        
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem com Agno: {e}")
    
    def _extract_sender_number(self, item: Dict[str, Any]) -> Optional[str]:
        """
        Extrai número do remetente
        """
        try:
            remote_jid = item.get("key", {}).get("remoteJid", "")
            return remote_jid.replace("@s.whatsapp.net", "") if remote_jid else None
        except:
            return None
    
    def _extract_message_text(self, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Extrai texto da mensagem
        """
        try:
            text = (
                message_data.get("conversation") or
                message_data.get("extendedTextMessage", {}).get("text") or
                message_data.get("text") or
                ""
            )
            return text.strip() if text else None
        except:
            return None
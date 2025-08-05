#!/usr/bin/env python3
"""
Agente WhatsApp com Inteligência Artificial Real
Integra OpenAI, Anthropic e outras APIs para respostas inteligentes
"""
import asyncio
import os
import json
import httpx
from typing import Optional, Dict, Any, List
import structlog
from agno_core.interfaces import Agent, AgnoInput, AgnoOutput, MessageType, EventType

logger = structlog.get_logger(__name__)


class AIWhatsAppAgent(Agent):
    """
    Agente WhatsApp com IA real - OpenAI, Anthropic, etc.
    """
    
    def __init__(self):
        super().__init__(
            name="ai_whatsapp",
            description="Agente WhatsApp com IA conversacional avançada usando OpenAI/Anthropic"
        )
        self.logger = logger.bind(agent="AIWhatsAppAgent")
        
        # Configurações de IA
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.preferred_model = os.getenv("AI_MODEL", "gpt-3.5-turbo")
        
        # Configurações do agente
        self.max_response_length = 2000
        self.response_delay = 1
        self.max_context_messages = 10
        
        # Contexto de conversa persistente
        self.conversation_context = {}
        
        # Cliente HTTP assíncrono
        self.http_client = None
        
        # Personalidade do agente
        self.system_prompt = """Você é um assistente inteligente para WhatsApp chamado Agno.

PERSONALIDADE:
- Amigável, prestativo e conversacional
- Responde em português brasileiro
- Usa emojis apropriados
- Mantém conversas naturais
- É conciso mas informativo

CAPACIDADES:
- Conversar sobre qualquer assunto
- Responder perguntas
- Dar conselhos e sugestões
- Ajudar com tarefas
- Criar enquetes (quando solicitado)
- Processar imagens (quando disponível)

LIMITAÇÕES:
- Não pode acessar internet em tempo real
- Não pode fazer ligações ou enviar SMS
- Não pode acessar dados pessoais sem permissão

ESTILO DE RESPOSTA:
- Máximo 2000 caracteres
- Use quebras de linha para organizar
- Seja direto mas amigável
- Adapte o tom à conversa"""

    async def can_handle(self, input_data: AgnoInput) -> bool:
        """
        Verifica se pode processar a entrada
        """
        can_process = (
            input_data.message_type == MessageType.TEXT and
            input_data.event_type == EventType.MESSAGES_UPSERT and
            not input_data.is_from_me and
            input_data.text_content is not None and
            len(input_data.text_content.strip()) > 0
        )
        
        self.logger.info(
            "Verificação de capacidade IA",
            can_handle=can_process,
            has_openai_key=bool(self.openai_api_key),
            has_anthropic_key=bool(self.anthropic_api_key),
            model=self.preferred_model
        )
        
        return can_process

    async def run(self, input_data: AgnoInput) -> AgnoOutput:
        """
        Processa mensagem com IA real
        """
        self.logger.info(
            "Processando com IA",
            from_number=input_data.from_number,
            message_length=len(input_data.text_content or ""),
            model=self.preferred_model
        )
        
        try:
            # Obter contexto da conversa
            context = self._get_conversation_context(input_data.from_number)
            
            # Gerar resposta com IA
            response_text = await self._generate_ai_response(
                input_data.text_content,
                context,
                input_data
            )
            
            # Atualizar contexto
            self._update_conversation_context(
                input_data.from_number,
                input_data.text_content,
                response_text
            )
            
            # Criar resposta
            output = AgnoOutput(
                to_number=input_data.from_number,
                message_type=MessageType.TEXT,
                text_content=response_text,
                delay_seconds=self.response_delay,
                quote_message_id=input_data.message_id,
                metadata={
                    "agent": self.name,
                    "ai_model": self.preferred_model,
                    "processed_at": input_data.timestamp,
                    "context_length": len(context),
                    "ai_powered": True
                }
            )
            
            self.logger.info(
                "Resposta IA gerada com sucesso",
                response_length=len(response_text),
                model_used=self.preferred_model
            )
            
            return output
            
        except Exception as e:
            self.logger.error(
                "Erro no processamento IA",
                error=str(e),
                from_number=input_data.from_number
            )
            
            # Fallback para resposta simples
            return await self._fallback_response(input_data)

    async def _generate_ai_response(
        self, 
        text: str, 
        context: List[Dict], 
        input_data: AgnoInput
    ) -> str:
        """
        Gera resposta usando IA (OpenAI, Anthropic, etc.)
        """
        # Verificar se temos chaves de API
        if not self.openai_api_key and not self.anthropic_api_key:
            self.logger.warning("Nenhuma chave de IA configurada, usando fallback")
            return await self._fallback_simple_response(text)
        
        # Preparar contexto da conversa
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Adicionar histórico da conversa
        for interaction in context[-5:]:  # Últimas 5 interações
            messages.append({"role": "user", "content": interaction["user"]})
            messages.append({"role": "assistant", "content": interaction["bot"]})
        
        # Adicionar mensagem atual
        messages.append({"role": "user", "content": text})
        
        # Tentar OpenAI primeiro
        if self.openai_api_key:
            try:
                return await self._call_openai(messages)
            except Exception as e:
                self.logger.error(f"Erro OpenAI: {str(e)}")
        
        # Tentar Anthropic como fallback
        if self.anthropic_api_key:
            try:
                return await self._call_anthropic(messages)
            except Exception as e:
                self.logger.error(f"Erro Anthropic: {str(e)}")
        
        # Fallback final
        return await self._fallback_simple_response(text)

    async def _call_openai(self, messages: List[Dict]) -> str:
        """
        Chama API da OpenAI
        """
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.preferred_model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        response = await self.http_client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

    async def _call_anthropic(self, messages: List[Dict]) -> str:
        """
        Chama API da Anthropic (Claude)
        """
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        
        headers = {
            "x-api-key": self.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Converter formato para Anthropic
        system_message = messages[0]["content"]
        conversation_messages = messages[1:]
        
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 1000,
            "temperature": 0.7,
            "system": system_message,
            "messages": conversation_messages
        }
        
        response = await self.http_client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["content"][0]["text"].strip()
        else:
            raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")

    async def _fallback_simple_response(self, text: str) -> str:
        """
        Resposta de fallback quando IA não está disponível
        """
        text_lower = text.lower().strip()
        
        # Respostas inteligentes sem IA
        if any(greeting in text_lower for greeting in ["oi", "olá", "ola", "hey", "hello", "bom dia", "boa tarde", "boa noite"]):
            return "Olá! 👋 Como posso ajudá-lo hoje?\n\n💡 *Dica:* Configure uma chave de API (OpenAI ou Anthropic) para respostas ainda mais inteligentes!"
        
        elif any(thanks in text_lower for thanks in ["obrigado", "obrigada", "valeu", "thanks", "brigado"]):
            return "De nada! 😊 Fico feliz em ajudar!\n\nPrecisa de mais alguma coisa?"
        
        elif any(bye in text_lower for bye in ["tchau", "bye", "até logo", "falou", "até mais"]):
            return "Até logo! 👋 Foi um prazer conversar com você!\n\nVolte sempre que precisar! 😊"
        
        elif "como você está" in text_lower or "como vai" in text_lower:
            return "Estou funcionando perfeitamente! 🚀\n\nTodos os sistemas operacionais e pronto para ajudar. E você, como está?"
        
        elif any(help_cmd in text_lower for help_cmd in ["ajuda", "help", "menu", "comandos"]):
            return """🤖 *Agno AI Assistant*

*Funcionalidades Disponíveis:*

💬 *Conversação Inteligente*
• Respondo perguntas
• Converso sobre diversos assuntos
• Dou conselhos e sugestões

🔧 *Configuração IA:*
• Configure OPENAI_API_KEY para GPT
• Configure ANTHROPIC_API_KEY para Claude
• Defina AI_MODEL (padrão: gpt-3.5-turbo)

📊 *Comandos Especiais:*
• `ajuda` - Este menu
• `sobre` - Informações do sistema
• `status` - Status da IA

Digite qualquer coisa e vamos conversar! 🚀"""
        
        elif "sobre" in text_lower or "quem é você" in text_lower:
            return """🤖 *Sobre o Agno AI Assistant*

Sou um assistente inteligente para WhatsApp com capacidades avançadas de IA!

✨ *Características:*
• Processamento de linguagem natural
• Memória de conversas
• Respostas contextuais
• Integração com OpenAI e Anthropic

🧠 *Inteligência Artificial:*
• GPT-3.5/GPT-4 (OpenAI)
• Claude (Anthropic)
• Fallback inteligente

🔧 *Tecnologia:*
• Framework Agno personalizado
• Python assíncrono
• Arquitetura modular

Desenvolvido para ser seu assistente pessoal no WhatsApp! 💪"""
        
        elif "status" in text_lower:
            ai_status = "🟢 Configurada" if (self.openai_api_key or self.anthropic_api_key) else "🟡 Não configurada"
            model_info = f"Modelo: {self.preferred_model}" if (self.openai_api_key or self.anthropic_api_key) else "Modo Fallback"
            
            return f"""📊 *Status do Sistema*

🤖 *Agente IA:* Online
{ai_status} *IA Externa:* {ai_status}
📡 *Webhook:* Conectado
⚡ *Processamento:* Tempo real

🧠 *Configuração IA:*
• {model_info}
• OpenAI: {'✅' if self.openai_api_key else '❌'}
• Anthropic: {'✅' if self.anthropic_api_key else '❌'}

💬 *Conversas Ativas:* {len(self.conversation_context)}

Sistema 100% operacional! 🚀"""
        
        else:
            # Resposta contextual inteligente
            return f"""🤔 Interessante! Você disse: "{text[:150]}{'...' if len(text) > 150 else ''}"

💡 *Para respostas mais inteligentes:*
Configure uma chave de API no arquivo .env:
• `OPENAI_API_KEY=sua_chave_aqui`
• `ANTHROPIC_API_KEY=sua_chave_aqui`

Enquanto isso, posso ajudá-lo com:
• Conversas básicas
• Informações sobre o sistema
• Comandos especiais

Digite 'ajuda' para ver todas as opções! 😊"""

    async def _fallback_response(self, input_data: AgnoInput) -> AgnoOutput:
        """
        Resposta de fallback em caso de erro crítico
        """
        return AgnoOutput(
            to_number=input_data.from_number,
            message_type=MessageType.TEXT,
            text_content="🚨 Desculpe, ocorreu um erro interno. Tente novamente em alguns instantes.\n\nSe o problema persistir, digite 'status' para verificar o sistema.",
            delay_seconds=1,
            metadata={"agent": self.name, "fallback": True}
        )

    def _get_conversation_context(self, phone_number: str) -> List[Dict]:
        """
        Obtém contexto da conversa
        """
        return self.conversation_context.get(phone_number, [])

    def _update_conversation_context(
        self, 
        phone_number: str, 
        user_message: str, 
        bot_response: str
    ) -> None:
        """
        Atualiza contexto da conversa
        """
        if phone_number not in self.conversation_context:
            self.conversation_context[phone_number] = []
        
        context = self.conversation_context[phone_number]
        
        # Adicionar nova interação
        context.append({
            "user": user_message,
            "bot": bot_response,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Manter apenas últimas interações
        if len(context) > self.max_context_messages:
            context.pop(0)

    async def initialize(self) -> None:
        """
        Inicializa o agente IA
        """
        await super().initialize()
        
        # Inicializar cliente HTTP
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Verificar configurações de IA
        ai_configured = bool(self.openai_api_key or self.anthropic_api_key)
        
        self.logger.info(
            "AIWhatsAppAgent inicializado",
            ai_configured=ai_configured,
            openai_available=bool(self.openai_api_key),
            anthropic_available=bool(self.anthropic_api_key),
            model=self.preferred_model
        )

    async def cleanup(self) -> None:
        """
        Limpa recursos do agente
        """
        self.logger.info("Limpando recursos do AIWhatsAppAgent")
        
        # Fechar cliente HTTP
        if self.http_client:
            await self.http_client.aclose()
        
        # Limpar contexto
        self.conversation_context.clear()
        
        await super().cleanup()

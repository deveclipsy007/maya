# 🧠 Integração Framework Agno + WhatsApp

Guia completo para integrar seu agente do framework Agno com WhatsApp via Evolution API.

## 🎯 Como Funciona

```
Mensagem WhatsApp → Evolution API → Webhook → Agno Agent → Resposta → WhatsApp
```

## 🚀 Integração Rápida (3 Passos)

### 1. Importe seu Agente Agno

```python
# No arquivo examples/agno_whatsapp_bot.py
# Substitua a classe MeuAgenteAgno pela importação do seu agente

# Exemplo:
from meu_framework_agno import MeuAgente
meu_agente_agno = MeuAgente.load("caminho/para/seu/agente")
```

### 2. Adapte o Método de Processamento

Na classe `AgnoWhatsAppBridge`, adapte o método `_call_agno_agent()`:

```python
def _call_agno_agent(self, message: str, user_id: str, context: Dict = None) -> Optional[str]:
    try:
        # ADAPTE PARA SEU AGENTE AGNO
        
        # Se seu agente tem método 'chat':
        return self.agno_agent.chat(message, user_id=user_id)
        
        # Se seu agente tem método 'process':
        return self.agno_agent.process(message, context=context)
        
        # Se seu agente tem método 'generate_response':
        return self.agno_agent.generate_response(message, user_context=context)
        
        # Se seu agente é callable:
        return self.agno_agent(message, user_id=user_id)
        
    except Exception as e:
        self.logger.error(f"Erro ao chamar agente Agno: {e}")
        return None
```

### 3. Execute

```bash
python examples/agno_whatsapp_bot.py
```

## 📋 Exemplos de Integração

### Exemplo 1: Agente com método `chat()`

```python
# Seu agente Agno
class MeuAgenteAgno:
    def chat(self, message: str, user_id: str = None) -> str:
        # Sua lógica aqui
        return "Resposta do agente"

# Integração
from core.agno_integration import AgnoWhatsAppBridge
from core import WhatsAppClient

agente = MeuAgenteAgno()
whatsapp = WhatsAppClient()
bridge = AgnoWhatsAppBridge(agente, whatsapp)

# Processa mensagem
bridge.process_message("5511999999999", "Olá!")
```

### Exemplo 2: Agente com contexto

```python
class MeuAgenteAgno:
    def process(self, message: str, user_id: str, context: dict = None) -> str:
        # Usa contexto da conversa
        historico = context.get('messages', []) if context else []
        
        # Sua lógica com contexto
        resposta = self.gerar_resposta(message, historico)
        return resposta

# A ponte automaticamente mantém o contexto
bridge = AgnoWhatsAppBridge(agente, whatsapp)
bridge.set_context_enabled(True)  # Habilita contexto
```

### Exemplo 3: Agente assíncrono

```python
import asyncio

class MeuAgenteAgnoAsync:
    async def chat_async(self, message: str, user_id: str) -> str:
        # Processamento assíncrono
        await asyncio.sleep(0.1)  # Simula processamento
        return "Resposta assíncrona"

# Adapte o método _call_agno_agent para async:
def _call_agno_agent(self, message: str, user_id: str, context: Dict = None) -> Optional[str]:
    try:
        # Para agentes assíncronos
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.agno_agent.chat_async(message, user_id)
        )
    except Exception as e:
        self.logger.error(f"Erro: {e}")
        return None
```

## 🔧 Configurações Avançadas

### Contexto de Conversa

```python
# Habilitar/desabilitar contexto
bridge.set_context_enabled(True)

# Limpar contexto de um usuário
bridge.clear_user_context("5511999999999")

# Acessar contexto manualmente
context = bridge._get_user_context("5511999999999")
print(context['messages'])  # Histórico da conversa
```

### Personalização de Respostas

```python
class MeuAgentePersonalizado:
    def __init__(self):
        self.personalidade = "amigável"
        self.empresa = "Minha Empresa"
    
    def process(self, message: str, user_id: str, context: dict = None) -> str:
        # Adiciona personalidade às respostas
        resposta_base = self.processar_logica(message)
        
        if self.personalidade == "amigável":
            return f"😊 {resposta_base}\n\nEquipe {self.empresa}"
        else:
            return resposta_base
```

## 🧪 Testes

### Teste Direto do Agente

```bash
curl -X POST http://localhost:5000/agno/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, como você está?", "user_id": "test"}'
```

### Teste via WhatsApp

```bash
# Envio com processamento Agno
curl -X POST http://localhost:5000/send \
  -H "Content-Type: application/json" \
  -d '{"number": "5511999999999", "message": "teste", "use_agno": true}'
```

### Verificar Status

```bash
curl http://localhost:5000/status
```

## 🔌 Adaptações Comuns

### Para diferentes frameworks Agno:

```python
# Framework Agno v1
def _call_agno_agent(self, message, user_id, context):
    return self.agno_agent.chat(message, user_id)

# Framework Agno v2 com contexto
def _call_agno_agent(self, message, user_id, context):
    return self.agno_agent.process(
        input_text=message,
        user_context=context,
        session_id=user_id
    )

# Framework Agno com configurações
def _call_agno_agent(self, message, user_id, context):
    config = {
        'temperature': 0.7,
        'max_tokens': 150,
        'user_id': user_id
    }
    return self.agno_agent.generate(message, **config)
```

## 📊 Monitoramento

O sistema automaticamente loga:

- 📨 Mensagens recebidas
- 🧠 Processamento pelo Agno
- ✅ Respostas enviadas
- ❌ Erros e falhas

```python
# Logs típicos:
# [2024-01-01 10:00:00] INFO: 📨 Mensagem para Agno de 5511999999999: Olá!
# [2024-01-01 10:00:01] INFO: 🧠 Processando com Agno: Olá!
# [2024-01-01 10:00:02] INFO: ✅ Resposta Agno enviada para 5511999999999
```

## 🚨 Troubleshooting

### Agente não responde
1. Verifique se o método do agente está correto
2. Teste o agente isoladamente com `/agno/test`
3. Verifique os logs para erros

### Contexto não funciona
1. Verifique se `enable_context=True`
2. Confirme se o agente aceita parâmetro `context`

### Performance lenta
1. Considere processamento assíncrono
2. Implemente cache de respostas
3. Otimize o agente Agno

## 🎯 Casos de Uso

- ✅ **Atendimento ao cliente** com IA
- ✅ **Vendas automatizadas** 
- ✅ **Suporte técnico** inteligente
- ✅ **FAQ dinâmico**
- ✅ **Agendamento** de serviços
- ✅ **Coleta de feedback**

## 🔄 Próximos Passos

1. **Teste** com seu agente Agno
2. **Personalize** as respostas
3. **Configure** contexto se necessário
4. **Deploy** em produção
5. **Monitore** performance

---

**🎉 Seu agente Agno está pronto para WhatsApp!**
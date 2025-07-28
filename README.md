# 🤖 Agente WhatsApp Modular

Sistema modular e reutilizável para automação de mensagens WhatsApp via Evolution API.

## 🎯 Características

✅ **Modular** - Componentes independentes e reutilizáveis  
✅ **Limpo** - Código organizado e fácil de entender  
✅ **Plug & Play** - Fácil integração em outros projetos  
✅ **Configurável** - Respostas e comportamentos personalizáveis  
✅ **Robusto** - Tratamento de erros e logs detalhados  

## 📁 Estrutura Modular

```
├── docker-compose.yml          # Evolution API v1.8.2
├── whatsapp-agent/
│   ├── app.py                 # 🚀 Aplicação principal
│   ├── quick_start.py         # ⚡ Início rápido
│   ├── .env                   # ⚙️ Configurações
│   ├── requirements.txt       # 📦 Dependências
│   ├── core/                  # 🧠 Módulos principais
│   │   ├── __init__.py
│   │   ├── whatsapp_client.py    # 📱 Cliente WhatsApp
│   │   ├── message_handler.py    # 💬 Processador de mensagens
│   │   └── response_generator.py # 🤖 Gerador de respostas
│   └── examples/              # 📚 Exemplos de uso
│       ├── custom_responses.py
│       └── send_message.py
```

## 🚀 Início Rápido

### 1. Configuração Inicial
```bash
# Inicie a Evolution API
docker-compose up -d

# Instale dependências
cd whatsapp-agent
pip install -r requirements.txt
```

### 2. Quick Start
```bash

### 1. Ambiente Virtual

```bash
python -m venv .venv
python app.py
```

## 💬 Como Usar

### Envio Programático
```python
from core import WhatsAppClient

client = WhatsAppClient()
client.send_message("5511999999999", "Olá! Como posso ajudar?")
```

### Respostas Personalizadas
```python
from core import ResponseGenerator

# Cria gerador personalizado
response_gen = ResponseGenerator()

# Adiciona padrões customizados
response_gen.add_custom_pattern(
    category="vendas",
    patterns=["preço", "valor", "quanto custa"],
    responses=["Entre em contato com nossa equipe comercial! 💰"]
)
```

### API REST
```bash
# Enviar mensagem via API
curl -X POST http://localhost:5000/send \
  -H "Content-Type: application/json" \
  -d '{"number": "5511999999999", "message": "Sua mensagem"}'

# Verificar status
curl http://localhost:5000/status
```

## 🔧 Endpoints da API

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Informações da API |
| `/status` | GET | Status do agente |
| `/send` | POST | Enviar mensagem |
| `/webhook` | POST | Receber mensagens (Evolution API) |

## 🤖 Respostas Inteligentes

O agente responde automaticamente para:

- **Saudações**: "oi", "olá", "bom dia" → Mensagens de boas-vindas
- **Despedidas**: "tchau", "até logo" → Mensagens de despedida  
- **Agradecimentos**: "obrigado", "valeu" → Mensagens de cortesia
- **Ajuda**: "ajuda", "help" → Lista de funcionalidades
- **Sobre**: "quem é você", "bot" → Informações do agente
- **Outras**: Resposta personalizada com eco da mensagem

## 🔌 Integração em Outros Projetos

### Opção 1: Copiar Módulos Core
```bash
# Copie a pasta core/ para seu projeto
cp -r whatsapp-agent/core/ seu-projeto/
```

### Opção 2: Usar como Submódulo
```bash
# Adicione como submódulo Git
git submodule add https://github.com/seu-repo/whatsapp-agent.git
```

### Opção 3: Importar Diretamente
```python
# No seu projeto
import sys
sys.path.append('caminho/para/whatsapp-agent')

from core import WhatsAppClient, MessageHandler, ResponseGenerator
```

## ⚙️ Configuração (.env)

```env
EVOLUTION_API_URL=http://localhost:8080
INSTANCE_NAME=agente_bot
API_KEY=1234
```

## 📚 Exemplos Práticos

### Bot de Vendas
```python
from core import ResponseGenerator

sales_bot = ResponseGenerator()
sales_bot.add_custom_pattern(
    "produtos",
    ["produto", "catálogo", "o que vocês vendem"],
    ["Temos diversos produtos! Acesse nosso catálogo: link.com 🛒"]
)
```

### Bot de Suporte
```python
support_bot = ResponseGenerator()
support_bot.add_custom_pattern(
    "suporte",
    ["problema", "erro", "não funciona"],
    ["Vou te ajudar! Descreva o problema detalhadamente 🔧"]
)
```

## 🐳 Docker

```bash
# Iniciar Evolution API
docker-compose up -d

# Parar serviços  
docker-compose down

# Ver logs
docker-compose logs -f evolution-api
```

## 🔍 Monitoramento

Logs estruturados mostram:
- 📨 Mensagens recebidas
- 🤖 Respostas geradas  
- ✅ Envios bem-sucedidos
- ❌ Erros e falhas

## � Troubleshooting

### Evolution API não responde
```bash
# Verificar se está rodando
docker ps | grep evolution

# Verificar logs
docker logs evolution-api
```

### Webhook não funciona
1. Verifique se o agente está rodando na porta 5000
2. Confirme se o WhatsApp está conectado
3. Verifique os logs do agente

## 🎯 Casos de Uso

- ✅ **Atendimento automatizado**
- ✅ **Notificações de sistema**  
- ✅ **Bot de vendas**
- ✅ **Suporte técnico**
- ✅ **Campanhas de marketing**
- ✅ **Integração com CRM**

## 🔄 Próximas Versões

- [ ] Interface web de gerenciamento
- [ ] Integração com IA (GPT, Claude)
- [ ] Suporte a mídias (imagens, áudios)
- [ ] Banco de dados para histórico
- [ ] Agendamento de mensagens
- [ ] Métricas e analytics

---

**🎉 Sistema modular pronto para produção!**


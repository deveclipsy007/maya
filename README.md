# 🌿 Maya HopeCann - Atendente Virtual

**Maya** é uma atendente virtual especializada em agendamento de consultas médicas para cannabis medicinal, integrada com WhatsApp via Evolution API.

## ✨ Funcionalidades Principais

🎙️ **Transcrição de Áudio** - Converte áudios WhatsApp em texto usando OpenAI Whisper  
🤖 **IA Conversacional** - Respostas naturais e inteligentes com Agno Framework  
📅 **Agendamento Inteligente** - Agenda consultas automaticamente  
🎥 **Google Meet** - Cria reuniões automáticas para consultas  
💾 **Memória Persistente** - Lembra conversas e preferências dos pacientes  
🔗 **Integração Completa** - Supabase, OpenAI, Evolution API, Google Calendar  

## 🚀 Deploy Web

### Render (Recomendado)

1. **Fork este repositório**
2. **Configure no [Render](https://render.com):**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Environment: Python 3

3. **Variáveis de Ambiente:**
```env
OPENAI_API_KEY=sk-...
EVOLUTION_API_URL=https://sua-evolution-api.com
EVOLUTION_API_KEY=sua-chave
EVOLUTION_INSTANCE_NAME=maya-bot
SUPABASE_URL=https://projeto.supabase.co
SUPABASE_KEY=sua-chave
```

## 🛠️ Desenvolvimento Local

```bash
# 1. Clone o repositório
git clone https://github.com/deveclipsy007/maya.git
cd maya

# 2. Instale dependências
pip install -r requirements.txt

# 3. Configure .env
cp .env.example .env
# Edite .env com suas chaves

# 4. Execute
python maya_hopecann.py
```

## 📡 API Endpoints

- `POST /webhook` - Recebe mensagens WhatsApp
- `GET /health` - Status do sistema
- `GET /agendamentos` - Lista agendamentos
- `GET /medicos` - Lista médicos disponíveis

## 🏗️ Arquitetura

```
├── app.py                 # 🚀 Ponto de entrada (deploy)
├── maya_hopecann.py       # 🧠 Aplicação principal
├── requirements.txt       # 📦 Dependências
├── render.yaml           # ⚙️ Configuração Render
├── agents/               # 🤖 Agentes especializados
├── evolution_client/     # 📱 Cliente Evolution API
└── webhook_server/       # 🔗 Servidor de webhooks
```

## 🔐 Segurança

- ✅ Variáveis de ambiente para credenciais
- ✅ Arquivos sensíveis no `.gitignore`
- ✅ Validação robusta de entrada
- ✅ Logs sem informações pessoais

## 📖 Documentação

- [README_DEPLOY.md](README_DEPLOY.md) - Guia completo de deploy
- [GUIA_MAYA_HOPECANN.md](GUIA_MAYA_HOPECANN.md) - Documentação técnica
- [EVOLUTION_API_CONFIG.md](EVOLUTION_API_CONFIG.md) - Configuração Evolution API

---

**Maya HopeCann** - Transformando o atendimento médico com IA 🌿
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

=======
# maya
>>>>>>> 7e84ea569a577f9f9f6f3053d34f6ada10123d05

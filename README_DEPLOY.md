# 🌿 Maya HopeCann - Atendente Virtual

Maya é uma atendente virtual especializada em agendamento de consultas médicas para cannabis medicinal, integrada com WhatsApp via Evolution API.

## 🚀 Deploy Web (Render)

### Pré-requisitos
- Conta no [Render](https://render.com)
- Repositório no GitHub
- Chaves de API configuradas

### Configuração Rápida

1. **Fork/Clone este repositório**
2. **Configure as variáveis de ambiente no Render:**

```env
# OpenAI (obrigatório)
OPENAI_API_KEY=sk-...

# Evolution API (obrigatório)
EVOLUTION_API_URL=https://sua-evolution-api.com
EVOLUTION_API_KEY=sua-chave-api
EVOLUTION_INSTANCE_NAME=maya-bot

# Supabase (opcional)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-supabase

# Google Meet (opcional)
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
```

3. **Deploy automático:**
   - Conecte seu repositório GitHub no Render
   - O arquivo `render.yaml` já está configurado
   - Deploy será automático a cada push

### Estrutura do Projeto

```
├── app.py                 # 🚀 Ponto de entrada para deploy
├── maya_hopecann.py       # 🧠 Aplicação principal Maya
├── requirements.txt       # 📦 Dependências Python
├── render.yaml           # ⚙️ Configuração Render
├── .gitignore            # 🚫 Arquivos ignorados
└── agents/               # 🤖 Agentes especializados
```

## 🔧 Funcionalidades

✅ **Transcrição de Áudio** - Converte áudios WhatsApp em texto  
✅ **Agendamento Inteligente** - Agenda consultas automaticamente  
✅ **Google Meet** - Cria reuniões automáticas  
✅ **Memória de Contatos** - Lembra conversas anteriores  
✅ **Respostas Naturais** - IA conversacional avançada  
✅ **Suporte Multimídia** - Processa áudio, texto e imagens  

## 🛠️ Desenvolvimento Local

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/maya-hopecann.git
cd maya-hopecann

# 2. Instale dependências
pip install -r requirements.txt

# 3. Configure .env
cp .env.example .env
# Edite .env com suas chaves

# 4. Execute localmente
python maya_hopecann.py
```

## 📡 Endpoints da API

- `POST /webhook` - Recebe mensagens WhatsApp
- `GET /health` - Status do sistema
- `GET /agendamentos` - Lista agendamentos
- `GET /medicos` - Lista médicos disponíveis

## 🔐 Segurança

- Todas as credenciais via variáveis de ambiente
- Arquivos sensíveis no `.gitignore`
- Logs sem informações pessoais
- Validação de entrada robusta

## 📞 Suporte

Para dúvidas sobre deploy ou configuração, consulte a documentação do Render ou abra uma issue neste repositório.

---

**Maya HopeCann** - Transformando o atendimento médico com IA 🌿

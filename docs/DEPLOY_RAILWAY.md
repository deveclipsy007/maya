# 🚀 Deploy Maya HopeCann no Railway

Este guia explica como fazer deploy da aplicação Maya HopeCann no Railway usando a moderna estrutura TOML.

## 📋 Pré-requisitos

1. **Conta no Railway**: [railway.app](https://railway.app)
2. **Node.js**: Para instalar o Railway CLI
3. **Git**: Para versionamento do código

## 🛠️ Instalação Railway CLI

### Windows (PowerShell)
```powershell
npm install -g @railway/cli
```

### Linux/macOS
```bash
npm install -g @railway/cli
```

## 🔐 Autenticação

```bash
railway login
```

## 📁 Estrutura do Projeto

O projeto está organizado com a moderna estrutura TOML:

```
maya-hopecann/
├── pyproject.toml          # Configuração moderna Python
├── railway.toml            # Configurações Railway
├── requirements.txt        # Dependências (backup)
├── Dockerfile             # Container Docker
├── .env.example           # Exemplo variáveis ambiente
├── src/
│   ├── main.py            # Entrada FastAPI
│   ├── core/              # Lógica principal
│   ├── utils/             # Utilitários
│   ├── integrations/      # APIs externas
│   └── agents/            # Sistema de agentes
├── config/                # Configurações
├── docs/                  # Documentação
└── scripts/               # Scripts deploy
```

## 🚀 Deploy Automático

### Opção 1: Script PowerShell (Windows)
```powershell
.\scripts\deploy-railway.ps1
```

### Opção 2: Script Bash (Linux/macOS)
```bash
chmod +x scripts/deploy-railway.sh
./scripts/deploy-railway.sh
```

### Opção 3: Deploy Manual

1. **Criar projeto**:
```bash
railway project:create maya-hopecann
```

2. **Conectar repositório**:
```bash
railway link
```

3. **Configurar variáveis**:
```bash
railway variables:set PORT=8000
railway variables:set ENVIRONMENT=production
railway variables:set PYTHONPATH=/app/src
```

4. **Deploy**:
```bash
railway up
```

## ⚙️ Variáveis de Ambiente Obrigatórias

Configure no Railway Dashboard:

### APIs Essenciais
```env
OPENAI_API_KEY=sk-your-openai-key
ASSEMBLYAI_API_KEY=your-assemblyai-key
EVOLUTION_API_URL=https://your-evolution-api.com
EVOLUTION_API_KEY=your-evolution-key
```

### Banco de Dados
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

### Configurações App
```env
PORT=8000
ENVIRONMENT=production
SECRET_KEY=your-secret-key
WEBHOOK_URL=https://your-app.railway.app/webhook
```

## 📊 Monitoramento

### Health Check
```
GET https://your-app.railway.app/health
```

### Status Sistema
```
GET https://your-app.railway.app/status
```

### Logs
```bash
railway logs
```

## 🔧 Configuração Evolution API

Após deploy, configure o webhook no Evolution API:

```json
{
  "webhook": {
    "url": "https://your-app.railway.app/webhook",
    "events": ["messages.upsert", "messages.update"]
  }
}
```

## 📈 Recursos Railway

- **Auto-deploy**: A cada push no GitHub
- **Logs em tempo real**: Via dashboard
- **Métricas**: CPU, memória, requests
- **Custom domain**: Configurável
- **Environment variables**: Interface web
- **Database**: PostgreSQL integrado

## 🐛 Troubleshooting

### Erro de Build
```bash
# Verificar logs
railway logs --deployment

# Rebuild
railway up --detach
```

### Erro de Variáveis
```bash
# Listar variáveis
railway variables

# Definir variável
railway variables:set KEY=value
```

### Erro de Conectividade
```bash
# Verificar status
railway status

# Reiniciar serviço
railway restart
```

## 📚 Links Úteis

- **Railway Dashboard**: https://railway.app/dashboard
- **Documentação Railway**: https://docs.railway.app
- **Railway CLI**: https://docs.railway.app/develop/cli
- **FastAPI Docs**: Acessível em `/docs` após deploy
- **Logs**: Acessível via dashboard ou CLI

## 🎯 Próximos Passos

1. ✅ Deploy realizado
2. ⚙️ Configurar variáveis de ambiente
3. 🔗 Configurar webhook Evolution API
4. 🧪 Testar endpoints
5. 📊 Monitorar logs e métricas
6. 🌐 Configurar domínio personalizado (opcional)

---

**✨ Maya HopeCann está pronta para produção no Railway!**

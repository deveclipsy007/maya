#!/bin/bash

# Maya HopeCann - Script de Deploy para Railway
echo "🌿 Maya HopeCann - Deploy Railway"
echo "================================="

# Verificar se Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI não encontrado. Instalando..."
    npm install -g @railway/cli
fi

# Login no Railway (se necessário)
echo "🔑 Verificando autenticação Railway..."
railway whoami || railway login

# Criar projeto se não existir
echo "📁 Configurando projeto..."
railway project:create maya-hopecann

# Conectar ao projeto
railway link

# Configurar variáveis de ambiente
echo "⚙️  Configurando variáveis de ambiente..."
railway variables:set PORT=8000
railway variables:set ENVIRONMENT=production
railway variables:set PYTHONPATH=/app/src
railway variables:set PYTHONUNBUFFERED=1

# Fazer deploy
echo "🚀 Iniciando deploy..."
railway up --detach

# Mostrar status
echo "📊 Status do deploy:"
railway status

# Mostrar logs
echo "📝 Logs do deploy:"
railway logs

echo "✅ Deploy concluído!"
echo "🌐 URL: $(railway domain)"
echo "📊 Dashboard: https://railway.app/dashboard"

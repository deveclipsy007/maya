# Maya HopeCann - Script de Deploy para Railway (PowerShell)
Write-Host "🌿 Maya HopeCann - Deploy Railway" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Verificar se Railway CLI está instalado
$railwayExists = Get-Command "railway" -ErrorAction SilentlyContinue
if (-not $railwayExists) {
    Write-Host "❌ Railway CLI não encontrado. Instalando..." -ForegroundColor Red
    npm install -g @railway/cli
}

# Login no Railway (se necessário)
Write-Host "🔑 Verificando autenticação Railway..." -ForegroundColor Cyan
railway whoami
if ($LASTEXITCODE -ne 0) {
    railway login
}

# Criar projeto se não existir
Write-Host "📁 Configurando projeto..." -ForegroundColor Yellow
railway project:create maya-hopecann

# Conectar ao projeto
railway link

# Configurar variáveis de ambiente
Write-Host "⚙️  Configurando variáveis de ambiente..." -ForegroundColor Magenta
railway variables:set PORT=8000
railway variables:set ENVIRONMENT=production
railway variables:set PYTHONPATH=/app/src
railway variables:set PYTHONUNBUFFERED=1

# Fazer deploy
Write-Host "🚀 Iniciando deploy..." -ForegroundColor Blue
railway up --detach

# Mostrar status
Write-Host "📊 Status do deploy:" -ForegroundColor Green
railway status

# Mostrar logs
Write-Host "📝 Logs do deploy:" -ForegroundColor Cyan
railway logs

Write-Host "✅ Deploy concluído!" -ForegroundColor Green
Write-Host "🌐 URL: $(railway domain)" -ForegroundColor Blue
Write-Host "📊 Dashboard: https://railway.app/dashboard" -ForegroundColor Blue

Write-Host "`n📋 Próximos passos:" -ForegroundColor Yellow
Write-Host "1. Configure as variáveis de ambiente no dashboard do Railway" -ForegroundColor White
Write-Host "2. Adicione seus tokens de API (OpenAI, AssemblyAI, etc.)" -ForegroundColor White
Write-Host "3. Configure o webhook URL no Evolution API" -ForegroundColor White
Write-Host "4. Teste a aplicação com o endpoint /health" -ForegroundColor White

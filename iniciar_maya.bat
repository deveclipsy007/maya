@echo off
echo ========================================
echo      INICIANDO SISTEMA MAYA AI
echo ========================================
echo.

:: Definir variáveis
set DOCKER_CONTAINER=evolution-api
set WEBHOOK_IP=192.168.15.8
set WEBHOOK_PORT=5000
set EVOLUTION_PORT=8090
set API_KEY=1234
set INSTANCE=agente_bot

:: Cores para output
echo [32m1. Verificando Docker...[0m
docker --version >nul 2>&1
if errorlevel 1 (
    echo [31mERRO: Docker não encontrado! Instale o Docker primeiro.[0m
    pause
    exit /b 1
)

echo [32m2. Parando containers antigos...[0m
docker stop %DOCKER_CONTAINER% >nul 2>&1
docker rm %DOCKER_CONTAINER% >nul 2>&1

echo [32m3. Iniciando Evolution API...[0m
docker run -d ^
  --name %DOCKER_CONTAINER% ^
  -p %EVOLUTION_PORT%:8080 ^
  -v evolution_instances:/evolution/instances ^
  -v evolution_store:/evolution/store ^
  atendai/evolution-api:v1.8.2

if errorlevel 1 (
    echo [31mERRO: Falha ao iniciar Evolution API[0m
    pause
    exit /b 1
)

echo [32m4. Aguardando Evolution API inicializar...[0m
:wait_evolution
timeout /t 3 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://localhost:%EVOLUTION_PORT% | findstr "200\|404" >nul
if errorlevel 1 (
    echo Aguardando Evolution API... 
    goto wait_evolution
)

echo [32m5. Evolution API iniciado com sucesso![0m

echo [32m6. Configurando webhook...[0m
powershell -Command ^
"$webhookConfig = @{ ^
    url = 'http://%WEBHOOK_IP%:%WEBHOOK_PORT%/webhook'; ^
    enabled = $true; ^
    events = @('MESSAGES_UPSERT'); ^
    webhook_by_events = $false; ^
    webhook_base64 = $true ^
} | ConvertTo-Json; ^
try { ^
    Invoke-RestMethod -Uri 'http://localhost:%EVOLUTION_PORT%/webhook/set/%INSTANCE%' -Method POST -Body $webhookConfig -ContentType 'application/json' -Headers @{'apikey'='%API_KEY%'} | Out-Null; ^
    Write-Host 'Webhook configurado com sucesso!' -ForegroundColor Green ^
} catch { ^
    Write-Host 'Erro ao configurar webhook:' $_.Exception.Message -ForegroundColor Red ^
}"

echo [32m7. Verificando status da instância...[0m
powershell -Command ^
"try { ^
    $status = Invoke-RestMethod -Uri 'http://localhost:%EVOLUTION_PORT%/instance/connectionState/%INSTANCE%' -Headers @{'apikey'='%API_KEY%'}; ^
    Write-Host 'Instância %INSTANCE%:' $status.instance.state -ForegroundColor Yellow ^
} catch { ^
    Write-Host 'Instância não encontrada - será criada automaticamente ao conectar WhatsApp' -ForegroundColor Yellow ^
}"

echo.
echo [32m8. Iniciando servidor Maya...[0m
echo [33mSistema Evolution API rodando em: http://localhost:%EVOLUTION_PORT%[0m
echo [33mWebhook configurado para: http://%WEBHOOK_IP%:%WEBHOOK_PORT%/webhook[0m
echo [33mInstância WhatsApp: %INSTANCE%[0m
echo.
echo [36mPara conectar o WhatsApp, acesse: http://localhost:%EVOLUTION_PORT%[0m
echo [36mPara parar o sistema, pressione Ctrl+C[0m
echo.

:: Iniciar servidor Maya
python webhook_flask.py

:: Se chegar aqui, o servidor foi interrompido
echo.
echo [33mServidor Maya parado.[0m
echo [32mPara parar completamente o sistema, execute: docker stop %DOCKER_CONTAINER%[0m
pause

@echo off
echo ========================================
echo       STATUS SISTEMA MAYA AI
echo ========================================
echo.

:: Definir variáveis
set DOCKER_CONTAINER=evolution-api
set EVOLUTION_PORT=8090
set WEBHOOK_PORT=5000
set API_KEY=1234
set INSTANCE=agente_bot

echo [32m1. Verificando Docker...[0m
docker ps --filter "name=%DOCKER_CONTAINER%" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo [32m2. Verificando Evolution API...[0m
powershell -Command ^
"try { ^
    $response = Invoke-RestMethod -Uri 'http://localhost:%EVOLUTION_PORT%' -TimeoutSec 5; ^
    Write-Host 'Evolution API: ONLINE' -ForegroundColor Green ^
} catch { ^
    Write-Host 'Evolution API: OFFLINE' -ForegroundColor Red ^
}"

echo.
echo [32m3. Verificando instância WhatsApp...[0m
powershell -Command ^
"try { ^
    $status = Invoke-RestMethod -Uri 'http://localhost:%EVOLUTION_PORT%/instance/connectionState/%INSTANCE%' -Headers @{'apikey'='%API_KEY%'} -TimeoutSec 5; ^
    $state = $status.instance.state; ^
    if ($state -eq 'open') { ^
        Write-Host 'WhatsApp (%INSTANCE%): CONECTADO' -ForegroundColor Green ^
    } else { ^
        Write-Host 'WhatsApp (%INSTANCE%):' $state -ForegroundColor Yellow ^
    } ^
} catch { ^
    Write-Host 'WhatsApp (%INSTANCE%): NÃO ENCONTRADO' -ForegroundColor Red ^
}"

echo.
echo [32m4. Verificando webhook...[0m
powershell -Command ^
"try { ^
    $webhook = Invoke-RestMethod -Uri 'http://localhost:%EVOLUTION_PORT%/webhook/find/%INSTANCE%' -Headers @{'apikey'='%API_KEY%'} -TimeoutSec 5; ^
    if ($webhook.enabled) { ^
        Write-Host 'Webhook: CONFIGURADO (' $webhook.url ')' -ForegroundColor Green ^
    } else { ^
        Write-Host 'Webhook: DESABILITADO' -ForegroundColor Yellow ^
    } ^
} catch { ^
    Write-Host 'Webhook: NÃO CONFIGURADO' -ForegroundColor Red ^
}"

echo.
echo [32m5. Verificando servidor Maya...[0m
powershell -Command ^
"try { ^
    $response = Invoke-RestMethod -Uri 'http://localhost:%WEBHOOK_PORT%/health' -TimeoutSec 5; ^
    Write-Host 'Servidor Maya: ONLINE' -ForegroundColor Green ^
} catch { ^
    Write-Host 'Servidor Maya: OFFLINE' -ForegroundColor Red ^
}"

echo.
echo [32m6. Processos Python ativos...[0m
tasklist /fi "imagename eq python.exe" /fo table 2>nul | findstr python.exe
if errorlevel 1 (
    echo [33mNenhum processo Python encontrado.[0m
)

echo.
echo [36m========================================[0m
echo [36mURLs importantes:[0m
echo [36mEvolution API: http://localhost:%EVOLUTION_PORT%[0m
echo [36mServidor Maya: http://localhost:%WEBHOOK_PORT%[0m
echo [36mWebhook Status: http://localhost:%WEBHOOK_PORT%/mensagens[0m
echo [36m========================================[0m
echo.
pause

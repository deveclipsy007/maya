@echo off
echo ========================================
echo    RECONECTANDO WHATSAPP - MAYA AI
echo ========================================
echo.

:: Definir variáveis
set EVOLUTION_PORT=8090
set API_KEY=1234
set INSTANCE=agente_bot

echo [32mVerificando status atual...[0m
powershell -Command ^
"try { ^
    $status = Invoke-RestMethod -Uri 'http://localhost:%EVOLUTION_PORT%/instance/connectionState/%INSTANCE%' -Headers @{'apikey'='%API_KEY%'}; ^
    Write-Host 'Status atual:' $status.instance.state -ForegroundColor Yellow ^
} catch { ^
    Write-Host 'Erro ao verificar status' -ForegroundColor Red; ^
    exit 1 ^
}"

echo.
echo [33mPara reconectar o WhatsApp:[0m
echo [36m1. Acesse: http://localhost:%EVOLUTION_PORT%[0m
echo [36m2. Vá para a seção "Instance"[0m
echo [36m3. Encontre a instância "%INSTANCE%"[0m
echo [36m4. Clique em "Connect" para gerar QR Code[0m
echo [36m5. Escaneie o QR Code com seu WhatsApp[0m
echo.

echo [32mAbrindo Evolution API no navegador...[0m
start http://localhost:%EVOLUTION_PORT%

echo.
echo [33mApós conectar o WhatsApp, o sistema estará pronto![0m
echo.
pause

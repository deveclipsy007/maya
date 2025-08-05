@echo off
echo ========================================
echo      PARANDO SISTEMA MAYA AI
echo ========================================
echo.

:: Definir variáveis
set DOCKER_CONTAINER=evolution-api

echo [32m1. Parando servidor Maya...[0m
taskkill /f /im python.exe >nul 2>&1
if not errorlevel 1 (
    echo [32mServidor Maya parado.[0m
) else (
    echo [33mServidor Maya não estava rodando.[0m
)

echo [32m2. Parando Evolution API (Docker)...[0m
docker stop %DOCKER_CONTAINER% >nul 2>&1
if not errorlevel 1 (
    echo [32mEvolution API parado.[0m
) else (
    echo [33mEvolution API não estava rodando.[0m
)

echo [32m3. Removendo container...[0m
docker rm %DOCKER_CONTAINER% >nul 2>&1

echo.
echo [32mSistema Maya AI parado completamente![0m
echo [33mPara reiniciar, execute: iniciar_maya.bat[0m
echo.
pause

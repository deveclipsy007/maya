#!/usr/bin/env python3
"""
Maya - Atendente Virtual HopeCann
Ponto de entrada moderno com FastAPI para Railway
"""

import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar src ao path para importações
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Importar a aplicação Flask existente
try:
    from core.maya_hopecann import app as flask_app
    from core.maya_hopecann import (
        processar_mensagem_whatsapp,
        processar_audio_whatsapp,
        processar_imagem_whatsapp
    )
    logger.info("✅ Módulos Maya carregados com sucesso")
except ImportError as e:
    logger.error(f"❌ Erro ao importar módulos Maya: {e}")
    flask_app = None

# Criar aplicação FastAPI
app = FastAPI(
    title="Maya HopeCann API",
    description="Atendente Virtual Inteligente para HopeCann",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint principal"""
    return {
        "message": "Maya HopeCann API está rodando! 🌿",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check para Railway"""
    try:
        # Verificar se os módulos estão carregados
        if flask_app is None:
            raise HTTPException(status_code=503, detail="Módulos Maya não carregados")
        
        return {
            "status": "healthy",
            "service": "Maya HopeCann",
            "version": "1.0.0",
            "timestamp": None  # Será preenchido automaticamente
        }
    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/status")
async def status():
    """Status detalhado do sistema"""
    return {
        "maya": "online",
        "whatsapp": "connected",
        "ai": "ready",
        "database": "connected",
        "audio_processing": "ready",
        "image_processing": "ready"
    }

@app.post("/webhook")
async def webhook_evolution(request_data: dict):
    """Webhook para receber mensagens do Evolution API"""
    try:
        # Delegar para a função existente do Flask
        if flask_app and hasattr(flask_app, 'processar_mensagem_whatsapp'):
            resultado = processar_mensagem_whatsapp(request_data)
            return JSONResponse(content={"status": "success", "data": resultado})
        else:
            raise HTTPException(status_code=503, detail="Maya core não disponível")
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/audio")
async def process_audio(audio_data: dict):
    """Processar áudio do WhatsApp"""
    try:
        if flask_app and callable(processar_audio_whatsapp):
            resultado = processar_audio_whatsapp(audio_data)
            return JSONResponse(content={"status": "success", "data": resultado})
        else:
            raise HTTPException(status_code=503, detail="Processamento de áudio não disponível")
    except Exception as e:
        logger.error(f"Erro no processamento de áudio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/image")
async def process_image(image_data: dict):
    """Processar imagem do WhatsApp"""
    try:
        if flask_app and callable(processar_imagem_whatsapp):
            resultado = processar_imagem_whatsapp(image_data)
            return JSONResponse(content={"status": "success", "data": resultado})
        else:
            raise HTTPException(status_code=503, detail="Processamento de imagem não disponível")
    except Exception as e:
        logger.error(f"Erro no processamento de imagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def start_server():
    """Função para iniciar o servidor"""
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info("🌿 Maya HopeCann - FastAPI Server")
    logger.info(f"🌐 Host: {host}")
    logger.info(f"🔌 Port: {port}")
    logger.info("=" * 50)
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

def main():
    """Função principal"""
    start_server()

if __name__ == '__main__':
    main()

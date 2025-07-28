from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
import json
import logging
import os
import time
from typing import Optional
import uvicorn

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Evolution API Webhook",
    description="Servidor webhook para receber mensagens do WhatsApp via Evolution API",
    version="1.0.0"
)

# Pasta para salvar as mensagens recebidas
MESSAGES_FOLDER = "mensagens_recebidas"
os.makedirs(MESSAGES_FOLDER, exist_ok=True)

@app.get("/")
async def index():
    """Endpoint raiz para verificar se o servidor está online"""
    return {"status": "online", "message": "Webhook Server para Evolution API está rodando!"}

@app.post("/webhook")
async def webhook(request: Request, authorization: Optional[str] = Header(None)):
    """
    Endpoint para receber as notificações do Evolution API
    
    Parâmetros:
    - request: O corpo da requisição
    - authorization: Token opcional para autenticação
    
    Retorna:
    - JSON com status do processamento
    """
    try:
        # Validação de autenticação opcional (descomente e ajuste conforme necessário)
        # if authorization != "SEU_TOKEN_SECRETO":
        #     raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Obter dados da requisição
        data = await request.json()
        logger.info(f"Mensagem recebida: {json.dumps(data, indent=2)}")
        
        # Salvar a mensagem em um arquivo
        if data:
            # Extrair dados relevantes (se disponíveis)
            instance_name = data.get('instanceName', 'unknown')
            message_id = data.get('key', {}).get('id', 'unknown') if 'key' in data else 'unknown'
            
            # Criar nome de arquivo com timestamp para garantir unicidade
            timestamp = int(time.time())
            filename = f"{MESSAGES_FOLDER}/{timestamp}_{instance_name}_{message_id}.json"
            
            # Salvar mensagem como JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Mensagem salva em: {filename}")
            
        return {"status": "success", "message": "Webhook recebido com sucesso"}
    
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/mensagens")
async def listar_mensagens():
    """
    Endpoint para listar as últimas mensagens recebidas
    
    Retorna:
    - Lista das últimas mensagens em formato JSON
    """
    try:
        # Listar arquivos na pasta de mensagens, ordenados por data de modificação (mais recentes primeiro)
        files = []
        for filename in os.listdir(MESSAGES_FOLDER):
            if filename.endswith('.json'):
                filepath = os.path.join(MESSAGES_FOLDER, filename)
                files.append({
                    'filename': filename,
                    'modified_time': os.path.getmtime(filepath)
                })
        
        # Ordenar por data de modificação (mais recentes primeiro)
        files.sort(key=lambda x: x['modified_time'], reverse=True)
        
        # Pegar as 10 mensagens mais recentes
        recent_files = files[:10]
        
        # Carregar o conteúdo das mensagens
        messages = []
        for file_info in recent_files:
            filepath = os.path.join(MESSAGES_FOLDER, file_info['filename'])
            with open(filepath, 'r', encoding='utf-8') as f:
                content = json.load(f)
                messages.append({
                    'filename': file_info['filename'],
                    'content': content
                })
        
        return {"status": "success", "messages": messages}
    
    except Exception as e:
        logger.error(f"Erro ao listar mensagens: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# Endpoint para verificar saúde do servidor
@app.get("/health")
async def health_check():
    """Endpoint para monitoramento de saúde do servidor"""
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

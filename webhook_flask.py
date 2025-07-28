from flask import Flask, request, jsonify
import json
import os
import sys
import logging
import time
from datetime import datetime

# Adicionar paths para importar módulos
sys.path.append('evolution_client')
sys.path.append('agents/agno_core')
sys.path.append('agents/agent_whatsapp')
sys.path.append('agents/agent_poll')

# Importar cliente Evolution e agentes
try:
    from evolution_client.simple_client import SimpleEvolutionClient
    from evolution_client.config import EvolutionConfig
    from agno_core.interfaces import AgnoInput, MessageType, EventType
    from agent_whatsapp.whatsapp_agent import WhatsAppAgent
    from agent_poll.poll_agent import PollAgent
    MODULES_LOADED = True
except ImportError as e:
    print(f"Aviso: Módulos não carregados: {e}")
    MODULES_LOADED = False

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Pasta para salvar mensagens
MESSAGES_FOLDER = "mensagens_recebidas"
if not os.path.exists(MESSAGES_FOLDER):
    os.makedirs(MESSAGES_FOLDER)

# Inicializar cliente Evolution e agentes
evolution_client = None
whatsapp_agent = None
poll_agent = None

def initialize_system():
    """Inicializa o sistema de agentes"""
    global evolution_client, whatsapp_agent, poll_agent
    
    if not MODULES_LOADED:
        logger.warning("Módulos não carregados - sistema funcionando em modo básico")
        return
    
    try:
        # Inicializar cliente Evolution
        config = EvolutionConfig()
        evolution_client = SimpleEvolutionClient(config)
        
        # Inicializar agentes
        whatsapp_agent = WhatsAppAgent()
        poll_agent = PollAgent()
        
        logger.info("Sistema de agentes inicializado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar sistema: {str(e)}")

# Inicializar sistema na inicialização do Flask
initialize_system()

def process_and_respond(webhook_data):
    """
    Processa dados do webhook e envia resposta automática
    Esta é a função principal que conecta webhook -> agentes -> Evolution API
    """
    global evolution_client, whatsapp_agent, poll_agent
    
    try:
        # Extrair informações da mensagem
        event_type = webhook_data.get('event', '')
        data = webhook_data.get('data', {})
        
        # Processar apenas mensagens recebidas
        if event_type != 'messages.upsert':
            return False
        
        # Extrair dados da mensagem
        key = data.get('key', {})
        message = data.get('message', {})
        
        # Ignorar mensagens próprias
        if key.get('fromMe', False):
            logger.info("Ignorando mensagem própria")
            return False
        
        # Extrair número do remetente
        remote_jid = key.get('remoteJid', '')
        from_number = remote_jid.replace('@s.whatsapp.net', '').replace('@g.us', '')
        
        # Extrair conteúdo da mensagem
        text_content = None
        if 'conversation' in message:
            text_content = message['conversation']
        elif 'extendedTextMessage' in message:
            text_content = message['extendedTextMessage'].get('text', '')
        
        if not text_content:
            logger.info("Mensagem sem conteúdo de texto")
            return False
        
        logger.info(f"Processando mensagem de {from_number}: {text_content[:50]}...")
        
        # Criar AgnoInput
        agno_input = AgnoInput(
            instance_name=webhook_data.get('instance', 'agente_bot'),
            event_type=EventType.MESSAGES_UPSERT,
            message_type=MessageType.TEXT,
            from_number=from_number,
            to_number='agente_bot',
            message_id=key.get('id', 'unknown'),
            timestamp=data.get('messageTimestamp', int(time.time())),
            text_content=text_content,
            is_from_me=False,
            is_group='@g.us' in remote_jid,
            raw_data=webhook_data
        )
        
        # Tentar processar com agente WhatsApp
        response_text = None
        
        if whatsapp_agent:
            try:
                can_handle = whatsapp_agent.can_handle(agno_input)
                if can_handle:
                    # Executar de forma síncrona (sem await)
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        output = loop.run_until_complete(whatsapp_agent.run(agno_input))
                        response_text = output.text_content
                        logger.info(f"WhatsApp agent gerou resposta: {len(response_text)} chars")
                    finally:
                        loop.close()
            except Exception as e:
                logger.error(f"Erro no WhatsApp agent: {str(e)}")
        
        # Tentar processar com agente Poll se WhatsApp não processou
        if not response_text and poll_agent:
            try:
                can_handle = poll_agent.can_handle(agno_input)
                if can_handle:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        output = loop.run_until_complete(poll_agent.run(agno_input))
                        response_text = output.text_content
                        logger.info(f"Poll agent gerou resposta: {len(response_text)} chars")
                    finally:
                        loop.close()
            except Exception as e:
                logger.error(f"Erro no Poll agent: {str(e)}")
        
        # Enviar resposta se foi gerada
        if response_text and evolution_client:
            try:
                result = evolution_client.send_text(from_number, response_text)
                logger.info(f"Resposta enviada para {from_number}: {response_text[:50]}...")
                return True
            except Exception as e:
                logger.error(f"Erro ao enviar resposta: {str(e)}")
                return False
        
        return False
        
    except Exception as e:
        logger.error(f"Erro geral no processamento: {str(e)}")
        return False

@app.route("/", methods=["GET"])
def index():
    """Endpoint raiz para verificar se o servidor está online"""
    return jsonify({
        "status": "online", 
        "message": "Webhook Server para Evolution API está rodando!",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Endpoint para receber as notificações do Evolution API
    """
    try:
        # Log dos cabeçalhos para diagnóstico
        logger.info(f"Headers recebidos: {dict(request.headers)}")
        
        # Validação de autenticação opcional (descomente e ajuste conforme necessário)
        # auth_header = request.headers.get('Authorization')
        # if auth_header != "SEU_TOKEN_SECRETO":
        #     return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
        # Obter dados da requisição de forma segura
        content_type = request.headers.get('Content-Type', '')
        logger.info(f"Content-Type: {content_type}")
        
        # Tentar processar os dados independentemente do content-type
        try:
            if request.data:
                if 'application/json' in content_type:
                    data = request.json
                else:
                    # Tentar interpretar como JSON mesmo sem o header correto
                    try:
                        data = json.loads(request.data)
                    except:
                        # Se falhar, aceitar como texto ou dados brutos
                        data = {"raw_content": request.data.decode('utf-8', errors='ignore'),
                                "content_type": content_type}
            else:
                # Aceitar form data ou query params se não houver body
                data = {}
                data.update(request.form.to_dict())
                data.update(request.args.to_dict())
                if not data:
                    data = {"info": "Webhook recebido, mas sem dados"}
            
            logger.info(f"Mensagem processada: {json.dumps(data, indent=2, default=str)}")
            
            # Salvar a mensagem em um arquivo
            if data:
                # Extrair dados relevantes (se disponíveis)
                instance_name = data.get('instanceName', 'unknown')
                message_id = data.get('key', {}).get('id', 'unknown') if isinstance(data, dict) and 'key' in data else 'unknown'
                
                # Criar nome de arquivo com timestamp para garantir unicidade
                timestamp = int(time.time())
                filename = f"{MESSAGES_FOLDER}/{timestamp}_{instance_name}_{message_id}.json"
                
                # Salvar mensagem como JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                    
                logger.info(f"Mensagem salva em: {filename}")
                
            # NOVO: Processar mensagem e enviar resposta automática
            if MODULES_LOADED and data:
                try:
                    response_sent = process_and_respond(data)
                    if response_sent:
                        logger.info("Resposta automática enviada com sucesso")
                    else:
                        logger.info("Mensagem processada mas sem resposta necessária")
                except Exception as e:
                    logger.error(f"Erro ao processar resposta automática: {str(e)}")
                
            return jsonify({"status": "success", "message": "Webhook recebido com sucesso"})
        except Exception as inner_e:
            logger.error(f"Erro ao processar corpo da requisição: {str(inner_e)}")
            # Retornar 200 mesmo com erro para não causar reenvios
            return jsonify({"status": "warning", "message": f"Webhook recebido, mas com problemas no processamento: {str(inner_e)}"})
    
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        # Retornar 200 para evitar que o remetente considere uma falha
        return jsonify({"status": "error", "message": str(e)})

@app.route("/mensagens", methods=["GET"])
def listar_mensagens():
    """
    Endpoint para listar as últimas mensagens recebidas
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
        
        return jsonify({"status": "success", "messages": messages})
    
    except Exception as e:
        logger.error(f"Erro ao listar mensagens: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint para monitoramento de saúde do servidor"""
    return jsonify({
        "status": "healthy", 
        "timestamp": time.time()
    })

if __name__ == "__main__":
    # Usar 0.0.0.0 para permitir acesso externo e porta 5000 para compatibilidade
    app.run(host="0.0.0.0", port=5000, debug=True)

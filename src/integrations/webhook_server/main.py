"""
Servidor Webhook FastAPI para Evolution API
Integra com o sistema modular de agentes Agno
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
import structlog
from flask import Flask, request, jsonify
from agno_core.orchestrator import manager
from evolution_client.client import EvolutionClient
from evolution_client.config import EvolutionConfig
from .adapters.evolution_adapter import EvolutionAdapter
from .schemas.webhook_schemas import WebhookEvent

# Configurar logging estruturado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Instâncias globais
evolution_client: EvolutionClient = None
evolution_adapter: EvolutionAdapter = None

app = Flask(__name__)


async def startup_event():
    """
    Evento de inicialização do servidor
    Carrega agentes e inicializa clientes
    """
    global evolution_client, evolution_adapter
    
    logger.info("Iniciando servidor webhook...")
    
    try:
        # Inicializar gerenciador de agentes
        await manager.load_plugins()
        
        # Inicializar cliente Evolution API
        config = EvolutionConfig()
        evolution_client = EvolutionClient(config)
        await evolution_client.initialize()
        
        # Inicializar adapter
        evolution_adapter = EvolutionAdapter()
        
        logger.info(
            "Servidor webhook inicializado com sucesso",
            agents_count=len(manager.registry.list_agents()),
            evolution_url=config.base_url,
            instance_name=config.instance_name
        )
        
    except Exception as e:
        logger.error(
            "Erro crítico na inicialização do servidor",
            error=str(e)
        )
        raise


async def shutdown_event():
    """
    Evento de finalização do servidor
    Limpa recursos
    """
    global evolution_client
    
    logger.info("Finalizando servidor webhook...")
    
    try:
        # Finalizar gerenciador de agentes
        await manager.shutdown()
        
        # Finalizar cliente Evolution API
        if evolution_client:
            await evolution_client.cleanup()
        
        logger.info("Servidor webhook finalizado com sucesso")
        
    except Exception as e:
        logger.error(
            "Erro na finalização do servidor",
            error=str(e)
        )


@app.route("/", methods=["GET"])
def index():
    """
    Endpoint raiz - status do servidor
    """
    return jsonify({
        "status": "online",
        "message": "Agno WhatsApp Webhook Server está rodando!",
        "version": "1.0.0",
        "agents": manager.registry.list_agents() if manager._initialized else []
    })


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Endpoint principal do webhook
    Recebe eventos da Evolution API e processa com agentes
    """
    try:
        # Log da requisição
        logger.info(
            "Webhook recebido",
            headers=dict(request.headers),
            content_type=request.headers.get('Content-Type', '')
        )
        
        # Obter dados da requisição
        try:
            if request.is_json:
                data = request.json
            else:
                # Tentar interpretar como JSON mesmo sem header correto
                import json
                data = json.loads(request.data)
        except Exception as e:
            logger.error(
                "Erro ao parsear dados do webhook",
                error=str(e),
                data_preview=str(request.data)[:200]
            )
            return jsonify({"status": "error", "message": "Invalid JSON data"}), 400
        
        if not data:
            logger.warning("Webhook recebido sem dados")
            return jsonify({"status": "warning", "message": "No data received"})
        
        # Processar de forma assíncrona
        asyncio.create_task(process_webhook_async(data))
        
        # Retornar 200 imediatamente (padrão webhook)
        return jsonify({"status": "success", "message": "Webhook received"})
        
    except Exception as e:
        logger.error(
            "Erro crítico no webhook",
            error=str(e)
        )
        # Sempre retornar 200 para evitar reenvios
        return jsonify({"status": "error", "message": "Internal error"})


async def process_webhook_async(data: Dict[str, Any]) -> None:
    """
    Processa webhook de forma assíncrona
    
    Args:
        data: Dados do webhook
    """
    try:
        logger.info(
            "Iniciando processamento assíncrono do webhook",
            event_type=data.get("event"),
            instance=data.get("instance")
        )
        
        # Validar e converter dados
        webhook_event = evolution_adapter.parse_webhook_event(data)
        
        if not webhook_event:
            logger.warning("Evento webhook não pôde ser processado")
            return
        
        # Converter para AgnoInput
        agno_input = evolution_adapter.to_agno_input(webhook_event)
        
        if not agno_input:
            logger.info("Evento não requer processamento por agentes")
            return
        
        # Processar com agentes
        agno_output = await manager.dispatch(agno_input)
        
        if not agno_output:
            logger.info("Nenhum agente processou a mensagem")
            return
        
        # Enviar resposta via Evolution API
        await send_response(agno_output)
        
        logger.info(
            "Webhook processado com sucesso",
            agent_response=agno_output.message_type.value
        )
        
    except Exception as e:
        logger.error(
            "Erro no processamento assíncrono do webhook",
            error=str(e),
            data_preview=str(data)[:200]
        )


async def send_response(output: 'AgnoOutput') -> None:
    """
    Envia resposta via Evolution API
    
    Args:
        output: Saída do agente
    """
    try:
        if output.message_type.value == "text":
            await evolution_client.send_text(
                to=output.to_number,
                text=output.text_content,
                quote_message_id=output.quote_message_id,
                delay_seconds=output.delay_seconds
            )
        
        elif output.message_type.value == "image":
            await evolution_client.send_image(
                to=output.to_number,
                image_url=output.media_url,
                image_base64=output.media_base64,
                caption=output.text_content
            )
        
        elif output.message_type.value == "poll":
            # Implementar envio de enquete
            pass
        
        logger.info(
            "Resposta enviada com sucesso",
            to=output.to_number,
            type=output.message_type.value
        )
        
    except Exception as e:
        logger.error(
            "Erro ao enviar resposta",
            error=str(e),
            to=output.to_number,
            type=output.message_type.value
        )


@app.route("/health", methods=["GET"])
def health_check():
    """
    Endpoint de verificação de saúde
    """
    try:
        # Verificar status dos componentes
        health_status = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "components": {
                "agent_manager": manager._initialized,
                "evolution_client": evolution_client is not None,
                "total_agents": len(manager.registry.list_agents()) if manager._initialized else 0
            }
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error("Erro no health check", error=str(e))
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


@app.route("/agents", methods=["GET"])
def list_agents():
    """
    Lista agentes disponíveis
    """
    try:
        if not manager._initialized:
            return jsonify({
                "status": "not_initialized",
                "agents": []
            })
        
        agents_info = {}
        for agent_name in manager.registry.list_agents():
            agent = manager.registry.get_agent(agent_name)
            agents_info[agent_name] = {
                "name": agent.name,
                "description": agent.description,
                "initialized": agent.is_initialized
            }
        
        return jsonify({
            "status": "success",
            "total": len(agents_info),
            "agents": agents_info
        })
        
    except Exception as e:
        logger.error("Erro ao listar agentes", error=str(e))
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    # Executar inicialização assíncrona
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(startup_event())
        
        # Executar servidor Flask
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False  # Desabilitar debug em produção
        )
        
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    finally:
        loop.run_until_complete(shutdown_event())
        loop.close()

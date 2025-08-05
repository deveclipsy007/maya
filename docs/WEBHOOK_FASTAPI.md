# Webhook Server com FastAPI para Evolution API

Este documento descreve como usar o servidor webhook FastAPI para receber mensagens do WhatsApp via Evolution API.

## Visão Geral

* **Framework**: FastAPI
* **Servidor ASGI**: Uvicorn
* **Containerização**: Docker
* **Endpoint principal**: `/webhook`
* **Porta padrão**: 8000

## Estrutura do Projeto

```
mayahope/
├── main.py                  # Aplicação FastAPI 
├── requirements.txt         # Dependências Python
├── Dockerfile               # Configuração Docker
└── mensagens_recebidas/     # Diretório onde as mensagens são salvas
```

## Executando Localmente (Sem Docker)

1. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Execute a aplicação**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Verifique se está rodando**:
   Acesse `http://localhost:8000` no navegador. Você deve ver uma mensagem: "Webhook Server para Evolution API está rodando!"

## Executando com Docker

1. **Construa a imagem Docker**:
   ```bash
   docker build -t webhook-server .
   ```

2. **Execute o container**:
   ```bash
   docker run -d -p 8000:8000 --name webhook-server webhook-server
   ```

3. **Verifique se está rodando**:
   Acesse `http://localhost:8000` no navegador.

## Integrando com Evolution API

Para configurar o webhook na sua instância do WhatsApp:

1. **Criar uma instância do WhatsApp** (se ainda não tiver):

   ```
   POST http://localhost:8080/instance/create
   Content-Type: application/json

   {
     "instanceName": "agente_bot",
     "token": "1234",
     "qrcode": true
   }
   ```

2. **Configurar o webhook na instância**:

   ```
   POST http://localhost:8080/webhook/set/agente_bot
   Content-Type: application/json
   apikey: 1234

   {
     "url": "http://localhost:8000/webhook",
     "webhook_by_events": false,
     "webhook_events": {
       "APPLICATION_STARTUP": true,
       "QRCODE_UPDATED": true,
       "MESSAGES_UPSERT": true,
       "MESSAGES_UPDATE": true,
       "MESSAGES_DELETE": true,
       "SEND_MESSAGE": true,
       "CONNECTION_UPDATE": true
     }
   }
   ```

## Endpoints Disponíveis

- **GET /** - Página inicial (status do servidor)
- **POST /webhook** - Endpoint que recebe as notificações do Evolution API
- **GET /mensagens** - Lista as últimas 10 mensagens recebidas
- **GET /health** - Verificação de saúde do servidor

## Segurança (Recomendações para Produção)

Para um ambiente de produção, recomenda-se:

1. **Habilitar autenticação** - Edite `main.py` e descomente o bloco de autenticação no endpoint `/webhook`
2. **Usar HTTPS** - Configure um proxy reverso (nginx, traefik) com certificado SSL
3. **Limitar acesso por IP** - Configure firewall para permitir apenas IPs conhecidos
4. **Monitorar logs** - Configure um serviço de log centralizado

## Deploy em Produção

### Opção A: Render.com
1. Suba o repositório no GitHub
2. Conecte ao Render e escolha **Web Service**
3. Configure o comando de start: `uvicorn main:app --host 0.0.0.0 --port 8000`
4. Use a URL fornecida para configurar no Evolution API

### Opção B: VPS/Servidor Próprio
1. Instale Docker no servidor
2. Faça upload dos arquivos e construa a imagem
3. Execute usando `docker-compose` ou gerenciador de containers

## Testando a Integração

Para verificar se o webhook está funcionando:

1. Envie uma mensagem de teste via Evolution API
2. Verifique se ela aparece em `http://localhost:8000/mensagens`
3. Verifique os logs do servidor para confirmar o recebimento

## Documentação da API

O FastAPI gera automaticamente documentação interativa:

- **Swagger UI**: Acesse `http://localhost:8000/docs`
- **ReDoc**: Acesse `http://localhost:8000/redoc`

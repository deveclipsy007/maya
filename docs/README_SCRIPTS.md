# 🤖 Maya AI - Sistema de WhatsApp Bot

Sistema completo de bot WhatsApp com inteligência artificial Maya para consultas sobre cannabis medicinal.

## 📁 Scripts Disponíveis

### 🚀 `iniciar_maya.bat`
**Inicia todo o sistema automaticamente**
- Inicia Evolution API (Docker)
- Configura webhooks automaticamente  
- Inicia servidor Maya
- Exibe status e URLs importantes

### 🛑 `parar_maya.bat`
**Para todo o sistema**
- Para servidor Maya
- Para Evolution API (Docker)
- Remove containers

### 📊 `status_maya.bat`
**Verifica status de todos os componentes**
- Docker containers
- Evolution API
- Instância WhatsApp
- Webhook configuração
- Servidor Maya

### 🔗 `reconectar_whatsapp.bat`
**Ajuda na reconexão do WhatsApp**
- Abre Evolution API no navegador
- Mostra instruções para gerar QR Code

## 🚀 Como Usar

### Primeira vez:
1. Execute `iniciar_maya.bat`
2. Aguarde o sistema inicializar
3. Acesse http://localhost:8090
4. Conecte seu WhatsApp escaneando o QR Code
5. Pronto! Maya está funcionando

### Uso diário:
- **Iniciar**: Duplo clique em `iniciar_maya.bat`
- **Parar**: Duplo clique em `parar_maya.bat`
- **Status**: Duplo clique em `status_maya.bat`

## 📱 Informações da Instância

- **Nome da instância**: `agente_bot`
- **Número WhatsApp**: `+55 62 8195-9177`
- **Evolution API**: http://localhost:8090
- **Servidor Maya**: http://localhost:5000

## 🔧 Configurações

- **Webhook URL**: `http://192.168.15.8:5000/webhook`
- **API Key**: `1234`
- **Eventos**: `MESSAGES_UPSERT`

## 🎯 Funcionalidades da Maya

- 🌿 Consultas sobre cannabis medicinal
- 📅 Agendamento de consultas
- 💬 Conversas inteligentes
- 🔍 Informações médicas
- 📋 Orientações sobre tratamentos

## 🆘 Resolução de Problemas

1. **Maya não responde**:
   - Execute `status_maya.bat` para verificar componentes
   - Verifique se WhatsApp está conectado

2. **WhatsApp desconectado**:
   - Execute `reconectar_whatsapp.bat`
   - Escaneie novo QR Code

3. **Evolution API não inicia**:
   - Verifique se Docker está instalado e rodando
   - Execute `parar_maya.bat` e depois `iniciar_maya.bat`

4. **Webhook não funciona**:
   - Verifique seu IP local no arquivo `iniciar_maya.bat`
   - Pode precisar ajustar a variável `WEBHOOK_IP`

## 📝 Logs

- **Mensagens recebidas**: Pasta `mensagens_recebidas/`
- **Logs Maya**: Terminal do `iniciar_maya.bat`
- **Status webhooks**: http://localhost:5000/mensagens

## 🔄 Atualizações

Para atualizar o sistema:
1. Execute `parar_maya.bat`
2. Faça pull das atualizações
3. Execute `iniciar_maya.bat`

---

**🎉 Sistema criado com sucesso! Maya está pronta para atender no WhatsApp! 🤖**

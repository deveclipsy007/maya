# 🎯 GUIA DE CONFIGURAÇÃO - Evolution API para Áudio Descriptografado

## 📋 **PROBLEMA RESOLVIDO:**
- ✅ Áudio WhatsApp criptografado (.enc) agora é processado automaticamente
- ✅ 3 métodos implementados com fallback inteligente
- ✅ Transcrição funcional usando OpenAI Whisper

## 🔧 **CONFIGURAÇÃO NECESSÁRIA:**

### **MÉTODO 1: Configurar Webhook para Base64**

Execute este comando para configurar sua instância Evolution API:

```bash
curl --request POST \
  --url https://SEU_SERVIDOR/webhook/set/SEU_INSTANCE \
  --header 'Content-Type: application/json' \
  --header 'apikey: SUA_API_KEY' \
  --data '{
    "url": "http://192.168.15.8:5000/webhook/messages-upsert",
    "webhook_by_events": false,
    "webhook_base64": true,
    "events": [
      "MESSAGES_UPSERT",
      "MESSAGES_UPDATE", 
      "CONNECTION_UPDATE"
    ]
  }'
```

### **PARÂMETROS IMPORTANTES:**

- `webhook_base64: true` ← **CRUCIAL!** Faz a Evolution API enviar mídia já descriptografada
- `convertToMp3: true` ← Converte áudio para formato suportado pelo Whisper

## 🚀 **MÉTODOS IMPLEMENTADOS:**

### **MÉTODO 1**: Mídia Base64 no Webhook
- ✅ Se `webhook_base64=true`, mídia vem descriptografada
- ✅ Processamento direto sem download
- ✅ Mais rápido e eficiente

### **MÉTODO 2**: Endpoint getBase64FromMediaMessage  
- ✅ Solicita mídia descriptografada via API
- ✅ Usa ID da mensagem para obter conteúdo
- ✅ Fallback automático se Método 1 falhar

### **MÉTODO 3**: Download Híbrido (Fallback)
- ✅ Download tradicional + conversão ffmpeg
- ✅ Detecção de criptografia
- ✅ Orientação ao usuário

## 📊 **FLUXO DE EXECUÇÃO:**

```
📱 WhatsApp Áudio → Evolution API → Maya HopeCann
                        ↓
    🔄 MÉTODO 1: webhook_base64=true?
                        ↓ (se não)
    🔄 MÉTODO 2: getBase64FromMediaMessage
                        ↓ (se falhar)  
    🔄 MÉTODO 3: Download + Híbrido
                        ↓
    🎤 OpenAI Whisper → 🤖 Maya Response
```

## ⚙️ **VARIÁVEIS DE AMBIENTE:**

Certifique-se de que estas variáveis estão configuradas:

```env
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_INSTANCE_NAME=agente_bot
EVOLUTION_API_KEY=sua_api_key_aqui
OPENAI_API_KEY=sua_openai_key_aqui
```

## 🧪 **TESTE DA CONFIGURAÇÃO:**

1. **Envie um áudio via WhatsApp**
2. **Verifique os logs:**
   - ✅ "MÉTODO 1: Mídia base64 encontrada no webhook!" 
   - ✅ "MÉTODO 2: Obtendo mídia descriptografada via API"
   - ✅ "Transcrição bem-sucedida"

## 🎯 **BENEFÍCIOS:**

- 🚀 **Performance**: Mídia já vem descriptografada
- 🔒 **Segurança**: Sem arquivos temporários criptografados  
- 🎤 **Qualidade**: Áudio convertido para MP3 otimizado
- 🤖 **Inteligência**: Fallback automático entre métodos
- 📱 **Compatibilidade**: Funciona com todos os tipos de áudio WhatsApp

## 📝 **LOGS DE SUCESSO:**

```
🎤 Processando mensagem de áudio de 556298550007
✅ MÉTODO 1: Mídia base64 encontrada no webhook!
🎤 Processando áudio base64 descriptografado
📊 Tamanho do áudio decodificado: 15234 bytes
🎤 Enviando áudio descriptografado para Whisper...
✅ Transcrição bem-sucedida: Olá Maya, preciso agendar uma consulta...
✅ Resposta para áudio enviada com sucesso!
```

---

**🎉 IMPLEMENTAÇÃO COMPLETA! A Maya agora processa áudio WhatsApp perfeitamente!**

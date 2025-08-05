# 🌿 Maya HopeCann - Guia Completo de Configuração

## 📋 Visão Geral

Maya é a atendente virtual especializada da HopeCann, criada com Agno Framework para agendamento de consultas médicas de cannabis medicinal. Ela integra:

- **🤖 Agno Framework**: IA conversacional avançada
- **🗄️ Supabase**: Banco de dados para agendamentos e médicos
- **📅 Google Meet**: Criação automática de reuniões
- **📱 WhatsApp**: Interface via Evolution API

## 🚀 Configuração Passo a Passo

### 1. Configurar Supabase

1. **Criar Projeto Supabase:**
   - Acesse https://supabase.com
   - Crie um novo projeto
   - Anote a URL e a chave pública

2. **Executar Schema:**
   ```sql
   -- Execute o arquivo supabase_schema.sql no SQL Editor do Supabase
   ```

3. **Configurar Variáveis:**
   ```bash
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua_chave_publica_supabase
   ```

### 2. Configurar Google Meet

1. **Google Cloud Console:**
   - Acesse https://console.cloud.google.com
   - Crie um projeto ou use existente
   - Ative a Google Calendar API
   - Crie credenciais OAuth 2.0
   - Baixe o arquivo `credentials.json`

2. **Configurar Variáveis:**
   ```bash
   GOOGLE_CREDENTIALS_FILE=credentials.json
   GOOGLE_TOKEN_FILE=token.json
   ```

3. **Primeira Autenticação:**
   - Na primeira execução, Maya solicitará autorização
   - Siga o link e autorize o acesso
   - O token será salvo automaticamente

### 3. Executar Maya

```bash
# Ativar ambiente virtual
.venv\Scripts\activate

# Executar Maya
python maya_hopecann.py
```

## 🎯 Funcionalidades da Maya

### Conversação Natural
- Apresenta-se como Maya da HopeCann
- Explica sobre cannabis medicinal
- Coleta dados do paciente
- Agenda consultas

### Integração Supabase
- Busca horários disponíveis
- Lista médicos especializados
- Salva agendamentos
- Histórico de consultas

### Integração Google Meet
- Cria reuniões automaticamente
- Envia link pelo WhatsApp
- Agenda no Google Calendar
- Convida participantes

## 📱 Fluxo de Atendimento

1. **Saudação:**
   ```
   Usuário: "Oi"
   Maya: "Olá! 🌿 Sou Maya da HopeCann. Como posso ajudar você a agendar uma consulta médica para cannabis medicinal?"
   ```

2. **Coleta de Dados:**
   ```
   Maya: "Para agendar sua consulta, preciso de algumas informações:
   📝 Nome completo
   📞 Telefone
   📧 Email
   🩺 Condição médica
   📅 Preferência de data/horário"
   ```

3. **Horários Disponíveis:**
   ```
   Maya: "🗓️ Horários disponíveis:
   📅 25/07/2025 14:00 - Dr. Carlos Silva
   📅 26/07/2025 10:00 - Dra. Ana Santos
   📅 27/07/2025 16:00 - Dr. João Oliveira"
   ```

4. **Confirmação e Meet:**
   ```
   Maya: "✅ Consulta agendada com sucesso!
   🔗 Link da consulta: https://meet.google.com/xxx-yyyy-zzz
   📅 Data: 25/07/2025 às 14:00
   🩺 Médico: Dr. Carlos Silva"
   ```

## 🔧 Endpoints Disponíveis

- `GET /health` - Status do sistema Maya
- `GET /agendamentos` - Listar agendamentos
- `GET /medicos` - Listar médicos
- `POST /webhook` - Receber mensagens WhatsApp

## 🛠️ Troubleshooting

### Supabase não conecta
- Verifique URL e chave
- Confirme que as tabelas foram criadas
- Teste conexão no dashboard

### Google Meet não funciona
- Verifique credenciais OAuth
- Confirme que Calendar API está ativa
- Reautorize se necessário

### Maya não responde
- Verifique logs no terminal
- Confirme que OpenAI API está funcionando
- Teste webhook com curl

## 📊 Monitoramento

### Logs Detalhados
Maya exibe logs coloridos com:
- 🔔 Webhooks recebidos
- 📱 Mensagens processadas
- 🌿 Respostas geradas
- 📅 Reuniões criadas
- 🗄️ Operações Supabase

### Health Check
```bash
curl http://localhost:5000/health
```

Retorna status de todos os componentes:
- Maya Agno Framework
- Supabase
- Google Meet
- Evolution API

## 🎨 Personalização

### Modificar Personalidade
Edite a seção `description` em `create_maya_agent()`:

```python
description="""
Você é Maya, a atendente virtual da HopeCann! 🌿
[Personalize aqui a personalidade da Maya]
"""
```

### Adicionar Comandos
Implemente em `processar_comandos_agendamento()`:

```python
if 'cancelar' in texto_lower:
    # Lógica para cancelamento
    pass
```

### Customizar Respostas
Modifique `fallback_responses` para respostas personalizadas.

## 🚀 Próximos Passos

1. **Teste Completo**: Envie mensagens e verifique o fluxo
2. **Configure Integrações**: Supabase e Google Meet
3. **Personalize**: Ajuste personalidade e comandos
4. **Monitore**: Acompanhe logs e performance
5. **Expanda**: Adicione novas funcionalidades

---

**Maya está pronta para transformar o atendimento da HopeCann! 🌿💚**

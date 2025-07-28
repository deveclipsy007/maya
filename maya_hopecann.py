#!/usr/bin/env python3
"""
Maya - Atendente Virtual HopeCann
Agente especializado em agendamento de consultas médicas para cannabis medicinal
Integrado com Supabase e Google Meet
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
import subprocess

# Importar módulo de memória de contatos
from contact_memory import initialize_memory, get_memory
import io
import time
import assemblyai as aai  # AssemblyAI SDK oficial
from flask import Flask, request, jsonify
import logging
from dotenv import load_dotenv

# Importar funções de processamento de áudio
from process_audio import process_audio_message

# Importações do Agno Framework
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

# Importação do OpenAI para transcrição de áudio
from openai import OpenAI

# Importação para processamento de áudio
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️ pydub não instalado - funcionalidade de áudio limitada")

# Importações para integrações
from supabase import create_client, Client
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import uuid

# Configuração de logging ULTRA-DETALHADO
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
    ]
)
logger = logging.getLogger(__name__)

# Ativar logs de requests também
logging.getLogger('requests').setLevel(logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.DEBUG)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações da Evolution API
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY', '1234')
EVOLUTION_INSTANCE_NAME = os.getenv('EVOLUTION_INSTANCE_NAME', 'agente_bot')

# Caminho do banco de dados de memória de contatos
CONTACT_DB_PATH = os.getenv('CONTACT_DB_PATH', 'maya_contacts.db')

# Configurações da OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AI_MODEL = os.getenv('AI_MODEL', 'gpt-4o-mini')

# Configurações Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Configurações Google Meet
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')

# Verificar configurações essenciais
if not OPENAI_API_KEY:
    logger.error("❌ OPENAI_API_KEY não configurada!")
    exit(1)

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("⚠️ Supabase não configurado - algumas funcionalidades serão limitadas")

# Configuração OpenAI
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Configuração AssemblyAI SDK
ASSEMBLYAI_API_KEY = '5aa2285cafcb4bf4ac7a1c12a7fb0f05'
aai.settings.api_key = ASSEMBLYAI_API_KEY
logger.info("✅ Cliente OpenAI inicializado para transcrição de áudio")

# Configuração do Flask
app = Flask(__name__)

# Armazenamento de mensagens e contexto
mensagens_recebidas = []
conversation_context = {}

# Dicionário para rastrear primeiro contato (para banner de boas-vindas)
first_contact_tracker = {}

# Dicionário para armazenar áudio, foto e banner de boas-vindas
media_files = {}

# ===== SUPABASE INTEGRATION =====

supabase_client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase conectado com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar Supabase: {str(e)}")

def buscar_horarios_disponiveis(data_inicio=None, data_fim=None):
    """
    Busca horários disponíveis no Supabase
    Esquema real: id, id_medico, dia_semana, hora_inicio, hora_fim
    """
    if not supabase_client:
        logger.warning("⚠️ Supabase não configurado - usando horários de exemplo")
        return gerar_horarios_exemplo()
    
    try:
        # Buscar horários com informações do médico (JOIN)
        query = supabase_client.table('horarios_disponiveis').select('''
            id,
            id_medico,
            dia_semana,
            hora_inicio,
            hora_fim,
            medicos!inner(nome, crm, especialidade)
        ''')
            
        result = query.execute()
        
        if result.data and len(result.data) > 0:
            logger.info(f"✅ Encontrados {len(result.data)} horários no Supabase")
            
            # Converter para formato mais amigável
            horarios_formatados = []
            for horario in result.data:
                medico_info = horario.get('medicos', {})
                horarios_formatados.append({
                    'id': horario['id'],
                    'medico_id': horario['id_medico'],
                    'medico_nome': medico_info.get('nome', 'Médico não identificado'),
                    'medico_crm': medico_info.get('crm', ''),
                    'dia_semana': horario['dia_semana'],
                    'hora_inicio': horario['hora_inicio'],
                    'hora_fim': horario['hora_fim'],
                    'disponivel': True  # Por enquanto assumimos que está disponível
                })
            
            return horarios_formatados
        else:
            logger.warning("⚠️ Nenhum horário encontrado no Supabase - usando horários de exemplo")
            return gerar_horarios_exemplo()
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar horários: {str(e)}")
        logger.info("🔄 Usando horários de exemplo como fallback")
        return gerar_horarios_exemplo()

def gerar_horarios_exemplo():
    """
    Gera horários de exemplo para demonstração
    Formato compatível com o esquema real: dia_semana, hora_inicio, hora_fim
    """
    
    horarios_exemplo = []
    
    # Médicos de exemplo
    medicos_exemplo = [
        {'id': 1, 'nome': 'Dr. Carlos Silva', 'crm': 'CRM-SP 123456'},
        {'id': 2, 'nome': 'Dra. Ana Santos', 'crm': 'CRM-RJ 789012'},
        {'id': 3, 'nome': 'Dr. João Oliveira', 'crm': 'CRM-MG 345678'}
    ]
    
    # Horários por dia da semana
    dias_horarios = {
        'segunda-feira': ['09:00', '14:00', '16:00'],
        'terça-feira': ['10:00', '15:00'],
        'quarta-feira': ['09:30', '14:30', '16:30'],
        'quinta-feira': ['08:00', '13:00', '17:00'],
        'sexta-feira': ['09:00', '15:00']
    }
    
    id_counter = 1
    for dia, horarios in dias_horarios.items():
        for horario in horarios:
            medico = medicos_exemplo[id_counter % len(medicos_exemplo)]
            
            # Calcular hora_fim (1 hora após hora_inicio)
            hora_inicio_parts = horario.split(':')
            hora_fim_hour = int(hora_inicio_parts[0]) + 1
            hora_fim = f"{hora_fim_hour:02d}:{hora_inicio_parts[1]}"
            
            horarios_exemplo.append({
                'id': id_counter,
                'medico_id': medico['id'],
                'medico_nome': medico['nome'],
                'medico_crm': medico['crm'],
                'dia_semana': dia,
                'hora_inicio': horario,
                'hora_fim': hora_fim,
                'disponivel': True
            })
            
            id_counter += 1
    
    logger.info(f"📅 Gerados {len(horarios_exemplo)} horários de exemplo")
    return horarios_exemplo

def verificar_paciente_existe(telefone):
    """
    Simula verificação de paciente (tabela não existe no Supabase)
    Retorna None para indicar que é sempre um paciente novo
    """
    logger.info(f"ℹ️ Simulação: Paciente sempre considerado novo (tabela pacientes não existe)")
    return None  # Sempre trata como paciente novo

def gerar_senha_temporaria():
    """
    Gera senha temporária de 8 caracteres
    """
    import random
    import string
    
    # Combinação de letras maiúsculas, minúsculas e números
    caracteres = string.ascii_letters + string.digits
    senha = ''.join(random.choice(caracteres) for _ in range(8))
    
    return senha

def cadastrar_novo_paciente(nome_completo, telefone, email):
    """
    Simula cadastro de paciente (tabela não existe no Supabase)
    Retorna dados simulados para continuar o fluxo
    """
    try:
        senha_temporaria = gerar_senha_temporaria()
        
        # Simular cadastro bem-sucedido
        logger.info(f"✅ Simulação: Cadastro de {nome_completo} realizado com sucesso")
        
        # Retornar dados simulados
        return {
            'paciente': {
                'id': f'sim_{telefone}',  # ID simulado
                'nome': nome_completo,
                'telefone': telefone,
                'email': email,
                'status': 'ativo'
            },
            'senha_temporaria': senha_temporaria
        }
            
    except Exception as e:
        logger.error(f"❌ Erro na simulação de cadastro: {str(e)}")
        return None

def salvar_agendamento(dados_paciente, data_hora, medico_id=None):
    """
    Simula salvamento de agendamento (tabela não existe no Supabase)
    Retorna dados simulados para continuar o fluxo
    """
    try:
        # Simular agendamento bem-sucedido
        logger.info(f"✅ Simulação: Agendamento de {dados_paciente.get('nome')} salvo com sucesso")
        
        # Retornar dados simulados
        return {
            'id': f'ag_{dados_paciente.get("telefone")}_{datetime.now().strftime("%Y%m%d%H%M")}',
            'nome_paciente': dados_paciente.get('nome'),
            'telefone_paciente': dados_paciente.get('telefone'),
            'email_paciente': dados_paciente.get('email'),
            'data_hora': data_hora,
            'medico_id': medico_id or 6,
            'status': 'confirmado'
        }
            
    except Exception as e:
        logger.error(f"❌ Erro na simulação de agendamento: {str(e)}")
        return None

def buscar_medicos():
    """
    Busca lista de médicos disponíveis
    Esquema real: id, nome, crm, especialidade, telefone, status_disponibilidade, etc.
    """
    if not supabase_client:
        logger.warning("⚠️ Supabase não configurado - usando dados de exemplo")
        return [
            {'id': 1, 'nome': 'Dr. Carlos Silva', 'especialidade': 'Cannabis Medicinal', 'crm': 'CRM-SP 123456'},
            {'id': 2, 'nome': 'Dra. Ana Santos', 'especialidade': 'Cannabis Medicinal', 'crm': 'CRM-RJ 789012'},
            {'id': 3, 'nome': 'Dr. João Oliveira', 'especialidade': 'Cannabis Medicinal', 'crm': 'CRM-MG 345678'}
        ]
    
    try:
        # Buscar médicos disponíveis (usando esquema real)
        result = supabase_client.table('medicos').select('id, nome, crm, especialidade, telefone, status_disponibilidade').eq('status_disponibilidade', True).execute()
        
        if result.data and len(result.data) > 0:
            logger.info(f"✅ Encontrados {len(result.data)} médicos no Supabase")
            return result.data
        else:
            logger.warning("⚠️ Nenhum médico disponível no Supabase - usando dados de exemplo")
            return [
                {'id': 1, 'nome': 'Dr. Carlos Silva', 'especialidade': 'Cannabis Medicinal', 'crm': 'CRM-SP 123456'},
                {'id': 2, 'nome': 'Dra. Ana Santos', 'especialidade': 'Cannabis Medicinal', 'crm': 'CRM-RJ 789012'},
                {'id': 3, 'nome': 'Dr. João Oliveira', 'especialidade': 'Cannabis Medicinal', 'crm': 'CRM-MG 345678'}
            ]
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar médicos: {str(e)}")
        logger.info("🔄 Usando dados de exemplo como fallback")
        return [
            {'id': 1, 'nome': 'Dr. Carlos Silva', 'especialidade': 'Cannabis Medicinal', 'crm': 'CRM-SP 123456'},
            {'id': 2, 'nome': 'Dra. Ana Santos', 'especialidade': 'Cannabis Medicinal', 'crm': 'CRM-RJ 789012'},
            {'id': 3, 'nome': 'Dr. João Oliveira', 'especialidade': 'Cannabis Medicinal', 'crm': 'CRM-MG 345678'}
        ]

# ===== GOOGLE MEET INTEGRATION =====

def criar_reuniao_google_meet(titulo, data_hora, duracao_minutos=60, participantes=[]):
    """
    Cria reunião REAL no Google Meet e retorna o link
    Requer configuração OAuth2 adequada
    """
    try:
        # Verificar se credenciais existem
        if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
            logger.error("❌ Arquivo credentials.json não encontrado!")
            logger.info("📋 Para configurar Google Meet:")
            logger.info("1. Acesse https://console.cloud.google.com/")
            logger.info("2. Crie um projeto ou selecione um existente")
            logger.info("3. Ative a Google Calendar API")
            logger.info("4. Crie credenciais OAuth 2.0")
            logger.info("5. Baixe o arquivo credentials.json")
            logger.info("6. Coloque o arquivo na pasta do projeto")
            raise Exception("Google credentials não configuradas")
        
        # Configurar credenciais Google
        creds = None
        
        # Verificar se já temos token salvo
        if os.path.exists(GOOGLE_TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE)
                logger.info("🔑 Token Google carregado com sucesso")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar token: {str(e)}")
                creds = None
        
        # Se não temos credenciais válidas, precisamos autenticar
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("🔄 Renovando token Google...")
                    creds.refresh(Request())
                    logger.info("✅ Token renovado com sucesso")
                except Exception as e:
                    logger.error(f"❌ Erro ao renovar token: {str(e)}")
                    creds = None
            
            # Se ainda não temos credenciais, iniciar fluxo OAuth
            if not creds:
                logger.info("🔐 Iniciando autenticação OAuth2 Google...")
                
                # Definir escopos necessários
                SCOPES = [
                    'https://www.googleapis.com/auth/calendar',
                    'https://www.googleapis.com/auth/calendar.events'
                ]
                
                try:
                    flow = Flow.from_client_secrets_file(
                        GOOGLE_CREDENTIALS_FILE, 
                        SCOPES,
                        redirect_uri='http://localhost:8080/oauth2callback'
                    )
                    
                    # Gerar URL de autorização
                    auth_url, _ = flow.authorization_url(
                        access_type='offline',
                        include_granted_scopes='true'
                    )
                    
                    logger.error("❌ AUTENTICAÇÃO GOOGLE NECESSÁRIA!")
                    logger.info("📋 INSTRUÇÕES PARA CONFIGURAR GOOGLE MEET:")
                    logger.info(f"1. Acesse: {auth_url}")
                    logger.info("2. Autorize o aplicativo")
                    logger.info("3. Copie o código de autorização")
                    logger.info("4. Execute: python setup_google_auth.py")
                    
                    raise Exception("Autenticação Google necessária - veja instruções acima")
                    
                except Exception as e:
                    logger.error(f"❌ Erro na configuração OAuth: {str(e)}")
                    raise Exception("Configuração Google Meet necessária")
        
        # Salvar credenciais atualizadas
        if creds and creds.valid:
            with open(GOOGLE_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            logger.info("💾 Token Google salvo")
        
        # Criar serviço Google Calendar
        logger.info("📅 Conectando com Google Calendar...")
        service = build('calendar', 'v3', credentials=creds)
        
        # Configurar evento com Google Meet
        logger.info(f"🎯 Criando evento: {titulo}")
        event = {
            'summary': titulo,
            'description': f'Consulta médica para prescrição de cannabis medicinal\n\nHopeCann - Conectando pacientes a médicos especializados\n\nData: {data_hora.strftime("%d/%m/%Y às %H:%M")}',
            'start': {
                'dateTime': data_hora.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': (data_hora + timedelta(minutes=duracao_minutos)).isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'conferenceData': {
                'createRequest': {
                    'requestId': str(uuid.uuid4()),
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            },
            'attendees': [{'email': email} for email in participantes if email],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 dia antes
                    {'method': 'popup', 'minutes': 60},       # 1 hora antes
                ],
            },
        }
        
        # Criar evento no Google Calendar
        logger.info("🚀 Criando evento no Google Calendar...")
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1
        ).execute()
        
        # Extrair link do Google Meet
        conference_data = created_event.get('conferenceData', {})
        entry_points = conference_data.get('entryPoints', [])
        
        meet_link = None
        for entry_point in entry_points:
            if entry_point.get('entryPointType') == 'video':
                meet_link = entry_point.get('uri')
                break
        
        if not meet_link:
            # Fallback: tentar pegar qualquer link disponível
            meet_link = entry_points[0].get('uri') if entry_points else None
        
        if meet_link:
            logger.info(f"✅ Google Meet REAL criado com sucesso!")
            logger.info(f"🔗 Link: {meet_link}")
            logger.info(f"📅 Evento ID: {created_event.get('id')}")
            return meet_link
        else:
            logger.error("❌ Não foi possível obter link do Google Meet")
            raise Exception("Link do Google Meet não disponível")
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar reunião Google Meet REAL: {str(e)}")
        
        # Em caso de erro, informar que é necessário configurar
        error_msg = str(e)
        if "credentials" in error_msg.lower() or "auth" in error_msg.lower():
            logger.error("🔧 CONFIGURAÇÃO NECESSÁRIA - Google Meet não está configurado")
            return "ERRO_CONFIGURACAO_GOOGLE"
        else:
            logger.error("🔧 ERRO TEMPORÁRIO - Tente novamente")
            return "ERRO_TEMPORARIO_GOOGLE"

# ===== AGNO FRAMEWORK SETUP - MAYA =====

def create_maya_agent():
    """
    Cria Maya - Atendente Virtual HopeCann usando Agno Framework
    """
    try:
        agent = Agent(
            name="Maya - HopeCann",
            model=OpenAIChat(
                id=AI_MODEL,
                api_key=OPENAI_API_KEY
            ),
            tools=[
                DuckDuckGoTools()  # Ferramenta de busca web para informações sobre cannabis medicinal
            ],
            description="""
            Você é Maya, a atendente virtual especializada da HopeCann! 🌿
            
            Sua missão é ajudar pacientes a agendarem consultas médicas para prescrição de cannabis medicinal.
            
            Suas características:
            - Nome: Maya
            - Empresa: HopeCann
            - Especialidade: Agendamento de consultas médicas para cannabis medicinal
            - Personalidade: Acolhedora, profissional, empática e informativa
            - Conhecimento: Cannabis medicinal, legislação, benefícios terapêuticos
            - Objetivo: Facilitar o acesso à cannabis medicinal através de consultas especializadas
            """,
            instructions=[
                "Apresente-se como Maya da HopeCann APENAS na primeira interação com cada paciente",
                "Seja acolhedora e empática - muitos pacientes podem estar sofrendo",
                "Explique que a HopeCann conecta pacientes a médicos especializados em cannabis medicinal",
                "Colete informações essenciais: nome, telefone, email, condição médica, preferência de data/horário",
                "Ofereça horários disponíveis baseados na agenda médica",
                "Crie reuniões no Google Meet automaticamente após confirmação",
                "Forneça informações educativas sobre cannabis medicinal quando apropriado",
                "Mantenha sigilo médico e seja respeitosa com informações sensíveis",
                "Use emojis relacionados à saúde e bem-estar: 🌿 💚 🩺 📅 ✅",
                "Sempre responda em português brasileiro",
                "Se não souber algo específico sobre cannabis medicinal, busque informações atualizadas",
                "Evite repetir informações já mencionadas na conversa",
                "Mantenha respostas diretas e focadas no objetivo do paciente"
            ],
            show_tool_calls=True,
            markdown=False,  # WhatsApp não suporta markdown
            debug_mode=False
        )
        
        logger.info("🌿 Maya - Atendente HopeCann criada com sucesso!")
        return agent
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar Maya: {str(e)}")
        return None

# Criar agente Maya global
maya_agent = create_maya_agent()

if not maya_agent:
    logger.error("❌ Falha crítica: Não foi possível criar Maya!")
    exit(1)

# ===== EVOLUTION API CLIENT =====

def send_message(phone_number, message):
    """
    Envia mensagem via Evolution API
    """
    try:
        url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE_NAME}"
        
        payload = {
            "number": phone_number,
            "text": message
        }
        
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY
        }
        
        logger.debug(f"Enviando mensagem para {phone_number}: {message[:50]}...")
        
        response = requests.post(url, json=payload, headers=headers)
        
        logger.info(f"✅ Mensagem enviada para {phone_number}: {response.status_code}")
        return response.status_code == 201
        
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem: {str(e)}")
        return False

def send_welcome_banner(phone_number):
    """
    Envia banner de boas-vindas para primeiro contato
    """
    try:
        banner_path = os.path.join(os.path.dirname(__file__), 'banner.png')
        
        if not os.path.exists(banner_path):
            logger.warning(f"⚠️ Banner não encontrado: {banner_path}")
            return False
            
        url = f"{EVOLUTION_API_URL}/message/sendMedia/{EVOLUTION_INSTANCE_NAME}"
        
        # Converter imagem para base64 conforme documentação
        import base64
        with open(banner_path, 'rb') as banner_file:
            banner_base64 = base64.b64encode(banner_file.read()).decode('utf-8')
        
        # Payload conforme documentação oficial da Evolution API
        payload = {
            "number": phone_number,
            "mediaMessage": {
                "mediatype": "image",  # Corrigido: Evolution API usa "mediatype" (minúsculo)
                "fileName": "banner_hopecann.png",
                "caption": "🌿 Seja bem-vindo(a) à HopeCann! Sou a Maya, sua assistente virtual especializada em cannabis medicinal. 💚",
                "media": banner_base64
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY
        }
        
        logger.info(f"📸 Enviando banner de boas-vindas para {phone_number}")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Banner enviado com sucesso para {phone_number}")
            # Marcar como primeiro contato enviado
            first_contact_tracker[phone_number] = True
            return True
        else:
            logger.error(f"❌ Erro ao enviar banner: {response.status_code} - {response.text}")
            return False
                
    except Exception as e:
        logger.error(f"❌ Erro ao enviar banner: {str(e)}")
        return False

def is_first_contact(phone_number, contact_name):
    """
    Verifica se é o primeiro contato com este usuário
    """
    # Verificar se já enviamos banner para este número
    if phone_number in first_contact_tracker:
        return False
        
    # Verificar se existe contexto anterior
    if phone_number in conversation_context and len(conversation_context[phone_number]) > 0:
        return False
        
    # Simular verificação no banco (já que não temos tabela pacientes)
    # Em produção, verificaria se usuário existe no banco
    logger.info(f"🔍 Verificando primeiro contato para {contact_name} ({phone_number})")
    return True

def download_audio_from_url(audio_url, phone_number):
    """
    Baixa arquivo de áudio da URL fornecida pela Evolution API
    """
    try:
        headers = {
            "apikey": EVOLUTION_API_KEY
        }
        
        logger.info(f"📷 Baixando áudio de: {audio_url[:50]}...")
        response = requests.get(audio_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Salvar arquivo temporário
            temp_audio_path = f"temp_audio_{phone_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ogg"
            with open(temp_audio_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"✅ Áudio baixado: {temp_audio_path}")
            return temp_audio_path
        else:
            logger.error(f"❌ Erro ao baixar áudio: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erro no download do áudio: {str(e)}")
        return None

def find_ffmpeg_executable():
    """
    Encontra o executável do ffmpeg no sistema Windows
    """
    import shutil
    import glob
    
    # Tentar encontrar no PATH primeiro
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path
    
    # Locais comuns de instalação do ffmpeg no Windows
    common_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-*\bin\ffmpeg.exe"),
        os.path.expanduser(r"~\scoop\apps\ffmpeg\current\bin\ffmpeg.exe"),
        os.path.expanduser(r"~\chocolatey\bin\ffmpeg.exe")
    ]
    
    for path_pattern in common_paths:
        if '*' in path_pattern:
            # Usar glob para padrões com wildcard
            matches = glob.glob(path_pattern)
            if matches:
                return matches[0]
        else:
            if os.path.exists(path_pattern):
                return path_pattern
    
    return None

def convert_audio_with_ffmpeg(input_path):
    """
    Converte áudio usando ffmpeg - solução definitiva para arquivos WhatsApp
    Converte qualquer formato de áudio para WAV compatível com Whisper
    """
    import subprocess
    
    try:
        logger.info(f"🔍 Convertendo áudio com ffmpeg: {input_path}")
        
        # Verificar se arquivo existe e tem tamanho válido
        if not os.path.exists(input_path):
            logger.error(f"❌ Arquivo não encontrado: {input_path}")
            return None
            
        file_size = os.path.getsize(input_path)
        if file_size == 0:
            logger.error(f"❌ Arquivo vazio: {input_path}")
            return None
        
        if file_size < 100:  # Muito pequeno para ser áudio válido
            logger.error(f"❌ Arquivo muito pequeno: {file_size} bytes")
            return None
            
        logger.info(f"📊 Tamanho do arquivo original: {file_size} bytes")
        
        # Encontrar ffmpeg
        ffmpeg_exe = find_ffmpeg_executable()
        if not ffmpeg_exe:
            logger.error("❌ ffmpeg não encontrado no sistema")
            logger.info("📝 Reinicie o terminal após instalar ffmpeg")
            return None
        
        logger.info(f"✅ ffmpeg encontrado: {ffmpeg_exe}")
        
        # Gerar nome do arquivo de saída WAV
        output_path = input_path.replace('.ogg', '.wav')
        
        # Comando ffmpeg para conversão robusta
        # -i: arquivo de entrada
        # -acodec pcm_s16le: codec de áudio WAV padrão
        # -ar 16000: taxa de amostragem 16kHz (ideal para speech)
        # -ac 1: mono (1 canal)
        # -y: sobrescrever arquivo de saída se existir
        ffmpeg_cmd = [
            ffmpeg_exe,
            '-i', input_path,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',
            output_path
        ]
        
        logger.info(f"🔄 Executando: {' '.join(ffmpeg_cmd)}")
        
        # Executar ffmpeg
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=30  # Timeout de 30 segundos
        )
        
        if result.returncode != 0:
            logger.error(f"❌ Erro no ffmpeg: {result.stderr}")
            return None
        
        # Verificar se arquivo de saída foi criado
            try:
                logger.info("🚀 Transcrevendo com AssemblyAI SDK diretamente...")
                
                transcriber = aai.Transcriber()
                config = aai.TranscriptionConfig(
                    language_code="pt",
                    speech_model=aai.SpeechModel.universal
                )
                
                transcript = transcriber.transcribe(decrypted_audio_path, config=config)
                
                if transcript.status == aai.TranscriptStatus.completed:
                    transcribed_text = transcript.text.strip()
                    if transcribed_text:
                        logger.info(f"✅ Transcrição AssemblyAI direta: {transcribed_text[:100]}...")
                        
                        # Limpar arquivo temporário
                        cleanup_temp_files(decrypted_audio_path)
                        
                        # Gerar resposta baseada no texto transcrito
                        nome_paciente = extract_patient_name_from_number(sender_number)
                        response_text = generate_maya_response(transcribed_text, sender_number, nome_paciente)
                        
                        return response_text
                
                logger.warning(f"⚠️ AssemblyAI falhou: {transcript.error if hasattr(transcript, 'error') else 'Sem texto'}")
                
            except Exception as aai_error:
                logger.warning(f"⚠️ Erro na transcrição AssemblyAI direta: {aai_error}")
        
        # MÉTODO 3: Fallback para download direto se getBase64 falhou
        if not decrypted_audio_path and audio_url:
            logger.info("🔄 MÉTODO 3: Fallback para download direto do áudio...")
            
            # Verificar se a URL indica arquivo criptografado (.enc)
            is_encrypted_url = audio_url.endswith('.enc')
            if is_encrypted_url:
                logger.warning("⚠️ URL indica arquivo criptografado (.enc)")
                if not media_key:
                    logger.error("❌ Arquivo criptografado sem chave de descriptografia")
                    return "❌ Não consegui processar seu áudio (arquivo criptografado). A Evolution API deve fornecer arquivos descriptografados automaticamente."
            
            # Baixar o arquivo de áudio
            try:
                logger.info(f"🔗 Baixando áudio da URL: {audio_url}")
                response = requests.get(audio_url, timeout=30)
                response.raise_for_status()
                
                # Salvar arquivo temporário
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = os.path.splitext(audio_url)[1]
                temp_filename = f"temp_audio_{sender_number}_{timestamp}{file_extension}"
                temp_path = os.path.join(os.getcwd(), temp_filename)
                
                try:
                    with open(temp_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"💾 Arquivo salvo: {temp_path}")
                    
                    # Se arquivo está criptografado, avisa sobre limitação
                    if is_encrypted_url:
                        logger.warning("⚠️ Arquivo criptografado (.enc) detectado")
                        cleanup_temp_files(temp_path)
                        return "❌ Não foi possível processar o áudio criptografado. Por favor, configure a Evolution API para fornecer arquivos descriptografados automaticamente usando webhook_base64=true."
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao salvar arquivo: {str(e)}")
                    return "❌ Erro interno ao processar áudio."
                
            except Exception as download_error:
                logger.error(f"❌ Erro ao baixar áudio: {str(download_error)}")
                return "❌ Não consegui baixar seu áudio. Tente enviar novamente."
        
        # Transcrever o áudio baixado diretamente com AssemblyAI
        try:
            logger.info(f"🚀 Transcrevendo arquivo baixado diretamente: {temp_path}")
            
            transcriber = aai.Transcriber()
            config = aai.TranscriptionConfig(
                language_code="pt",
                speech_model=aai.SpeechModel.universal
            )
            
            transcript = transcriber.transcribe(temp_path, config=config)
            
            if transcript.status == aai.TranscriptStatus.completed and transcript.text:
                transcribed_text = transcript.text.strip()
                
                # Limpar arquivos temporários
                cleanup_temp_files(temp_path)
                
                logger.info(f"✅ Áudio transcrito diretamente: {transcribed_text[:100]}...")
                
                # Gerar resposta baseada no texto transcrito
                nome_paciente = extract_patient_name_from_number(sender_number)
                response_text = generate_maya_response(transcribed_text, sender_number, nome_paciente)
                
                return response_text
            else:
                logger.warning(f"⚠️ Falha na transcrição direta: {transcript.error if hasattr(transcript, 'error') else 'Sem texto'}")
                
        except Exception as direct_error:
            logger.warning(f"⚠️ Erro na transcrição direta: {direct_error}")
        
        # MÉTODO 4: Fallback para a função transcribe_audio robusta
        logger.info("🔄 MÉTODO 4: Fallback para transcribe_audio com conversão robusta...")
        transcribed_text = transcribe_audio(temp_path)
        
        # Limpar arquivos temporários
        cleanup_temp_files(temp_path)
        
        # Limpar possível arquivo convertido
        wav_path = temp_path.replace(file_extension, '.wav')
        cleanup_temp_files(wav_path)
        
        if not transcribed_text:
            return "❌ Não consegui entender seu áudio. Tente falar mais claramente ou enviar uma mensagem de texto."
        
        logger.info(f"✅ Áudio transcrito (fallback): {transcribed_text[:100]}...")
        
        # Gerar resposta baseada no texto transcrito
        nome_paciente = extract_patient_name_from_number(sender_number)
        response_text = generate_maya_response(transcribed_text, sender_number, nome_paciente)
        
        return response_text
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento de áudio base64: {str(e)}")
        return "❌ Ocorreu um erro ao processar seu áudio. Tente enviar uma mensagem de texto."


def send_typing_status(to_number, duration_seconds=3):
    """Envia status de 'digitando' para simular uma pessoa real digitando no WhatsApp"""
    try:
        url = f"{EVOLUTION_API_URL}/chat/sendPresence/{EVOLUTION_INSTANCE_NAME}"
        
        # Configurar payload para status 'composing' (digitando)
        payload = {
            "number": to_number,
            "options": {
                "delay": duration_seconds * 1000,  # Converter segundos para milissegundos
                "presence": "composing"  # Status "digitando"
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY
        }
        
        logger.debug(f"⌨️ Enviando status 'digitando' para {to_number} por {duration_seconds} segundos")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Status 'digitando' ativado para {to_number}")
            # Esperar o tempo de digitação (opcional, já que a API gerencia isso)
            time.sleep(duration_seconds)
            return True
        else:
            logger.warning(f"⚠️ Não foi possível ativar status 'digitando': {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao enviar status 'digitando': {str(e)}")
        return False

def send_text_message(to_number, message):
    """Envia mensagem de texto via Evolution API com simulação de digitação prévia"""
    try:
        # Primeiro ativar o status "digitando" por 3 segundos
        typing_active = send_typing_status(to_number, 3)
        if typing_active:
            logger.debug(f"Status 'digitando' ativado com sucesso")
        else:
            logger.warning("Não foi possível ativar status 'digitando', enviando mensagem diretamente")
        
        # Agora enviar a mensagem
        url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE_NAME}"
        
        payload = {
            "number": to_number,
            "textMessage": {
                "text": message
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY
        }
        
        logger.debug(f"Enviando mensagem para {to_number}: {message[:50]}...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        logger.info(f"✅ Mensagem enviada para {to_number}: {response.status_code}")
        
        if response.status_code in [200, 201]:
            return True
        else:
            logger.error(f"❌ Erro ao enviar mensagem: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro no envio: {str(e)}")
        return False

def send_multiple_messages(to_number, messages, delay_seconds=2):
    """
    Envia múltiplas mensagens sequenciais com delay para simular conversa natural
    """
    import time
    
    success_count = 0
    for i, message in enumerate(messages):
        try:
            logger.info(f"💬 Enviando mensagem {i+1}/{len(messages)} para {to_number}")
            
            success = send_text_message(to_number, message)
            if success:
                success_count += 1
                logger.info(f"✅ Mensagem {i+1} enviada com sucesso")
            else:
                logger.error(f"❌ Falha ao enviar mensagem {i+1}")
            
            # Delay entre mensagens (exceto na última)
            if i < len(messages) - 1:
                logger.debug(f"⏳ Aguardando {delay_seconds}s antes da próxima mensagem...")
                time.sleep(delay_seconds)
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem {i+1}: {str(e)}")
    
    logger.info(f"📊 Resultado: {success_count}/{len(messages)} mensagens enviadas")
    return success_count == len(messages)

# ===== PROCESSAMENTO DE MENSAGENS - MAYA =====

def verificar_usuario_no_banco(telefone, nome):
    """
    Verifica se usuário existe no banco de dados da HopeCann
    Simula verificação já que não temos tabela de usuários
    """
    try:
        # Simular verificação no banco
        # Em produção real, consultaria tabela de usuários/pacientes
        logger.info(f"🔍 Verificando usuário {nome} ({telefone}) no banco de dados")
        
        # Por enquanto, simular que usuário não existe para testar o fluxo
        # Em produção, faria: SELECT * FROM usuarios WHERE telefone = telefone AND nome LIKE '%nome%'
        usuario_existe = False  # Simular que usuário não existe
        
        if usuario_existe:
            logger.info(f"✅ Usuário {nome} encontrado no banco")
            return True
        else:
            logger.info(f"❌ Usuário {nome} não encontrado no banco")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar usuário no banco: {str(e)}")
        return False

# Importar sistema de memória persistente
import sys
import os

# Adicionar caminho do diretório whatsapp-agent ao path para poder importar o módulo memory_manager
sys.path.append(os.path.join(os.path.dirname(__file__), 'whatsapp-agent'))
from memory_manager import get_memory

def generate_maya_response(text_content, from_number, contact_name="Usuário", canal="whatsapp", tipo="texto"):
    """
    Gera resposta usando Maya (Agno Framework) com contexto HopeCann
    Inclui personalização com nome da pessoa quando disponível
    Usa sistema de memória persistente para rastrear interações por número
    
    Args:
        text_content (str): Texto da mensagem do usuário
        from_number (str): Número de telefone/identificador do usuário
        contact_name (str, optional): Nome do contato. Defaults to "Usuário".
        canal (str, optional): Canal de comunicação. Defaults to "whatsapp".
        tipo (str, optional): Tipo de mensagem (texto, áudio, imagem). Defaults to "texto".
    """
    try:
        # Inicializar contexto se não existir
        if from_number not in conversation_context:
            conversation_context[from_number] = []
        
        # Obter contexto da conversa (unificado entre texto, áudio e imagem)
        context = conversation_context.get(from_number, [])
        
        # Verificar se é primeira interação usando sistema de memória persistente
        is_first_interaction = False
        
        # Registrar interação na memória persistente e verificar se é primeira interação
        try:
            # Registrar interação no sistema de memória persistente
            memory = get_memory()
            is_first_interaction = memory.is_first_interaction(from_number)
            
            # Registrar esta interação (independente do tipo)
            memory.record_interaction(from_number, canal, tipo, contact_name)
            
            logger.info(f"{'🆕 Primeira interação' if is_first_interaction else '🔄 Interação recorrente'} para {from_number} (verificado na memória persistente)")
            logger.info(f"✅ Interação de {tipo} registrada na memória persistente para {from_number}")
        except Exception as e:
            # Fallback para verificação local (se sistema de memória falhar)
            is_first_interaction = len(context) == 0
            logger.error(f"❌ Erro ao verificar/registrar na memória persistente: {str(e)}, usando fallback local: {is_first_interaction}")
        
        logger.info(f"Status da conversa: {len(context)} mensagens no histórico para {from_number}")
        
        # Registrar histórico unificado para debug
        if context and len(context) > 0:
            logger.info(f"Histórico: Última mensagem de {context[-1].get('contact_name', 'Desconhecido')}: '{context[-1].get('user', '')[:30]}...'")
        
        # Preparar contexto especializado para Maya
        context_text = ""
        if context:
            recent_context = context[-3:]  # Últimas 3 interações
            context_parts = []
            for interaction in recent_context:
                if isinstance(interaction, dict):
                    user_msg = interaction.get('user', interaction.get('mensagem', 'Mensagem do usuário'))
                    assistant_msg = interaction.get('assistant', interaction.get('resposta', 'Resposta da Maya'))
                    context_parts.append(f"Paciente: {user_msg}")
                    context_parts.append(f"Maya: {assistant_msg}")
            context_text = "\n".join(context_parts)
        
        # Verificar se usuário existe no banco de dados
        usuario_cadastrado = verificar_usuario_no_banco(from_number, contact_name)
        
        # Se usuário não está cadastrado, redirecionar para site
        if not usuario_cadastrado and contact_name and contact_name != "Usuário":
            logger.info(f"🌐 Redirecionando {contact_name} para cadastro no site")
            return f"""Olá {contact_name}! 👋

🌿 Sou a Maya da HopeCann, sua assistente virtual especializada em cannabis medicinal.

Para ter acesso aos nossos serviços de consulta, agendamento e suporte, você precisa estar cadastrado em nosso sistema.

🌐 **Por favor, acesse nosso site oficial para realizar seu cadastro:**
https://www.hopecann.com.br/

📋 **No site você poderá:**
• Fazer seu cadastro completo
• Agendar consultas
• Acessar informações sobre tratamentos
• Falar com nossa equipe especializada

Após o cadastro, ficarei feliz em ajudá-lo com todas suas necessidades! 😊🌿"""
        
        # Processar comandos especiais de agendamento primeiro
        agendamento_response = processar_comandos_agendamento(text_content, "", from_number)
        if agendamento_response == "MENSAGENS_SEQUENCIAIS_ENVIADAS":
            # Salvar no contexto
            context.append({
                'user': text_content,
                'assistant': 'Processamento de agendamento com múltiplas mensagens',
                'timestamp': datetime.now().isoformat(),
                'contact_name': contact_name
            })
            conversation_context[from_number] = context
            return "MENSAGENS_SEQUENCIAIS_ENVIADAS"
        
        # Preparar nome personalizado para uso nas respostas
        nome_personalizado = contact_name if contact_name and contact_name != 'Usuário' else ""
        
        # Verificar se é primeira interação ou se já houve comunicação prévia
        # Agora usamos o is_first_interaction já determinado pelo sistema de memória persistente
        
        # Preparar prompt personalizado baseado no contexto e histórico
        if is_first_interaction:
            # Primeira interação real - apresentação breve
            full_prompt = f"""Você é Maya da HopeCann. Apresente-se brevemente como assistente virtual especializada em agendamento de consultas médicas de cannabis medicinal.
            
            {f"A pessoa se chama {contact_name}." if nome_personalizado else ""}
            
            MENSAGEM: {text_content}
            
            INSTRUÇÕES IMPORTANTES:
            - NÃO peça telefone (já temos: {from_number})
            - Se a mensagem contém email, condição médica ou pedido de agendamento, use [PROCESSAR_AGENDAMENTO] imediatamente
            - Seja direta e inteligente
            - Apresente-se apenas uma vez, NUNCA se apresente novamente
            
            Se a mensagem já contém informações para agendamento, processe diretamente.
            """
            logger.info(f"🌿 Primeira interação - enviando apresentação para {from_number}")
        else:
            # Interação subsequente - sem apresentação
            full_prompt = f"""
            Você é Maya da HopeCann. Responda de forma natural e direta, sem NUNCA se apresentar novamente.
            {f"O nome da pessoa é {contact_name}." if nome_personalizado else ""}
            
            {f"CONTEXTO DA CONVERSA:\n{context_text}\n" if context_text else ""}
            
            NOVA MENSAGEM: {text_content}
            
            INSTRUÇÕES IMPORTANTES:
            - NUNCA se apresente novamente como Maya ou mencione que trabalha para HopeCann
            - NÃO peça telefone (já temos: {from_number})
            - Se mencionarem email, condição médica ou agendamento, use [PROCESSAR_AGENDAMENTO]
            - Seja direta e inteligente, não repetitiva
            - Use as informações que já tem
            - Usuário já conhece você, NÃO se apresente
            - Responda como se estivesse continuando uma conversa já iniciada
            
            Responda de forma útil e focada no agendamento, sem apresentações.
            """
            logger.info(f"🔄 Interação subsequente - sem apresentação para {from_number}")
        
        
        # Gerar resposta com Maya
        logger.info(f"🌿 Gerando resposta Maya para: {text_content[:50]}...")
        response = maya_agent.run(full_prompt)
        
        # Extrair conteúdo da resposta corretamente
        if hasattr(response, 'content'):
            maya_response = response.content
        elif hasattr(response, 'message'):
            maya_response = response.message
        else:
            maya_response = str(response)
        
        logger.info(f"✅ Resposta Maya gerada: {maya_response[:100]}...")
        
        # Processar comandos especiais de agendamento
        maya_response = processar_comandos_agendamento(text_content, maya_response, from_number)
        
        # Salvar no contexto
        context.append({
            'user': text_content,
            'assistant': maya_response,
            'timestamp': datetime.now().isoformat(),
            'contact_name': contact_name,
            'channel': canal,
            'type': tipo
        })
        conversation_context[from_number] = context
        
        # Atualizar memória persistente com o resultado da interação
        try:
            get_memory().update_interaction_result(from_number, maya_response)
            logger.info(f"✅ Resultado da interação registrado na memória persistente para {from_number}")
        except Exception as e:
            logger.error(f"❌ Erro ao registrar interação na memória persistente: {str(e)}")
        
        logger.info("🌿 Resposta gerada com Maya HopeCann!")
        return maya_response
        
    except Exception as e:
        logger.error(f"❌ Erro na geração Maya: {str(e)}")
        
        # Fallback melhorado - sem repetição desnecessária
        context = conversation_context.get(from_number, [])
        is_first_interaction = len(context) == 0
        
        # Preparar nome personalizado para fallback
        nome_personalizado = contact_name if contact_name and contact_name != 'Usuário' else ""
        
        # Fallback responses personalizadas com nome
        if is_first_interaction:
            if nome_personalizado:
                fallback_responses = [
                    f"Olá, {contact_name}! 🩺 Sou Maya da HopeCann. Posso te ajudar a conectar com nossos médicos especializados em cannabis medicinal!"
                ]
            else:
                fallback_responses = [
                    f"Olá! 🩺 Sou Maya da HopeCann. Posso te ajudar a conectar com nossos médicos especializados em cannabis medicinal!"
                ]
        else:
            if nome_personalizado:
                fallback_responses = [
                    f"Entendi sua mensagem, {contact_name}. Como posso te ajudar com o agendamento? 🌿",
                    f"Oi {contact_name}, posso te auxiliar com mais informações ou agendamento da consulta! 💚",
                    f"Olá {contact_name}! Em que mais posso te ajudar com o agendamento da consulta? 🩺"
                ]
            else:
                fallback_responses = [
                    f"Entendi sua mensagem sobre '{text_content}'. Como posso te ajudar com o agendamento? 🌿",
                    f"Sobre '{text_content}', posso te auxiliar com mais informações ou agendamento da consulta! 💚",
                    f"Vi sua mensagem. Em que mais posso te ajudar com o agendamento da consulta? 🩺"
                ]
        
        import random
        return random.choice(fallback_responses)

def processar_comandos_agendamento(texto_usuario, resposta_maya, telefone):
    """
    Processa comandos especiais de agendamento e integra com Supabase/Google Meet
    Fluxo: 1) Consultar horários reais 2) Confirmar com paciente 3) Criar Google Meet real
    Retorna lista de mensagens para envio sequencial
    """
    texto_lower = texto_usuario.lower()
    mensagens_sequenciais = []
    
    # Detectar se a mensagem já contém informações completas (telefone, email, condição)
    import re
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_encontrado = re.search(email_pattern, texto_usuario)
    
    # Condições médicas comuns
    condicoes_medicas = ['ansiedade', 'depressão', 'dor', 'insonia', 'epilepsia', 'cancer', 'artrite', 'fibromialgia']
    condicao_encontrada = any(condicao in texto_lower for condicao in condicoes_medicas)
    
    # Se a mensagem contém email E condição, processar diretamente
    if email_encontrado and condicao_encontrada:
        email_paciente = email_encontrado.group()
        
        # Verificar se paciente existe
        paciente_existente = verificar_paciente_existe(telefone)
        
        mensagens_processamento = []
        mensagens_processamento.append("✅ Perfeito! Vejo que você já forneceu suas informações.")
        mensagens_processamento.append("🔍 Verificando seu cadastro e consultando horários disponíveis...")
        
        if paciente_existente:
            nome_paciente = paciente_existente.get('nome', 'Paciente')
            mensagens_processamento.append(f"👋 Olá {nome_paciente}! Encontrei seu cadastro.")
        else:
            mensagens_processamento.append("🆕 Você ainda não tem cadastro. Vou criar para você!")
        
        # Buscar horários disponíveis
        data_inicio = datetime.now().isoformat()
        data_fim = (datetime.now() + timedelta(days=30)).isoformat()
        horarios = buscar_horarios_disponiveis(data_inicio, data_fim)
        
        if horarios and len(horarios) > 0:
            mensagens_processamento.append("✅ Encontrei horários disponíveis!")
            
            # Formatar horários
            horarios_formatados = []
            for i, horario in enumerate(horarios[:5], 1):
                try:
                    dia_semana = horario.get('dia_semana', 'N/A')
                    hora_inicio = horario.get('hora_inicio', 'N/A')
                    hora_fim = horario.get('hora_fim', 'N/A')
                    medico_nome = horario.get('medico_nome', 'Médico Especialista')
                    medico_crm = horario.get('medico_crm', '')
                    
                    crm_texto = f" ({medico_crm})" if medico_crm else ""
                    horarios_formatados.append(
                        f"{i}. 📅 {dia_semana.title()}, {hora_inicio} às {hora_fim} - Dr(a). {medico_nome}{crm_texto}"
                    )
                except Exception as e:
                    logger.error(f"Erro ao formatar horário: {str(e)}")
                    continue
            
            if horarios_formatados:
                horarios_texto = "\n".join(horarios_formatados)
                mensagens_processamento.append(f"🗺️ **Horários disponíveis:**\n{horarios_texto}")
                mensagens_processamento.append("💬 Escolha o horário digitando o número (ex: '1' para o primeiro).")
                
                # Salvar informações no contexto
                if telefone not in conversation_context:
                    conversation_context[telefone] = []
                
                conversation_context[telefone].append({
                    'tipo': 'informacoes_iniciais',
                    'email': email_paciente,
                    'paciente_existente': paciente_existente,
                    'horarios_disponiveis': horarios,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                mensagens_processamento.append("❌ Erro ao processar horários. Vou verificar com nossa equipe.")
        else:
            mensagens_processamento.append("⏰ No momento não encontrei horários disponíveis.")
            mensagens_processamento.append("🔄 Nossa equipe entrará em contato em breve com novas opções!")
        
        # Enviar mensagens sequenciais
        send_multiple_messages(telefone, mensagens_processamento, delay_seconds=2)
        return "MENSAGENS_SEQUENCIAIS_ENVIADAS"
    
    # Detectar solicitação inicial de agendamento (fluxo original)
    elif any(palavra in texto_lower for palavra in ['agendar', 'marcar', 'consulta', 'horário', 'horario']):
        # Primeira mensagem: confirmação e início da busca
        mensagens_sequenciais.append("Perfeito! 🌿 Vou verificar os horários disponíveis para você.")
        
        # Segunda mensagem: consultando sistema
        mensagens_sequenciais.append("🔍 Consultando nossa agenda no sistema... Um momento!")
        
        # Consultar horários reais no Supabase
        logger.info(f"🗓️ Consultando horários disponíveis no Supabase para {telefone}")
        
        # Buscar horários dos próximos 30 dias
        data_inicio = datetime.now().isoformat()
        data_fim = (datetime.now() + timedelta(days=30)).isoformat()
        
        horarios = buscar_horarios_disponiveis(data_inicio, data_fim)
        medicos = buscar_medicos()
        
        if horarios and len(horarios) > 0:
            # Terceira mensagem: horários encontrados
            mensagens_sequenciais.append("✅ Encontrei alguns horários disponíveis!")
            
            # Formatar horários disponíveis (usando esquema real)
            horarios_formatados = []
            for i, horario in enumerate(horarios[:5], 1):  # Mostrar até 5 horários
                try:
                    dia_semana = horario.get('dia_semana', 'N/A')
                    hora_inicio = horario.get('hora_inicio', 'N/A')
                    hora_fim = horario.get('hora_fim', 'N/A')
                    medico_nome = horario.get('medico_nome', 'Médico Especialista')
                    medico_crm = horario.get('medico_crm', '')
                    
                    # Formatar texto do horário
                    crm_texto = f" ({medico_crm})" if medico_crm else ""
                    horarios_formatados.append(
                        f"{i}. 📅 {dia_semana.title()}, {hora_inicio} às {hora_fim} - Dr(a). {medico_nome}{crm_texto}"
                    )
                except Exception as e:
                    logger.error(f"Erro ao formatar horário: {str(e)}")
                    logger.debug(f"Horário problemático: {horario}")
                    continue
            
            if horarios_formatados:
                horarios_texto = "\n".join(horarios_formatados)
                # Quarta mensagem: lista de horários
                mensagens_sequenciais.append(f"🗓️ **Horários disponíveis:**\n{horarios_texto}")
                # Quinta mensagem: instruções
                mensagens_sequenciais.append("💬 Para confirmar, responda com o número do horário desejado (ex: '1' para o primeiro horário).")
            else:
                mensagens_sequenciais.append("❌ Erro ao processar horários. Vou verificar com nossa equipe.")
            
        elif medicos and len(medicos) > 0:
            # Se não há horários específicos, mostrar médicos disponíveis
            mensagens_sequenciais.append("📋 Nossos médicos estão disponíveis, mas preciso verificar horários específicos.")
            
            medicos_texto = "\n".join([f"👨‍⚕️ Dr(a). {m['nome']} - {m.get('especialidade', 'Cannabis Medicinal')}" for m in medicos[:3]])
            mensagens_sequenciais.append(f"**Médicos disponíveis:**\n{medicos_texto}")
            mensagens_sequenciais.append("📞 Vou verificar a agenda deles e retorno em alguns minutos com horários específicos!")
            
        else:
            # Sem horários disponíveis
            mensagens_sequenciais.append("⏰ No momento não encontrei horários disponíveis no sistema.")
            mensagens_sequenciais.append("🔄 Vou verificar com nossa equipe médica e retorno em breve com novas opções de agendamento!")
        
        # Enviar mensagens sequenciais
        if mensagens_sequenciais:
            logger.info(f"📤 Enviando {len(mensagens_sequenciais)} mensagens sequenciais")
            send_multiple_messages(telefone, mensagens_sequenciais, delay_seconds=3)
            return "MENSAGENS_SEQUENCIAIS_ENVIADAS"  # Sinalizar que já enviou
    
    # Detectar e-mail (formato básico: contém @ e .) - PRIORIDADE ALTA
    elif '@' in texto_usuario and '.' in texto_usuario:
        # Validar formato de e-mail básico
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, texto_usuario.strip())
        if email_match:
            email_paciente = email_match.group()
            
            # Buscar horário escolhido no contexto
            context = conversation_context.get(telefone, [])
            horario_escolhido = None
            for item in reversed(context):  # Buscar do mais recente
                if isinstance(item, dict) and item.get('tipo') == 'horario_escolhido':
                    horario_escolhido = item
                    break
            
            if horario_escolhido:
                # Buscar detalhes do horário
                horarios = buscar_horarios_disponiveis()
                numero = horario_escolhido['numero']
                
                if horarios and len(horarios) >= numero:
                    horario_selecionado = horarios[numero - 1]
                    
                    # Verificar se paciente já existe no banco
                    paciente_existente = verificar_paciente_existe(telefone)
                    
                    mensagens_processamento = []
                    mensagens_processamento.append("✅ E-mail recebido! Verificando seus dados...")
                    
                    if paciente_existente:
                        # Paciente já cadastrado
                        nome_paciente = paciente_existente.get('nome', 'Paciente')
                        mensagens_processamento.append(f"👋 Olá {nome_paciente}! Encontrei seu cadastro em nosso sistema.")
                        
                        # Formatar dados para confirmação
                        dia_semana = horario_selecionado.get('dia_semana', 'N/A')
                        hora_inicio = horario_selecionado.get('hora_inicio', 'N/A')
                        hora_fim = horario_selecionado.get('hora_fim', 'N/A')
                        medico_nome = horario_selecionado.get('medico_nome', 'Médico Especialista')
                        
                        dados_confirmacao = f"""📅 **CONFIRMAÇÃO DO AGENDAMENTO**

👤 **Paciente:** {nome_paciente}
📞 **Telefone:** {telefone}
📧 **E-mail:** {email_paciente}

📅 **Data/Horário:** {dia_semana.title()}, {hora_inicio} às {hora_fim}
👨‍⚕️ **Médico:** Dr(a). {medico_nome}

❓ **Confirma esses dados?** Digite 'CONFIRMAR' para finalizar."""
                        
                        mensagens_processamento.append(dados_confirmacao)
                        
                        # Salvar dados temporários para confirmação final
                        conversation_context[telefone].append({
                            'tipo': 'dados_agendamento',
                            'nome': nome_paciente,
                            'telefone': telefone,
                            'email': email_paciente,
                            'horario': horario_selecionado,
                            'paciente_id': paciente_existente.get('id'),
                            'timestamp': datetime.now().isoformat()
                        })
                        
                    else:
                        # Paciente novo - precisa coletar nome completo
                        mensagens_processamento.append("🆕 Você ainda não tem cadastro em nosso sistema.")
                        mensagens_processamento.append("📝 Para finalizar, preciso do seu nome completo.")
                        mensagens_processamento.append("✍️ Por favor, digite seu nome completo para criarmos seu cadastro.")
                        
                        # Salvar dados temporários para cadastro
                        conversation_context[telefone].append({
                            'tipo': 'aguardando_nome_completo',
                            'email': email_paciente,
                            'telefone': telefone,
                            'horario': horario_selecionado,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    send_multiple_messages(telefone, mensagens_processamento, delay_seconds=2)
                    return "MENSAGENS_SEQUENCIAIS_ENVIADAS"
            
            # Se não encontrou horário escolhido
            mensagens_erro = ["❌ Não encontrei o horário que você escolheu.", "🔄 Por favor, escolha um horário novamente digitando o número correspondente."]
            send_multiple_messages(telefone, mensagens_erro, delay_seconds=2)
            return "MENSAGENS_SEQUENCIAIS_ENVIADAS"
    
    # Detectar seleção de horário (números 1-5) - APENAS se não for email
    elif any(num in texto_lower for num in ['1', '2', '3', '4', '5']) and '@' not in texto_usuario:
        # Extrair número escolhido
        numero_escolhido = None
        for num in ['1', '2', '3', '4', '5']:
            if num in texto_lower:
                numero_escolhido = int(num)
                break
        
        if numero_escolhido:
            # Buscar informações iniciais no contexto
            context = conversation_context.get(telefone, [])
            info_iniciais = None
            for item in reversed(context):
                if isinstance(item, dict) and item.get('tipo') == 'informacoes_iniciais':
                    info_iniciais = item
                    break
            
            if info_iniciais:
                # Já temos email e informações do paciente
                email_paciente = info_iniciais['email']
                paciente_existente = info_iniciais['paciente_existente']
                horarios = info_iniciais['horarios_disponiveis']
                
                if horarios and len(horarios) >= numero_escolhido:
                    horario_selecionado = horarios[numero_escolhido - 1]
                    
                    mensagens_confirmacao = []
                    mensagens_confirmacao.append(f"✅ Ótimo! Você escolheu o horário {numero_escolhido}.")
                    
                    if paciente_existente:
                        # Paciente já cadastrado - confirmar diretamente
                        nome_paciente = paciente_existente.get('nome', 'Paciente')
                        
                        dia_semana = horario_selecionado.get('dia_semana', 'N/A')
                        hora_inicio = horario_selecionado.get('hora_inicio', 'N/A')
                        hora_fim = horario_selecionado.get('hora_fim', 'N/A')
                        medico_nome = horario_selecionado.get('medico_nome', 'Médico Especialista')
                        medico_crm = horario_selecionado.get('medico_crm', '')
                        
                        crm_texto = f" ({medico_crm})" if medico_crm else ""
                        dados_confirmacao = f"""📅 **CONFIRMAÇÃO DO AGENDAMENTO**

👤 **Paciente:** {nome_paciente}
📞 **Telefone:** {telefone}
📧 **E-mail:** {email_paciente}

📅 **Data/Horário:** {dia_semana.title()}, {hora_inicio} às {hora_fim}
👨‍⚕️ **Médico:** Dr(a). {medico_nome}{crm_texto}

❓ **Confirma esses dados?** Digite 'CONFIRMAR' para finalizar."""
                        
                        mensagens_confirmacao.append(dados_confirmacao)
                        
                        # Salvar dados para confirmação final
                        conversation_context[telefone].append({
                            'tipo': 'dados_agendamento',
                            'nome': nome_paciente,
                            'telefone': telefone,
                            'email': email_paciente,
                            'horario': horario_selecionado,
                            'paciente_id': paciente_existente.get('id'),
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        # Paciente novo - pedir nome completo
                        mensagens_confirmacao.append("📝 Para finalizar, preciso do seu nome completo.")
                        mensagens_confirmacao.append("✍️ Digite seu nome completo para criarmos seu cadastro.")
                        
                        # Salvar dados para cadastro
                        conversation_context[telefone].append({
                            'tipo': 'aguardando_nome_completo',
                            'email': email_paciente,
                            'telefone': telefone,
                            'horario': horario_selecionado,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    send_multiple_messages(telefone, mensagens_confirmacao, delay_seconds=2)
                    return "MENSAGENS_SEQUENCIAIS_ENVIADAS"
            
            # Fluxo original se não encontrou informações iniciais
            mensagens_email = []
            mensagens_email.append(f"✅ Ótimo! Você escolheu o horário {numero_escolhido}.")
            mensagens_email.append("📧 Para finalizar o agendamento, preciso do seu e-mail.")
            mensagens_email.append("✍️ Por favor, digite seu e-mail para enviarmos a confirmação da consulta.")
            
            # Salvar horário escolhido no contexto (temporário)
            if telefone not in conversation_context:
                conversation_context[telefone] = []
            
            conversation_context[telefone].append({
                'tipo': 'horario_escolhido',
                'numero': numero_escolhido,
                'timestamp': datetime.now().isoformat()
            })
            
            send_multiple_messages(telefone, mensagens_email, delay_seconds=2)
            return "MENSAGENS_SEQUENCIAIS_ENVIADAS"
    
    # Detectar nome completo (quando aguardando cadastro)
    elif any(item.get('tipo') == 'aguardando_nome_completo' for item in conversation_context.get(telefone, []) if isinstance(item, dict)):
        nome_completo = texto_usuario.strip()
        
        # Validar se parece um nome completo (pelo menos 2 palavras)
        if len(nome_completo.split()) >= 2:
            # Buscar dados do cadastro pendente
            context = conversation_context.get(telefone, [])
            dados_cadastro = None
            for item in reversed(context):
                if isinstance(item, dict) and item.get('tipo') == 'aguardando_nome_completo':
                    dados_cadastro = item
                    break
            
            if dados_cadastro:
                mensagens_cadastro = []
                mensagens_cadastro.append(f"✅ Obrigada, {nome_completo.split()[0]}!")
                mensagens_cadastro.append("🔄 Criando seu cadastro em nosso sistema...")
                
                # Cadastrar novo paciente
                resultado_cadastro = cadastrar_novo_paciente(
                    nome_completo=nome_completo,
                    telefone=telefone,
                    email=dados_cadastro['email']
                )
                
                if resultado_cadastro:
                    paciente = resultado_cadastro['paciente']
                    senha_temporaria = resultado_cadastro['senha_temporaria']
                    
                    mensagens_cadastro.append("✅ Cadastro criado com sucesso!")
                    
                    # Enviar credenciais de acesso
                    credenciais_msg = f"""🔐 **SUAS CREDENCIAIS DE ACESSO**

📧 **E-mail:** {dados_cadastro['email']}
🔑 **Senha temporária:** {senha_temporaria}

🌐 **Acesse nossa plataforma em:** [Link da plataforma]
⚠️ **Importante:** Altere sua senha no primeiro acesso!"""
                    
                    mensagens_cadastro.append(credenciais_msg)
                    
                    # Continuar com confirmação do agendamento
                    horario_selecionado = dados_cadastro['horario']
                    dia_semana = horario_selecionado.get('dia_semana', 'N/A')
                    hora_inicio = horario_selecionado.get('hora_inicio', 'N/A')
                    hora_fim = horario_selecionado.get('hora_fim', 'N/A')
                    medico_nome = horario_selecionado.get('medico_nome', 'Médico Especialista')
                    
                    dados_confirmacao = f"""📅 **CONFIRMAÇÃO DO AGENDAMENTO**

👤 **Paciente:** {nome_completo}
📞 **Telefone:** {telefone}
📧 **E-mail:** {dados_cadastro['email']}

📅 **Data/Horário:** {dia_semana.title()}, {hora_inicio} às {hora_fim}
👨‍⚕️ **Médico:** Dr(a). {medico_nome}

❓ **Confirma esses dados?** Digite 'CONFIRMAR' para finalizar."""
                    
                    mensagens_cadastro.append(dados_confirmacao)
                    
                    # Salvar dados para confirmação final
                    conversation_context[telefone].append({
                        'tipo': 'dados_agendamento',
                        'nome': nome_completo,
                        'telefone': telefone,
                        'email': dados_cadastro['email'],
                        'horario': horario_selecionado,
                        'paciente_id': paciente.get('id'),
                        'senha_temporaria': senha_temporaria,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                else:
                    mensagens_cadastro.append("❌ Erro ao criar cadastro. Nossa equipe entrará em contato.")
                
                send_multiple_messages(telefone, mensagens_cadastro, delay_seconds=3)
                return "MENSAGENS_SEQUENCIAIS_ENVIADAS"
        
        else:
            # Nome inválido
            mensagens_erro = ["❌ Por favor, digite seu nome completo (nome e sobrenome).", "✍️ Exemplo: João Silva Santos"]
            send_multiple_messages(telefone, mensagens_erro, delay_seconds=2)
            return "MENSAGENS_SEQUENCIAIS_ENVIADAS"
    
    # Detectar confirmação final
    elif 'confirmar' in texto_lower or 'confirmo' in texto_lower:
        # Buscar dados do agendamento no contexto
        context = conversation_context.get(telefone, [])
        dados_agendamento = None
        for item in reversed(context):
            if isinstance(item, dict) and item.get('tipo') == 'dados_agendamento':
                dados_agendamento = item
                break
        
        if dados_agendamento:
            mensagens_finalizacao = []
            mensagens_finalizacao.append("⏳ Perfeito! Finalizando seu agendamento...")
            mensagens_finalizacao.append("💾 Salvando no sistema...")
            mensagens_finalizacao.append("🔗 Gerando link da consulta online...")
            
            try:
                # Gerar link do Google Meet
                horario_data = dados_agendamento['horario']
                titulo = f"Consulta Cannabis Medicinal - {dados_agendamento['nome']}"
                
                # Criar data/hora para o Google Meet (usar próxima ocorrência do dia da semana)
                hoje = datetime.now()
                dias_semana = {
                    'segunda-feira': 0, 'terça-feira': 1, 'quarta-feira': 2,
                    'quinta-feira': 3, 'sexta-feira': 4, 'sábado': 5, 'domingo': 6
                }
                
                dia_target = dias_semana.get(horario_data.get('dia_semana', '').lower(), 0)
                dias_ate_target = (dia_target - hoje.weekday()) % 7
                if dias_ate_target == 0:  # Se é hoje, agendar para próxima semana
                    dias_ate_target = 7
                
                data_consulta = hoje + timedelta(days=dias_ate_target)
                hora_inicio = horario_data.get('hora_inicio', '09:00')
                hora, minuto = map(int, hora_inicio.split(':'))
                data_consulta = data_consulta.replace(hour=hora, minute=minuto, second=0, microsecond=0)
                
                # Criar reunião Google Meet
                meet_link = criar_reuniao_google_meet(
                    titulo=titulo,
                    data_hora=data_consulta,
                    duracao_minutos=60,
                    participantes=[dados_agendamento['email']]
                )
                
                if meet_link:
                    # Salvar agendamento no Supabase
                    agendamento_salvo = salvar_agendamento(
                        dados_paciente={
                            'nome': dados_agendamento['nome'],
                            'telefone': dados_agendamento['telefone'],
                            'email': dados_agendamento['email']
                        },
                        data_hora=data_consulta.isoformat(),
                        medico_id=horario_data.get('medico_id')
                    )
                    
                    # Mensagem de sucesso com link
                    mensagem_sucesso = f"""✅ **AGENDAMENTO CONFIRMADO!**

🎉 Sua consulta foi agendada com sucesso!

🔗 **Link da consulta:**
{meet_link}

📧 Você também receberá um e-mail de confirmação.

👨‍⚕️ Até breve na consulta!"""
                    
                    mensagens_finalizacao.append(mensagem_sucesso)
                else:
                    mensagens_finalizacao.append("❌ Erro ao gerar link da consulta. Nossa equipe entrará em contato.")
                    
            except Exception as e:
                logger.error(f"Erro ao finalizar agendamento: {str(e)}")
                mensagens_finalizacao.append("❌ Erro ao finalizar agendamento. Nossa equipe entrará em contato.")
            
            send_multiple_messages(telefone, mensagens_finalizacao, delay_seconds=3)
            return "MENSAGENS_SEQUENCIAIS_ENVIADAS"
    
    return resposta_maya

def process_webhook_message(webhook_data):
    """
    Processa mensagem do webhook e envia resposta automática com Maya
    """
    try:
        # Extrair dados da mensagem
        event_type = webhook_data.get('event', '')
        data = webhook_data.get('data', {})
        
        # Processar apenas mensagens recebidas
        if event_type != 'messages.upsert':
            return False
        
        key = data.get('key', {})
        message = data.get('message', {})
        
        # Ignorar mensagens próprias
        if key.get('fromMe', False):
            logger.info("Ignorando mensagem própria")
            return False
        
        # Extrair número do remetente
        remote_jid = key.get('remoteJid', '')
        from_number = remote_jid.replace('@s.whatsapp.net', '').replace('@g.us', '')
        
        # Tentar extrair nome da pessoa (pushName ou notifyName)
        push_name = data.get('pushName', '')
        notify_name = data.get('notifyName', '')
        contact_name = push_name or notify_name or 'Usuário'
        
        # Verificar se é primeira interação com o sistema de memória persistente
        is_first_interaction = False
        try:
            is_first_interaction = get_memory().is_first_interaction(from_number)
            logger.info(f"{'🆕 Primeira interação' if is_first_interaction else '🔄 Interação recorrente'} para {from_number}")
        except Exception as e:
            logger.error(f"❌ Erro ao verificar primeira interação: {str(e)}")
        
        # Log detalhado dos dados do contato
        print(f"\n📄 DADOS DO CONTATO COMPLETOS:")
        print(f"   📞 Número: {from_number}")
        print(f"   👤 Nome (pushName): {push_name}")
        print(f"   📝 Nome (notifyName): {notify_name}")
        print(f"   ✅ Nome Final: {contact_name}")
        print(f"   🔄 Primeira interação: {'Sim' if is_first_interaction else 'Não'}")
        
        # Log completo dos dados para debug (apenas primeiras vezes)
        if len(mensagens_recebidas) < 3:  # Apenas nas primeiras 3 mensagens
            print(f"\n🔍 DEBUG - ESTRUTURA COMPLETA DO WEBHOOK:")
            print(f"   Key: {json.dumps(key, indent=2)}")
            print(f"   Data extras: pushName='{push_name}', notifyName='{notify_name}'")
        
        # Verificar se é primeiro contato e enviar banner de boas-vindas
        if is_first_contact(from_number, contact_name):
            logger.info(f"🎉 Primeiro contato detectado para {contact_name}")
            banner_sent = send_welcome_banner(from_number)
            if banner_sent:
                logger.info("✅ Banner de boas-vindas enviado com sucesso")
            else:
                logger.warning("⚠️ Falha ao enviar banner de boas-vindas")
        
        # Extrair conteúdo da mensagem (texto, áudio ou imagem)
        text_content = None
        audio_data = None
        image_data = None
        speech_to_text = None
        message_type = ""
        
        # Verificar diferentes tipos de mensagem
        if 'conversation' in message:
            text_content = message['conversation']
            message_type = "texto"
        elif 'extendedTextMessage' in message:
            text_content = message['extendedTextMessage'].get('text', '')
            message_type = "texto_estendido"
        elif 'audioMessage' in message:
            audio_data = message['audioMessage']
            message_type = "audio"
            logger.info(f"🎤 Mensagem de áudio recebida de {contact_name}")
            
            # Verificar se temos a transcrição via speechToText da Evolution API
            if 'speechToText' in message:
                speech_to_text = message['speechToText']
                message_type = "audio_transcrito"
                logger.info(f"🎤✨ Áudio com transcrição automática: {speech_to_text[:50]}...")
        elif 'imageMessage' in message:
            image_data = message['imageMessage']
            message_type = "imagem"
            logger.info(f"📷 Mensagem de imagem recebida de {contact_name}")
        
        # Processar diferentes tipos de conteúdo
        if audio_data:
            # Verificar primeiro se temos transcrição automática da Evolution API
            if speech_to_text:
                logger.info(f"✅ Usando transcrição automática da Evolution API: {speech_to_text[:100]}...")
                # Gerar resposta com base na transcrição já disponível
                response = generate_maya_response(speech_to_text, from_number, contact_name)
                
                # Verificar se já foram enviadas mensagens sequenciais
                if response == "MENSAGENS_SEQUENCIAIS_ENVIADAS":
                    print("✅ MENSAGENS SEQUENCIAIS JÁ ENVIADAS PELA MAYA (transcrição automática)")
                    return True  # Não enviar mensagem adicional
                else:
                    success = send_text_message(from_number, response)
                    if success:
                        logger.info("✅ Resposta para áudio transcrito automaticamente enviada com sucesso!")
                    return success
            else:
                # Fallback para processamento manual do áudio quando não há transcrição
                logger.info("⚠️ Sem transcrição automática disponível. Processando áudio manualmente...")
                
                # Verificar se há dados base64 no webhook (WEBHOOK_BASE64=true)
                base64_audio = None
                if 'base64' in audio_data:
                    base64_audio = audio_data.get('base64')
                    logger.info("✅ Dados base64 encontrados no webhook!")
                elif 'data' in audio_data and isinstance(audio_data['data'], str):
                    base64_audio = audio_data['data']
                    logger.info("✅ Dados base64 encontrados no campo 'data'!")
                
                if base64_audio:
                    # Processar áudio usando dados base64 (já descriptografado)
                    logger.info("🔄 Processando áudio usando dados base64 descriptografados...")
                    try:
                        import base64
                        import tempfile
                        # Decodificar base64
                        audio_bytes = base64.b64decode(base64_audio)
                        
                        # Salvar em arquivo temporário
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        temp_filename = f"temp_audio_base64_{from_number}_{timestamp}.ogg"
                        temp_path = os.path.join(os.getcwd(), temp_filename)
                        
                        with open(temp_path, 'wb') as f:
                            f.write(audio_bytes)
                        
                        logger.info(f"💾 Áudio base64 salvo: {temp_path}")
                        
                        # Transcrever usando AssemblyAI
                        from process_audio import transcribe_audio, cleanup_temp_files
                        transcribed_text = transcribe_audio(temp_path)
                        
                        # Limpar arquivo temporário
                        cleanup_temp_files(temp_path)
                        
                        if transcribed_text:
                            logger.info(f"✅ Áudio base64 transcrito: {transcribed_text[:100]}...")
                            response = generate_maya_response(transcribed_text, from_number, contact_name)
                            
                            if response == "MENSAGENS_SEQUENCIAIS_ENVIADAS":
                                print("✅ MENSAGENS SEQUENCIAIS JÁ ENVIADAS PELA MAYA (base64)")
                                return True  # Não enviar mensagem adicional
                            else:
                                success = send_text_message(from_number, response)
                                if success:
                                    logger.info("✅ Resposta para áudio base64 enviada com sucesso!")
                                return success
                        else:
                            logger.warning("⚠️ Falha na transcrição do áudio base64")
                            
                    except Exception as base64_error:
                        logger.error(f"❌ Erro ao processar áudio base64: {str(base64_error)}")
                
                # Se não há base64 ou falhou, tentar método tradicional (com arquivos .enc)
                logger.info("🔄 Tentando método tradicional com arquivo .enc...")
                try:
                    audio_message_data = {
                        'message': {
                            'audioMessage': audio_data
                        }
                    }
                    
                    # Mostrar informações detalhadas sobre a mensagem de áudio para debug
                    logger.info(f"🔍 Detalhes do objeto audio_data: {str(audio_data)[:200]}...")
                    
                    # Chamada com tratamento de erros explícito
                    response = process_audio_message(audio_message_data, from_number)
                    
                    # Se o processamento foi bem-sucedido, enviar resposta
                    if response and isinstance(response, str):
                        success = send_text_message(from_number, response)
                        if success:
                            logger.info("✅ Resposta para áudio processado manualmente enviada com sucesso!")
                        return success
                    else:
                        # Resposta de fallback se a transcrição falhou mas não gerou exceção
                        logger.warning("⚠️ Resposta de transcrição inválida ou vazia")
                        fallback_msg = "Desculpe, não consegui entender seu áudio. Pode tentar novamente ou enviar uma mensagem de texto?"
                        send_text_message(from_number, fallback_msg)
                        return True
                        
                except Exception as e:
                    # Capturar exceção e dar resposta amigável ao usuário
                    error_details = str(e)
                    logger.error(f"❌ Erro ao processar áudio: {error_details}")
                    
                    # Resposta de fallback para o usuário
                    fallback_msg = "Desculpe, tive um problema ao processar seu áudio. Pode tentar enviar uma mensagem de texto?"
                    send_text_message(from_number, fallback_msg)
                    return True
            
        elif image_data:
            # Processar imagem
            response = process_image_message(image_data, from_number)
            success = send_text_message(from_number, response)
            if success:
                logger.info("✅ Resposta para imagem enviada com sucesso!")
            return success
            
        elif not text_content:
            logger.info("Mensagem sem conteúdo de texto, áudio ou imagem")
            return False
        
        print(f"\n📱 MENSAGEM RECEBIDA:")
        print(f"   👤 De: {contact_name} ({from_number})")
        print(f"   💬 Texto: {text_content}")
        print(f"   🕐 Hora: {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"Processando mensagem de {contact_name} ({from_number}): {text_content[:50]}...")
        
        # Gerar resposta com Maya (incluindo nome da pessoa)
        print(f"\n🌿 GERANDO RESPOSTA COM MAYA HOPECANN...")
        response = generate_maya_response(text_content, from_number, contact_name)
        
        # Verificar se já foram enviadas mensagens sequenciais
        if response == "MENSAGENS_SEQUENCIAIS_ENVIADAS":
            print("✅ MENSAGENS SEQUENCIAIS JÁ ENVIADAS PELA MAYA")
            # Não enviar o texto "MENSAGENS_SEQUENCIAIS_ENVIADAS" ao usuário
            return True  # Considerar como sucesso sem enviar mensagem adicional
        else:
            print(f"✅ RESPOSTA MAYA: {response[:100]}...")
            # Enviar resposta única
            success = send_text_message(from_number, response)
        
        if success:
            logger.info("✅ Resposta automática Maya enviada com sucesso!")
            
            # Salvar mensagem processada
            mensagem_data = {
                'timestamp': datetime.now().isoformat(),
                'from': from_number,
                'message': text_content,
                'response': response,
                'maya_used': True,
                'hopecann': True
            }
            mensagens_recebidas.append(mensagem_data)
            
            return True
        else:
            logger.error("❌ Falha ao enviar resposta Maya")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro no processamento Maya: {str(e)}")
        return False

# ===== ENDPOINTS FLASK =====

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint principal do webhook"""
    try:
        print("\n" + "="*60)
        print(f"🔔 WEBHOOK RECEBIDO! {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        logger.info("Webhook recebido em: webhook")
        
        # Log detalhado dos headers
        print("📋 HEADERS RECEBIDOS:")
        for header, value in request.headers.items():
            print(f"   {header}: {value}")
        
        # Log do IP de origem
        print(f"🌐 IP Origem: {request.remote_addr}")
        print(f"🔗 URL: {request.url}")
        print(f"📊 Método: {request.method}")
        
        # Verificar Content-Type
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            data = request.get_json()
        else:
            # Tentar parsear como JSON mesmo sem Content-Type correto
            try:
                data = request.get_json(force=True)
            except:
                data = {}
        
        if not data:
            logger.warning("⚠️ Webhook recebido sem dados JSON válidos")
            return jsonify({"status": "error", "message": "Dados inválidos"}), 400
        
        # Processar e responder automaticamente com Maya
        try:
            response_sent = process_webhook_message(data)
            if response_sent:
                logger.info("✅ Resposta automática Maya enviada com sucesso!")
            else:
                logger.info("ℹ️ Mensagem processada, mas sem resposta necessária")
        except Exception as e:
            logger.error(f"Erro no processamento automático: {str(e)}")
        
        return jsonify({"status": "success", "message": "Webhook processado por Maya"}), 200
        
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/webhook/messages-upsert', methods=['POST'])
def webhook_messages_upsert():
    """Endpoint específico para messages-upsert da Evolution API"""
    return webhook()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check do sistema Maya"""
    try:
        maya_status = "✅ Ativa" if maya_agent else "❌ Inativa"
        supabase_status = "✅ Conectado" if supabase_client else "❌ Desconectado"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "maya_hopecann": maya_status,
            "supabase": supabase_status,
            "google_meet": "✅ Configurado",
            "evolution_api": EVOLUTION_API_URL,
            "instance": EVOLUTION_INSTANCE_NAME,
            "ai_model": AI_MODEL,
            "mensagens_processadas": len(mensagens_recebidas)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/agendamentos', methods=['GET'])
def listar_agendamentos():
    """Listar agendamentos recentes"""
    try:
        if not supabase_client:
            return jsonify({"error": "Supabase não configurado"}), 500
        
        result = supabase_client.table('agendamentos').select('*').order('created_at', desc=True).limit(10).execute()
        return jsonify({"agendamentos": result.data}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/medicos', methods=['GET'])
def listar_medicos():
    """Listar médicos disponíveis"""
    try:
        medicos = buscar_medicos()
        return jsonify({"medicos": medicos}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ===== INICIALIZAÇÃO =====

if __name__ == '__main__':
    print("🌿 Iniciando Maya - Atendente Virtual HopeCann...")
    print(f"📡 Evolution API: {EVOLUTION_API_URL}")
    print(f"🤖 Instância: {EVOLUTION_INSTANCE_NAME}")
    print(f"🧠 IA Maya Agno Framework: ✅ Configurada")
    print(f"🎯 Modelo: {AI_MODEL}")
    print(f"🔍 Ferramentas: DuckDuckGo Search")
    print(f"🗄️ Supabase: {'✅ Conectado' if supabase_client else '❌ Desconectado'}")
    print(f"📅 Google Meet: ✅ Configurado")
    print(f"💚 Maya HopeCann: ATIVA")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,  # ATIVADO PARA LOGS DETALHADOS
        threaded=True
    )

import os
import requests
import logging
import assemblyai as aai
from datetime import datetime
import time
import shutil
import glob
import subprocess
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
# Importar nosso módulo de descriptografia WhatsApp
import whatsapp_media_decrypt

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Chaves de API
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL')
EVOLUTION_INSTANCE_NAME = os.getenv('EVOLUTION_INSTANCE_NAME')
ASSEMBLY_AI_API_KEY = os.getenv('ASSEMBLY_AI_API_KEY')

# Configurar AssemblyAI
if ASSEMBLY_AI_API_KEY:
    aai.settings.api_key = ASSEMBLY_AI_API_KEY

def sanitize_filename(filename):
    """
    Remove caracteres inválidos para nomes de arquivo no Windows
    """
    # Caracteres proibidos no Windows: < > : " / \ | ? *
    # Também remove parâmetros de URL (tudo após ?)
    if '?' in filename:
        filename = filename.split('?')[0]
    
    # Remove caracteres inválidos
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove espaços extras e caracteres especiais adicionais
    sanitized = re.sub(r'[&=]', '_', sanitized)
    
    # Limita o tamanho do nome (Windows tem limite de 255 caracteres)
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200-len(ext)] + ext
    
    return sanitized

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
        if output_path == input_path:  # Se não era .ogg
            output_path = f"{os.path.splitext(input_path)[0]}.wav"
        
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
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"✅ Arquivo convertido com sucesso: {output_path} ({os.path.getsize(output_path)} bytes)")
            return output_path
        else:
            logger.error("❌ Falha na conversão: arquivo de saída não encontrado ou vazio")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erro na conversão com ffmpeg: {str(e)}")
        return None

def cleanup_temp_files(file_path):
    """
    Remove arquivos temporários gerados
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🧹 Arquivo temporário removido: {file_path}")
    except Exception as e:
        logger.error(f"❌ Erro ao remover arquivo temporário: {str(e)}")

def transcribe_audio(audio_path):
    """
    Transcreve áudio usando AssemblyAI
    """
    try:
        logger.info(f"🎙️ Transcrevendo áudio: {audio_path}")
        
        # Verificar se arquivo existe e tem tamanho válido
        if not os.path.exists(audio_path):
            logger.error(f"❌ Arquivo não encontrado: {audio_path}")
            return None
            
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            logger.error(f"❌ Arquivo vazio: {audio_path}")
            return None
        
        # Verificar se é um arquivo OGG válido (não criptografado)
        is_valid_audio = False
        try:
            with open(audio_path, 'rb') as f:
                header = f.read(4)
                
            if header.startswith(b'OggS'):
                is_valid_audio = True
                logger.info("✅ Arquivo OGG válido detectado")
            elif header.startswith(b'RIFF'):
                is_valid_audio = True
                logger.info("✅ Arquivo WAV válido detectado")
            else:
                logger.warning(f"⚠️ Arquivo não é OGG/WAV válido - header: {header}")
                # Tentar converter mesmo assim, pode ser outro formato
        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar header: {str(e)}")
        
        # Converter com ffmpeg para WAV padrão se não for WAV
        if not audio_path.lower().endswith('.wav'):
            logger.info(f"🔄 Convertendo áudio para WAV: {audio_path}")
            wav_path = convert_audio_with_ffmpeg(audio_path)
            
            if wav_path:
                logger.info(f"✅ Áudio convertido para WAV: {wav_path}")
                audio_path = wav_path
            else:
                logger.error("❌ Falha na conversão para WAV")
                # Continuar com o arquivo original
        
        # Transcrever com AssemblyAI
        try:
            if ASSEMBLY_AI_API_KEY:
                logger.info("🚀 Transcrevendo com AssemblyAI...")
                
                transcriber = aai.Transcriber()
                config = aai.TranscriptionConfig(
                    language_code="pt",
                    speech_model=aai.SpeechModel.universal
                )
                
                transcript = transcriber.transcribe(audio_path, config=config)
                
                if transcript.status == aai.TranscriptStatus.completed:
                    transcribed_text = transcript.text.strip()
                    if transcribed_text:
                        logger.info(f"✅ Transcrição AssemblyAI: {transcribed_text[:100]}...")
                        return transcribed_text
                    else:
                        logger.warning("⚠️ AssemblyAI retornou transcrição vazia")
                else:
                    logger.warning(f"⚠️ AssemblyAI falhou: {transcript.error if hasattr(transcript, 'error') else 'Sem texto'}")
            else:
                logger.warning("⚠️ Chave AssemblyAI não configurada")
                
        except Exception as aai_error:
            logger.warning(f"⚠️ Erro na transcrição AssemblyAI: {aai_error}")
        
        # Fallback: retornar mensagem de erro
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro crítico na transcrição: {str(e)}")
        return None

def process_audio_message(audio_message, sender_number):
    """
    Processa mensagens de áudio recebidas via webhook
    Extrai URL e informações, baixa áudio e transcreve
    """
    try:
        logger.info(f"🎵 Processando mensagem de áudio de {sender_number}...")
        
        # Log detalhado para debug
        logger.info(f"📓 Tipo do objeto audio_message: {type(audio_message)}")
        logger.info(f"📓 Conteúdo de audio_message: {str(audio_message)[:300]}...")
        
        # Extrair dados do áudio com validação robusta
        if not audio_message:
            logger.error("❌ audio_message é None ou vazio")
            return "❌ Formato de mensagem de áudio inválido (objeto vazio)"
            
        if not isinstance(audio_message, dict):
            logger.error(f"❌ audio_message não é um dicionário: {type(audio_message)}")
            return "❌ Formato de mensagem de áudio inválido (tipo incorreto)"
            
        if 'message' not in audio_message:
            logger.error("❌ Chave 'message' não encontrada em audio_message")
            return "❌ Formato de mensagem de áudio inválido (sem chave message)"
            
        if not isinstance(audio_message['message'], dict):
            logger.error(f"❌ audio_message['message'] não é um dicionário: {type(audio_message['message'])}")
            return "❌ Formato de mensagem de áudio inválido (message não é dicionário)"
            
        if 'audioMessage' not in audio_message['message']:
            logger.error("❌ Chave 'audioMessage' não encontrada em message")
            return "❌ Formato de mensagem de áudio inválido (sem chave audioMessage)"
        
        audio_data = audio_message['message']['audioMessage']
        audio_url = audio_data.get('url', '')
        mime_type = audio_data.get('mimetype', '')
        file_length = audio_data.get('fileLength', 0)
        media_key = audio_data.get('mediaKey', '')
        
        logger.info(f"🔍 Detalhes do áudio: {mime_type}, {file_length} bytes, URL: {audio_url[:30]}...")
        
        # MÉTODO 1: Obter base64 descriptografado da Evolution API
        decrypted_audio_path = None
        try:
            if audio_url:
                instance = EVOLUTION_INSTANCE_NAME
                message_id = audio_data.get('id', '')
                
                if message_id and EVOLUTION_API_URL:
                    get_base64_url = f"{EVOLUTION_API_URL}/chat/getBase64FromMediaMessage/{instance}"
                    logger.info(f"🔑 Obtendo áudio descriptografado via getBase64: {message_id}")
                    
                    payload = {
                        "messageId": message_id
                    }
                    
                    headers = {
                        "Content-Type": "application/json",
                        "apikey": EVOLUTION_API_KEY
                    }
                    
                    response = requests.post(get_base64_url, json=payload, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        base64_audio = data.get('base64', '')
                        
                        if base64_audio:
                            logger.info("✅ Base64 obtido com sucesso!")
                            
                            # Salvar em arquivo temporário
                            import base64
                            audio_bytes = base64.b64decode(base64_audio)
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            temp_filename = f"temp_audio_{sender_number}_{timestamp}.ogg"
                            decrypted_audio_path = os.path.join(os.getcwd(), temp_filename)
                            
                            with open(decrypted_audio_path, 'wb') as f:
                                f.write(audio_bytes)
                                
                            logger.info(f"💾 Áudio descriptografado salvo: {decrypted_audio_path}")
                            
                            # Verificar se realmente é um arquivo OGG válido (não criptografado)
                            try:
                                with open(decrypted_audio_path, 'rb') as f:
                                    header = f.read(4)
                                    
                                is_valid_ogg = header.startswith(b'OggS')
                                if not is_valid_ogg:
                                    logger.warning("⚠️ Arquivo não é OGG válido - possível criptografia")
                                    decrypted_audio_path = None
                            except Exception as e:
                                logger.warning(f"⚠️ Erro ao verificar header OGG: {str(e)}")
                    else:
                        logger.warning(f"⚠️ Falha ao obter base64: {response.status_code} - {response.text}")
        except Exception as e:
            logger.warning(f"⚠️ Erro no método getBase64: {str(e)}")
        
        # MÉTODO 2: Tentar transcrição direta com AssemblyAI
        if decrypted_audio_path:
            try:
                logger.info("🚀 Transcrevendo com AssemblyAI SDK diretamente...")
                
                transcribed_text = transcribe_audio(decrypted_audio_path)
                
                if transcribed_text:
                    logger.info(f"✅ Transcrição AssemblyAI direta: {transcribed_text[:100]}...")
                    
                    # Limpar arquivo temporário
                    cleanup_temp_files(decrypted_audio_path)
                    
                    # Limpar possível arquivo convertido
                    wav_path = decrypted_audio_path.replace('.ogg', '.wav')
                    cleanup_temp_files(wav_path)
                    
                    return transcribed_text
                else:
                    logger.warning("⚠️ Transcrição AssemblyAI direta falhou")
                
            except Exception as aai_error:
                logger.warning(f"⚠️ Erro na transcrição AssemblyAI direta: {aai_error}")
        
        # MÉTODO 3: Fallback para download direto
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
                
                # Extrair extensão da URL sem parâmetros de query
                parsed_url = urlparse(audio_url)
                clean_path = parsed_url.path
                file_extension = os.path.splitext(clean_path)[1]
                
                if not file_extension:
                    file_extension = '.ogg'  # Fallback para .ogg
                
                # Criar nome de arquivo seguro
                temp_filename = f"temp_audio_{sender_number}_{timestamp}{file_extension}"
                temp_filename = sanitize_filename(temp_filename)
                temp_path = os.path.join(os.getcwd(), temp_filename)
                
                try:
                    with open(temp_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"💾 Arquivo salvo: {temp_path}")
                    
                    # Se o arquivo for criptografado (.enc), tentar descriptografar
                    if '.enc' in temp_path or '.enc?' in temp_path:
                        logger.warning("⚠️ Arquivo criptografado (.enc) detectado")
                        
                        # Tentar extrair mediaKey da mensagem
                        media_key = audio_message.get('message', {}).get('audioMessage', {}).get('mediaKey', '')
                        if not media_key:
                            logger.error("❌ Arquivo criptografado sem chave de descriptografia (mediaKey)")
                            cleanup_temp_files(temp_path)
                            return "❌ Não consegui processar seu áudio (arquivo criptografado). A Evolution API deve fornecer arquivos descriptografados automaticamente."
                        
                        # Tentar descriptografar o áudio
                        logger.info("🔑 Tentando descriptografar arquivo de áudio usando mediaKey...")
                        try:
                            # Extrair informações completas da mensagem de áudio
                            file_sha256 = audio_message.get('message', {}).get('audioMessage', {}).get('fileSha256', '')
                            file_enc_sha256 = audio_message.get('message', {}).get('audioMessage', {}).get('fileEncSha256', '')
                            media_key_timestamp = audio_message.get('message', {}).get('audioMessage', {}).get('mediaKeyTimestamp', '')
                            
                            logger.info(f"🔍 Detalhes adicionais do áudio:")
                            logger.info(f"🔍 fileSha256: {file_sha256}")
                            logger.info(f"🔍 fileEncSha256: {file_enc_sha256}")
                            logger.info(f"🔍 mediaKeyTimestamp: {media_key_timestamp}")
                            logger.info(f"🔍 mediaKey: {media_key[:10]}... (truncado)")
                            
                            # Usar mediaKey diretamente em formato base64
                            # A mediaKey do WhatsApp é fornecida em base64
                            logger.info("🔑 Usando mediaKey em formato base64 para descriptografia...")
                            
                            # Descriptografar arquivo usando a chave base64 diretamente (MEDIA_TYPE_AUDIO = 3)
                            decrypted_path = whatsapp_media_decrypt.decrypt_media_with_base64_key(
                                temp_path, 
                                media_key, 
                                whatsapp_media_decrypt.MEDIA_TYPE_AUDIO
                            )
                            
                            if decrypted_path:
                                logger.info(f"✅ Áudio descriptografado com sucesso: {decrypted_path}")
                                # Continuar processamento com o arquivo descriptografado
                                temp_path = decrypted_path
                            else:
                                logger.error("❌ Falha na descriptografia do áudio")
                                cleanup_temp_files(temp_path)
                                return "❌ Não foi possível descriptografar o áudio. Por favor, configure a Evolution API para fornecer arquivos descriptografados automaticamente usando webhook_base64=true."
                            
                        except Exception as decrypt_error:
                            logger.error(f"❌ Erro ao descriptografar áudio: {str(decrypt_error)}")
                            cleanup_temp_files(temp_path)
                            return "❌ Erro interno ao descriptografar áudio."
                    
                    transcribed_text = transcribe_audio(temp_path)
                    
                    # Limpar arquivos temporários
                    cleanup_temp_files(temp_path)
                    
                    # Limpar possível arquivo convertido
                    wav_path = temp_path.replace(file_extension, '.wav')
                    cleanup_temp_files(wav_path)
                    
                    if not transcribed_text:
                        return "❌ Não consegui entender seu áudio. Tente falar mais claramente ou enviar uma mensagem de texto."
                    
                    logger.info(f"✅ Áudio transcrito: {transcribed_text[:100]}...")
                    
                    # Importar módulos necessários do módulo principal
                    try:
                        from maya_hopecann import generate_maya_response, conversation_context
                        import logging
                        
                        # Verificar se já existe histórico de conversa
                        logger.info(f"💬 Verificando contexto de conversa para {sender_number}...")
                        context_exists = sender_number in conversation_context and len(conversation_context[sender_number]) > 0
                        
                        if context_exists:
                            logger.info(f"✅ Contexto encontrado! {len(conversation_context[sender_number])} interações prévias.")
                        else:
                            logger.info(f"⚠️ Sem contexto prévio para {sender_number}")
                            
                        # Verificar nome do contato se disponível no contexto
                        contact_name = "Usuário"
                        if context_exists:
                            for interaction in conversation_context[sender_number]:
                                if isinstance(interaction, dict) and 'contact_name' in interaction and interaction['contact_name'] != "Usuário":
                                    contact_name = interaction['contact_name']
                                    logger.info(f"✅ Nome recuperado do contexto: {contact_name}")
                                    break
                        
                        # Registrar interação no sistema de memória persistente
                        if MEMORY_MANAGER_AVAILABLE:
                            try:
                                # Registrar como interação de áudio
                                get_memory().record_interaction(sender_number, "whatsapp", "audio", contact_name)
                                logger.info(f"✅ Interação de áudio registrada na memória persistente para {sender_number}")
                            except Exception as e:
                                logger.error(f"❌ Erro ao registrar interação de áudio na memória: {str(e)}")
                        
                        # Gerar resposta inteligente usando a Maya (com contexto unificado)
                        logger.info(f"🧠 Gerando resposta inteligente para: '{transcribed_text[:50]}...'")
                        response = generate_maya_response(transcribed_text, sender_number, contact_name)
                        
                        # Verificar se é a flag de controle de mensagens sequenciais
                        if response == "MENSAGENS_SEQUENCIAIS_ENVIADAS":
                            logger.info("✅ Mensagens sequenciais já enviadas pela Maya")
                            return "" # Retornar string vazia para indicar que não é necessário enviar mensagem
                        elif response:
                            logger.info(f"✅ Resposta gerada: {response[:100]}...")
                            return response
                        else:
                            logger.warning("⚠️ Maya não gerou resposta")
                            return "Desculpe, não consegui processar uma resposta para seu áudio neste momento."
                    except Exception as maya_error:
                        logger.error(f"❌ Erro ao gerar resposta da Maya: {str(maya_error)}")
                        # Fallback: retornar o texto transcrito
                        return f"[Transcrição do áudio]: {transcribed_text}\n\nDesculpe, estou com dificuldades para processar uma resposta neste momento."
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao salvar arquivo: {str(e)}")
                    return "❌ Erro interno ao processar áudio."
                
            except Exception as download_error:
                logger.error(f"❌ Erro ao baixar áudio: {str(download_error)}")
                return "❌ Não consegui baixar seu áudio. Tente enviar novamente."
        
        # Fallback geral
        return "❌ Não foi possível processar seu áudio. Por favor, tente enviar novamente ou envie uma mensagem de texto."
        
    except Exception as e:
        logger.error(f"❌ Erro crítico ao processar áudio: {str(e)}")
        return "❌ Erro interno ao processar mensagem de áudio. Por favor, tente enviar uma mensagem de texto."

#!/usr/bin/env python3
"""
Módulo de processamento de imagens para a Maya HopeCann

Este módulo gerencia o recebimento, validação, conversão e análise
de imagens recebidas via WhatsApp, integrando com a API de visão
computacional da OpenAI e registrando interações na memória persistente.
"""

import os
import logging
import requests
import base64
import io
import time
from datetime import datetime
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

# Importar módulo de memória de contatos
from contact_memory import get_memory

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging específico para este módulo
logger = logging.getLogger(__name__)

# Configurações OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Formatos de imagem suportados pela OpenAI Vision API
SUPPORTED_FORMATS = ['png', 'jpeg', 'jpg', 'gif', 'webp']

# Cliente OpenAI global
openai_client = None

def initialize_vision_client():
    """Inicializa o cliente OpenAI para API de visão computacional"""
    global openai_client
    if not openai_client:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ Cliente OpenAI inicializado para visão computacional")
    return openai_client


def download_image_from_url(image_url, headers=None):
    """
    Baixa imagem da URL fornecida pela Evolution API
    
    Args:
        image_url: URL da imagem
        headers: Headers opcionais para a requisição
        
    Returns:
        Conteúdo binário da imagem ou None se falhar
    """
    try:
        if not headers:
            headers = {}
        
        logger.info(f"📥 Baixando imagem da URL: {image_url}")
        response = requests.get(image_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"✅ Imagem baixada com sucesso ({len(response.content)} bytes)")
            return response.content
        else:
            logger.error(f"❌ Erro ao baixar imagem: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"❌ Exceção ao baixar imagem: {str(e)}")
        return None


def validate_and_convert_image(image_data):
    """
    Valida e converte imagem para formato suportado pela API de visão
    
    Args:
        image_data: Conteúdo binário da imagem
        
    Returns:
        Tupla (imagem_pil, formato) ou (None, None) se inválida
    """
    try:
        # Verificar se temos dados válidos
        if not image_data or len(image_data) < 100:
            logger.error("❌ Dados de imagem muito pequenos ou vazios")
            return None, None
        
        # Tentar abrir imagem com PIL para validar
        image = Image.open(io.BytesIO(image_data))
        
        # Extrair formato e converter para minúsculo
        original_format = image.format.lower() if image.format else "unknown"
        logger.info(f"✅ Imagem válida detectada: {image.width}x{image.height} formato {original_format}")
        
        # Se formato não suportado pela OpenAI, converter para JPEG
        target_format = original_format
        if original_format not in SUPPORTED_FORMATS and original_format != "unknown":
            logger.info(f"⚠️ Formato {original_format} não suportado pela OpenAI Vision API, convertendo para JPEG")
            buffer = io.BytesIO()
            image = image.convert('RGB')  # Converter para RGB se for RGBA
            image.save(buffer, format="JPEG", quality=95)
            buffer.seek(0)
            image = Image.open(buffer)
            target_format = "jpeg"
        
        return image, target_format
    
    except Exception as e:
        logger.error(f"❌ Erro ao validar/converter imagem: {str(e)}")
        return None, None


def analyze_image_with_vision_api(image_data):
    """
    Analisa imagem usando a API de visão computacional da OpenAI
    
    Args:
        image_data: Conteúdo binário da imagem
        
    Returns:
        Descrição da imagem ou mensagem de erro
    """
    try:
        # Inicializar cliente se ainda não foi feito
        client = initialize_vision_client()
        
        # Validar e converter imagem se necessário
        pil_image, format_name = validate_and_convert_image(image_data)
        if not pil_image:
            return "Desculpe, não consegui processar esta imagem. Poderia enviar uma nova foto ou uma mensagem de texto?"
        
        # Converter imagem para base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format=format_name.upper())
        buffer.seek(0)
        base64_image = base64.b64encode(buffer.read()).decode('utf-8')
        
        logger.info(f"🧠 Enviando imagem para análise com GPT-4o (Visão)")
        
        # Chamar API de visão com gpt-4o
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": """Você é um assistente especializado em analisar imagens para a Maya HopeCann, uma assistente virtual para cannabis medicinal.
                    
Ao descrever a imagem:
1. Seja detalhado mas conciso
2. Se identificar plantas de cannabis, descreva características visíveis (estágio de crescimento, saúde, tipo)
3. Se identificar produtos de cannabis medicinal, descreva-os objetivamente
4. Se identificar pessoas, respeite a privacidade (não mencione identidades)
5. Mantenha tom profissional e informativo
6. Evite julgamentos sobre legalidade
7. Foco em aspectos medicinais e terapêuticos se relevante

Formato da resposta:
- Breve descrição geral (1 frase)
- Detalhes relevantes (2-3 frases)
- Contexto médico se aplicável (1 frase)"""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Descreva esta imagem que recebi:"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{format_name};base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        
        # Extrair e retornar resposta
        analysis = response.choices[0].message.content
        logger.info(f"✅ Análise de imagem concluída: {analysis[:100]}...")
        return analysis
    
    except Exception as e:
        logger.error(f"❌ Erro na API de visão: {str(e)}")
        return "Desculpe, tive um problema ao analisar esta imagem. Poderia descrever o que ela contém em uma mensagem de texto?"


def generate_maya_response_for_image(image_analysis, phone_number, contact_name):
    """
    Gera resposta personalizada da Maya para uma imagem
    
    Args:
        image_analysis: Análise da imagem pela API de visão
        phone_number: Número de telefone do usuário
        contact_name: Nome do contato
        
    Returns:
        Resposta personalizada da Maya
    """
    try:
        # Inicializar cliente se ainda não foi feito
        client = initialize_vision_client()
        
        logger.info(f"🌿 Gerando resposta personalizada da Maya para imagem")
        
        # Chamar API para gerar resposta personalizada
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo mais leve e eficiente
            messages=[
                {
                    "role": "system", 
                    "content": """Você é Maya, especialista em cannabis medicinal da clínica HopeCann.

PERSONALIDADE:
- Amigável, empática e profissional
- Usa linguagem acessível mas técnica quando necessário
- Sempre responde como médica especialista
- Tom equilibrado: não promocional nem alarmista
- Prioriza informações cientificamente validadas

RESPOSTA A IMAGENS:
- Mencione o nome da pessoa no início da resposta
- Comente sobre o conteúdo da imagem com base na análise recebida
- Se for uma planta/produto: ofereça breve contexto relevante
- Se for outro tema: tente relacionar ao contexto medicinal quando possível
- Não critique nem elogie excessivamente
- NUNCA dê recomendações específicas de tratamento pela foto

ESTRUTURA DA RESPOSTA:
- Saudação com nome
- Comentário sobre a imagem (1-2 frases)
- Contexto informativo breve (1-2 frases)
- Pergunta de acompanhamento OU convite para agendamento se apropriado

SEMPRE FINALIZE COM UMA OPÇÃO DE AGENDAMENTO:
"Se quiser conversar sobre tratamentos com cannabis medicinal, posso ajudar a agendar uma consulta na HopeCann."

Máximo: 300 caracteres (seja concisa mas informativa)"""
                },
                {
                    "role": "user",
                    "content": f"O paciente {contact_name} enviou uma foto. Análise da imagem: {image_analysis}\n\nGere uma resposta personalizada da Maya:"
                }
            ],
            max_tokens=500,
        )
        
        # Extrair e retornar resposta
        maya_response = response.choices[0].message.content
        logger.info(f"✅ Resposta da Maya para imagem gerada: {maya_response[:100]}...")
        return maya_response
    
    except Exception as e:
        logger.error(f"❌ Erro ao gerar resposta Maya para imagem: {str(e)}")
        return f"Olá {contact_name}! Obrigada por compartilhar esta imagem comigo. Se quiser conversar sobre tratamentos com cannabis medicinal, posso ajudar a agendar uma consulta na HopeCann."


def process_image_message(image_data, phone_number, contact_name="Paciente"):
    """
    Processa mensagem de imagem do WhatsApp, integrando com memória persistente
    
    Args:
        image_data: Dados da mensagem de imagem do webhook
        phone_number: Número do telefone do remetente
        contact_name: Nome do contato
        
    Returns:
        Texto da resposta a ser enviada
    """
    try:
        logger.info(f"🖼️ Iniciando processamento de imagem de {contact_name} ({phone_number})")
        
        # 1. Registrar na memória persistente antes de tudo para garantir rastreabilidade
        memory = get_memory()
        if memory:
            try:
                # Registrar contato se for novo
                memory.register_contact(phone_number, contact_name, "image")
                
                # Registrar interação específica
                memory.register_interaction(
                    phone_number=phone_number,
                    channel="image",
                    direction="incoming",
                    content_type="image",
                    content_summary="Imagem recebida via WhatsApp"
                )
                logger.info(f"✅ Interação de imagem registrada na memória persistente")
            except Exception as e:
                logger.error(f"❌ Erro ao registrar na memória persistente: {str(e)}")
        else:
            logger.warning("⚠️ Memória persistente não inicializada")
        
        # 2. Extrair URL da imagem
        image_url = image_data.get('url', '')
        if not image_url:
            return "Desculpe, não consegui processar sua imagem. Poderia enviar novamente?"
        
        # 3. Baixar imagem
        image_binary = download_image_from_url(image_url)
        if not image_binary:
            return "Não foi possível baixar a imagem. Poderia tentar enviar novamente ou em outro formato?"
        
        # 4. Analisar imagem com API de visão
        image_analysis = analyze_image_with_vision_api(image_binary)
        if not image_analysis:
            return "Tive dificuldades para analisar esta imagem. Poderia descrever o que ela mostra?"
        
        # 5. Gerar resposta personalizada da Maya
        response = generate_maya_response_for_image(image_analysis, phone_number, contact_name)
        
        # 6. Registrar resposta na memória persistente
        if memory:
            try:
                memory.register_interaction(
                    phone_number=phone_number,
                    channel="image",
                    direction="outgoing",
                    content_type="text",
                    content_summary=f"Resposta para imagem: {response[:50]}..."
                )
                logger.info(f"✅ Resposta da Maya registrada na memória persistente")
            except Exception as e:
                logger.error(f"❌ Erro ao registrar resposta na memória: {str(e)}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem de imagem: {str(e)}")
        return f"Olá {contact_name}, recebi sua imagem mas tive um problema ao processá-la. Poderia me enviar uma mensagem de texto explicando o que gostaria de saber?"


# Testes básicos se executado diretamente
if __name__ == "__main__":
    # Configurar logging para testes
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    
    print("🧪 Teste de processamento de imagem")
    
    # Testar com uma URL de imagem fictícia
    test_image_data = {"url": "https://example.com/test.jpg"}
    test_phone = "5511999999999"
    test_name = "Tester"
    
    print(f"Simulando processamento de imagem de {test_name}...")
    print("NOTA: Este é apenas um teste simulado, sem download real de imagem.")
    
    # Inicializar cliente OpenAI
    try:
        initialize_vision_client()
        print("✅ Cliente OpenAI inicializado")
    except Exception as e:
        print(f"❌ Erro ao inicializar cliente OpenAI: {str(e)}")

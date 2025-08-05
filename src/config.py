"""
Configuração principal da Maya
Centraliza todas as configurações e variáveis de ambiente
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class Config:
    """Configurações da aplicação Maya"""
    
    # Configurações gerais
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'maya-secret-key-2024')
    
    # Servidor
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    
    # AssemblyAI
    ASSEMBLY_AI_API_KEY = os.getenv('ASSEMBLY_AI_API_KEY')
    
    # Evolution API
    EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8090')
    EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')
    EVOLUTION_INSTANCE_NAME = os.getenv('EVOLUTION_INSTANCE_NAME', 'maya-bot')
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Google APIs
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    GOOGLE_TOKEN_PATH = os.getenv('GOOGLE_TOKEN_PATH', 'token.json')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/maya.log')
    
    # Diretórios
    TEMP_DIR = os.getenv('TEMP_DIR', 'temp')
    UPLOADS_DIR = os.getenv('UPLOADS_DIR', 'uploads')
    
    @classmethod
    def validate(cls):
        """Valida se todas as configurações obrigatórias estão presentes"""
        required_vars = [
            'OPENAI_API_KEY',
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'EVOLUTION_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_vars)}")
        
        return True

#!/usr/bin/env python3
"""
Script para configurar autenticação Google OAuth2 para Maya HopeCann
Execute este script após baixar o credentials.json do Google Cloud Console
"""

import os
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# Configurações
GOOGLE_CREDENTIALS_FILE = 'credentials.json'
GOOGLE_TOKEN_FILE = 'token.json'

def setup_google_auth():
    """
    Configura autenticação Google OAuth2 para Google Meet/Calendar
    """
    print("🔐 Configurando autenticação Google para Maya HopeCann...")
    print("=" * 60)
    
    # Verificar se credentials.json existe
    if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        print("❌ Arquivo credentials.json não encontrado!")
        print("\n📋 INSTRUÇÕES PARA OBTER CREDENTIALS.JSON:")
        print("1. Acesse: https://console.cloud.google.com/")
        print("2. Crie um projeto ou selecione um existente")
        print("3. Vá para 'APIs e Serviços' > 'Biblioteca'")
        print("4. Ative a 'Google Calendar API'")
        print("5. Vá para 'APIs e Serviços' > 'Credenciais'")
        print("6. Clique em 'Criar Credenciais' > 'ID do cliente OAuth 2.0'")
        print("7. Escolha 'Aplicativo para computador'")
        print("8. Baixe o arquivo JSON e renomeie para 'credentials.json'")
        print("9. Coloque o arquivo na pasta do projeto Maya")
        print("10. Execute este script novamente")
        return False
    
    print("\n⚠️ IMPORTANTE - Para evitar erro 403 'access_denied':")
    print("1. Acesse: https://console.cloud.google.com/")
    print("2. Vá em 'APIs & Services' > 'OAuth consent screen'")
    print("3. OPÇÃO A: Adicione seu email em 'Test users'")
    print("4. OPÇÃO B: Clique em 'PUBLISH APP' (Recomendado)")
    print("5. Confirme que quer tornar a aplicação pública")
    print("\n🔄 Pressione ENTER para continuar após fazer isso...")
    input()
    
    # Definir escopos necessários
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    try:
        print("🚀 Iniciando fluxo de autenticação OAuth2...")
        
        # Criar fluxo OAuth com servidor local (substituição do OOB descontinuado)
        flow = Flow.from_client_secrets_file(
            GOOGLE_CREDENTIALS_FILE,
            SCOPES
        )
        
        # Configurar redirect URI para servidor local (não mais OOB)
        flow.redirect_uri = 'http://localhost:8080'
        
        # Gerar URL de autorização
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        print(f"\n🌐 Acesse este URL no seu navegador:")
        print(f"{auth_url}")
        print("\n📝 Após autorizar, o Google vai redirecionar para localhost.")
        print("🔗 Copie a URL completa da página de erro (que contém o código) e cole aqui:")
        print("Exemplo: http://localhost:8080/?code=4/0AX4XfWh...&scope=...")
        
        # Solicitar URL completa
        callback_url = input("\nURL completa do callback: ").strip()
        
        if not callback_url or 'code=' not in callback_url:
            print("❌ URL de callback inválida ou não contém código!")
            return False
        
        print("🔄 Processando código de autorização...")
        
        # Extrair código da URL
        import urllib.parse as urlparse
        from urllib.parse import parse_qs
        
        parsed_url = urlparse.urlparse(callback_url)
        code = parse_qs(parsed_url.query).get('code')
        
        if not code:
            print("❌ Não foi possível extrair o código da URL!")
            return False
        
        auth_code = code[0]
        
        # Trocar código por token
        flow.fetch_token(code=auth_code)
        
        # Salvar credenciais
        creds = flow.credentials
        with open(GOOGLE_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        print("✅ Autenticação Google configurada com sucesso!")
        print(f"💾 Token salvo em: {GOOGLE_TOKEN_FILE}")
        print("\n🎉 Maya HopeCann agora pode criar reuniões reais no Google Meet!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na configuração: {str(e)}")
        return False

def test_google_auth():
    """
    Testa se a autenticação Google está funcionando
    """
    try:
        if not os.path.exists(GOOGLE_TOKEN_FILE):
            print("❌ Token não encontrado. Execute a configuração primeiro.")
            return False
        
        print("🧪 Testando autenticação Google...")
        
        # Carregar credenciais
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE)
        
        # Verificar se precisa renovar
        if creds.expired and creds.refresh_token:
            print("🔄 Renovando token...")
            creds.refresh(Request())
            
            # Salvar token renovado
            with open(GOOGLE_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        if creds.valid:
            print("✅ Autenticação Google funcionando corretamente!")
            return True
        else:
            print("❌ Credenciais inválidas. Reconfigure a autenticação.")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return False

if __name__ == '__main__':
    print("🌿 Maya HopeCann - Configuração Google OAuth2")
    print("=" * 50)
    
    while True:
        print("\nEscolha uma opção:")
        print("1. Configurar autenticação Google")
        print("2. Testar autenticação existente")
        print("3. Sair")
        
        choice = input("\nOpção (1-3): ").strip()
        
        if choice == '1':
            setup_google_auth()
        elif choice == '2':
            test_google_auth()
        elif choice == '3':
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida!")

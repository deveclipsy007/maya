#!/usr/bin/env python3
"""
Script para criar a estrutura modular do Agente Agno
"""
import os

def create_directory_structure():
    """Cria a estrutura de diretórios do projeto"""
    
    # Estrutura principal
    directories = [
        # Core do Agno
        "agents/agno_core/agno_core",
        "agents/agno_core/tests",
        
        # Agente WhatsApp
        "agents/agent_whatsapp/agent_whatsapp", 
        "agents/agent_whatsapp/tests",
        
        # Agente de Imagem
        "agents/agent_image/agent_image",
        "agents/agent_image/tests",
        
        # Agente de Enquete
        "agents/agent_poll/agent_poll",
        "agents/agent_poll/tests",
        
        # Servidor Webhook
        "webhook_server",
        "webhook_server/schemas",
        "webhook_server/adapters",
        
        # Cliente Evolution API
        "evolution_client",
        
        # Configurações e utilitários
        "config",
        "tests",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Criado: {directory}")
        
        # Criar __init__.py para pacotes Python
        if not directory.endswith(('tests', 'logs', 'config')):
            init_file = os.path.join(directory, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('"""Módulo do Agente Agno"""\n')

if __name__ == "__main__":
    create_directory_structure()
    print("\n🎉 Estrutura de diretórios criada com sucesso!")

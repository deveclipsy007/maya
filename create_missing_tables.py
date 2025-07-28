#!/usr/bin/env python3
"""
Script para criar as tabelas que estão faltando no Supabase
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def main():
    print("🌿 Maya HopeCann - Criação de Tabelas Faltantes")
    print("=" * 60)
    
    # Configurar cliente Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Erro: Variáveis SUPABASE_URL e SUPABASE_KEY não encontradas no .env")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Cliente Supabase criado com sucesso")
    
    # SQL para criar tabela pacientes
    create_pacientes_sql = """
    CREATE TABLE IF NOT EXISTS pacientes (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(255) NOT NULL,
        telefone VARCHAR(20) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        senha_temporaria VARCHAR(50),
        status VARCHAR(20) DEFAULT 'ativo',
        tipo VARCHAR(20) DEFAULT 'paciente',
        primeiro_acesso BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # SQL para criar tabela agendamentos
    create_agendamentos_sql = """
    CREATE TABLE IF NOT EXISTS agendamentos (
        id SERIAL PRIMARY KEY,
        nome_paciente VARCHAR(255) NOT NULL,
        telefone_paciente VARCHAR(20) NOT NULL,
        email_paciente VARCHAR(255) NOT NULL,
        data_hora TIMESTAMP WITH TIME ZONE NOT NULL,
        medico_id INTEGER REFERENCES medicos(id),
        status VARCHAR(20) DEFAULT 'confirmado',
        meet_link TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    try:
        print("\n📋 Criando tabela 'pacientes'...")
        # Usar RPC para executar SQL diretamente
        result = supabase.rpc('exec_sql', {'sql': create_pacientes_sql}).execute()
        print("✅ Tabela 'pacientes' criada com sucesso!")
        
        print("\n📅 Criando tabela 'agendamentos'...")
        result = supabase.rpc('exec_sql', {'sql': create_agendamentos_sql}).execute()
        print("✅ Tabela 'agendamentos' criada com sucesso!")
        
        print("\n🎉 Todas as tabelas foram criadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {str(e)}")
        print("\n💡 Alternativa: Criar as tabelas manualmente no painel do Supabase")
        print("📋 SQL para tabela pacientes:")
        print(create_pacientes_sql)
        print("\n📅 SQL para tabela agendamentos:")
        print(create_agendamentos_sql)

if __name__ == "__main__":
    main()

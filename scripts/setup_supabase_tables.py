#!/usr/bin/env python3
"""
Script para criar tabelas no Supabase usando supabase-py
Maya HopeCann - Setup do banco de dados
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Biblioteca supabase não encontrada. Instale com: pip install supabase")
    exit(1)

# Carregar variáveis de ambiente
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def criar_cliente_supabase():
    """
    Cria cliente Supabase
    """
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        print(f"❌ Erro ao criar cliente Supabase: {str(e)}")
        return None

def criar_tabelas():
    """
    Cria as tabelas necessárias para a Maya
    """
    print("🏗️ Criando tabelas do Supabase para Maya HopeCann...")
    
    # SQL para criar tabelas
    sql_medicos = """
    CREATE TABLE IF NOT EXISTS medicos (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        nome VARCHAR(255) NOT NULL,
        especialidade VARCHAR(255) DEFAULT 'Cannabis Medicinal',
        crm VARCHAR(50) NOT NULL,
        email VARCHAR(255),
        telefone VARCHAR(20),
        ativo BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    sql_horarios = """
    CREATE TABLE IF NOT EXISTS horarios_disponiveis (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        medico_id UUID REFERENCES medicos(id),
        medico_nome VARCHAR(255),
        data_hora TIMESTAMP WITH TIME ZONE NOT NULL,
        disponivel BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    sql_agendamentos = """
    CREATE TABLE IF NOT EXISTS agendamentos (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        paciente_nome VARCHAR(255) NOT NULL,
        paciente_telefone VARCHAR(20) NOT NULL,
        paciente_email VARCHAR(255),
        medico_id UUID REFERENCES medicos(id),
        data_hora TIMESTAMP WITH TIME ZONE NOT NULL,
        meet_link VARCHAR(500),
        status VARCHAR(50) DEFAULT 'agendado',
        observacoes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Executar criação das tabelas
    print("📋 Criando tabela 'medicos'...")
    if not executar_sql(sql_medicos):
        return False
        
    print("📅 Criando tabela 'horarios_disponiveis'...")
    if not executar_sql(sql_horarios):
        return False
        
    print("🗓️ Criando tabela 'agendamentos'...")
    if not executar_sql(sql_agendamentos):
        return False
    
    return True

def inserir_dados_exemplo():
    """
    Insere dados de exemplo nas tabelas
    """
    print("📝 Inserindo dados de exemplo...")
    
    # Inserir médicos
    sql_insert_medicos = """
    INSERT INTO medicos (nome, especialidade, crm, email, telefone) VALUES
    ('Dr. Carlos Silva', 'Cannabis Medicinal', 'CRM-SP 123456', 'carlos@hopecann.com', '(11) 99999-0001'),
    ('Dra. Ana Santos', 'Cannabis Medicinal', 'CRM-RJ 789012', 'ana@hopecann.com', '(21) 99999-0002'),
    ('Dr. João Oliveira', 'Cannabis Medicinal', 'CRM-MG 345678', 'joao@hopecann.com', '(31) 99999-0003')
    ON CONFLICT (crm) DO NOTHING;
    """
    
    print("👨‍⚕️ Inserindo médicos de exemplo...")
    if not executar_sql(sql_insert_medicos):
        return False
    
    # Inserir horários (próximos 7 dias)
    base_date = datetime.now() + timedelta(days=1)
    horarios = []
    
    for dia in range(7):
        data_atual = base_date + timedelta(days=dia)
        for hora in ['09:00', '10:30', '14:00', '15:30', '16:00']:
            hora_int, min_int = map(int, hora.split(':'))
            data_hora = data_atual.replace(hour=hora_int, minute=min_int, second=0, microsecond=0)
            
            # Alternar entre médicos
            medico_idx = (dia * 5 + len(horarios)) % 3 + 1
            medico_nome = ['Dr. Carlos Silva', 'Dra. Ana Santos', 'Dr. João Oliveira'][medico_idx - 1]
            
            horarios.append(f"((SELECT id FROM medicos WHERE nome = '{medico_nome}'), '{medico_nome}', '{data_hora.isoformat()}')")
    
    sql_insert_horarios = f"""
    INSERT INTO horarios_disponiveis (medico_id, medico_nome, data_hora) VALUES
    {', '.join(horarios)}
    ON CONFLICT DO NOTHING;
    """
    
    print("⏰ Inserindo horários de exemplo...")
    if not executar_sql(sql_insert_horarios):
        return False
    
    return True

def verificar_conexao():
    """
    Verifica se a conexão com o Supabase está funcionando
    """
    print("🔍 Verificando conexão com Supabase...")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Variáveis SUPABASE_URL ou SUPABASE_KEY não encontradas no .env")
        return False
    
    # Testar conexão básica
    url = f"{SUPABASE_URL}/rest/v1/"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("✅ Conexão com Supabase OK")
            return True
        else:
            print(f"❌ Erro na conexão: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
        return False

def main():
    """
    Função principal
    """
    print("🌿 Maya HopeCann - Setup do Supabase")
    print("=" * 50)
    
    # Verificar conexão
    if not verificar_conexao():
        print("❌ Falha na verificação da conexão. Verifique suas credenciais.")
        return
    
    # Criar tabelas
    if not criar_tabelas():
        print("❌ Falha ao criar tabelas.")
        return
    
    # Inserir dados de exemplo
    if not inserir_dados_exemplo():
        print("❌ Falha ao inserir dados de exemplo.")
        return
    
    print("\n🎉 Setup do Supabase concluído com sucesso!")
    print("✅ Tabelas criadas: medicos, horarios_disponiveis, agendamentos")
    print("✅ Dados de exemplo inseridos")
    print("\n🚀 Agora você pode reiniciar a Maya e testar o agendamento!")

if __name__ == "__main__":
    main()

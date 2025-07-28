#!/usr/bin/env python3
"""
Script para inspecionar o esquema real das tabelas no Supabase
Maya HopeCann - Inspeção de esquema
"""

import os
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

def main():
    """
    Função principal para inspecionar esquema do Supabase
    """
    print("🌿 Maya HopeCann - Inspeção de Esquema Supabase")
    print("=" * 60)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Variáveis SUPABASE_URL ou SUPABASE_KEY não encontradas no .env")
        return
    
    try:
        # Criar cliente Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Cliente Supabase criado com sucesso")
        
        # Inspecionar tabela médicos
        print("\n👨‍⚕️ TABELA: medicos")
        print("-" * 30)
        try:
            result = supabase.table('medicos').select('*').limit(1).execute()
            if result.data:
                medico_exemplo = result.data[0]
                print("📋 Colunas encontradas:")
                for coluna, valor in medico_exemplo.items():
                    print(f"  - {coluna}: {type(valor).__name__} = {valor}")
            else:
                print("⚠️ Tabela vazia - não é possível inspecionar colunas")
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
        
        # Inspecionar tabela horários
        print("\n📅 TABELA: horarios_disponiveis")
        print("-" * 30)
        try:
            result = supabase.table('horarios_disponiveis').select('*').limit(1).execute()
            if result.data:
                horario_exemplo = result.data[0]
                print("📋 Colunas encontradas:")
                for coluna, valor in horario_exemplo.items():
                    print(f"  - {coluna}: {type(valor).__name__} = {valor}")
            else:
                print("⚠️ Tabela vazia - não é possível inspecionar colunas")
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
        
        # Inspecionar tabela agendamentos
        print("\n🗓️ TABELA: agendamentos")
        print("-" * 30)
        try:
            result = supabase.table('agendamentos').select('*').limit(1).execute()
            if result.data:
                agendamento_exemplo = result.data[0]
                print("📋 Colunas encontradas:")
                for coluna, valor in agendamento_exemplo.items():
                    print(f"  - {coluna}: {type(valor).__name__} = {valor}")
            else:
                print("⚠️ Tabela vazia - não é possível inspecionar colunas")
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
        
        print("\n" + "=" * 60)
        print("📊 RESUMO:")
        print("✅ Use essas informações para corrigir o código da Maya")
        print("💡 As colunas devem coincidir exatamente com o que está no banco")
        
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")

if __name__ == "__main__":
    main()

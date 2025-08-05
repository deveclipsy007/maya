#!/usr/bin/env python3
"""
Módulo de memória persistente para a Maya HopeCann

Este módulo gerencia o registro de contatos que já interagiram com a Maya,
permitindo identificar primeiras interações para envio de mensagem de apresentação.
"""

import os
import sqlite3
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configurar logging específico para este módulo
logger = logging.getLogger(__name__)

# Nome do arquivo do banco de dados SQLite
DEFAULT_DB_PATH = "maya_contacts.db"


class ContactMemory:
    """
    Gerencia a memória persistente de contatos da Maya
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        Inicializa a memória de contatos
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db_path = db_path
        self._initialize_db()
        logger.info(f"💾 Memória de contatos inicializada: {db_path}")

    def _initialize_db(self) -> None:
        """Inicializa o banco de dados e cria tabelas se necessário"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Criar tabela de contatos se não existir
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    phone_number TEXT PRIMARY KEY,
                    name TEXT,
                    first_interaction TIMESTAMP,
                    last_interaction TIMESTAMP,
                    interaction_count INTEGER DEFAULT 1,
                    channel TEXT
                )
            ''')
            
            # Criar tabela de histórico de interações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interaction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT,
                    timestamp TIMESTAMP,
                    channel TEXT,
                    direction TEXT,
                    content_type TEXT,
                    content_summary TEXT,
                    FOREIGN KEY (phone_number) REFERENCES contacts (phone_number)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Banco de dados de contatos inicializado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco de dados: {str(e)}")

    def is_first_interaction(self, phone_number: str) -> bool:
        """
        Verifica se é a primeira interação de um número com a Maya
        
        Args:
            phone_number: Número de telefone do contato
            
        Returns:
            True se for a primeira interação, False caso contrário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) FROM contacts WHERE phone_number = ?",
                (phone_number,)
            )
            count = cursor.fetchone()[0]
            
            conn.close()
            return count == 0
        except Exception as e:
            logger.error(f"❌ Erro ao verificar primeira interação: {str(e)}")
            # Em caso de erro, assumimos que é primeira interação
            # para garantir que a apresentação aconteça
            return True

    def register_contact(self, phone_number: str, name: str, channel: str = "text") -> bool:
        """
        Registra um novo contato ou atualiza um existente
        
        Args:
            phone_number: Número de telefone do contato
            name: Nome do contato
            channel: Canal da interação (text, audio, image)
            
        Returns:
            True se o registro foi bem-sucedido, False caso contrário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se o contato já existe
            cursor.execute(
                "SELECT interaction_count FROM contacts WHERE phone_number = ?",
                (phone_number,)
            )
            result = cursor.fetchone()
            
            now = datetime.now().isoformat()
            
            if result:
                # Contato já existe, atualizar
                interaction_count = result[0] + 1
                cursor.execute(
                    """
                    UPDATE contacts 
                    SET name = ?, 
                        last_interaction = ?, 
                        interaction_count = ?,
                        channel = ?
                    WHERE phone_number = ?
                    """,
                    (name, now, interaction_count, channel, phone_number)
                )
                logger.info(f"📝 Contato atualizado: {name} ({phone_number}) - {interaction_count} interações")
            else:
                # Novo contato
                cursor.execute(
                    """
                    INSERT INTO contacts 
                    (phone_number, name, first_interaction, last_interaction, channel) 
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (phone_number, name, now, now, channel)
                )
                logger.info(f"➕ Novo contato registrado: {name} ({phone_number})")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao registrar contato: {str(e)}")
            return False

    def register_interaction(self, 
                            phone_number: str, 
                            channel: str, 
                            direction: str, 
                            content_type: str, 
                            content_summary: str) -> bool:
        """
        Registra uma interação no histórico
        
        Args:
            phone_number: Número de telefone do contato
            channel: Canal da interação (text, audio, image)
            direction: Direção da mensagem (incoming, outgoing)
            content_type: Tipo do conteúdo (text, audio, image)
            content_summary: Resumo do conteúdo (primeiros caracteres)
            
        Returns:
            True se o registro foi bem-sucedido, False caso contrário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            # Registrar na tabela de histórico
            cursor.execute(
                """
                INSERT INTO interaction_history 
                (phone_number, timestamp, channel, direction, content_type, content_summary) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (phone_number, now, channel, direction, content_type, content_summary[:100] if content_summary else "")
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao registrar interação: {str(e)}")
            return False

    def get_contact_info(self, phone_number: str) -> Dict[str, Any]:
        """
        Obtém informações sobre um contato
        
        Args:
            phone_number: Número de telefone do contato
            
        Returns:
            Dicionário com informações do contato ou vazio se não encontrado
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Para retornar resultados como dicionários
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT phone_number, name, first_interaction, last_interaction, 
                       interaction_count, channel
                FROM contacts
                WHERE phone_number = ?
                """,
                (phone_number,)
            )
            
            row = cursor.fetchone()
            result = dict(row) if row else {}
            
            conn.close()
            return result
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações do contato: {str(e)}")
            return {}

    def get_interaction_history(self, phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtém histórico de interações de um contato
        
        Args:
            phone_number: Número de telefone do contato
            limit: Limite de registros para retornar
            
        Returns:
            Lista de dicionários com as interações
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT id, timestamp, channel, direction, content_type, content_summary
                FROM interaction_history
                WHERE phone_number = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (phone_number, limit)
            )
            
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            
            conn.close()
            return result
        except Exception as e:
            logger.error(f"❌ Erro ao obter histórico de interações: {str(e)}")
            return []

    def get_all_contacts(self) -> List[Dict[str, Any]]:
        """
        Obtém lista de todos os contatos registrados
        
        Returns:
            Lista de dicionários com informações dos contatos
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT phone_number, name, first_interaction, last_interaction, 
                       interaction_count, channel
                FROM contacts
                ORDER BY last_interaction DESC
                """
            )
            
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            
            conn.close()
            return result
        except Exception as e:
            logger.error(f"❌ Erro ao obter lista de contatos: {str(e)}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas gerais sobre contatos e interações
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total de contatos
            cursor.execute("SELECT COUNT(*) FROM contacts")
            total_contacts = cursor.fetchone()[0]
            
            # Total de interações
            cursor.execute("SELECT COUNT(*) FROM interaction_history")
            total_interactions = cursor.fetchone()[0]
            
            # Contatos por canal (último canal usado)
            cursor.execute(
                """
                SELECT channel, COUNT(*) as count
                FROM contacts
                GROUP BY channel
                """
            )
            channels = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Interações por direção
            cursor.execute(
                """
                SELECT direction, COUNT(*) as count
                FROM interaction_history
                GROUP BY direction
                """
            )
            directions = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                "total_contacts": total_contacts,
                "total_interactions": total_interactions,
                "channels": channels,
                "directions": directions,
                "db_path": self.db_path
            }
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {str(e)}")
            return {
                "error": str(e),
                "db_path": self.db_path
            }

# Instância global para uso em toda a aplicação
contact_memory = None

def initialize_memory(db_path: str = DEFAULT_DB_PATH) -> ContactMemory:
    """
    Inicializa a memória de contatos global
    
    Args:
        db_path: Caminho para o banco de dados
        
    Returns:
        Instância de ContactMemory
    """
    global contact_memory
    contact_memory = ContactMemory(db_path)
    return contact_memory

def get_memory() -> Optional[ContactMemory]:
    """
    Obtém a instância global da memória de contatos
    
    Returns:
        Instância de ContactMemory ou None se não inicializada
    """
    return contact_memory


# Testes básicos se executado diretamente
if __name__ == "__main__":
    # Configurar logging para testes
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )
    
    # Usar banco em memória para testes
    test_db = ":memory:"
    memory = ContactMemory(test_db)
    
    # Testar registro de contato
    memory.register_contact("5511999999999", "Teste Um", "text")
    memory.register_contact("5511888888888", "Teste Dois", "audio")
    
    # Testar verificação de primeira interação
    assert memory.is_first_interaction("5511777777777") == True
    assert memory.is_first_interaction("5511999999999") == False
    
    # Testar registro de interações
    memory.register_interaction("5511999999999", "text", "incoming", "text", "Olá, como vai?")
    memory.register_interaction("5511999999999", "text", "outgoing", "text", "Estou bem, obrigado!")
    
    # Testar obtenção de informações
    contact_info = memory.get_contact_info("5511999999999")
    assert contact_info["name"] == "Teste Um"
    assert contact_info["interaction_count"] == 1
    
    # Testar histórico
    history = memory.get_interaction_history("5511999999999")
    assert len(history) == 2
    
    # Testar atualização
    memory.register_contact("5511999999999", "Teste Um Atualizado", "text")
    contact_info = memory.get_contact_info("5511999999999")
    assert contact_info["name"] == "Teste Um Atualizado"
    assert contact_info["interaction_count"] == 2
    
    # Testar estatísticas
    stats = memory.get_stats()
    assert stats["total_contacts"] == 2
    assert stats["total_interactions"] == 2
    
    print("✅ Todos os testes passaram!")

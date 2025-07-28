"""
Módulo de memória persistente para Maya HopeCann
- Rastreia interações de usuários por número de telefone
- Garante apresentação única da Maya por usuário
- Funciona em todos os canais (texto/áudio)
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('memory_manager')

class MemoryManager:
    """
    Gerenciador de memória persistente para Maya HopeCann
    Armazena histórico de interações por número de telefone
    """
    def __init__(self, storage_path: str = "memory"):
        self.storage_path = storage_path
        self.memory_file = os.path.join(storage_path, "maya_user_memory.json")
        self.user_memory: Dict[str, Any] = {}
        self._initialize()
        
    def _initialize(self):
        """Inicializa o sistema de memória"""
        try:
            # Criar diretório se não existir
            os.makedirs(self.storage_path, exist_ok=True)
            
            # Carregar memória do arquivo se existir
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.user_memory = json.load(f)
                    logger.info(f"✅ Memória carregada: {len(self.user_memory)} contatos")
            else:
                # Criar arquivo de memória inicial
                self.user_memory = {}
                self._save_memory()
                logger.info("🆕 Arquivo de memória inicializado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar memória: {str(e)}")
            # Garantir que temos pelo menos um dicionário vazio
            self.user_memory = {}
    
    def _save_memory(self):
        """Salva memória no arquivo"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_memory, f, ensure_ascii=False, indent=2)
                logger.info("💾 Memória salva com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar memória: {str(e)}")
    
    def is_first_interaction(self, phone_number: str) -> bool:
        """
        Verifica se é a primeira interação do usuário
        Retorna True se for primeira interação, False caso contrário
        """
        return phone_number not in self.user_memory
    
    def record_interaction(self, phone_number: str, channel: str = "whatsapp", 
                          message_type: str = "text", contact_name: Optional[str] = None) -> None:
        """
        Registra uma interação com o usuário
        
        Args:
            phone_number: Número do telefone do usuário
            channel: Canal de comunicação (whatsapp, audio, etc)
            message_type: Tipo de mensagem (text, audio, image)
            contact_name: Nome do contato, se disponível
        """
        timestamp = datetime.now().isoformat()
        
        # Se for primeira interação deste número
        if phone_number not in self.user_memory:
            self.user_memory[phone_number] = {
                "first_interaction": timestamp,
                "channels": [channel],
                "contact_name": contact_name,
                "interactions": 1,
                "history": [{
                    "timestamp": timestamp,
                    "channel": channel,
                    "message_type": message_type
                }]
            }
            logger.info(f"🆕 Primeiro contato registrado para {phone_number}")
        else:
            # Atualizar informações de contato existente
            user_data = self.user_memory[phone_number]
            
            # Atualizar canais usados pelo usuário
            if channel not in user_data["channels"]:
                user_data["channels"].append(channel)
            
            # Atualizar nome do contato se for fornecido
            if contact_name and contact_name != "Usuário" and user_data.get("contact_name") in [None, "Usuário"]:
                user_data["contact_name"] = contact_name
            
            # Incrementar contador de interações
            user_data["interactions"] = user_data.get("interactions", 0) + 1
            
            # Adicionar ao histórico (limitado a 50 últimas entradas)
            history = user_data.get("history", [])
            history.append({
                "timestamp": timestamp,
                "channel": channel,
                "message_type": message_type
            })
            
            # Manter apenas últimas 50 interações no histórico
            if len(history) > 50:
                history = history[-50:]
                
            user_data["history"] = history
            user_data["last_interaction"] = timestamp
            
            # Atualizar memória
            self.user_memory[phone_number] = user_data
            logger.info(f"🔄 Contato atualizado para {phone_number} (interação #{user_data['interactions']})")
        
        # Salvar alterações
        self._save_memory()
    
    def get_user_data(self, phone_number: str) -> Dict[str, Any]:
        """
        Obtém dados do usuário por número de telefone
        
        Args:
            phone_number: Número do telefone do usuário
            
        Returns:
            Dicionário com dados do usuário ou vazio se não existir
        """
        return self.user_memory.get(phone_number, {})
    
    def get_all_users(self) -> Dict[str, Any]:
        """Retorna todos os usuários na memória"""
        return self.user_memory
    
    def get_total_users(self) -> int:
        """Retorna total de usuários únicos"""
        return len(self.user_memory)

# Singleton para memória persistente
_memory_instance = None

def get_memory() -> MemoryManager:
    """
    Retorna instância única do gerenciador de memória (Singleton)
    """
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = MemoryManager()
    return _memory_instance

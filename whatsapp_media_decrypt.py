import os
import hmac
import hashlib
import logging
from Crypto.Cipher import AES
import base64
from io import BytesIO

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tipos de mídia para descriptografia
MEDIA_TYPE_IMAGE = 1
MEDIA_TYPE_VIDEO = 2
MEDIA_TYPE_AUDIO = 3
MEDIA_TYPE_DOCUMENT = 4

# Informações para expansão HKDF
APP_INFO = {
    MEDIA_TYPE_IMAGE: b"WhatsApp Image Keys",
    MEDIA_TYPE_VIDEO: b"WhatsApp Video Keys",
    MEDIA_TYPE_AUDIO: b"WhatsApp Audio Keys",
    MEDIA_TYPE_DOCUMENT: b"WhatsApp Document Keys"
}

def hkdf_expand(key, length, app_info):
    """
    Implementa HKDF (RFC 5869) para expandir a chave de mídia
    Simplificação exata baseada na implementação de referência
    """
    if not isinstance(app_info, bytes):
        app_info = app_info.encode('utf-8')
        
    # Primeiro passo: HMAC com salt zero (simplificado da referência)
    key = hmac.new(b"\0"*32, key, hashlib.sha256).digest()
    
    # Expansão simples exatamente como no código de referência
    key_stream = b""
    key_block = b""
    block_index = 1
    
    while len(key_stream) < length:
        key_block = hmac.new(
            key,
            msg=key_block + app_info + bytes([block_index]),
            digestmod=hashlib.sha256
        ).digest()
        block_index += 1
        key_stream += key_block
    
    return key_stream[:length]

def validate_media(iv, file_data, mac_key, mac_value):
    """
    Valida a autenticidade do arquivo de mídia
    Equivalente à função validateMedia do repositório Go
    
    Versão depurável com mais logging para diagnóstico
    """
    try:
        # Calcular HMAC
        h = hmac.new(mac_key, iv + file_data, hashlib.sha256)
        calculated_mac = h.digest()[:10]
        
        # Debug: mostra os bytes para comparação
        logger.info(f"🔍 MAC calculado: {calculated_mac.hex()}")
        logger.info(f"🔍 MAC esperado: {mac_value.hex()}")
        
        # Comparar MACs byte a byte para diagnóstico
        match = True
        for i, (calc, expected) in enumerate(zip(calculated_mac, mac_value)):
            if calc != expected:
                logger.error(f"❌ MAC difere no byte {i}: {calc} != {expected}")
                match = False
        
        # Comparação final
        if not match:
            logger.error("❌ Validação HMAC falhou: arquivo corrompido ou chave incorreta")
            return False
        
        logger.info("✅ Validação HMAC bem-sucedida!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro durante validação HMAC: {str(e)}")
        return False

def aes_unpad(s):
    """
    Remove o padding AES (PKCS#7)
    """
    return s[:-ord(s[len(s)-1:])]    

def decrypt_media(enc_file_data, media_key, media_type):
    """
    Descriptografa dados de mídia do WhatsApp
    Implementação exata baseada no código de referência
    """
    try:
        logger.info(f"🔑 Descriptografando mídia do tipo {media_type}...")
        logger.info(f"📊 Tamanho do arquivo criptografado: {len(enc_file_data)} bytes")
        
        # Verificar tamanho da chave
        logger.info(f"📊 Tamanho da mediaKey: {len(media_key)} bytes")
        if len(media_key) != 32:
            logger.error(f"❌ Tamanho da chave de mídia inválido: {len(media_key)} (esperado: 32 bytes)")
            return None
            
        # Expandir chave usando HKDF (exatamente como na referência)
        if media_type not in APP_INFO:
            logger.error(f"❌ Tipo de mídia desconhecido: {media_type}")
            return None
            
        logger.info(f"🔄 Expandindo chave com HKDF usando app_info: {APP_INFO[media_type]}")
        media_key_expanded = hkdf_expand(media_key, 112, APP_INFO[media_type])
        logger.info(f"📊 Tamanho da chave expandida: {len(media_key_expanded)} bytes")
        
        # Extrair partes da chave exatamente como na referência
        iv = media_key_expanded[:16]           # Primeiros 16 bytes = IV
        cipher_key = media_key_expanded[16:48] # Bytes 16-48 = Chave de cifra
        mac_key = media_key_expanded[48:80]    # Bytes 48-80 = Chave MAC
        
        # Extrair arquivo e MAC (10 últimos bytes)
        file_data = enc_file_data[:-10]  # Dados sem o MAC
        mac_value = enc_file_data[-10:]  # Últimos 10 bytes são o MAC
        
        # Validar MAC (exatamente como na referência)
        # Calcular MAC: HMAC-SHA256(macKey, IV + fileData)[:10]
        h = hmac.new(mac_key, iv + file_data, hashlib.sha256)
        calculated_mac = h.digest()[:10]
        
        # Comparar MACs
        if calculated_mac != mac_value:
            logger.error(f"❌ Validação HMAC falhou")
            logger.error(f"❌ MAC calculado: {calculated_mac.hex()}")
            logger.error(f"❌ MAC esperado: {mac_value.hex()}")
            return None
        
        # Descriptografar com AES (exatamente como na referência)
        try:
            cipher = AES.new(cipher_key, AES.MODE_CBC, iv)
            decrypted_data = cipher.decrypt(file_data)
            
            # Remover padding PKCS#7
            decrypted_data = aes_unpad(decrypted_data)
            
            logger.info(f"✅ Descriptografia AES bem-sucedida: {len(decrypted_data)} bytes descriptografados")
            return decrypted_data
            
        except Exception as aes_error:
            logger.error(f"❌ Erro na descriptografia AES: {str(aes_error)}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erro ao descriptografar mídia: {str(e)}")
        return None

def decrypt_media_file(enc_file_path, hex_media_key, media_type):
    """
    Descriptografa arquivo de mídia do WhatsApp
    Equivalente à função decryptMediaFile do repositório Go
    
    Args:
        enc_file_path: Caminho para o arquivo criptografado (.enc)
        hex_media_key: Chave de mídia em formato hexadecimal (String)
        media_type: Tipo de mídia (1=imagem, 2=vídeo, 3=áudio, 4=documento)
        
    Returns:
        Bytes descriptografados ou None em caso de erro
    """
    try:
        logger.info(f"📂 Descriptografando arquivo: {enc_file_path}")
        
        # Ler arquivo criptografado
        with open(enc_file_path, 'rb') as f:
            enc_file_data = f.read()
        
        # Decodificar chave hex
        try:
            media_key = bytes.fromhex(hex_media_key)
        except ValueError:
            logger.error("❌ Chave de mídia inválida (formato hexadecimal inválido)")
            return None
        
        # Descriptografar
        return decrypt_media(enc_file_data, media_key, media_type)
        
    except FileNotFoundError:
        logger.error(f"❌ Arquivo não encontrado: {enc_file_path}")
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao processar arquivo: {str(e)}")
        return None

def decrypt_media_with_base64_key(enc_file_path, base64_media_key, media_type, output_file_path=None):
    """
    Descriptografa arquivo de mídia do WhatsApp usando chave em formato base64
    
    Args:
        enc_file_path: Caminho para o arquivo criptografado (.enc)
        base64_media_key: Chave de mídia em formato base64 (direto do webhook)
        media_type: Tipo de mídia (1=imagem, 2=vídeo, 3=áudio, 4=documento)
        output_file_path: Caminho para salvar o arquivo descriptografado (opcional)
        
    Returns:
        Caminho do arquivo descriptografado ou None em caso de erro
    """
    try:
        # Ler arquivo criptografado
        with open(enc_file_path, 'rb') as f:
            enc_file_data = f.read()
        
        # Decodificar chave base64
        try:
            import base64
            media_key = base64.b64decode(base64_media_key)
            logger.info(f"✅ Chave decodificada: {len(media_key)} bytes")
        except Exception as e:
            logger.error(f"❌ Erro ao decodificar chave base64: {str(e)}")
            return None
        
        # Descriptografar
        decrypted_data = decrypt_media(enc_file_data, media_key, media_type)
        if not decrypted_data:
            return None
            
        # Determinar caminho de saída se não especificado
        if not output_file_path:
            # Remover extensão .enc se presente
            base_path = enc_file_path.replace('.enc', '')
            
            # Adicionar extensão apropriada com base no tipo de mídia
            if media_type == MEDIA_TYPE_IMAGE:
                output_file_path = f"{base_path}.jpg"
            elif media_type == MEDIA_TYPE_VIDEO:
                output_file_path = f"{base_path}.mp4"
            elif media_type == MEDIA_TYPE_AUDIO:
                output_file_path = f"{base_path}.ogg"
            elif media_type == MEDIA_TYPE_DOCUMENT:
                output_file_path = f"{base_path}.bin"
            else:
                output_file_path = f"{base_path}.bin"
        
        # Salvar arquivo descriptografado
        with open(output_file_path, 'wb') as f:
            f.write(decrypted_data)
            
        logger.info(f"💾 Arquivo descriptografado salvo: {output_file_path}")
        return output_file_path
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar arquivo descriptografado: {str(e)}")
        return None

def decrypt_media_and_save(enc_file_path, hex_media_key, media_type, output_file_path=None):
    """
    Descriptografa arquivo de mídia do WhatsApp e salva em disco
    
    Args:
        enc_file_path: Caminho para o arquivo criptografado (.enc)
        hex_media_key: Chave de mídia em formato hexadecimal
        media_type: Tipo de mídia (1=imagem, 2=vídeo, 3=áudio, 4=documento)
        output_file_path: Caminho para salvar o arquivo descriptografado (opcional)
        
    Returns:
        Caminho do arquivo descriptografado ou None em caso de erro
    """
    try:
        # Descriptografar
        decrypted_data = decrypt_media_file(enc_file_path, hex_media_key, media_type)
        if not decrypted_data:
            return None
            
        # Determinar caminho de saída se não especificado
        if not output_file_path:
            # Remover extensão .enc se presente
            base_path = enc_file_path.replace('.enc', '')
            
            # Adicionar extensão apropriada com base no tipo de mídia
            if media_type == MEDIA_TYPE_IMAGE:
                output_file_path = f"{base_path}.jpg"
            elif media_type == MEDIA_TYPE_VIDEO:
                output_file_path = f"{base_path}.mp4"
            elif media_type == MEDIA_TYPE_AUDIO:
                output_file_path = f"{base_path}.ogg"
            elif media_type == MEDIA_TYPE_DOCUMENT:
                output_file_path = f"{base_path}.bin"
            else:
                output_file_path = f"{base_path}.bin"
        
        # Salvar arquivo descriptografado
        with open(output_file_path, 'wb') as f:
            f.write(decrypted_data)
            
        logger.info(f"💾 Arquivo descriptografado salvo: {output_file_path}")
        return output_file_path
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar arquivo descriptografado: {str(e)}")
        return None

def decrypt_from_base64(base64_media_key, base64_media_data, media_type):
    """
    Descriptografa mídia a partir de dados e chave em base64
    Útil para APIs que fornecem base64 diretamente
    
    Args:
        base64_media_key: Chave de mídia em formato base64
        base64_media_data: Dados da mídia criptografada em base64
        media_type: Tipo de mídia
        
    Returns:
        Bytes descriptografados ou None em caso de erro
    """
    try:
        # Decodificar base64
        media_key = base64.b64decode(base64_media_key)
        media_data = base64.b64decode(base64_media_data)
        
        # Descriptografar
        return decrypt_media(media_data, media_key, media_type)
    except Exception as e:
        logger.error(f"❌ Erro ao descriptografar mídia em base64: {str(e)}")
        return None

def is_encrypted_file(file_path):
    """
    Verifica se um arquivo é provavelmente criptografado (.enc)
    baseado na extensão e conteúdo
    
    Returns:
        True se for arquivo criptografado, False caso contrário
    """
    try:
        # Verificar extensão
        is_enc_extension = file_path.lower().endswith('.enc')
        
        # Verificar conteúdo (arquivos OGG começam com "OggS")
        with open(file_path, 'rb') as f:
            header = f.read(4)
            
        # Se tem extensão .enc ou não tem header OGG/RIFF válido
        if is_enc_extension or (not header.startswith(b'OggS') and not header.startswith(b'RIFF')):
            return True
            
        return False
    except Exception:
        # Em caso de erro, assumir que não é criptografado
        return False

# Exemplo de uso:
if __name__ == "__main__":
    # Exemplo de teste
    import sys
    
    if len(sys.argv) < 4:
        print("Uso: python whatsapp_media_decrypt.py arquivo.enc CHAVE_MEDIA_HEX TIPO_MEDIA")
        print("TIPO_MEDIA: 1=imagem, 2=vídeo, 3=áudio, 4=documento")
        sys.exit(1)
        
    enc_file = sys.argv[1]
    hex_key = sys.argv[2]
    media_type = int(sys.argv[3])
    
    output_path = decrypt_media_and_save(enc_file, hex_key, media_type)
    if output_path:
        print(f"Arquivo descriptografado: {output_path}")
    else:
        print("Falha na descriptografia")
        sys.exit(1)

import pickle
import json
from Crypto.PublicKey import RSA
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
import os
import base64
from logger_config import (
    log_key_generated, log_public_key_saved, log_private_key_stored,
    log_session_key_encrypted, log_session_key_decrypted,
    log_message_encrypted, log_message_decrypted, log_error, log_debug
)


RSA_KEY_SIZE = 2048


def generate_keypair():
    private_key = RSA.generate(RSA_KEY_SIZE)
    public_key = private_key.publickey()
    log_key_generated("RSA 2048-bit", "Memória", "utils.py", "generate_keypair")
    return private_key.export_key(), public_key.export_key()


def encrypt_with_public_key(data, public_key_pem):
    """
    Criptografa dados usando uma chave pública RSA.
    """
    public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
    encrypted_data = public_key.encrypt(
        data,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    log_debug("Dados criptografados com RSA - chave pública utilizada", "utils.py", "encrypt_with_public_key")
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_with_private_key(encrypted_data, private_key_pem, password=None):
    """
    Descriptografa dados usando uma chave privada RSA.
    """
    # Valida e decodifica os dados criptografados
    try:
        encrypted_data_bytes = base64.b64decode(encrypted_data)
    except Exception as e:
        log_error("Falha ao decodificar encrypted_data - não é um Base64 válido", "utils.py", "decrypt_with_private_key", str(e))
        raise ValueError("Falha ao decodificar encrypted_data: não é um Base64 válido.") from e

    # Valida a chave privada PEM
    if isinstance(private_key_pem, str):
        private_key_pem = private_key_pem.encode('utf-8')
    if not private_key_pem.startswith(b"-----BEGIN RSA PRIVATE KEY-----"):
        log_error("Chave privada inválida ou não está no formato PEM", "utils.py", "decrypt_with_private_key")
        raise ValueError("Chave privada inválida ou não está no formato PEM.")

    # Carrega a chave privada e descriptografa os dados
    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=password.encode('utf-8') if password else None
        )
        
        # Descriptografa os dados
        decrypted_data = private_key.decrypt(
            encrypted_data_bytes,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        log_debug("Dados descriptografados com RSA - chave privada utilizada", "utils.py", "decrypt_with_private_key")
        return decrypted_data
        
    except ValueError as e:
        log_error("Erro na descriptografia ou ao carregar chave privada", "utils.py", "decrypt_with_private_key", str(e))
        raise ValueError("Falha na descriptografia: verifique os dados criptografados e a chave privada.") from e


def encrypt_chacha20_message(key, message):
    nonce = os.urandom(16)
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(message.encode()) + encryptor.finalize()
    log_debug("Mensagem criptografada com ChaCha20", "utils.py", "encrypt_chacha20_message")
    return base64.b64encode(nonce + ciphertext).decode('utf-8')


def decrypt_chacha20_message(key, encrypted_message):
    decoded_data = base64.b64decode(encrypted_message.encode('utf-8'))
    nonce, ciphertext = decoded_data[:16], decoded_data[16:]
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    decryptor = cipher.decryptor()
    log_debug("Mensagem descriptografada com ChaCha20", "utils.py", "decrypt_chacha20_message")
    return (decryptor.update(ciphertext) + decryptor.finalize()).decode('utf-8')


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())


def encrypt_private_key(private_key: bytes, password: str) -> dict:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    nonce = os.urandom(12)

    aesgcm = AESGCM(key)
    encrypted_private_key = aesgcm.encrypt(nonce, private_key, None)

    return {
        'salt': salt,
        'nonce': nonce,
        'encrypted_key': encrypted_private_key
    }


def decrypt_private_key(encrypted_data: dict, password: str) -> bytes:
    salt = encrypted_data['salt']
    nonce = encrypted_data['nonce']
    encrypted_key = encrypted_data['encrypted_key']

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, encrypted_key, None)


def save_private_key(encrypted_data, username):
    filename = f"{username}_key.bin"
    file_path = f"users_key/{filename}"
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, "wb") as f:
            pickle.dump(encrypted_data, f)

        log_private_key_stored(username, f"Arquivo: {file_path}", "utils.py", "save_private_key")
        return True

    except (OSError, pickle.PickleError) as e:
        log_error(f"Erro ao salvar a chave privada criptografada", "utils.py", "save_private_key", str(e))
        return False


def recover_private_key(username):
    try:
        filename = f"{username}_key.bin"
        file_path = f"users_key/{filename}"
        with open(file_path, "rb") as f:
            loaded_encrypted_data = pickle.load(f)
        log_debug(f"Chave privada recuperada do arquivo: {file_path}", "utils.py", "recover_private_key")
        return loaded_encrypted_data

    except (OSError, pickle.PickleError) as e:
        log_error(f"Erro ao abrir a chave privada criptografada", "utils.py", "recover_private_key", str(e))
        return False


# ============ FUNÇÕES DESCONTINUADAS (SIMPLIFICAÇÃO) ============
# As funções abaixo foram descontinuadas para simplificar o sistema
# Session keys são agora transferidas apenas com RSA, sem camada adicional

def encrypt_session_key(session_key: bytes, room: str) -> dict:
    """DESCONTINUADA: Não mais usada após simplificação"""
    salt = os.urandom(16)
    key = derive_key(room, salt)
    nonce = os.urandom(12)

    aesgcm = AESGCM(key)
    encrypted_private_key = aesgcm.encrypt(nonce, session_key, None)

    return {
        'salt': salt,
        'nonce': nonce,
        'encrypted_key': encrypted_private_key
    }


def decrypt_session_key(encrypted_data: dict, room: str) -> bytes:
    """DESCONTINUADA: Não mais usada após simplificação"""
    salt = encrypted_data['salt']
    nonce = encrypted_data['nonce']
    encrypted_key = encrypted_data['encrypted_key']

    key = derive_key(room, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, encrypted_key, None)


def save_session_key(encrypted_data, room):
    """DESCONTINUADA: Não mais usada após simplificação"""
    filename = f"{room}_session_key.bin"
    file_path = f"session_keys/{filename}"
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, "wb") as f:
            pickle.dump(encrypted_data, f)

        print("DEBUG: A session key foi armazenada do lado do cliente.")
        return True

    except (OSError, pickle.PickleError) as e:
        print(f"Erro ao salvar a session key criptografada: {e}")
        return False


def recover_session_key(room):
    """DESCONTINUADA: Não mais usada após simplificação"""
    try:
        filename = f"{room}_session_key.bin"
        file_path = f"session_keys/{filename}"
        with open(file_path, "rb") as f:
            loaded_encrypted_data = pickle.load(f)
        return loaded_encrypted_data

    except (OSError, pickle.PickleError) as e:
        print(f"Erro ao abrir a session key criptografada: {e}")
        return False
    

def sign_message(data, private_key_pem):
    """
    INTEGRIDADE: Assina dados com chave privada RSA
    
    Garante que a mensagem não foi alterada em trânsito.
    Apenas o remetente (com sua chave privada) consegue assinar.
    
    Args:
        data: dict ou string a assinar
        private_key_pem: chave privada em formato PEM
    
    Returns:
        assinatura em base64
    """
    # Normaliza dados
    if isinstance(data, dict):
        data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
    elif isinstance(data, str):
        data_bytes = data.encode('utf-8')
    else:
        data_bytes = data
    
    # Carrega chave privada
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode('utf-8') if isinstance(private_key_pem, str) else private_key_pem,
        password=None
    )
    
    # Assina usando PKCS1v15 + SHA256
    signature = private_key.sign(
        data_bytes,
        asym_padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    log_debug("Mensagem assinada com RSA - integridade garantida", "utils.py", "sign_message")
    return base64.b64encode(signature).decode('utf-8')


def verify_signature(data, signature_b64, public_key_pem):
    """
    INTEGRIDADE: Verifica assinatura com chave pública RSA
    
    Valida se a mensagem foi alterada usando a chave pública do remetente.
    
    Args:
        data: dict ou string que foi assinado
        signature_b64: assinatura em base64
        public_key_pem: chave pública em formato PEM
    
    Returns:
        True se assinatura é válida, False caso contrário
    """
    try:
        # Normaliza dados
        if isinstance(data, dict):
            data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
        
        # Carrega chave pública
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8') if isinstance(public_key_pem, str) else public_key_pem
        )
        
        # Decodifica assinatura
        signature = base64.b64decode(signature_b64)
        
        # Valida assinatura
        public_key.verify(
            signature,
            data_bytes,
            asym_padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        log_debug("Assinatura verificada com sucesso - integridade confirmada", "utils.py", "verify_signature")
        return True
        
    except Exception as e:
        log_error(f"Falha ao verificar assinatura: {str(e)}", "utils.py", "verify_signature", str(e))
        return False

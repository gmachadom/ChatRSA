"""
Módulo de configuração de logs centralizado para ChatRSA
Fornece logs expressivos e facilmente identificáveis no terminal
"""
import logging
import sys
from datetime import datetime

# Cores ANSI para terminal
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Cores
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Fundos
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'


class CustomFormatter(logging.Formatter):
    """Formatter customizado com cores e formatação expressiva"""
    
    FORMATS = {
        logging.DEBUG: f"{Colors.CYAN}[DEBUG]{Colors.RESET} {{message}}",
        logging.INFO: f"{Colors.GREEN}[INFO]{Colors.RESET} {{message}}",
        logging.WARNING: f"{Colors.YELLOW}[WARNING]{Colors.RESET} {{message}}",
        logging.ERROR: f"{Colors.RED}[ERROR]{Colors.RESET} {{message}}",
        logging.CRITICAL: f"{Colors.BG_RED}{Colors.WHITE}[CRÍTICO]{Colors.RESET} {{message}}",
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt, style='{')
        return formatter.format(record)


def setup_logger(name, level=logging.INFO):
    """
    Configura e retorna um logger personalizado
    
    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        level: Nível de logging (padrão: INFO)
    
    Returns:
        logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove handlers existentes para evitar duplicação
    logger.handlers.clear()
    
    # Handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(CustomFormatter())
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


# Logger global para o sistema
system_logger = setup_logger('ChatRSA', logging.INFO)


# Funções de log expressivas para operações específicas
def log_key_generated(key_type, location, arquivo, funcao):
    """Log de geração de par de chaves"""
    msg = f"🔑 PAR DE CHAVES GERADO | Tipo: {key_type} | Armazenado em: {location} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.GREEN}{Colors.BOLD}{msg}{Colors.RESET}")


def log_public_key_saved(username, arquivo, funcao):
    """Log de salvamento de chave pública no servidor"""
    msg = f"🔐 CHAVE PÚBLICA SALVA NO SERVIDOR | Usuário: {username} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.GREEN}{Colors.BOLD}{msg}{Colors.RESET}")


def log_private_key_stored(username, location, arquivo, funcao):
    """Log de armazenamento de chave privada"""
    msg = f"🔒 CHAVE PRIVADA ARMAZENADA LOCALMENTE | Usuário: {username} | Local: {location} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.GREEN}{Colors.BOLD}{msg}{Colors.RESET}")


def log_session_key_generated(room_id, arquivo, funcao):
    """Log de geração de session_key"""
    msg = f"🗝️  SESSION_KEY GERADA | Room: {room_id} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.BLUE}{Colors.BOLD}{msg}{Colors.RESET}")


def log_session_key_encrypted(recipient_username, room_id, arquivo, funcao):
    """Log de encriptação de session_key com RSA"""
    msg = f"🔐 SESSION_KEY ENCRIPTADA COM RSA | Destinatário: {recipient_username} | Room: {room_id} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.BLUE}{Colors.BOLD}{msg}{Colors.RESET}")


def log_session_key_decrypted(username, room_id, arquivo, funcao):
    """Log de desencriptação de session_key com RSA"""
    msg = f"🔓 SESSION_KEY DESENCRIPTADA COM RSA | Usuário: {username} | Room: {room_id} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.BLUE}{Colors.BOLD}{msg}{Colors.RESET}")


def log_message_encrypted(sender, recipient, room_id, arquivo, funcao):
    """Log de encriptação de mensagem com ChaCha20"""
    msg = f"✉️  MENSAGEM ENCRIPTADA COM CHACHA20 | De: {sender} → Para: {recipient} | Room: {room_id} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.MAGENTA}{msg}{Colors.RESET}")


def log_message_decrypted(recipient, sender, room_id, arquivo, funcao):
    """Log de desencriptação de mensagem com ChaCha20"""
    msg = f"📬 MENSAGEM DESENCRIPTADA COM CHACHA20 | Destinatário: {recipient} | De: {sender} | Room: {room_id} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.MAGENTA}{msg}{Colors.RESET}")


def log_session_invalidated(room_id, username, arquivo, funcao):
    """Log de inativação de session"""
    msg = f"❌ SESSION INATIVADA | Room: {room_id} | Usuário que saiu: {username} | [{arquivo}::{funcao}()]"
    system_logger.warning(f"{Colors.YELLOW}{Colors.BOLD}{msg}{Colors.RESET}")


def log_friend_request_sent(from_user, to_user, arquivo, funcao):
    """Log de envio de friend request"""
    msg = f"👥 FRIEND REQUEST ENVIADO | De: {from_user} → Para: {to_user} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.CYAN}{msg}{Colors.RESET}")


def log_friend_request_accepted(from_user, to_user, arquivo, funcao):
    """Log de aceitação de friend request"""
    msg = f"✅ FRIEND REQUEST ACEITO | {from_user} ← → {to_user} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.GREEN}{Colors.BOLD}{msg}{Colors.RESET}")


def log_friend_request_rejected(from_user, to_user, arquivo, funcao):
    """Log de rejeição de friend request"""
    msg = f"❌ FRIEND REQUEST REJEITADO | De: {from_user} → Para: {to_user} | [{arquivo}::{funcao}()]"
    system_logger.warning(f"{Colors.YELLOW}{msg}{Colors.RESET}")


def log_chat_invitation_sent(inviter, invitee, room_id, arquivo, funcao):
    """Log de envio de chat invitation"""
    msg = f"💬 CHAT INVITATION ENVIADO | Convite de: {inviter} → Para: {invitee} | Room: {room_id} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.CYAN}{msg}{Colors.RESET}")


def log_chat_invitation_accepted(invitee, inviter, room_id, arquivo, funcao):
    """Log de aceitação de chat invitation"""
    msg = f"✅ CHAT INVITATION ACEITO | {invitee} entrou no chat com {inviter} | Room: {room_id} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.GREEN}{Colors.BOLD}{msg}{Colors.RESET}")


def log_chat_invitation_declined(invitee, inviter, room_id, arquivo, funcao):
    """Log de recusa de chat invitation"""
    msg = f"❌ CHAT INVITATION RECUSADO | {invitee} recusou convite de {inviter} | Room: {room_id} | [{arquivo}::{funcao}()]"
    system_logger.warning(f"{Colors.YELLOW}{msg}{Colors.RESET}")


def log_user_login(username, arquivo, funcao):
    """Log de login de usuário"""
    msg = f"🚪 USUÁRIO AUTENTICADO | Usuário: {username} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.GREEN}{Colors.BOLD}{msg}{Colors.RESET}")


def log_user_registered(username, arquivo, funcao):
    """Log de registro de novo usuário"""
    msg = f"📝 NOVO USUÁRIO REGISTRADO | Usuário: {username} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.GREEN}{Colors.BOLD}{msg}{Colors.RESET}")


def log_user_joined_session(username, room_id, arquivo, funcao):
    """Log de entrada de usuário em sessão de chat"""
    msg = f"👋 USUÁRIO ENTROU NA SESSÃO | Usuário: {username} | Room: {room_id} | [{arquivo}::{funcao}()]"
    system_logger.info(f"{Colors.CYAN}{msg}{Colors.RESET}")


def log_user_left_session(username, room_id, arquivo, funcao):
    """Log de saída de usuário da sessão de chat"""
    msg = f"🚪 USUÁRIO SAIU DA SESSÃO | Usuário: {username} | Room: {room_id} | [{arquivo}::{funcao}()]"
    system_logger.warning(f"{Colors.YELLOW}{msg}{Colors.RESET}")


def log_error(erro, arquivo, funcao, detalhes=""):
    """Log de erro com detalhes"""
    msg = f"💥 ERRO | {erro} | [{arquivo}::{funcao}()] {detalhes}"
    system_logger.error(f"{Colors.RED}{Colors.BOLD}{msg}{Colors.RESET}")


def log_debug(mensagem, arquivo, funcao):
    """Log de debug detalhado"""
    msg = f"🔍 DEBUG | {mensagem} | [{arquivo}::{funcao}()]"
    system_logger.debug(f"{Colors.CYAN}{msg}{Colors.RESET}")

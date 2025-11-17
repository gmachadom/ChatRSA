#!/usr/bin/env python3
"""
Script de demonstração do sistema de logging do ChatRSA v2.0

Este script testa todas as funções de logging do sistema
e exibe exemplos de como os logs aparecem no terminal.
"""

import sys
import os

# Adiciona o diretório raiz ao path
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from logger_config import (
    log_key_generated,
    log_public_key_saved,
    log_private_key_stored,
    log_session_key_generated,
    log_session_key_encrypted,
    log_session_key_decrypted,
    log_message_encrypted,
    log_message_decrypted,
    log_session_invalidated,
    log_friend_request_sent,
    log_friend_request_accepted,
    log_friend_request_rejected,
    log_chat_invitation_sent,
    log_chat_invitation_accepted,
    log_chat_invitation_declined,
    log_user_login,
    log_user_registered,
    log_user_joined_session,
    log_user_left_session,
    log_error,
    log_debug
)

print("\n" + "="*80)
print("🧪 DEMONSTRAÇÃO DO SISTEMA DE LOGGING - ChatRSA v2.0")
print("="*80 + "\n")

# ======================== LOGS DE AUTENTICAÇÃO ========================
print("\n📍 SEÇÃO 1: LOGS DE AUTENTICAÇÃO")
print("-" * 80)

log_user_registered("alice", "registrationScreen.py", "submit_form")
log_user_login("alice", "loginScreen.py", "submit_form")

# ======================== LOGS DE CHAVES ========================
print("\n📍 SEÇÃO 2: LOGS DE CHAVES CRIPTOGRÁFICAS")
print("-" * 80)

log_key_generated("RSA 2048-bit", "Memória", "utils.py", "generate_keypair")
log_public_key_saved("alice", "server.py", "register")
log_private_key_stored("alice", "users_key/alice_key.bin", "utils.py", "save_private_key")

# ======================== LOGS DE SESSION KEY ========================
print("\n📍 SEÇÃO 3: LOGS DE SESSION KEY")
print("-" * 80)

log_session_key_generated("alice_bob_chat_room", "client.py", "generate_session_key")
log_session_key_encrypted("bob", "alice_bob_chat_room", "client.py", "generate_session_key")
log_session_key_decrypted("bob", "alice_bob_chat_room", "client.py", "on_receive_session_key")

# ======================== LOGS DE MENSAGENS ========================
print("\n📍 SEÇÃO 4: LOGS DE MENSAGENS")
print("-" * 80)

log_message_encrypted("alice", "bob", "alice_bob_chat_room", "client.py", "send_message")
log_message_decrypted("bob", "alice", "alice_bob_chat_room", "client.py", "on_receive_message")

# ======================== LOGS DE FRIEND REQUESTS ========================
print("\n📍 SEÇÃO 5: LOGS DE FRIEND REQUESTS")
print("-" * 80)

log_friend_request_sent("alice", "bob", "client.py", "send_friend_request")
log_friend_request_accepted("alice", "bob", "server.py", "accept_friend_request")
log_friend_request_rejected("carol", "dave", "server.py", "reject_friend_request")

# ======================== LOGS DE CHAT INVITATIONS ========================
print("\n📍 SEÇÃO 6: LOGS DE CHAT INVITATIONS")
print("-" * 80)

log_chat_invitation_sent("alice", "bob", "alice_bob_chat_room", "client.py", "send_chat_invitation")
log_chat_invitation_accepted("bob", "alice", "alice_bob_chat_room", "server.py", "accept_chat_invitation")
log_chat_invitation_declined("carol", "dave", "carol_dave_chat_room", "server.py", "decline_chat_invitation")

# ======================== LOGS DE SESSÃO ========================
print("\n📍 SEÇÃO 7: LOGS DE SESSÃO")
print("-" * 80)

log_user_joined_session("alice", "alice_bob_chat_room", "server.py", "on_join")
log_user_joined_session("bob", "alice_bob_chat_room", "server.py", "on_join")
log_user_left_session("alice", "alice_bob_chat_room", "server.py", "on_leave")
log_session_invalidated("alice_bob_chat_room", "alice", "server.py", "on_leave")

# ======================== LOGS DE DEBUG E ERRO ========================
print("\n📍 SEÇÃO 8: LOGS DE DEBUG E ERRO")
print("-" * 80)

log_debug("Sistema de logging inicializado com sucesso", "test_logs.py", "main")
log_error("Tentativa de acesso negada", "test_logs.py", "test_error", "Usuário não autenticado")

# ======================== FIM ========================
print("\n" + "="*80)
print("✅ DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO")
print("="*80 + "\n")

print("💡 DICAS:")
print("  • Todos os logs incluem informações sobre arquivo e função")
print("  • Use cores e emojis para identificar rapidamente cada tipo de evento")
print("  • Logs de erro aparecem em vermelho para destaque especial")
print("  • Logs de warning aparecem em amarelo")
print("\n")

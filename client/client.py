import pyotp
import qrcode
from flask import jsonify
from flask_socketio import leave_room
from datetime import datetime, timedelta

import logging
import os
import requests
import socketio
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..')

if root_dir not in sys.path:
    sys.path.append(root_dir)

from server.utils import *
from logger_config import (
    log_key_generated, log_private_key_stored, log_session_key_generated,
    log_session_key_encrypted, log_session_key_decrypted,
    log_message_encrypted, log_message_decrypted,
    log_friend_request_sent, log_friend_request_accepted, log_friend_request_rejected,
    log_chat_invitation_sent, log_chat_invitation_accepted, log_chat_invitation_declined,
    log_user_joined_session, log_user_left_session, log_debug, log_error
)

sio = socketio.Client()

global global_private_key
session_keys = {}
public_keys = {}
local_notifications = {}


# ---------- User/Friendlist Functions -------------
def get_all_users():
    try:
        response = requests.get('http://localhost:5000/all_users')

    except requests.exceptions.RequestException as e:
        return False, f"Connection error with server: {e}"

    if response.ok:
        all_users = response.json().get("users", [])
        return all_users
    else:
        try:
            detail = response.json().get("detail", None)
        except Exception:
            detail = None

        if response.status_code == 404:
            return ("Any user founded.")
        elif response.status_code == 401:
            return ("Not authorized.")
        else:
            return ("Error retrieving users list.")


# ---------- Friend Request Functions (NOVO) ----------

def send_friend_request(sender_username, receiver_username):
    """Envia pedido de amizade"""
    if not sender_username or not receiver_username:
        log_error("Tentativa de enviar friend request sem usernames válidos", "client.py", "send_friend_request")
        return False, "Invalid usernames"

    if sender_username == receiver_username:
        log_error("Tentativa de enviar friend request para si mesmo", "client.py", "send_friend_request",
                  sender_username)
        return False, "You can't send friend request to yourself"

    try:
        response = requests.post('http://localhost:5000/friend_request/send', json={
            'sender_username': sender_username,
            'receiver_username': receiver_username
        })
    except requests.exceptions.RequestException as e:
        log_error("Erro de conexão ao enviar friend request", "client.py", "send_friend_request", str(e))
        return False, f"Connection error: {e}"

    if response.status_code == 201:
        log_friend_request_sent(sender_username, receiver_username, "client.py", "send_friend_request")
        return True, "Friend request sent!"
    elif response.status_code == 400:
        log_debug("Friend request duplicado ou usuário já amigo", "client.py", "send_friend_request")
        return False, response.json().get('message', 'Error sending request')
    else:
        log_error("Erro ao enviar friend request", "client.py", "send_friend_request",
                  f"Status: {response.status_code}")
        return False, f"Error: {response.status_code}"


def get_pending_friend_requests(username):
    """Retorna pedidos de amizade pendentes"""
    try:
        response = requests.get(f'http://localhost:5000/friend_requests/{username}')
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {e}"

    if response.ok:
        requests_data = response.json().get('friend_requests', [])
        return True, requests_data
    else:
        return False, []


def accept_friend_request(request_id):
    """Aceita pedido de amizade"""
    try:
        response = requests.post(f'http://localhost:5000/friend_request/{request_id}/accept')
    except requests.exceptions.RequestException as e:
        log_error("Erro de conexão ao aceitar friend request", "client.py", "accept_friend_request", str(e))
        return False, f"Connection error: {e}"

    if response.ok:
        log_debug("Friend request aceito com sucesso", "client.py", "accept_friend_request")
        return True, "Friend request accepted!"
    else:
        log_error("Erro ao aceitar friend request", "client.py", "accept_friend_request",
                  f"Status: {response.status_code}")
        return False, response.json().get('message', 'Error')


def reject_friend_request(request_id):
    """Rejeita pedido de amizade"""
    try:
        response = requests.post(f'http://localhost:5000/friend_request/{request_id}/reject')
    except requests.exceptions.RequestException as e:
        log_error("Erro de conexão ao rejeitar friend request", "client.py", "reject_friend_request", str(e))
        return False, f"Connection error: {e}"

    if response.ok:
        log_debug("Friend request rejeitado com sucesso", "client.py", "reject_friend_request")
        return True, "Friend request rejected!"
    else:
        log_error("Erro ao rejeitar friend request", "client.py", "reject_friend_request",
                  f"Status: {response.status_code}")
        return False, response.json().get('message', 'Error')


# ---------- Chat Invitation Functions (NOVO) ----------

def send_chat_invitation(inviter_username, invitee_username, room_id):
    """Envia convite de chat"""
    try:
        response = requests.post('http://localhost:5000/chat_invitation/send', json={
            'inviter_username': inviter_username,
            'invitee_username': invitee_username,
            'room_id': room_id
        })
    except requests.exceptions.RequestException as e:
        log_error("Erro de conexão ao enviar chat invitation", "client.py", "send_chat_invitation", str(e))
        return False, f"Connection error: {e}"

    if response.status_code == 201:
        log_chat_invitation_sent(inviter_username, invitee_username, room_id, "client.py", "send_chat_invitation")
        return True, "Chat invitation sent!"
    elif response.status_code == 403:
        log_error("Tentativa de convite para chat sem amizade", "client.py", "send_chat_invitation",
                  f"De: {inviter_username}, Para: {invitee_username}")
        return False, "You are not friends with this user"
    else:
        log_error("Erro ao enviar chat invitation", "client.py", "send_chat_invitation",
                  f"Status: {response.status_code}")
        return False, response.json().get('message', 'Error')


def get_pending_chat_invitations(username):
    """Retorna convites de chat pendentes"""
    try:
        response = requests.get(f'http://localhost:5000/chat_invitations/{username}')
    except requests.exceptions.RequestException as e:
        log_error("Erro de conexão ao recuperar chat invitations", "client.py", "get_pending_chat_invitations", str(e))
        return False, f"Connection error: {e}"

    if response.ok:
        invitations_data = response.json().get('chat_invitations', [])
        return True, invitations_data
    else:
        log_error("Erro ao recuperar chat invitations", "client.py", "get_pending_chat_invitations",
                  f"Status: {response.status_code}")
        return False, []


def accept_chat_invitation(invitation_id):
    """Aceita convite de chat"""
    try:
        response = requests.post(f'http://localhost:5000/chat_invitation/{invitation_id}/accept')
    except requests.exceptions.RequestException as e:
        log_error("Erro de conexão ao aceitar chat invitation", "client.py", "accept_chat_invitation", str(e))
        return False, f"Connection error: {e}"

    if response.ok:
        log_debug("Chat invitation aceito com sucesso", "client.py", "accept_chat_invitation")
        return True, "Chat invitation accepted!"
    else:
        log_error("Erro ao aceitar chat invitation", "client.py", "accept_chat_invitation",
                  f"Status: {response.status_code}")
        return False, response.json().get('message', 'Error')


def decline_chat_invitation(invitation_id):
    """Declina convite de chat"""
    try:
        response = requests.post(f'http://localhost:5000/chat_invitation/{invitation_id}/decline')
    except requests.exceptions.RequestException as e:
        log_error("Erro de conexão ao recusar chat invitation", "client.py", "decline_chat_invitation", str(e))
        return False, f"Connection error: {e}"

    if response.ok:
        return True, "Chat invitation declined!"
    else:
        return False, response.json().get('message', 'Error')


def get_sent_invitations(username):
    """Retorna convites de chat enviados pelo usuário (pending ou accepted)"""
    try:
        response = requests.get(f'http://localhost:5000/user/{username}/sent_invitations')
    except requests.exceptions.RequestException as e:
        log_error("Erro de conexão ao recuperar sent invitations", "client.py", "get_sent_invitations", str(e))
        return False, []

    if response.ok:
        invitations_data = response.json().get('sent_invitations', [])
        return True, invitations_data
    else:
        log_error("Erro ao recuperar sent invitations", "client.py", "get_sent_invitations",
                  f"Status: {response.status_code}")
        return False, []


def get_active_chats(username):
    """Retorna salas de chat ativas onde o usuário é participante"""
    try:
        response = requests.get(f'http://localhost:5000/user/{username}/active_chats')
    except requests.exceptions.RequestException as e:
        log_error("Erro de conexão ao recuperar active chats", "client.py", "get_active_chats", str(e))
        return False, []

    if response.ok:
        chats_data = response.json().get('active_chats', [])
        return True, chats_data
    else:
        log_error("Erro ao recuperar active chats", "client.py", "get_active_chats", f"Status: {response.status_code}")
        return False, []


def get_friend_list(username):
    try:
        response = requests.get(f'http://localhost:5000/friendlist/{username}')

    except requests.exceptions.RequestException as e:
        return False, f"Connection error with server: {e}"

    if response.ok:
        friend_list = response.json().get("friends", [])
        return True, friend_list

    detail = None
    try:
        detail = response.json().get("detail")
    except Exception:
        pass

    if response.status_code == 404:
        return True, []
    elif response.status_code == 401:
        return False, "Not authorized."
    else:
        return False, "Error retrieving friend list."


def request_user_public_key(username_to_talk, room):
    response = requests.get(f'http://localhost:5000/public_key/{username_to_talk}')
    if response.ok:
        public_key = response.json().get("user_public_key")
        public_keys[room] = public_key
        return public_key
    else:
        print(f"Error retrieving {username_to_talk} public key.")
        return


def request_user_public_key_group(group_to_talk, room):
    """
    Busca e armazena as chaves públicas de TODOS os participantes do grupo.

    Armazena em public_keys como dicionário:
    public_keys[room] = {
        'username1': 'RSA_PUBLIC_KEY_1',
        'username2': 'RSA_PUBLIC_KEY_2',
        ...
    }
    """
    if room not in public_keys:
        public_keys[room] = {}

    for friend in group_to_talk:
        try:
            response = requests.get(f'http://localhost:5000/public_key/{friend}')
            if response.ok:
                public_key = response.json().get("user_public_key")
                # Armazena a chave do amigo mapeada por seu username
                public_keys[room][friend] = public_key
                print(f"✅ Chave pública recebida para {friend}")
            else:
                print(f"❌ Erro ao buscar chave pública de {friend}")
        except Exception as e:
            print(f"❌ Erro ao buscar chave pública de {friend}: {e}")


# ---------- Chat Functions -------------

def get_message_history(username, room):
    try:
        response = requests.get(f'http://localhost:5000/messages/{username}/{room}')

    except requests.exceptions.RequestException as e:
        return False, f"Server Connection error: {e}"

    if not response.ok:
        return False, f"Error retrieving message history for room {room} ({response.status_code})."

    message_history = response.json().get("history_messages", [])
    message_senders = response.json().get("message_senders", [])
    message_timestamps = response.json().get("message_timestamps", [])

    messages = []
    if not message_history:
        return True, []

    for message, sender_username, timestamp in zip(message_history, message_senders, message_timestamps):
        try:
            decrypted = decrypt_chacha20_message(session_keys[room], message)
        except Exception:
            decrypted = "<error decrypting message>"
        messages.append({
            "timestamp": timestamp,
            "sender": "You" if sender_username == username else sender_username,
            "text": decrypted
        })
    return True, messages


def wait_for_new_messages(username: str, room: str, old_len: int, timeout: float = 15.0, interval: float = 1.5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        ok2, hist2 = get_message_history(username, room)
        if ok2:
            new_len = len(hist2)
            if new_len > old_len:
                return True
        time.sleep(interval)
    return False


def is_master_key_expired(username):
    response = requests.get(f'http://localhost:5000/master_key_timestamp/{username}')

    timestamp = datetime.fromisoformat(response.json().get("timestamp"))

    gap_of_time = datetime.now() - timestamp
    return gap_of_time.days > 90


def connect_to_server():
    if not sio.connected:
        try:
            sio.connect("http://localhost:5000")  # ou o IP/porta do seu servidor Flask-SocketIO
            print("Conexão bem-sucedida!")
        except Exception as e:
            print("Erro ao conectar:", e)


def join(username, room, user_id):
    """Entra em uma sala de chat"""
    connect_to_server()
    sio.emit('join', {
        'room': room,
        'username': username,
        'user_id': user_id
    })


def leave_room_client(room, username, user_id):
    """Sai de uma sala de chat"""
    if not sio.connected:
        try:
            sio.connect("http://localhost:5000")
        except Exception:
            pass
    sio.emit('leave', {
        'room': room,
        'username': username,
        'user_id': user_id
    })


@sio.on('generate_session_key')
def generate_session_key(data):
    """
    🔗 HANDSHAKE EM CADEIA - Primeira pessoa gera a session key

    Suporta AMBOS:
    - Chat 1-a-1: public_keys[room] = STRING (chave pública do outro)
    - Chat grupo: public_keys[room] = DICT {'user1': key, 'user2': key, ...}
    """
    room = data['room']
    username = data.get('username')
    session_keys[room] = os.urandom(32)  # Gera chave aleatória de 32 bytes

    log_session_key_generated(room, "client.py", "generate_session_key")
    
    if room in public_keys and public_keys[room]:
        try:
            # Verifica o tipo de armazenamento
            if isinstance(public_keys[room], dict):
                # Chat de grupo: pega a primeira chave do dicionário
                first_friend_key = next(iter(public_keys[room].values()), None)
                first_friend_name = next(iter(public_keys[room].keys()), "Unknown")
            else:
                # Chat 1-a-1: public_keys[room] é uma string (a chave pública)
                first_friend_key = public_keys[room]
                first_friend_name = data.get('user_to_talk', 'Unknown')
            
            if first_friend_key:
                encrypted_session_key_with_public_key = encrypt_with_public_key(
                    session_keys[room],
                    first_friend_key
                )
                
                log_session_key_encrypted(f"{first_friend_name} (segundo participante)", room, "client.py", "generate_session_key")
                
                sio.emit('send_session_key', {
                    'encrypted_session_key': encrypted_session_key_with_public_key,
                    'room': room,
                    'username': username
                })

                log_debug(
                    f"Session key gerada e criptografada para {first_friend_name}. Aguardando...",
                    "client.py", "generate_session_key"
                )
            else:
                log_error("Nenhuma chave pública encontrada", "client.py", "generate_session_key", f"Room: {room}")
                print(f"⚠️  No public keys found for room {room}")
        except Exception as e:
            log_error(f"Erro ao criptografar session key", "client.py", "generate_session_key", str(e))
            print(f"❌ Erro ao criptografar: {e}")
    else:
        log_error("Estrutura de chaves públicas inválida ou ausente", "client.py", "generate_session_key", f"Room: {room}")
        print(f"⚠️  Public keys not properly loaded for room {room}")


@sio.on('new_participant_joined')
def on_new_participant_joined(data):
    """
    🔗 HANDSHAKE EM CADEIA - Notificação que um novo participante entrou

    ALICE recebe essa notificação quando CARLOS entra.
    ALICE então:
    1. Descriptografa a session_key com sua chave privada (ela tem!)
    2. Re-criptografa com RSA de CARLOS
    3. Envia para o servidor, que distribui para CARLOS
    """
    room = data['room']
    new_username = data['new_username']
    new_participant_key = data.get('new_public_key')

    # Verifica se THIS CLIENT foi quem gerou a chave (é o primeiro?)
    if room in session_keys:
        # ✅ Sim, este cliente tem a chave não-criptografada em memória

        log_debug(
            f"Novo participante entrou na sala {room}: {new_username}. Vou re-criptografar a chave...",
            "client.py", "on_new_participant_joined"
        )

        # Se há chave pública do novo participante, usa
        if new_participant_key:
            try:
                # Re-criptografa para o novo participante
                reencrypted_key = encrypt_with_public_key(
                    session_keys[room],
                    new_participant_key
                )

                log_debug(
                    f"Session key re-criptografada para {new_username}",
                    "client.py", "on_new_participant_joined"
                )

                # Armazena também a chave pública do novo participante localmente
                if room in public_keys and isinstance(public_keys[room], dict):
                    public_keys[room][new_username] = new_participant_key

                # Envia ao servidor, que distribui para o novo
                sio.emit('send_reencrypted_session_key', {
                    'room': room,
                    'new_username': new_username,
                    'encrypted_session_key': reencrypted_key,
                    'from_username': 'first_participant'
                })
            except Exception as e:
                log_error(
                    f"Erro ao re-criptografar para {new_username}",
                    "client.py", "on_new_participant_joined", str(e)
                )
        else:
            log_debug(
                f"⚠️  Chave pública de {new_username} não foi recebida",
                "client.py", "on_new_participant_joined"
            )


@sio.on('receive_session_key')
def on_receive_session_key(data):
    """
    Recebe session key criptografada com RSA.
    BOB (segundo participante) recebe aqui a chave criptografada por ALICE
    """
    encrypted_session_key = data['encrypted_session_key']
    room = data['room']
    username = data.get('username')

    try:
        # Tenta descriptografar com sua chave privada (RSA)
        session_keys[room] = decrypt_with_private_key(
            encrypted_session_key,
            global_private_key
        )
        log_session_key_decrypted(username or "Usuário atual", room, "client.py", "on_receive_session_key")
        print(f"✅ Session key received and decrypted for room: {room}")
    except Exception as e:
        # Se falhar, significa a chave foi criptografada com outra chave pública
        log_error(f"Não conseguiu descriptografar a session key", "client.py", "on_receive_session_key", str(e))
        print(f"⚠️  Failed to decrypt session key: {e}")
        print(f"⚠️  This key was encrypted for another participant...")


@sio.on('receive_reencrypted_session_key')
def on_receive_reencrypted_session_key(data):
    """
    🔗 HANDSHAKE EM CADEIA - CARLOS recebe a chave re-criptografada

    CARLOS (terceiro ou posterior) recebe a session_key que ALICE re-criptografou
    especialmente com sua chave pública. Apenas CARLOS consegue descriptografar.
    """
    encrypted_session_key = data['encrypted_session_key']
    room = data['room']
    from_username = data.get('from_username', 'participant')

    try:
        # Descriptografa com sua chave privada (RSA)
        session_keys[room] = decrypt_with_private_key(
            encrypted_session_key,
            global_private_key
        )

        log_session_key_decrypted(
            f"CARLOS (via re-encryption de {from_username})",
            room,
            "client.py",
            "on_receive_reencrypted_session_key"
        )

        log_debug(
            f"✅ CARLOS: Recebi session_key re-criptografada e descriptografei com sucesso!",
            "client.py", "on_receive_reencrypted_session_key"
        )

        print(f"✅ Reencrypted session key received, decrypted, and stored for room: {room}")

    except Exception as e:
        log_error(
            f"Erro ao descriptografar session_key re-criptografada",
            "client.py",
            "on_receive_reencrypted_session_key",
            str(e)
        )
        print(f"❌ Failed to decrypt reencrypted session key: {e}")


# Handler for accepted chat invitations coming from server
@sio.on('chat_invitation_accepted')
def on_chat_invitation_accepted(data):
    """
    Recebe notificação quando um invitee aceita o convite.
    Armazena em `local_notifications` para que a UI (Streamlit) possa reagir.
    """
    try:
        room = data.get('room_id')
        invitee = data.get('invitee_username')
        # Store the notification keyed by room
        local_notifications[room] = {
            'invitee_username': invitee,
            'room_id': room
        }
        log_debug(f"Recebido chat_invitation_accepted -> {invitee} entrou na sala {room}", "client.py",
                  "on_chat_invitation_accepted")
        print(f"🔔 Invitation accepted: {invitee} -> room {room}")
    except Exception as e:
        log_error("Erro ao processar chat_invitation_accepted", "client.py", "on_chat_invitation_accepted", str(e))


@sio.on('session_invalidated')
def on_session_invalidated(data):
    """
    Recebe notificação quando a sessão é invalidada (outro participante saiu).
    Remove a chave da sessão para evitar reutilização com segurança comprometida.
    """
    try:
        room = data.get('room')
        username = data.get('username')
        message = data.get('message', f'{username} saiu do chat')

        # Deletar chave para não tentar reutilizar
        if room in session_keys:
            del session_keys[room]

        log_session_invalidated(room, username, "client.py", "on_session_invalidated")
        print(f"⚠️  Session invalidated: {message}")
    except Exception as e:
        log_error("Erro ao processar session_invalidated", "client.py", "on_session_invalidated", str(e))


def send_message_to_group(username, group_to_talk, message, room, timestamp):
    """
    Envia mensagem para uma sala de grupo.

    ✅ CORRETO: Envia UMA ÚNICA mensagem para a room (sala)
    ❌ ERRADO: Enviar para cada amigo individualmente (causava duplicação)

    O servidor recebe uma mensagem e distribui para TODOS na sala.
    
    ✅ NOVO: Assina mensagem criptografada para garantir INTEGRIDADE
    """
    encrypted_message = encrypt_chacha20_message(session_keys[room], message)
    log_message_encrypted(username, "group", room, "client.py", "send_message_to_group")
    
    # ✅ NOVO: Assina a mensagem criptografada com chave privada
    # Isso garante que ninguém consegue alterá-la em trânsito
    try:
        signature = sign_message(encrypted_message, global_private_key)
        log_debug("Mensagem assinada para integridade", "client.py", "send_message_to_group")
    except Exception as e:
        log_error("Erro ao assinar mensagem", "client.py", "send_message_to_group", str(e))
        signature = ""
    
    # Envia para a SALA (room), não para cada amigo
    sio.emit('send_message', {
        'username': username,
        'user_to_talk': None,  # Não é 1-a-1, é para toda a sala
        'encrypted_message': encrypted_message,
        'signature': signature,  # ✅ Envia assinatura
        'room': room,
        'timestamp': timestamp
    })

def send_message(username, user_to_talk, message, room, timestamp):
    encrypted_message = encrypt_chacha20_message(session_keys[room], message)
    log_message_encrypted(username, user_to_talk, room, "client.py", "send_message")
    
    # ✅ NOVO: Assina a mensagem criptografada
    try:
        signature = sign_message(encrypted_message, global_private_key)
        log_debug("Mensagem assinada para integridade", "client.py", "send_message")
    except Exception as e:
        log_error("Erro ao assinar mensagem", "client.py", "send_message", str(e))
        signature = ""
    
    sio.emit('send_message', {
        'username': username,
        'user_to_talk': user_to_talk,
        'encrypted_message': encrypted_message,
        'signature': signature,  # ✅ Envia assinatura
        'room': room,
        'timestamp': timestamp
    })


# Callback para recebimento de mensagem
@sio.on('receive_message')
def on_receive_message(data):
    encrypted_message = data['encrypted_message']
    username = data['username']
    room = data['room']
    timestamp = data['timestamp']
    signature = data.get('signature')
    
    # ========== VERIFICAÇÃO DE INTEGRIDADE ==========
    if not signature:
        print(f"⚠️ AVISO: Mensagem sem assinatura de {username}")
        return
    
    try:
        # Buscar chave pública do remetente
        response = requests.get(f'http://localhost:5000/public_key/{username}')
        if response.status_code != 200:
            print(f"❌ Erro: Não foi possível obter chave pública de {username}")
            return
        
        sender_public_key = response.json().get('user_public_key')
        if not sender_public_key:
            print(f"❌ Erro: Chave pública inválida para {username}")
            return
        
        # Verificar assinatura (integridade da mensagem)
        is_valid = verify_signature(encrypted_message, signature, sender_public_key)
        
        if not is_valid:
            print(f"🔴 SEGURANÇA: Integridade comprometida! Mensagem de {username} foi alterada!")
            print(f"   Assinatura INVÁLIDA - mensagem será IGNORADA")
            return
        
        print(f"✅ Assinatura verificada: mensagem de {username} é autêntica")
        
    except Exception as e:
        print(f"❌ Erro ao verificar assinatura: {str(e)}")
        return
    
    # ========== DESCRIPTOGRAFIA ==========
    decrypted_message = decrypt_chacha20_message(session_keys[room], encrypted_message)
    log_message_decrypted("Usuário atual", username, room, "client.py", "on_receive_message")
    print(f"{timestamp} {username}:", decrypted_message)


# ---------- Autentication -------------

def register_user(username, password, master_key):
    if not username or not password:
        log_error("Tentativa de registro sem username ou password", "client.py", "register_user")
        return False, "Inform username and password."

    username = username.strip()
    password = password.strip()

    private_key, public_key = generate_keypair()
    public_key_str = public_key.decode('utf-8')

    global global_private_key
    global_private_key = private_key

    # TODO: chave está sendo gerada de forma aleatória, existe a chance de criar chaves iguais para diferentes usuários.

    try:
        response = requests.post('http://localhost:5000/register', json={
            'username': username,
            'password': password,
            'public_key': public_key_str,
            'master_key': master_key,
        })

    except requests.exceptions.RequestException as e:
        log_error(f"Erro de conexão com servidor durante registro", "client.py", "register_user", str(e))
        return False, f"Conection error with server: {e}"

    if response.ok:
        encrypted_data = encrypt_private_key(private_key, password)
        save_private_key(username=username, encrypted_data=encrypted_data)

        log_key_generated("RSA 2048-bit", "Memória + Arquivo Local", "client.py", "register_user")
        log_private_key_stored(username, "users_key/", "client.py", "register_user")

        print(encrypted_data)
        return True, "Register successfully!"
    else:
        detail = None
        try:
            detail = response.json().get("detail", None)
        except Exception:
            pass

        # se for o caso específico de usuário já existente
        if response.status_code == 409:
            log_error(f"Username já existe no servidor", "client.py", "register_user", f"Username: {username}")
            return False, "User already exists."

        return False, f"Falha na requisição."


def login_user(username, password, auth_code):
    if not username or not password:
        log_error("Tentativa de login sem username ou password", "client.py", "login_user")
        return False, "Inform username and password."

    response = requests.get(f'http://localhost:5000/auth_code/{username}/')

    code = pyotp.TOTP(response.json().get("master_key"))

    if code.now() != auth_code:
        print(f"valor de code: {code.now()}\n"
              f"valor de auth_code: {auth_code}")
        log_error("Tentativa de autenticar com código falhada", "client.py", "login_user")
        return False, "Failed to authenticate."

    try:
        response = requests.post('http://localhost:5000/login', json={
            'username': username,
            'password': password,
        })

    except requests.exceptions.RequestException as e:
        log_error(f"Erro de conexão com servidor durante login", "client.py", "login_user", str(e))
        return False, f"Conection error with server: {e}"

    if response.ok:
        private_key_encrypted = recover_private_key(username)
        private_key = decrypt_private_key(private_key_encrypted, password)

        global global_private_key
        global_private_key = private_key

        print(private_key)
        log_debug(f"Chave privada recuperada e descriptografada com sucesso", "client.py", "login_user")

        return True, "Login successfully!"
    else:
        print("\nLogin failed. Check your username and password.\n")

        try:
            # Tenta pegar o campo detail da resposta JSON
            detail = response.json().get("detail", None)
        except Exception:
            detail = None

        log_error(f"Falha na autenticação do usuário", "client.py", "login_user", f"Status: {response.status_code}")
        if detail:
            return False, f"Erro do servidor: {detail}"
        else:
            return False, f"Falha na requisição ({response.status_code} ---- {response.text})."


# ---------- Interface functions -------------

def chat_with_user(username, user_to_talk, room):
    request_user_public_key(user_to_talk, room)
    join(username, room)
    print(f"\n╔═════════════════╗")
    print(f" Chat com {user_to_talk}")
    print("╚═════════════════╝")
    print("Type 'exit' to exit\n")
    get_message_history(username, room)

    while True:
        message = input()
        timestamp = datetime.now().strftime("(%a, %d %b %Y %H:%M:%S GMT)")
        if message.lower() == "exit":
            print("Back to main menu")
            leave_room(room)
            break
        print(f"\n{timestamp} You: {message}")
        send_message(username, user_to_talk, message, room, timestamp)


def main_menu(username):
    while True:
        print("\n╔═════════════════╗")
        print("  ChatRSA")
        print("╚═════════════════╝")
        print("1 - Add user")
        print("2 - Chat with a friend")
        print("3 - Group chat")
        print("0 - Exit")

        choice = input("Type your option: ")

        if choice == "1":
            # Obtenha e exiba a lista de todos os usuários do sistema
            all_users = get_all_users()
            friend_list = get_friend_list(username)
            all_users_avaliable = list(set(all_users) - set(friend_list))
            if all_users:
                print("\nAvailable users:")
                for user in all_users_avaliable:
                    if user != username:  # Exclui o próprio usuário da lista
                        print(f" - {user}")
            else:
                print("No user was found in the system.")

            # Continuar pedindo para digitar o nome do usuário que deseja adicionar
            user_to_add = input("Type user name to add: ")
            add_user_in_friendlist(username, user_to_add)
        elif choice == "2":
            friend_list = get_friend_list(username)
            # print friend list
            if friend_list:
                print("\nFriend list:")
                for friend in friend_list:
                    print(f" - {friend}")
            else:
                print("You have no friends. Loser.")

            user_to_talk = input("Type friend username to start a conversation: ")
            room = f"room_{'_'.join(sorted([username, user_to_talk]))}"
            if not is_user_in_friendlist(username, user_to_talk):
                print("User not found.")
                continue
            chat_with_user(username, user_to_talk, room)
        elif choice == "3":
            friend_list = get_friend_list(username)

            if friend_list:
                print("\nFriend list:")
                for friend in friend_list:
                    print(f" - {friend}")
            else:
                print("You have no friends. Loser.")

            group_users = []
            print("Type the usernames of friends to add to the group chat (type 'done' when finished):")

            while True:
                user = input("Add user: ")
                if user.lower() == 'done':
                    break
                if is_user_in_friendlist(username, user) and user != username and user not in group_users:
                    group_users.append(user)
                else:
                    print("User not found in your friend list or already on the group.")
            room = f"room_{'_'.join(sorted([username, *group_users]))}"
            for user in group_users:
                chat_with_user(username, user, room)

        elif choice == "0":
            print("Exiting...")
            break
        else:
            print("Not a valid option. Try again.")


# Função principal para execução do chat
def run_chat():
    sio.connect('http://localhost:5000/')
    # sio.connect('http://192.168.1.7:5000', headers={'sid': sid})

    print("\nChatRSA\n")

    while True:
        print("\nLogin (l) or register (r)?")
        option = input()

        # Register
        if option == 'r':
            username = input("\nUsername: ")
            password = input("Password: ")
            if register_user(username, password):
                print("Register successful!")
                main_menu(username)
                break
            else:
                print("Something went wrong. Try again.")

        # Login
        elif option == 'l':
            print("\n╔═══════════════╗")
            print("      Login")
            print("╚═══════════════╝")
            username = input("\nUsername: ")
            password = input("Password: ")
            login_success, private_key = login_user(username, password)

            if login_success:
                main_menu(username)

                break
            else:
                print("Something went wrong. Try again.")
        else:
            print("Not a valid option. Try again.")

    sio.disconnect()


if __name__ == '__main__':
    run_chat()
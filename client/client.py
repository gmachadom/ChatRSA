from flask_socketio import leave_room
from datetime import datetime, timedelta

import logging
import os
import requests
import socketio
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..')

if root_dir not in sys.path:
    sys.path.append(root_dir)

from server.utils import * 


sio = socketio.Client()

global global_private_key
session_keys = {}
public_keys = {}


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


def add_user_in_friendlist(username, username_to_add):
    if not username_to_add:
        return False, "Please enter a username."

    if username_to_add == username:
        return False, "You can not add yourself as friend."

    friendlist = get_friend_list(username)

    if username_to_add not in friendlist:
        response = requests.post('http://localhost:5000/user', json={
            'username': username,
            'username_to_add': username_to_add
        })
        if response.ok:
            return True, "User added successfully!"
        else:
            return False, "User not found."
    else:
        return False, "This user is already in your friend list."


def is_user_in_friendlist(username, username_to_talk):
    response = requests.post('http://localhost:5000/friendlist', json={
        'username': username,
        'username_to_talk': username_to_talk
    })
    if response.ok:
        return True
    return False


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

# def get_friend_list(username):
#     try:
#         response = requests.get(f'http://localhost:5000/friendlist/{username}')
#
#     except requests.exceptions.RequestException as e:
#         return False, f"Connection error with server: {e}"
#
#     if response.ok:
#         friend_list = response.json().get("friends", [])
#         return True, "Friends", friend_list
#     else:
#         try:
#             detail = response.json().get("detail", None)
#         except Exception:
#             detail = None
#
#         if response.status_code == 404:
#             return False, "Any friend founded.", None
#         elif response.status_code == 401:
#             return False, "Not authorized.", None
#         else:
#             return False, "Error retrieving friend list.", None



def request_user_public_key(username_to_talk, room):
    response = requests.get(f'http://localhost:5000/public_key/{username_to_talk}')
    if response.ok:
        public_key = response.json().get("user_public_key")
        public_keys[room] = public_key
        return public_key
    else:
        print(f"Error retrieving {username_to_talk} public key.")
        return


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

def connect_to_server():
    if not sio.connected:
        try:
            sio.connect("http://localhost:5000")  # ou o IP/porta do seu servidor Flask-SocketIO
            print("Conexão bem-sucedida!")
        except Exception as e:
            print("Erro ao conectar:", e)

def join(username, room):
    connect_to_server()
    sio.emit('join', {'room': room, 'username': username})


@sio.on('generate_session_key')
def generate_session_key(data):
    room = data['room']
    session_keys[room] = os.urandom(32)
    encrypted_session_key = encrypt_session_key(session_keys[room], room)
    save_session_key(encrypted_session_key, room)
    encrypted_session_key_with_public_key = encrypt_with_public_key(session_keys[room], public_keys[room])
    sio.emit('send_session_key', {'encrypted_session_key': encrypted_session_key_with_public_key, 'room': room})


# Callback 
@sio.on('receive_session_key')
def on_receive_session_key(data):
    encrypted_session_key = data['encrypted_session_key']
    room = data['room']
    file_path = f"session_keys/{room}_session_key.bin"
    if not os.path.isfile(file_path):
        session_keys[room] = decrypt_with_private_key(encrypted_session_key, global_private_key)
        encrypted_session_key = encrypt_session_key(session_keys[room], room)
        save_session_key(encrypted_session_key, room)
    else:
        session_key_encrypted = recover_session_key(room)
        session_key = decrypt_session_key(session_key_encrypted, room)
        session_keys[room] = session_key


def send_message(username, user_to_talk, message, room, timestamp):

    encrypted_message = encrypt_chacha20_message(session_keys[room], message)
    sio.emit('send_message', {
        'username': username,
        'user_to_talk': user_to_talk,
        'encrypted_message': encrypted_message,
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
    decrypted_message = decrypt_chacha20_message(session_keys[room], encrypted_message)
    print(f"{timestamp} {username}:", decrypted_message)


# ---------- Autentication -------------

def register_user(username, password):
    if not username or not password:
        return False, "Inform username and password."

    username = username.strip()
    password = password.strip()

    private_key, public_key = generate_keypair()
    public_key_str = public_key.decode('utf-8')

    global global_private_key
    global_private_key = private_key

    try:
        response = requests.post('http://localhost:5000/register', json={
            'username': username,
            'password': password,
            'public_key': public_key_str
        })

    except requests.exceptions.RequestException as e:
        return False, f"Conection error with server: {e}"

    if response.ok:
        encrypted_data = encrypt_private_key(private_key, password)
        save_private_key(username=username, encrypted_data=encrypted_data)

        print(encrypted_data)
        return True, "Register successfully!"
    else:
        detail = None
        try:
            detail = response.json().get("detail", None)
        except Exception:
            pass

        # se for o caso específico de usuário já existente
        if response.status_code == 409 :
            return False, "User already exists."

        return False, f"Falha na requisição."


def login_user(username, password):
    if not username or not password:
        return False, "Inform username and password."
    try:
        response = requests.post('http://localhost:5000/login', json={
            'username': username,
            'password': password,
        })

    except requests.exceptions.RequestException as e:
        return False, f"Conection error with server: {e}"

    if response.ok:
        private_key_encrypted = recover_private_key(username)
        private_key = decrypt_private_key(private_key_encrypted, password)

        global global_private_key
        global_private_key = private_key

        print(private_key)

        return True, "Login successfully!"
    else:
        print("\nLogin failed. Check your username and password.\n")

        try:
            # Tenta pegar o campo detail da resposta JSON
            detail = response.json().get("detail", None)
        except Exception:
            detail = None
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
        print(  "  ChatRSA"  )
        print(  "╚═════════════════╝")
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
            room = f"room_{'_'.join(sorted([username, *group_users ]))}"
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

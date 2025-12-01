from datetime import datetime
import time
import streamlit as st
import sys
import os
import requests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from client.client import (
    join,
    request_user_public_key,
    get_message_history,
    leave_room_client,
    wait_for_new_messages,
    send_message,
    get_pending_chat_invitations,
    get_sent_invitations,
    get_active_chats
)
from logger_config import log_debug, log_error, log_user_joined_session, log_user_left_session

# Não esconde o menu padrão — vamos usar a sidebar
# hide_sidebar_style = """
#     <style>
#     [data-testid="stSidebarNav"] {display: none;}
#     </style>
# """
# st.markdown(hide_sidebar_style, unsafe_allow_html=True)

username = st.session_state.get("username")

if not username:
    log_error("Tentativa de acessar chat sem login", "chatScreen.py", "page_load")
    st.error("Please log in first")
    st.switch_page("pages/loginScreen.py")

# Get chat info
user_to_talk = st.session_state.get("chat_partner")
room = st.session_state.get("pending_room")

if not user_to_talk or not room:
    log_error("Tentativa de acessar chat sem parceiro ou sala válida", "chatScreen.py", "page_load")
    st.error("Invalid chat session")
    st.switch_page("pages/mainMenu.py")

# ===== SIDEBAR: Chats Ativos e Navegação =====
with st.sidebar:
    st.title("💬 ChatRSA")
    st.divider()
    
    # Seção de chats ativos
    st.write("### 🟢 Active Chats")
    ok, active_chats = get_active_chats(username)
    if ok and active_chats:
        for chat in active_chats:
            room_id = chat['room_id']
            # Extrai o nome do parceiro do room_id (formato: "room_alice_bob")
            room_parts = room_id.replace("room_", "").split("_")
            chat_partner = next((p for p in room_parts if p != username), "Unknown")
            
            # Botão para entrar no chat
            if st.button(
                f"💬 {chat_partner}",
                use_container_width=True,
                key=f"active_chat_{room_id}"
            ):
                st.session_state["pending_room"] = room_id
                st.session_state["chat_partner"] = chat_partner
                st.rerun()
    else:
        st.caption("No active chats")
    
    st.divider()
    
    # Seção de convites recebidos
    st.write("### 📥 Pending Invitations")
    ok, pending_invs = get_pending_chat_invitations(username)
    if ok and pending_invs:
        st.info(f"💌 {len(pending_invs)} pending invitation(s)")
        if st.button("View →", use_container_width=True, key="view_pending_invs"):
            st.switch_page("pages/chatInvitationsScreen.py")
    else:
        st.caption("No pending invitations")
    
    st.divider()
    
    # Navigation
    if st.button("🏠 Back to Menu", use_container_width=True):
        log_user_left_session(username, room, "chatScreen.py", "back_to_menu")
        leave_room_client(room, username, hash(username) % 1000)
        st.session_state.pop("pending_room", None)
        st.session_state.pop("chat_partner", None)
        st.switch_page("pages/mainMenu.py")

# ===== MAIN CHAT AREA =====
log_user_joined_session(username, room, "chatScreen.py", "page_load")
st.header(f"💬 Chat with {user_to_talk}")

# Request public key and join room
request_user_public_key(user_to_talk, room)
    # Obter user_id real do servidor
    
try:
    response = requests.get(f'http://localhost:5000/user/id/{username}')
    user_id = response.json().get('user_id') if response.ok else hash(username) % 1000
except:
    user_id = hash(username) % 1000

join(username, room, user_id)# Give socket time to exchange session keys
time.sleep(0.5)

# Load message history
ok, history = get_message_history(username, room)
if not ok:
    st.warning("Could not load message history")
    history = []

# Display messages
st.write("---")
if not history:
    st.info("No messages yet. Start the conversation!")
else:
    for m in history:
        is_user = m["sender"] == "You"
        with st.chat_message("user" if is_user else "assistant"):
            st.markdown(f"**{m['sender']}**")
            st.markdown(m['text'])
            st.caption(m['timestamp'])

st.write("---")

# Message input
msg = st.chat_input("Type your message...")
if msg is not None:
    msg = msg.strip()
    if not msg:
        log_error("Tentativa de enviar mensagem vazia", "chatScreen.py", "send_message")
        st.error("Cannot send empty message")
    else:
        ts = datetime.utcnow().strftime("(%a, %d %b %Y %H:%M:%S GMT)")
        try:
            log_debug(f"Mensagem digitada e pronta para enviar", "chatScreen.py", "send_message")
            send_message(username, user_to_talk, msg, room, ts)
            st.success("Message sent!")
            time.sleep(0.5)
            st.rerun()
        except KeyError:
            log_error("Session key não disponível", "chatScreen.py", "send_message")
            st.error("⚠️ Session key not available - the other user may have left the chat")
        except Exception as e:
            log_error(f"Erro ao enviar mensagem", "chatScreen.py", "send_message", str(e))
            st.error(f"Error sending message: {e}")

# Check if session was invalidated (other user left)
# if room not in st.session_state.get("active_sessions", []):
#     st.warning("No one is here")

# Refresh messages periodically
if st.button("🔄 Refresh Messages"):
    st.rerun()

st.divider()

# Exit button
if st.button("🚪 Exit Chat", use_container_width=True):
    log_user_left_session(username, room, "chatScreen.py", "exit_chat")
    leave_room_client(room, username, hash(username) % 1000)
    st.session_state.pop("pending_room", None)
    st.session_state.pop("chat_partner", None)
    st.switch_page("pages/mainMenu.py")

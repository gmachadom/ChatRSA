import streamlit as st
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from client.client import (
    get_pending_friend_requests,
    get_pending_chat_invitations,
    get_active_chats
)

# Esconde o menu padrão
# hide_sidebar_style = """
#     <style>
#     [data-testid="stSidebarNav"] {display: none;}
#     </style>
# """

# st.markdown(hide_sidebar_style, unsafe_allow_html=True)

username = st.session_state.get("username")

if not username:
    st.error("Please log in first")
    st.switch_page("pages/loginScreen.py")

# ===== SIDEBAR: Chats Ativos =====
with st.sidebar:
    st.title("💬 ChatRSA")
    st.divider()
    
    # Seção de chats ativos
    st.write("### 🟢 Active Chats")
    ok, active_chats = get_active_chats(username)
    if ok and active_chats:
        for chat in active_chats:
            room_id = chat['room_id']
            # Extrai o nome do parceiro do room_id
            room_parts = room_id.replace("room_", "").split("_")
            chat_partner = next((p for p in room_parts if p != username), "Unknown")
            
            if st.button(
                f"💬 {chat_partner}",
                use_container_width=True,
                key=f"active_chat_{room_id}"
            ):
                st.session_state["pending_room"] = room_id
                st.session_state["chat_partner"] = chat_partner
                st.switch_page("pages/chatScreen.py")
    else:
        st.caption("No active chats")
    
    st.divider()

st.header(f"Welcome, {username}! 👋")

# Get notifications
ok_friend, friend_reqs = get_pending_friend_requests(username)
ok_chat, chat_invs = get_pending_chat_invitations(username)

friend_count = len(friend_reqs) if ok_friend else 0
chat_count = len(chat_invs) if ok_chat else 0

# Display notifications
col1, col2 = st.columns(2)
with col1:
    if friend_count > 0:
        st.warning(f"🤝 {friend_count} friend request(s) waiting!")
    else:
        st.info("🤝 No pending friend requests")

with col2:
    if chat_count > 0:
        st.warning(f"💬 {chat_count} chat invitation(s) waiting!")
    else:
        st.info("💬 No pending chat invitations")

st.divider()

st.write("### What would you like to do?")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("➕ Add Friend", use_container_width=True):
        st.switch_page("pages/addFriendScreen.py")

with col2:
    if st.button("💬 Chat", use_container_width=True):
        st.switch_page("pages/chatWithFriendMenuScreen.py")

with col3:
    if st.button("👥 Group Chat", use_container_width=True):
        st.switch_page("pages/groupChatMenuScreen.py")

st.divider()

col1, col2 = st.columns(2)

with col1:
    if friend_count > 0 and st.button("🤝 View Friend Requests", use_container_width=True):
        st.switch_page("pages/friendRequestsScreen.py")

with col2:
    if chat_count > 0 and st.button("💌 View Chat Invitations", use_container_width=True):
        st.switch_page("pages/chatInvitationsScreen.py")

st.divider()

if st.button("🚪 Log Out", use_container_width=True):
    st.session_state.clear()
    st.switch_page("pages/loginScreen.py")

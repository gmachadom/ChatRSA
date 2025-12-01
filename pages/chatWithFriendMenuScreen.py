import streamlit as st
import sys
import os
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from client.client import (
    get_friend_list,
    send_chat_invitation,
    request_user_public_key,
    join,
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
    ok_active, active_chats = get_active_chats(username)
    if ok_active and active_chats:
        for chat in active_chats:
            room_id = chat['room_id']
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

st.header("💬 Chat with Friend")

# Load friends
with st.spinner("Loading your friends..."):
    ok, result = get_friend_list(username)

st.write("**Your Friends:**")

if not ok:
    st.error(result)
else:
    friend_list = result
    if friend_list:
        for friend in friend_list:
            st.write(f"• {friend}")
    else:
        st.info("You don't have any friends yet.")
        if st.button("➕ Add a friend"):
            st.switch_page("pages/addFriendScreen.py")
        st.stop()

st.divider()

# Send chat invitation
with st.form("start_chat_form", clear_on_submit=True):
    friend_to_chat = st.text_input("Friend to chat with:")
    submitted = st.form_submit_button("📤 Send Chat Invitation")

if submitted:
    if not friend_to_chat:
        st.error("Please enter a friend's username")
    else:
        # Generate room ID
        room = f"room_{'_'.join(sorted([username, friend_to_chat]))}"
        
        # Request friend's public key
        request_user_public_key(friend_to_chat, room)
        
        # Send invitation
        ok, msg = send_chat_invitation(username, friend_to_chat, room)
        if ok:
            st.success(f"Chat invitation sent to {friend_to_chat}!")
            st.info("💡 You can check the status in the sidebar of the chat screen!")
            
            # Store for chat screen sidebar
            st.session_state["pending_room"] = room
            st.session_state["chat_partner"] = friend_to_chat
            
            time.sleep(2)
            st.switch_page("pages/chatScreen.py")
        else:
            st.error(f"Error: {msg}")

st.divider()

if st.button("← Back to Menu", use_container_width=True):
    st.switch_page("pages/mainMenu.py")

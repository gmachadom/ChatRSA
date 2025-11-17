import streamlit as st
import sys
import os
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from client.client import (
    get_pending_chat_invitations,
    accept_chat_invitation,
    decline_chat_invitation,
    get_message_history,
    get_active_chats
)
from logger_config import log_debug, log_chat_invitation_accepted, log_chat_invitation_declined

# Esconde o menu padrão
# hide_sidebar_style = """
#     <style>
#     [data-testid="stSidebarNav"] {display: none;}
#     </style>
# """

# st.markdown(hide_sidebar_style, unsafe_allow_html=True)

username = st.session_state.get("username")

if not username:
    log_debug("Tentativa de acessar chat invitations sem login", "chatInvitationsScreen.py", "page_load")
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

st.header("💬 Chat Invitations")

# Refresh button
if st.button("🔄 Refresh", use_container_width=True):
    log_debug(f"Página de chat invitations recarregada", "chatInvitationsScreen.py", "refresh")
    st.rerun()

# Get pending chat invitations
ok, invitations_data = get_pending_chat_invitations(username)

if not ok:
    st.warning("Unable to load chat invitations")
else:
    if not invitations_data:
        st.info("No pending chat invitations")
    else:
        st.write(f"**{len(invitations_data)} pending invitation(s):**")
        st.divider()

        for inv in invitations_data:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"💬 **{inv['inviter_username']}** invited you to chat")
                st.caption(f"Sent: {inv['created_at']}")
            
            with col2:
                if st.button("✅ Accept", key=f"accept_{inv['invitation_id']}", use_container_width=True):
                    ok, msg = accept_chat_invitation(inv['invitation_id'])
                    if ok:
                        log_chat_invitation_accepted(username, inv['inviter_username'], inv['room_id'], "chatInvitationsScreen.py", "accept_button")
                        st.success("Chat invitation accepted!")
                        st.session_state["pending_room"] = inv['room_id']
                        st.session_state["chat_partner"] = inv['inviter_username']
                        time.sleep(1)
                        st.switch_page("pages/chatScreen.py")
                    else:
                        st.error(f"Error: {msg}")
            
            with col3:
                if st.button("❌ Decline", key=f"decline_{inv['invitation_id']}", use_container_width=True):
                    ok, msg = decline_chat_invitation(inv['invitation_id'])
                    if ok:
                        log_chat_invitation_declined(username, inv['inviter_username'], inv['room_id'], "chatInvitationsScreen.py", "decline_button")
                        st.success("Chat invitation declined!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")
            
            st.divider()

# Navigation
st.divider()
if st.button("← Back to Menu", use_container_width=True):
    st.switch_page("pages/mainMenu.py")

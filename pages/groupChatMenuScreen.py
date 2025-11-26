import streamlit as st
import time

from client.client import get_friend_list, send_chat_invitation

username = st.session_state["username"]

# Esconde o menu padrão
hide_sidebar_style = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""

st.markdown(hide_sidebar_style, unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"Oi, {username}!")
    st.title("⚙️ Menu")
    if st.button("Main Menu"):
        st.switch_page("pages/mainMenu.py")
    if st.button("Add a friend"):
        st.switch_page("pages/addFriendScreen.py")
    if st.button("Chat with friend"):
        st.switch_page("pages/chatWithFriendMenuScreen.py")


ok, friend_list = get_friend_list(username)

st.header("👥 Group Chat")

group_users = st.multiselect("Select friends to create a group chat:", friend_list)
button_start_group_chat = st.button("Start Group Chat", use_container_width=True)

if button_start_group_chat:
    if not group_users:
        st.error("Select at least one friend")
    else:
        room = f"room_{'_'.join(sorted([username, *group_users]))}"
        
        st.info(f"📤 Enviando convites para {len(group_users)} amigo(s)...")
        
        # Enviar convite SEPARADAMENTE para cada usuário
        success_count = 0
        for friend in group_users:
            ok, msg = send_chat_invitation(username, friend, room)
            if ok:
                success_count += 1
                st.success(f"✅ Convite enviado para {friend}")
            else:
                st.error(f"❌ Erro ao enviar para {friend}: {msg}")
        
        if success_count == len(group_users):
            st.success(f"✅ Todos os {len(group_users)} convites foram enviados!")
            st.session_state["roomGroup"] = room
            st.session_state["listToAddInGroup"] = group_users
            time.sleep(1)
            st.switch_page("pages/chatGroupScreen.py")
        else:
            st.warning(f"⚠️ Apenas {success_count} de {len(group_users)} convites foram enviados")

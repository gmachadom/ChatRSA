from datetime import datetime
import time
import streamlit as st
from flask_socketio import leave_room
from client.client import (
    join, request_user_public_key, get_message_history, wait_for_new_messages, leave_room_client, send_message_to_group, send_message,
    request_user_public_key_group
)

username = st.session_state["username"]
group_users = st.session_state["listToAddInGroup"]
room = st.session_state["roomGroup"]

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
        leave_room_client(room, username)
        st.session_state["roomGroup"] = ""
        st.switch_page("pages/mainMenu.py")
    if st.button("Add a friend"):
        leave_room_client(room, username)
        st.session_state["roomGroup"] = ""
        st.switch_page("pages/addFriendScreen.py")
    if st.button("Chat with friend"):
        leave_room_client(room, username)
        st.session_state["roomGroup"] = ""
        st.switch_page("pages/chatWithFriendMenuScreen.py")
    if st.button("Chat with group"):
        leave_room_client(room, username)
        st.session_state["roomGroup"] = ""
        st.switch_page("pages/groupChatMenuScreen.py")

st.header(f"Group Chat with: {", ".join(sorted(group_users))}")

request_user_public_key_group(group_users, room)
join(username, room)

# Historico das mensagens
ok, history = get_message_history(username, room)
if not ok:
    st.error(history)
    history = []

if not history:
    st.info("No messages in this chat yet. Start the conversation!")
else:
    last_timestamp = history[-1]["timestamp"]
    for m in history:
        role = "user" if m["sender"] == "You" else "assistant"
        print(f"{m["sender"]}: mandou")
        if m["timestamp"] != last_timestamp:
            with st.chat_message(role):
                st.markdown(f"{m['sender']}\n\n")
                st.markdown(
                    f"{m['text']}\n\n"
                    f"<span style='font-size:0.8em;color:gray'>{m['timestamp']}</span>",
                    unsafe_allow_html=True
                )
        last_timestamp = m["timestamp"]

msg = st.chat_input("Enter your message:")
if msg is not None:  # usuário apertou Enter
    msg = msg.strip()
    if not msg:
        st.error("Empty message.")
    else:
        ts = datetime.utcnow().strftime("(%a, %d %b %Y %H:%M:%S GMT)")

        try:
            send_message_to_group(username, group_users, msg, room, ts)
        except KeyError:
            st.error("No session key to this chat yet. Wait for pairing.")
        except Exception as e:
            st.error(f"Failed to send: {e}")
        else:
            st.rerun()  # recarregar historico

#  ----- Loop de atualização -----
old_len = len(history)
ok2, hist2 = get_message_history(username, room)

update = wait_for_new_messages(username, room, old_len, timeout=15, interval=1.5)

if update:
    st.session_state[f"_last_count_{room}"] = hist2
    st.rerun()



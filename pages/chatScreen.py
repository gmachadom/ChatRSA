from datetime import datetime
import time
import streamlit as st
from flask_socketio import leave_room
from client.client import join, request_user_public_key, get_message_history, leave_room_client, wait_for_new_messages, send_message

userToTalk = st.session_state['userToTalk']
username = st.session_state["username"]
room = st.session_state["roomWithFriend"]

st.header(f"Chat with {userToTalk}")

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

request_user_public_key(userToTalk, room)
join(username, room)

# Historico das mensagens
ok, history = get_message_history(username, room)
if not ok:
    st.error(history)
    history = []

if not history:
    st.info("No messages in this chat yet. Start the conversation!")
else:
    for m in history:
        role = "user" if m["sender"] == "You" else "assistant"
        with st.chat_message(role):
            st.markdown(f"{m['sender']}\n\n")
            st.markdown(
                f"{m['text']}\n\n"
                f"<span style='font-size:0.8em;color:gray'>{m['timestamp']}</span>",
                unsafe_allow_html=True
            )

buttonBack = st.button("Back")

msg = st.chat_input("Enter your message:")
if msg is not None:  # usuário apertou Enter
    msg = msg.strip()
    if not msg:
        st.error("Empty message.")
    else:
        ts = datetime.utcnow().strftime("(%a, %d %b %Y %H:%M:%S GMT)")

        try:
            send_message(username, userToTalk, msg, room, ts)
        except KeyError:
            st.error("No session key to this chat yet. Wait for pairing.")
        except Exception as e:
            st.error(f"Failed to send: {e}")
        else:
            st.rerun()  # recarregar historico

if buttonBack:
    with st.chat_message("user"):
        st.markdown(
            "conversa tá uma merda kkkkk. Vou dar o fora.\n\n"
            f"<span style='font-size:0.8em;color:gray'>{datetime.utcnow().strftime('(%a, %d %b %Y %H:%M:%S GMT)')}</span>",
            unsafe_allow_html=True
        )
    time.sleep(3)
    leave_room_client(room, username)
    st.session_state["roomGroup"] = ""
    st.switch_page("pages/chatWithFriendMenuScreen.py")

#  ----- Loop de atualização -----
old_len = len(history)
ok2, hist2 = get_message_history(username, room)

update = wait_for_new_messages(username, room, old_len, timeout=15, interval=1.5)

if update:
    st.session_state[f"_last_count_{room}"] = hist2
    st.rerun()
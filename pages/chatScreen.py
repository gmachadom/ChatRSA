from datetime import datetime
from time import sleep

import streamlit as st
from flask_socketio import leave_room

from client.client import join, request_user_public_key, get_message_history, send_message

userToTalk = st.session_state['userToTalk']
username = st.session_state["username"]

st.header(f"Chat with {userToTalk}")

request_user_public_key(userToTalk, st.session_state["roomWithFriend"])
join(username, st.session_state["roomWithFriend"])

ok, history = get_message_history(username, st.session_state["roomWithFriend"])
if not ok:
    st.error(history)
elif not history:
    st.info("No messages in this chat yet. Start the conversation!")
else:
    for msg in history:
        role = "user" if msg["sender"] == "You" else "assistant"
        with st.chat_message(role):
            st.markdown(
                f"{msg['text']}\n\n"
                f"<span style='font-size:0.8em;color:gray'>{msg['timestamp']}</span>",
                unsafe_allow_html=True
            )

buttonBack = st.button("Back")

msg = st.chat_input("Enter your message:")
if msg is not None: # usuário apertou Enter
    msg = msg.strip()
    if msg:
        # timestamp sempre no UTC em string igual ao backend
        ts = datetime.utcnow().strftime("(%a, %d %b %Y %H:%M:%S GMT)")

        # # eco local antes de enviar (sensação de instantâneo)
        st.session_state["messages"].setdefault(st.session_state["roomWithFriend"], []).append(
            {"sender": username, "timestamp": ts, "text": msg}
        )

        # envia (usa a chave de sessão do room, já criada no teu fluxo)
        try:
            send_message(username, userToTalk, msg, st.session_state["roomWithFriend"], ts)
        except KeyError:
            # sem chave de sessão para esse room
            st.error("Sem chave de sessão para este chat. Aguarde o pareamento.")
            # remove eco local se quiser
        except Exception as e:
            st.error(f"Falha ao enviar: {e}")
    else:
        st.error("Mensagem vazia.")

if buttonBack:
    st.chat_message(f"\n{ts} You: {"conversa tá uma merda kkkkk. Vou dar o fora."}")
    sleep(5)
    leave_room(st.session_state["roomWithFriend"])
    st.switch_page("mainMenu.py")

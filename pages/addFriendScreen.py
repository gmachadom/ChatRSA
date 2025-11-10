import streamlit as st
from client.client import *

st.header("Add friend")

# Esconde o menu padrão
hide_sidebar_style = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""

st.markdown(hide_sidebar_style, unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Menu")
    if st.button("Main Menu"):
        st.switch_page("pages/mainMenu.py")
    if st.button("Chat with friend"):
        st.switch_page("pages/chatWithFriendMenuScreen.py")
    if st.button("Chat with group"):
        st.switch_page("pages/groupChatMenuScreen.py")

all_users = get_all_users()
if isinstance(all_users, tuple):
    ok, all_users = all_users
    if not ok:
        st.error(all_users)
        st.stop()
    else:
        all_users = all_users

username = st.session_state.get("username")

ok, friend_list = get_friend_list(username)
if not ok:
    st.error(friend_list)
    st.stop()
friend_list = friend_list or []

all_users_set = set(all_users) - {username}
all_users_available = list(set(all_users_set) - set(friend_list))

if all_users_available:
    st.write("All users:")
    for u in all_users_available:
        st.write(f"- {u}")
else:
    st.info("No users available to add")

st.markdown("---")

# Add friend
with st.form("add_friend_form", clear_on_submit=True):
    user_to_add = st.text_input("Username:")
    submitted_add = st.form_submit_button("Add friend")

if submitted_add:
    ok, msg = add_user_in_friendlist(username, user_to_add)
    if ok:
        st.success(msg)
    else:
        st.error(msg)

st.markdown("---")

buttonChatWithFriend = st.button("Start a chat with Friend", use_container_width=True)
if buttonChatWithFriend:
    st.switch_page("pages/chatWithFriendMenuScreen.py")

buttonChatWithGroup = st.button("Start a chat with group", use_container_width=True)
if buttonChatWithGroup:
    st.switch_page("pages/groupChatMenuScreen.py")
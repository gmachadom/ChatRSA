import streamlit as st

from client.client import get_friend_list

st.header("Group Chat")

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
    if st.button("Add a friend"):
        st.switch_page("pages/addFriendScreen.py")
    if st.button("Chat with friend"):
        st.switch_page("pages/chatWithFriendMenuScreen.py")

username = st.session_state["username"]

ok, friend_list = get_friend_list(username)

group_users = st.multiselect("Create your group chat.", friend_list)
buttonStartGroupChat = st.button("Start Group Chat")

if buttonStartGroupChat:
    room = f"room_{'_'.join(sorted([username, *group_users]))}"

    st.session_state["roomGroup"] = room
    st.session_state["listToAddInGroup"] = group_users

    st.success("Group Chat created successfully")
    st.switch_page("pages/chatGroupScreen.py")
# else:
#     st.error("Error creating group chat")
#     st.switch_page("pages/addFriendScreen.py")

import streamlit as st

username = st.session_state["username"]

st.header("Main Menu")

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
    if st.button("Add a friend"):
        st.switch_page("pages/addFriendScreen.py")
    if st.button("Chat with friend"):
        st.switch_page("pages/chatWithFriendMenuScreen.py")
    if st.button("Chat with group"):
        st.switch_page("pages/groupChatMenuScreen.py")
    if st.button("Log Out"):
        st.switch_page("pages/loginScreen.py")

st.write("# What will be your next step?")

buttonAddFriend = st.button("add friend")

if buttonAddFriend:
    st.switch_page("pages/addFriendScreen.py")

buttonChatWithFriend = st.button("Chat with a friend")
if buttonChatWithFriend:
    st.switch_page("pages/chatWithFriendMenuScreen.py")

buttonGroup = st.button("Group chat")
if buttonGroup:
    st.switch_page("pages/groupChatMenuScreen.py")
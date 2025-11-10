import streamlit as st


st.header("Main Menu")

st.write("# What will be your next step?")

buttonAddFriend = st.button("add friend")

if buttonAddFriend:
    st.switch_page("pages/addFriendScreen.py")

buttonChatWithFriend = st.button("Chat with a friend")
if buttonChatWithFriend:
    st.switch_page("pages/chatWithFriendMenuScreen.py")

buttonGroup = st.button("Group chat")
if buttonGroup:
    st.switch_page("pages/groupChatScreen.py")
import streamlit as st
import time

from client.client import get_friend_list, is_user_in_friendlist

st.header("Chat with Friend")

username = st.session_state.get("username")

with st.spinner("Loading your friends..."):
    ok, result = get_friend_list(username)

st.write("Friends List:")

if not ok:
    st.error(result)
else:
    friend_list = result
    if friend_list:
        for friend in friend_list:
            st.write(f"- {friend}")
    else:
        st.info("You don't have any friends yet.")
        if st.button("Add a friend"):
            st.switch_page("pages/addFriendScreen.py")


st.markdown("---")

with st.form("initiate_user_form"):
    st.session_state["userToTalk"] = st.text_input("User to Talk")
    submitted = st.form_submit_button("Start chat")

if submitted:

    if not is_user_in_friendlist(username, st.session_state["userToTalk"]):
        st.error("User not found.")
        time.sleep(2)
        st.rerun()

    st.session_state["roomWithFriend"] = f"room_{'_'.join(sorted([username, st.session_state["userToTalk"]]))}"

    st.switch_page("pages/chatScreen.py")
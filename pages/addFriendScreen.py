import streamlit as st
import sys
import os
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from client.client import (
    get_all_users,
    get_friend_list,
    send_friend_request
)

# Esconde o menu padrão
hide_sidebar_style = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""

st.markdown(hide_sidebar_style, unsafe_allow_html=True)

username = st.session_state.get("username")

if not username:
    st.error("Please log in first")
    st.switch_page("pages/loginScreen.py")

st.header("➕ Send Friend Request")

# Get all users
all_users = get_all_users()
if isinstance(all_users, tuple):
    ok, all_users = all_users
    if not ok:
        st.error("Error retrieving users")
        all_users = []

# Get friend list
ok, friend_list = get_friend_list(username)
if not ok:
    st.error("Error retrieving friend list")
    friend_list = []

friend_list = friend_list or []

# Calculate available users (not self, not already friend)
all_users_set = set(all_users) - {username} if all_users else set()
all_users_available = list(set(all_users_set) - set(friend_list))

if all_users_available:
    st.write(f"**{len(all_users_available)} user(s) available:**")
    for u in all_users_available:
        st.write(f"• {u}")
else:
    st.info("No users available to add (you're already friends with everyone or no other users exist)")

st.divider()

# Send friend request
with st.form("send_request_form", clear_on_submit=True):
    user_to_add = st.text_input("Enter username:")
    submitted = st.form_submit_button("Send Friend Request")

if submitted:
    if not user_to_add:
        st.error("Please enter a username")
    else:
        ok, msg = send_friend_request(username, user_to_add)
        if ok:
            st.success(msg)
            time.sleep(1)
            st.rerun()
        else:
            st.error(msg)

st.divider()

# Navigation
col1, col2 = st.columns(2)
with col1:
    if st.button("← Back to Menu", use_container_width=True):
        st.switch_page("pages/mainMenu.py")

with col2:
    if st.button("👥 View Requests", use_container_width=True):
        st.switch_page("pages/friendRequestsScreen.py")

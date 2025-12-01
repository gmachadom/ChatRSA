import streamlit as st
import sys
import os
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from client.client import (
    get_pending_friend_requests,
    accept_friend_request,
    reject_friend_request,
    get_friend_list
)
from logger_config import log_debug, log_friend_request_accepted, log_friend_request_rejected

# Esconde o menu padrão
hide_sidebar_style = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""

st.markdown(hide_sidebar_style, unsafe_allow_html=True)

username = st.session_state.get("username")

if not username:
    log_debug("Tentativa de acessar friend requests sem login", "friendRequestsScreen.py", "page_load")
    st.error("Please log in first")
    st.switch_page("pages/loginScreen.py")

st.header("🤝 Friend Requests")

# Refresh button
if st.button("🔄 Refresh", use_container_width=True):
    log_debug(f"Página de friend requests recarregada", "friendRequestsScreen.py", "refresh")
    st.rerun()

# Get pending friend requests
ok, requests_data = get_pending_friend_requests(username)

if not ok:
    st.warning("Unable to load friend requests")
else:
    if not requests_data:
        st.info("No pending friend requests")
    else:
        st.write(f"**{len(requests_data)} pending request(s):**")
        st.divider()

        for req in requests_data:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"👤 **{req['sender_username']}** sent you a friend request")
                st.caption(f"Sent: {req['created_at']}")
            
            with col2:
                if st.button("✅ Accept", key=f"accept_{req['request_id']}", use_container_width=True):
                    ok, msg = accept_friend_request(req['request_id'])
                    if ok:
                        log_friend_request_accepted(req['sender_username'], username, "friendRequestsScreen.py", "accept_button")
                        st.success("Friend request accepted!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")
            
            with col3:
                if st.button("❌ Reject", key=f"reject_{req['request_id']}", use_container_width=True):
                    ok, msg = reject_friend_request(req['request_id'])
                    if ok:
                        log_friend_request_rejected(req['sender_username'], username, "friendRequestsScreen.py", "reject_button")
                        st.success("Friend request rejected!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")
            
            st.divider()

# Show current friends
st.subheader("👥 Your Friends")

ok, friends = get_friend_list(username)
if ok and friends:
    for friend in friends:
        st.write(f"• {friend}")
else:
    st.info("You have no friends yet")

# Navigation
st.divider()
if st.button("← Back to Menu", use_container_width=True):
    st.switch_page("pages/mainMenu.py")

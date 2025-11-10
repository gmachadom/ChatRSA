import streamlit as st
import time
import sys, os

# Esconde o menu padrão
hide_sidebar_style = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""

st.markdown(hide_sidebar_style, unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Menu")
    st.write("Sign in to access the side menu options")

import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from client.client import login_user, main_menu

st.header("Login")

with st.form("login_form"):
    username = st.text_input("username")
    password = st.text_input("password", type="password")
    submitted = st.form_submit_button("Login")

if submitted:
    ok, msg = login_user(username, password)
    if ok:
        st.success(msg)
        time.sleep(2)
        st.session_state["username"] = username
        st.switch_page("pages/mainMenu.py")
    else:
        st.error(msg)


login_btn = st.button("I don't have an account", use_container_width=True)

if login_btn:
    st.switch_page("pages/RegistrationScreen.py")
import streamlit as st
import time
import sys, os

from streamlit import popover

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
from logger_config import log_debug

st.header("Login")

with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    code = st.text_input("Code")
    submitted = st.form_submit_button("Login")

if submitted:
    log_debug(f"Formulário de login submetido - Username: {username}", "loginScreen.py", "form_submit")
    ok, msg = login_user(username, password, code)
    if ok:
        st.success(msg)
        log_debug(f"Login bem-sucedido - Redirecionando para menu principal", "loginScreen.py", "login_success")
        time.sleep(2)
        st.session_state["username"] = username
        st.switch_page("pages/mainMenu.py")
    else:
        log_debug(f"Erro no login - {msg}", "loginScreen.py", "login_error")
        st.error(msg)


login_btn = st.button("I don't have an account", use_container_width=True)

if login_btn:
    st.switch_page("pages/RegistrationScreen.py")
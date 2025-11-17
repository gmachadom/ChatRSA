import time

import streamlit as st
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
    st.write("Sign up to access the side menu options")

import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from client.client import register_user
from logger_config import log_debug

st.header("Register")

with st.form("register_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Register")

if submitted:
    log_debug(f"Formulário de registro submetido - Username: {username}", "registrationScreen.py", "form_submit")
    ok, msg = register_user(username, password)
    if ok:
        st.success(msg)
        log_debug(f"Registro bem-sucedido - Redirecionando para login", "registrationScreen.py", "register_success")
        time.sleep(2)
        st.switch_page("pages/loginScreen.py")
    else:
        log_debug(f"Erro no registro - {msg}", "registrationScreen.py", "register_error")
        st.error(msg)

login_btn = st.button("I already have an account", use_container_width=True)

if login_btn:
    st.switch_page("pages/loginScreen.py")
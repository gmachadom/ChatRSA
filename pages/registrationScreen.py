import time

import pyotp
import qrcode
import streamlit as st
import sys, os

from streamlit import popover

from client.client import register_user

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

from logger_config import log_debug

st.header("Register")

with st.form("register_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Register")

    st.session_state["username"] = username
    st.session_state["password"] = password

if submitted:
    log_debug(f"Formulário de registro submetido - Username: {username}", "registrationScreen.py", "form_submit")
    st.switch_page("pages/qrcodeScreen.py")

login_btn = st.button("I already have an account", use_container_width=True)

if login_btn:
    st.switch_page("pages/loginScreen.py")
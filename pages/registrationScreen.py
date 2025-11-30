import re
import time

import pyotp
import qrcode
import streamlit as st
import sys, os

from streamlit import popover

from client.client import register_user


def validate_password(pw):
    errors = []

    valid_symbols = r"!@#$%^&*()\-_=+{}[\]|;:<>,.?/"

    if not (6 <= len(pw) <= 20):
        errors.append("Your password must be between 6 and 20 characters long")

    if " " in pw:
        errors.append("Your password must not contain any space")

    if not re.search("[a-z]", pw):
        errors.append("Your password must contain at least one lowercase letter")

    if not re.search("[A-Z]", pw):
        errors.append("Your password must contain at least one uppercase letter")

    if not re.search("[0-9]", pw):
        errors.append("Your password must contain at least one number")

    if not re.search(f"[{re.escape(valid_symbols)}]", pw):
        errors.append("Your password must contain at least one of the following symbols:\n\t!@#$%^&*()\\-_=+{}[]|;:<>,.?/")

    contains_invalid_characters = re.search(r"[^A-Za-z0-9" + re.escape(valid_symbols) + "]", pw.replace(" ", ""))
    if contains_invalid_characters:
        errors.append(f"Your password contains invalid characters: {contains_invalid_characters.group()}")

    return not errors, errors


def validate_username(un):
    errors = []
    valid_symbols = r"^[A-Za-z0-9._-]+$"

    if " " in un:
        errors.append("Your username must not contain any space")

    if not (4 <= len(un) <= 20):
        errors.append("Your username must be between 4 and 20 characters long")

    if not re.match(valid_symbols, un.replace(" ", "")):
        errors.append("Your username must contain only letters, numbers, underscores (_), dashes (-) and dots (.)")

    return not errors, errors


def show_errors(un, pw):
    error_message = ""
    if un:
        for e in un:
            error_message += f"- {e}\n"
    if pw:
        if error_message:
            error_message += f"\n"
        for e in pw:
            error_message += f"- {e}\n"

    return error_message


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

if submitted:
    un_ok, un_errors = validate_username(username)
    pw_ok, pw_errors = validate_password(password)

    if un_ok and pw_ok:
        st.session_state["username"] = username
        st.session_state["password"] = password
        log_debug(f"Formulário de registro submetido - Username: {username}", "registrationScreen.py", "form_submit")
        st.switch_page("pages/qrcodeScreen.py")
    else:
        st.warning(show_errors(un_errors, pw_errors))


login_btn = st.button("I already have an account", use_container_width=True)

if login_btn:
    st.switch_page("pages/loginScreen.py")
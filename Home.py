from flask_socketio import leave_room
from datetime import datetime, timedelta

import logging
import os
import requests
import socketio
import sys
import streamlit as st
from streamlit import switch_page

from client.client import *

global global_private_key
session_keys = {}
public_keys = {}


# Esconde o menu padrão
hide_sidebar_style = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""

st.markdown(hide_sidebar_style, unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Menu")
    st.write("Sign in or sign up to access the side menu options")

url = "http://127.0.0.1:5000/"

st.set_page_config(page_title="ChatAPP")

st.title("💬 ChatAPP")

st.markdown("Welcome to ChatAPP - your safety chat with end to end encrypt!")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.write("")  # espaço
    st.write("Choose one option:")
    login_btn = st.button("🔐 Login", use_container_width=True)
    register_btn = st.button("📝 Register", use_container_width=True)

if login_btn:
    st.switch_page("pages/loginScreen.py")

if register_btn:
    st.switch_page("pages/registrationScreen.py")
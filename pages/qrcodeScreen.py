import json
import time
from datetime import datetime

import pyotp
import qrcode
import streamlit as st
from flask import jsonify

from client.client import register_user
from logger_config import log_debug, log_error

st.header("Scan your QR Code")
master_key = st.session_state.get("master_key") or pyotp.random_base32()

st.session_state["master_key"] = master_key
link = pyotp.TOTP(master_key).provisioning_uri(name=st.session_state["username"], issuer_name="RSApp")
new_qrcode = qrcode.make(link)
new_qrcode.save("qrcode.png")
st.image('./qrcode.png', use_column_width=True)

st.title("Confirm that you scanned the qrcode and try to put your code here.")
code = pyotp.TOTP(master_key)

with st.form("register_form"):
    auth_code = st.text_input("Auth Code")
    submitted = st.form_submit_button("Done")

if code.now() != auth_code:
    submitted = False

object_master_key = json.dumps({'master_key': master_key, 'timestamp': datetime.now()})

if submitted:
    ok, msg = register_user(st.session_state["username"], st.session_state["password"], object_master_key)
    if ok:
        st.success(msg)
        log_debug(f"Registro bem-sucedido - Redirecionando para login", "registrationScreen.py", "register_success")
        time.sleep(2)
        del st.session_state["master_key"]
        st.switch_page("pages/loginScreen.py")
    else:
        log_debug(f"Erro no registro - {msg}", "registrationScreen.py", "register_error")
        st.error(msg)
"""Streamlit interface for a synchronized, read-only XRP/USDT review."""

import hmac
import zipfile

import requests
import streamlit as st
from nacl.exceptions import CryptoError

from run_now import check_result, dispatch


st.set_page_config(page_title="XRP/USDT · Consulta", page_icon="📊", layout="centered")
st.title("📊 Consulta XRP/USDT")
st.write("Consulta tu cuenta de Quantfury y las velas de Binance. El resultado aparecerá aquí.")
st.caption("La consulta no compra, vende ni mueve fondos. Las operaciones se realizan manualmente.")

try:
    token = st.secrets.get("GH_WORKFLOW_DISPATCH_TOKEN", "")
    password = st.secrets.get("APP_ACTION_PASSWORD", "")
except FileNotFoundError:
    token = password = ""

if not token or not password:
    st.error("Falta configurar la clave y el token de GitHub en Streamlit.")
else:
    entered = st.text_input("Clave para ejecutar la consulta", type="password")
    if st.button("▶️ Ejecutar todo ahora", use_container_width=True):
        if not hmac.compare_digest(entered, password):
            st.error("Clave incorrecta.")
        else:
            try:
                st.session_state.request_id = dispatch(token)
                st.session_state.result = None
            except (requests.RequestException, RuntimeError):
                st.error("GitHub no aceptó la consulta. Comprueba el permiso Actions: write del token.")

    @st.fragment(run_every="5s")
    def show_result():
        if not st.session_state.get("request_id"):
            return
        if st.session_state.get("result") is not None:
            st.text(st.session_state.result)
            return
        try:
            state, message, url = check_result(token, st.session_state.request_id, password)
        except CryptoError:
            st.error("La clave de APP_RESULT_PASSWORD en GitHub no coincide con APP_ACTION_PASSWORD en Streamlit.")
            return
        except requests.HTTPError as error:
            status = error.response.status_code if error.response is not None else "desconocido"
            st.error(f"GitHub impidió leer el resultado (HTTP {status}). Comprueba que el token de Streamlit tenga Actions: read and write.")
            return
        except requests.RequestException:
            st.error("No se pudo conectar con GitHub para recuperar el resultado. Vuelve a intentarlo.")
            return
        except (ValueError, zipfile.BadZipFile):
            st.error("El archivo de resultado recibido no tiene el formato esperado.")
            return
        if state == "pending":
            st.info(message)
        elif state == "failed":
            st.error(message)
        else:
            st.session_state.result = message
            st.text(message)
        if url:
            st.link_button("Ver esta ejecución en GitHub", url)

    show_result()

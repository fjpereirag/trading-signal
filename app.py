"""One-click read-only XRP/USDT review through GitHub Actions."""

import hmac

import requests
import streamlit as st

from run_now import dispatch


st.set_page_config(page_title="XRP/USDT · Consulta", page_icon="📊", layout="centered")
st.title("📊 Consulta XRP/USDT")
st.write("Consulta la cuenta de Quantfury y el mercado de Binance. Recibirás el resultado en Telegram.")
st.caption("La consulta no compra, vende ni mueve fondos. Las operaciones se realizan manualmente.")

try:
    dispatch_token = st.secrets.get("GH_WORKFLOW_DISPATCH_TOKEN", "")
    access_password = st.secrets.get("APP_ACTION_PASSWORD", "")
except FileNotFoundError:
    dispatch_token = access_password = ""

if dispatch_token and access_password:
    entered_password = st.text_input("Clave para ejecutar la consulta", type="password")
    if st.button("▶️ Ejecutar todo ahora", use_container_width=True):
        if not hmac.compare_digest(entered_password, access_password):
            st.error("Clave incorrecta.")
        else:
            try:
                dispatch(dispatch_token)
            except requests.RequestException:
                st.error("GitHub no aceptó la solicitud. Comprueba el token de Streamlit y su permiso Actions: write.")
            else:
                st.success("Consulta iniciada. Comprueba Telegram al finalizar la ejecución.")
else:
    st.warning("Falta configurar el botón directo en los secretos de Streamlit.")
    st.link_button(
        "Abrir ejecución manual en GitHub",
        "https://github.com/fjpereirag/trading-signal/actions/workflows/main.yml",
        use_container_width=True,
    )

st.link_button(
    "Ver estado de las consultas",
    "https://github.com/fjpereirag/trading-signal/actions/workflows/main.yml",
    use_container_width=True,
)

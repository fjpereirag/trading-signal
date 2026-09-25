"""Streamlit interface for synchronized, read-only trading plans."""

import hmac
import json
import zipfile

import requests
import streamlit as st
from nacl.exceptions import CryptoError

from run_now import check_result, dispatch


st.set_page_config(page_title="Objetivos de trading", page_icon="📊", layout="wide")
st.title("📊 Objetivos de trading")
st.write("Consulta la cuenta de Quantfury y velas cerradas de AVGO, ETH y SOL.")
st.caption("Plan simulado: +50 $ / −50 $ por operación. Esta app no envía órdenes.")


def show_dashboard(message):
    try:
        data = json.loads(message)
    except (ValueError, TypeError):
        st.text(message)
        return
    if data.get("type") != "opportunities-v1":
        st.error("El resultado no tiene el formato esperado.")
        return
    st.caption(f"Consulta generada: {data['generated']} · Cada precio muestra su propia hora de observación.")
    a, b, c = st.columns(3)
    a.metric("Saldo de trading", f"{data['balance']:.2f} {data['currency']}")
    b.metric("Poder disponible", f"{data['power']:.2f} $")
    c.metric("Posiciones abiertas", data["positions"])
    st.warning(f"Una pérdida prevista de 50 $ equivale al {data['risk_pct']:.1f}% del saldo. "
               "Los saltos de precio pueden causar una pérdida superior.")
    rows = []
    for plan in data["plans"]:
        rows.append({"Activo": plan["asset"], "Último cierre (USD)": plan["price"],
                     "Hora de la vela (UTC)": plan["observed"], "Zona": plan["reference"],
                     "Estado": plan["status"], "Cantidad orientativa": plan["quantity"],
                     "Exposición (USD)": plan["exposure"],
                     "Movimiento para ±50 $": plan["target_move"]})
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption("La señal técnica requiere dos velas cerradas sobre la zona, retroceso y recuperación. "
               "La cantidad y el movimiento son estimaciones con precios públicos. Antes de una operación "
               "real habría que verificar compra, venta, spread, stop, tamaño admitido y la posición en Quantfury.")

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
            show_dashboard(st.session_state.result)
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
            show_dashboard(message)
        if url:
            st.link_button("Ver esta ejecución en GitHub", url)

    show_result()

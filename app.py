import streamlit as st
from market import get_timeframes
from strategy_mobile import analyze, trade_plan
import json
from pathlib import Path
from datetime import datetime
import requests


def get_telegram_chat_id():
    try:
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        data = requests.get(url, timeout=10).json()

        if data.get("ok") and data.get("result"):
            return data["result"][-1]["message"]["chat"]["id"]
    except Exception:
        pass

    return None

st.set_page_config(page_title="Trading Signal V3.1", page_icon="📈", layout="centered")

st.markdown("""
<style>
.block-container {max-width:480px; padding-top:1.2rem; padding-bottom:2rem;}
.signal {
    border:1px solid #ddd; border-radius:24px; padding:28px 12px;
    text-align:center; font-size:2.15rem; font-weight:800; margin:18px 0 12px 0;
}
.card {border:1px solid #ddd; border-radius:18px; padding:16px; margin:12px 0;}
.small {opacity:.72; font-size:.92rem;}
</style>
""", unsafe_allow_html=True)

cfg_path = Path(__file__).with_name("config.json")
with open(cfg_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

st.title("📈 Trading Signal V3.1")
st.caption("M15 tendencia · M5 confirmación · M1 gatillo · filtros de calidad")

assets = {
    "Bitcoin · BTC/USD": "BTC-USD",
    "Ethereum · ETH/USD": "ETH-USD",
    "EUR/USD": "EURUSD=X",
    "Apple · AAPL": "AAPL",
    "Microsoft · MSFT": "MSFT",
}
asset_name = st.selectbox("Activo", list(assets.keys()))
symbol = assets[asset_name]

with st.expander("⚙️ Ajustes de riesgo"):
    balance = st.number_input("Capital de referencia", min_value=1.0, value=float(cfg.get("balance", 1000)))
    risk_pct = st.number_input("Riesgo máximo por operación (%)", min_value=0.1, max_value=10.0,
                               value=float(cfg.get("risk_pct", 1.0)), step=0.1)
    sl_pct = st.number_input("Stop Loss (%)", min_value=0.1, max_value=20.0,
                             value=float(cfg.get("sl_pct", 1.0)), step=0.1)
    tp_pct = st.number_input("Take Profit (%)", min_value=0.1, max_value=50.0,
                             value=float(cfg.get("tp_pct", 2.0)), step=0.1)

st.button("🔄 ACTUALIZAR", use_container_width=True)

try:
    tfs = get_timeframes(symbol)
    result = analyze(tfs, cfg)

    score = int(result.get("score", 0))
    raw_side = result.get("side", "WAIT")
    quality = result.get("quality", "BAJA")

    # Señal principal: nunca mostrar COMPRAR/VENDER si no existe entrada completa válida.
    operative = raw_side if score == 3 and raw_side in ("BUY", "SELL") and quality != "BAJA" else "WAIT"

    if operative == "BUY":
        label, icon = "COMPRAR", "🟢"
    elif operative == "SELL":
        label, icon = "VENDER", "🔴"
    else:
        label, icon = "ESPERAR", "🟡"

    st.markdown(f'<div class="signal">{icon} {label}</div>', unsafe_allow_html=True)

    if score == 3:
        st.markdown(f"### Calidad técnica: {quality}")
    else:
        st.markdown("### Calidad técnica: —")

    price = float(result.get("price", tfs["M1"]["Close"].iloc[-1]))
    c1, c2 = st.columns(2)
    c1.metric("Precio externo", f"{price:,.4f}")
    c2.metric("Reglas", f"{score}/3")

    direction = result.get("direction", result.get("trend", "WAIT"))
    trend_ok = bool(result.get("trend_ok", score >= 1))
    confirm_ok = bool(result.get("confirm_ok", False))
    trigger_ok = bool(result.get("trigger_ok", False))

    dir_txt = {"BUY":"Compradora", "SELL":"Vendedora", "WAIT":"Sin tendencia clara"}.get(direction, str(direction))
    st.markdown(f'<div class="card"><b>M15 · Tendencia</b><br>{"✅" if trend_ok else "⏳"} {dir_txt}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="card"><b>M5 · Confirmación</b><br>{"✅ Confirmada" if confirm_ok else "⏳ Pendiente"}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="card"><b>M1 · Gatillo de entrada</b><br>{"✅ Activado" if trigger_ok else "⏳ Pendiente"}</div>',
                unsafe_allow_html=True)

    if operative in ("BUY", "SELL"):
        plan = trade_plan(price, operative, balance, risk_pct, sl_pct, tp_pct)
        st.success("Señal completa 3/3 y filtros técnicos aceptados.")
        a, b = st.columns(2)
        a.metric("Entrada ref.", f"{plan['entry']:,.4f}")
        b.metric("Riesgo máx.", f"{plan['max_risk_cash']:,.2f}")
        a.metric("Stop Loss", f"{plan['stop']:,.4f}")
        b.metric("Take Profit", f"{plan['target']:,.4f}")
        rr = tp_pct / sl_pct if sl_pct else 0
        st.metric("Riesgo / beneficio", f"1 : {rr:.2f}")
    else:
        missing = []
        if not trend_ok: missing.append("tendencia M15")
        if not confirm_ok: missing.append("confirmación M5")
        if not trigger_ok: missing.append("gatillo M1")
        if score == 3 and quality == "BAJA":
            missing.append("filtros de calidad")
        msg = " · ".join(missing) if missing else "faltan condiciones de entrada"
        st.info(f"Sin operación: {msg}.")
        if direction in ("BUY", "SELL"):
            st.caption("Sesgo técnico actual: " + ("comprador" if direction == "BUY" else "vendedor") +
                       ". No es una orden de entrada.")

    with st.expander("🔎 ¿Por qué esta señal?"):
        st.write(result.get("reason", ""))
        filters = result.get("filters", {})
        if filters:
            for name, passed in filters.items():
                st.write(("✅ " if passed else "❌ ") + str(name))
        metrics = result.get("metrics", {})
        if metrics:
            st.write(metrics)
        st.caption("ALTA/MEDIA/BAJA clasifica las condiciones técnicas; no es una probabilidad de beneficio.")

    st.caption("Última consulta: " + datetime.now().strftime("%H:%M:%S"))
    st.caption("No conecta con Quantfury ni envía órdenes. El precio externo puede diferir del precio de ejecución.")

except Exception as e:
    st.error("No se pudieron obtener o analizar los datos.")
    st.exception(e)

chat_id = get_telegram_chat_id()

if chat_id:
    st.success(f"Telegram conectado · Chat ID: {chat_id}")
else:
    st.warning("Telegram todavía no conectado. Envía /start al bot.")

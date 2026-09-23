import streamlit as st
from market import get_timeframes
from strategy_mobile import analyze, trade_plan, risk_guard
import json
from pathlib import Path
from datetime import datetime
import requests


# ============================================================
# TELEGRAM
# ============================================================

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


# ============================================================
# CONFIGURACION
# ============================================================

st.set_page_config(
    page_title="Trading Signal V4",
    page_icon="📈",
    layout="centered"
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 480px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    .signal {
        border: 1px solid #ddd;
        border-radius: 24px;
        padding: 28px 12px;
        text-align: center;
        font-size: 2.15rem;
        font-weight: 800;
        margin: 18px 0 12px 0;
    }

    .card {
        border: 1px solid #ddd;
        border-radius: 18px;
        padding: 16px;
        margin: 12px 0;
    }

    .v4-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .small {
        opacity: 0.72;
        font-size: 0.90rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CARGAR CONFIG
# ============================================================

CONFIG_PATH = Path(__file__).with_name("config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    cfg = json.load(f)


# ============================================================
# ACTIVOS
# ============================================================

ASSETS = {
    "Bitcoin · BTC/USD": "BTC-USD",
    "Ethereum · ETH/USD": "ETH-USD",
    "EUR/USD": "EURUSD=X",
    "Apple · AAPL": "AAPL",
    "Microsoft · MSFT": "MSFT"
}


# ============================================================
# CABECERA
# ============================================================

st.title("📈 Trading Signal V4")

st.caption(
    "Contexto · zonas de valor · retrocesos · "
    "M15 tendencia · M5 confirmación · M1 gatillo"
)

asset_name = st.selectbox(
    "Activo",
    list(ASSETS.keys())
)

symbol = ASSETS[asset_name]


# ============================================================
# AJUSTES DE RIESGO
# ============================================================

with st.expander("⚙️ Ajustes de riesgo"):

    balance = st.number_input(
        "Capital de referencia",
        min_value=0.0,
        value=1000.0,
        step=100.0
    )

    risk_pct = st.number_input(
        "Riesgo máximo por operación (%)",
        min_value=0.1,
        max_value=10.0,
        value=1.0,
        step=0.1
    )

    sl_pct = st.number_input(
        "Stop de referencia (%)",
        min_value=0.1,
        max_value=20.0,
        value=1.0,
        step=0.1
    )

    tp_pct = st.number_input(
        "Objetivo de referencia (%)",
        min_value=0.1,
        max_value=50.0,
        value=2.0,
        step=0.1
    )

    exposure_pct = st.number_input(
        "Exposición actual (%)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=1.0
    )

    max_exposure_pct = st.number_input(
        "Exposición máxima permitida (%)",
        min_value=1.0,
        max_value=100.0,
        value=30.0,
        step=1.0
    )

    free_margin = st.number_input(
        "Margen libre",
        min_value=0.0,
        value=1000.0,
        step=100.0
    )


# ============================================================
# ACTUALIZAR
# ============================================================

refresh = st.button(
    "🔄 ACTUALIZAR",
    use_container_width=True
)


# ============================================================
# ANALISIS
# ============================================================

try:

    tfs = get_timeframes(symbol)

    result = analyze(tfs, cfg)

    price = result["price"]
    signal = result["signal"]
    quality = result["quality"]

    context = result.get("context", "—")
    zone = result.get("zone", "—")
    pullback = result.get("pullback", "—")
    action = result.get("action", "ESPERAR")

    risk = risk_guard(
        balance=balance,
        free_margin=free_margin,
        exposure_pct=exposure_pct,
        max_exposure_pct=max_exposure_pct
    )

    # --------------------------------------------------------
    # BLOQUEO DE SEGURIDAD
    # --------------------------------------------------------

    final_action = action

    if risk["block_buys"] and (
        "COMPRA" in final_action
        or signal == "BUY"
    ):
        final_action = "COMPRA BLOQUEADA"

    # --------------------------------------------------------
    # SEÑAL PRINCIPAL
    # --------------------------------------------------------

    if signal == "BUY":
        signal_text = "🟢 COMPRA"

    elif signal == "SELL":
        signal_text = "🔴 VENTA"

    else:
        signal_text = "🟡 ESPERAR"

    st.markdown(
        f'<div class="signal">{signal_text}</div>',
        unsafe_allow_html=True
    )

    if signal == "WAIT":
        st.subheader("Calidad técnica: —")
    else:
        st.subheader(f"Calidad técnica: {quality}")

    st.metric(
        "Precio externo",
        f"{price:,.2f}"
    )


    # ========================================================
    # MOTOR V4
    # ========================================================

    st.markdown("### 🧭 Motor V4")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Contexto",
            context
        )

        st.metric(
            "Retroceso",
            pullback
        )

    with col2:
        st.metric(
            "Zona",
            zone
        )

        st.metric(
            "Reglas",
            f'{result["score"]}/3'
        )


    # ========================================================
    # ACCION
    # ========================================================

    st.markdown(
        f"""
        <div class="card">
            <div class="v4-title">🎯 ACCIÓN V4</div>
            <div style="font-size:1.35rem;font-weight:800;">
                {final_action.replace("_", " ")}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # RIESGO
    # ========================================================

    risk_icon = "🟢" if risk["safe"] else "🔴"

    st.markdown(
        f"""
        <div class="card">
            <div class="v4-title">🛡️ Protección de riesgo</div>
            <b>{risk_icon} {risk["message"]}</b><br>
            Exposición: {exposure_pct:.1f}% /
            máximo {max_exposure_pct:.1f}%<br>
            Margen libre: {free_margin:,.2f}
        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # M15 / M5 / M1
    # ========================================================

    st.markdown("### 🔎 Confirmación técnica")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "M15",
            result["trend"]
        )

    with c2:
        st.metric(
            "M5",
            "OK" if result["confirm"] else "NO"
        )

    with c3:
        st.metric(
            "M1",
            "OK" if result["trigger"] else "NO"
        )


    # ========================================================
    # PLAN DE OPERACION
    # ========================================================

    if signal in ("BUY", "SELL") and not risk["block_buys"]:

        plan = trade_plan(
            price,
            signal,
            balance,
            risk_pct,
            sl_pct,
            tp_pct
        )

        st.markdown("### 📋 Plan de referencia")

        st.write(
            f"**Entrada de referencia:** "
            f"{price:,.2f}"
        )

        st.write(
            f"**Stop de referencia:** "
            f"{plan['stop']:,.2f}"
        )

        st.write(
            f"**Objetivo de referencia:** "
            f"{plan['target']:,.2f}"
        )

        st.write(
            f"**Riesgo máximo:** "
            f"{plan['risk_cash']:,.2f}"
        )


    # ========================================================
    # FILTROS
    # ========================================================

    with st.expander("🔬 Filtros técnicos"):

        filters = result["filters"]

        st.write(
            "EMA:",
            "✅" if filters["ema"] else "❌"
        )

        st.write(
            "RSI:",
            "✅" if filters["rsi"] else "❌"
        )

        st.write(
            "Momentum:",
            "✅" if filters["momentum"] else "❌"
        )

        st.write(
            "Volatilidad ATR:",
            "✅" if filters["atr"] else "❌"
        )


    # ========================================================
    # MOTIVO
    # ========================================================

    with st.expander("ℹ️ Motivo de la decisión"):
        st.write(result["reason"])


    # ========================================================
    # TELEGRAM
    # ========================================================

    chat_id = get_telegram_chat_id()

    if chat_id:
        st.caption(
            f"📨 Telegram conectado · Chat ID: {chat_id}"
        )
    else:
        st.caption(
            "📨 Telegram: esperando conexión"
        )


    # ========================================================
    # FECHA
    # ========================================================

    st.caption(
        "Última consulta: "
        + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )

    st.caption(
        "V4 funciona actualmente en modo análisis/simulación. "
        "No ejecuta órdenes reales."
    )


# ============================================================
# ERROR
# ============================================================

except Exception as e:

    st.error(
        "No se pudo completar el análisis."
    )

    st.exception(e)

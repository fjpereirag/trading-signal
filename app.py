import streamlit as st
from market import get_timeframes
from strategy_mobile import analyze, position_review
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
    "XRP · XRP/USD": "XRP-USD",
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
        value=500.0,
        step=100.0
    )

    max_exposure_pct = st.number_input(
        "Límite de exposición para simulación (%) · ajustable",
        min_value=1.0,
        max_value=100.0,
        value=30.0,
        step=1.0
    )

st.markdown("### 🛡️ Posición Quantfury · datos manuales")
st.caption("Referencia: capturas del 23/09/2026. Actualiza cada cifra antes de usar esta evaluación; no hay conexión con Quantfury.")
trading_balance = st.number_input("Saldo de la cuenta de trading (USD)", min_value=0.0, value=212.83, step=10.0)
trading_power = st.number_input("Poder de trading total (USD)", min_value=1.0, value=10000.0, step=100.0)
allocated_power = st.number_input("Posiciones y órdenes asignadas (USD)", min_value=0.0, value=9278.47, step=100.0)
quantity = st.number_input("Cantidad XRP", min_value=0.0, value=6022.41038875, format="%.8f")
average_price = st.number_input("Precio medio de compra (USDT)", min_value=0.0, value=1.5409, format="%.4f")
observed_price = st.number_input("Precio observado en Quantfury (USDT)", min_value=0.0, value=1.4944, format="%.4f")

review = position_review(balance, trading_balance, trading_power, allocated_power,
                         max_exposure_pct, quantity, average_price, observed_price)
st.metric("Exposición asignada", f"{review['exposure_pct']:.1f}%")
st.metric("Poder sin asignar (no es margen libre)", f"${review['available_power']:,.2f}")
st.metric("Saldo trading frente al 40% del saldo real", f"${review['trading_balance_gap']:,.2f}")
st.metric("Resultado aproximado de la posición", f"${review['pnl_estimate']:,.2f}")
if review["exposure_warning"]:
    st.warning("Compras bloqueadas en la simulación: exposición superior al límite elegido.")
if review["balance_warning"]:
    st.error("El saldo de trading está por debajo del umbral de referencia. Revisar protección manualmente.")
st.info("El documento no define qué dato de Quantfury equivale a «margen libre». El umbral del 40% aplicado al saldo de trading es solo una alerta orientativa. No demuestra que exista una orden de cierre ni garantiza proteger el saldo real.")
if not review["profit_target_met"]:
    st.caption("La posición completa no cumple el beneficio mínimo de $50 del stop/venta de beneficios. Una venta por protección es una excepción y podría realizarse con pérdidas.")


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

    block_buys = review["exposure_warning"] or review["balance_warning"]

    # --------------------------------------------------------
    # BLOQUEO DE SEGURIDAD
    # --------------------------------------------------------

    final_action = action

    if block_buys and (
        "COMPRA" in final_action
        or signal == "BUY"
    ):
        final_action = "COMPRA BLOQUEADA"

    # --------------------------------------------------------
    # SEÑAL PRINCIPAL
    # --------------------------------------------------------

    if signal == "BUY":
        signal_text = "🟢 SEÑAL ALCISTA"

    elif signal == "SELL":
        signal_text = "🔴 SEÑAL BAJISTA"

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

    st.markdown(
        f"""
        <div class="card">
            <div class="v4-title">🛡️ Protección de riesgo</div>
            <b>{'🔴 REVISAR' if block_buys else '🟢 DENTRO DE LOS LÍMITES INTRODUCIDOS'}</b><br>
            Exposición: {review['exposure_pct']:.1f}% /
            máximo {max_exposure_pct:.1f}%<br>
            Saldo de trading: {trading_balance:,.2f} USD
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
        "No ejecuta órdenes reales. Las señales M1/M5/M15 no son una decisión de inversión a meses."
    )


# ============================================================
# ERROR
# ============================================================

except Exception as e:

    st.error(
        "No se pudo completar el análisis."
    )

    st.exception(e)

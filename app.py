import json
from datetime import datetime
import streamlit as st
from market import get_timeframes
from strategy_mobile import analyze, trade_plan

st.set_page_config(page_title="Trading Signal V3", page_icon="📈",
                   layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden;}
.block-container {max-width:480px;padding:0.8rem 1rem 3rem;}
h1 {font-size:1.65rem!important;margin-bottom:.2rem!important;}
.signal {padding:24px 12px;border-radius:22px;text-align:center;margin:10px 0 8px;
font-size:2rem;font-weight:800;border:1px solid rgba(128,128,128,.25);}
.buy {background:rgba(0,180,90,.12)} .sell {background:rgba(230,70,70,.12)}
.wait {background:rgba(128,128,128,.10)}
.quality {text-align:center;font-size:1.05rem;font-weight:700;margin-bottom:14px;}
.status {border:1px solid rgba(128,128,128,.20);border-radius:16px;padding:12px 14px;
margin:7px 0;font-size:1.02rem;}
[data-testid="stMetricValue"] {font-size:1.35rem;}
.stButton button {height:3rem;border-radius:14px;font-weight:700;}
</style>
""", unsafe_allow_html=True)

with open("config.json","r",encoding="utf-8") as f:
    cfg=json.load(f)

st.title("📈 Trading Signal V3")
st.caption("M15 tendencia · M5 confirma · M1 entrada · filtros V3")

symbols={"Bitcoin · BTC/USD":"BTC-USD","Ethereum · ETH/USD":"ETH-USD",
         "EUR/USD":"EURUSD=X","Apple · AAPL":"AAPL","Microsoft · MSFT":"MSFT"}
choice=st.selectbox("Activo",list(symbols.keys()))
symbol=symbols[choice]

with st.expander("⚙️ Ajustes de riesgo"):
    balance=st.number_input("Capital de referencia",min_value=1.0,value=float(cfg["account_balance"]))
    risk=st.number_input("Riesgo máximo (%)",min_value=0.1,max_value=2.0,
                         value=float(cfg["risk_per_trade_pct"]),step=0.1)
    sl=st.number_input("Stop (%)",min_value=0.1,value=float(cfg["stop_loss_pct"]),step=0.1)
    tp=st.number_input("Objetivo (%)",min_value=0.1,value=float(cfg["take_profit_pct"]),step=0.1)

st.button("🔄 ACTUALIZAR",use_container_width=True)

try:
    with st.spinner("Analizando..."):
        tfs=get_timeframes(symbol)
        result=analyze(tfs,cfg)
        price=float(tfs["M1"]["Close"].iloc[-1])

    css={"BUY":"buy","SELL":"sell","WAIT":"wait"}[result["signal"]]
    label={"BUY":"🟢 COMPRAR","SELL":"🔴 VENDER","WAIT":"⚪ ESPERAR"}[result["signal"]]
    st.markdown(f'<div class="signal {css}">{label}</div>',unsafe_allow_html=True)

    q=result["quality"] if result["score"]==3 else "—"
    st.markdown(f'<div class="quality">Calidad técnica: {q}</div>',unsafe_allow_html=True)

    c1,c2=st.columns(2)
    c1.metric("Precio externo",f"{price:,.4f}")
    c2.metric("Reglas",f'{result["score"]}/3')

    st.markdown(f'<div class="status"><b>M15 · Tendencia</b><br>{result["trend_text"]}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="status"><b>M5 · Confirmación</b><br>{"✅ Confirmada" if result["confirm"] else "⏳ Pendiente"}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="status"><b>M1 · Entrada</b><br>{"✅ Activada" if result["trigger"] else "⏳ Pendiente"}</div>',
                unsafe_allow_html=True)

    plan=trade_plan(price,result["signal"],balance,risk,sl,tp)
    if plan:
        st.markdown("### Plan")
        a,b=st.columns(2)
        a.metric("Entrada ref.",f'{plan["entry"]:,.4f}')
        b.metric("STOP",f'{plan["stop"]:,.4f}')
        a.metric("OBJETIVO",f'{plan["target"]:,.4f}')
        b.metric("Riesgo máx.",f'{plan["risk_cash"]:,.2f}')
        st.success("Señal V3 válida. Comprueba el precio en Quantfury y decide tú.")
    else:
        st.info(result["reason"])

    with st.expander("🔎 ¿Por qué esta señal?"):
        st.write("Los filtros V3 valoran RSI, impulso, separación de medias y volatilidad.")
        for name,ok in result["filters"].items():
            st.write(("✅ " if ok else "⚠️ ")+name)
        st.caption("ALTA/MEDIA/BAJA clasifica condiciones técnicas; no es una probabilidad de ganar.")
        st.caption(f'RSI M5 {result["rsi5"]:.1f} · separación EMA {result["ema_sep"]:.3f}% · ATR M5 {result["atr_pct"]:.3f}%')

    st.caption("Última consulta: "+datetime.now().strftime("%H:%M:%S"))
    st.caption("No conecta con Quantfury ni envía órdenes. El precio externo puede diferir del ejecutable.")
except Exception as e:
    st.error("No he podido obtener los datos ahora.")
    with st.expander("Detalle técnico"):
        st.code(str(e))

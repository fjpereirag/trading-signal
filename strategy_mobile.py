import numpy as np


def indicators(df, cfg):
    x = df.copy()
    lo = x["Low"].rolling(cfg["stoch_k"]).min()
    hi = x["High"].rolling(cfg["stoch_k"]).max()
    den = (hi-lo).replace(0, np.nan)
    x["K"] = 100*(x["Close"]-lo)/den
    x["D"] = x["K"].rolling(cfg["stoch_d"]).mean()
    x["EMA200"] = x["Close"].ewm(span=cfg["ema_fast"], adjust=False).mean()
    x["EMA365"] = x["Close"].ewm(span=cfg["ema_slow"], adjust=False).mean()

    delta = x["Close"].diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    x["RSI"] = 100 - 100/(1+rs)

    prev_close = x["Close"].shift(1)
    tr = np.maximum(x["High"]-x["Low"],
                    np.maximum((x["High"]-prev_close).abs(),
                               (x["Low"]-prev_close).abs()))
    x["ATR"] = tr.ewm(alpha=1/14, adjust=False).mean()
    return x

def analyze(tfs, cfg):
    z = {k: indicators(v, cfg) for k,v in tfs.items()}
    m15, m5, m1 = z["M15"].iloc[-1], z["M5"].iloc[-1], z["M1"].iloc[-1]
    p1 = z["M1"].iloc[-2]

    up = m15.Close > m15.EMA200 > m15.EMA365
    down = m15.Close < m15.EMA200 < m15.EMA365
    direction = "BUY" if up else "SELL" if down else "WAIT"
    trend_text = "↑ Alcista" if up else "↓ Bajista" if down else "↔ Neutral"

    confirm = ((direction=="BUY" and m5.K>m5.D and m5.Close>m5.EMA200) or
               (direction=="SELL" and m5.K<m5.D and m5.Close<m5.EMA200))
    trigger = ((direction=="BUY" and p1.K<=p1.D and m1.K>m1.D) or
               (direction=="SELL" and p1.K>=p1.D and m1.K<m1.D))

    score = int(direction!="WAIT") + int(confirm) + int(trigger)
    base_signal = direction if score == 3 else "WAIT"

    # V3: filtros de calidad. No son una probabilidad de acierto.
    ema_sep = abs(m15.EMA200-m15.EMA365) / m15.Close * 100 if m15.Close else 0
    rsi_ok = ((direction=="BUY" and 52 <= m5.RSI <= 72) or
              (direction=="SELL" and 28 <= m5.RSI <= 48))
    momentum_ok = ((direction=="BUY" and m5.K > m5.D and m1.K > m1.D) or
                   (direction=="SELL" and m5.K < m5.D and m1.K < m1.D))
    trend_strength_ok = ema_sep >= 0.08
    atr_pct = (m5.ATR/m5.Close*100) if m5.Close else 0
    volatility_ok = 0.05 <= atr_pct <= 3.0

    quality_points = sum([bool(rsi_ok), bool(momentum_ok),
                          bool(trend_strength_ok), bool(volatility_ok)])
    quality = "ALTA" if quality_points >= 4 else "MEDIA" if quality_points >= 2 else "BAJA"

    # Una señal 3/3 de calidad baja se frena: se muestra ESPERAR.
    signal = base_signal if (base_signal!="WAIT" and quality!="BAJA") else "WAIT"

    if direction=="WAIT":
        reason = "Sin operación: M15 no define una tendencia clara."
    elif not confirm:
        reason = "Sin operación: M5 todavía no confirma M15."
    elif not trigger:
        reason = "Sin operación: falta el gatillo de entrada en M1."
    elif quality=="BAJA":
        reason = "3/3 técnico, pero los filtros V3 indican calidad baja: esperar."
    else:
        reason = f"Condiciones completas. Calidad técnica {quality.lower()}."

    return dict(
        signal=signal, raw_signal=base_signal, score=score, quality=quality,
        quality_points=quality_points, trend_text=trend_text,
        confirm=confirm, trigger=trigger, reason=reason,
        k15=m15.K, d15=m15.D, k5=m5.K, d5=m5.D, k1=m1.K, d1=m1.D,
        rsi5=m5.RSI, ema_sep=ema_sep, atr_pct=atr_pct,
        filters={"RSI":bool(rsi_ok), "Impulso":bool(momentum_ok),
                 "Tendencia":bool(trend_strength_ok), "Volatilidad":bool(volatility_ok)}
    )

def trade_plan(price, side, balance, risk_pct, sl_pct, tp_pct):
    if side=="WAIT":
        return None
    risk_cash = balance*risk_pct/100
    dist = price*sl_pct/100
    qty = risk_cash/dist if dist else 0
    if side=="BUY":
        stop=price*(1-sl_pct/100); target=price*(1+tp_pct/100)
    else:
        stop=price*(1+sl_pct/100); target=price*(1-tp_pct/100)
    return dict(entry=price, stop=stop, target=target,
                risk_cash=risk_cash, qty_reference=qty)

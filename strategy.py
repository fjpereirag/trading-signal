import pandas as pd
import numpy as np

def indicators(df, k_period=14, d_period=3, ema_fast=200, ema_slow=365):
    x = df.copy()
    close = x["Close"]
    low = x["Low"].rolling(k_period).min()
    high = x["High"].rolling(k_period).max()
    den = (high-low).replace(0, np.nan)
    x["K"] = 100*(close-low)/den
    x["D"] = x["K"].rolling(d_period).mean()
    x["EMA200"] = close.ewm(span=ema_fast, adjust=False).mean()
    x["EMA365"] = close.ewm(span=ema_slow, adjust=False).mean()
    return x

def timeframe_signal(df, cfg):
    x = indicators(df, cfg["stoch_k"], cfg["stoch_d"], cfg["ema_fast"], cfg["ema_slow"])
    if len(x.dropna()) < 2:
        return "WAIT", x
    a,b = x.iloc[-2], x.iloc[-1]
    bullish_cross = a.K <= a.D and b.K > b.D
    bearish_cross = a.K >= a.D and b.K < b.D
    trend_up = b.Close > b.EMA200 > b.EMA365
    trend_down = b.Close < b.EMA200 < b.EMA365
    if bullish_cross and b.K < cfg["oversold"] and trend_up:
        return "BUY", x
    if bearish_cross and b.K > cfg["overbought"] and trend_down:
        return "SELL", x
    return "WAIT", x

def combined_signal(signals):
    # Conservative: M5/M15 define direction; M1 is entry trigger.
    if signals["M1"] == signals["M5"] == signals["M15"] == "BUY":
        return "BUY"
    if signals["M1"] == signals["M5"] == signals["M15"] == "SELL":
        return "SELL"
    return "WAIT"

def trade_plan(price, side, balance, risk_pct, sl_pct, tp_pct):
    if side == "WAIT":
        return None
    risk_cash = balance * risk_pct/100
    stop_distance = price * sl_pct/100
    qty = risk_cash / stop_distance if stop_distance else 0
    if side == "BUY":
        sl, tp = price*(1-sl_pct/100), price*(1+tp_pct/100)
    else:
        sl, tp = price*(1+sl_pct/100), price*(1-tp_pct/100)
    return {"side":side, "entry":price, "stop":sl, "target":tp,
            "qty_reference":qty, "risk_cash":risk_cash}

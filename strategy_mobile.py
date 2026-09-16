import numpy as np

def indicators(df,cfg):
    x=df.copy()
    lo=x["Low"].rolling(cfg["stoch_k"]).min()
    hi=x["High"].rolling(cfg["stoch_k"]).max()
    den=(hi-lo).replace(0,np.nan)
    x["K"]=100*(x["Close"]-lo)/den
    x["D"]=x["K"].rolling(cfg["stoch_d"]).mean()
    x["EMA200"]=x["Close"].ewm(span=cfg["ema_fast"],adjust=False).mean()
    x["EMA365"]=x["Close"].ewm(span=cfg["ema_slow"],adjust=False).mean()
    return x

def analyze(tfs,cfg):
    z={k:indicators(v,cfg) for k,v in tfs.items()}
    m15,m5,m1=z["M15"].iloc[-1],z["M5"].iloc[-1],z["M1"].iloc[-1]
    p1=z["M1"].iloc[-2]

    up=m15.Close>m15.EMA200>m15.EMA365
    down=m15.Close<m15.EMA200<m15.EMA365
    direction="BUY" if up else "SELL" if down else "WAIT"
    trend_text="↑ Alcista" if up else "↓ Bajista" if down else "↔ Neutral"

    confirm=(direction=="BUY" and m5.K>m5.D and m5.Close>m5.EMA200) or \
            (direction=="SELL" and m5.K<m5.D and m5.Close<m5.EMA200)

    trigger=(direction=="BUY" and p1.K<=p1.D and m1.K>m1.D) or \
            (direction=="SELL" and p1.K>=p1.D and m1.K<m1.D)

    score=int(direction!="WAIT")+int(confirm)+int(trigger)
    signal=direction if score==3 else "WAIT"
    reason="Sin operación: "
    if direction=="WAIT": reason+="M15 no define una tendencia clara."
    elif not confirm: reason+="M5 todavía no confirma M15."
    elif not trigger: reason+="falta el gatillo de entrada en M1."
    else: reason="Condiciones completas."

    return dict(signal=signal,score=score,trend_text=trend_text,confirm=confirm,
                trigger=trigger,reason=reason,k15=m15.K,d15=m15.D,k5=m5.K,d5=m5.D,
                k1=m1.K,d1=m1.D)

def trade_plan(price,side,balance,risk_pct,sl_pct,tp_pct):
    if side=="WAIT": return None
    risk_cash=balance*risk_pct/100
    dist=price*sl_pct/100
    qty=risk_cash/dist if dist else 0
    if side=="BUY":
        stop=price*(1-sl_pct/100); target=price*(1+tp_pct/100)
    else:
        stop=price*(1+sl_pct/100); target=price*(1-tp_pct/100)
    return dict(entry=price,stop=stop,target=target,risk_cash=risk_cash,qty_reference=qty)

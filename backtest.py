import pandas as pd
from strategy import timeframe_signal

def simple_backtest(df, cfg):
    # Educational sanity check: long-only single timeframe, next-bar approximation.
    # Not a production execution simulator.
    rows=[]
    pos=None
    entry=None
    for i in range(max(cfg["ema_slow"]+5, 370), len(df)):
        chunk=df.iloc[:i+1]
        sig,_=timeframe_signal(chunk,cfg)
        px=float(chunk["Close"].iloc[-1])
        if pos is None and sig=="BUY":
            pos="LONG"; entry=px
        elif pos=="LONG":
            ret=(px-entry)/entry
            if ret <= -cfg["stop_loss_pct"]/100 or ret >= cfg["take_profit_pct"]/100 or sig=="SELL":
                rows.append({"entry":entry,"exit":px,"return_pct":ret*100})
                pos=None
    out=pd.DataFrame(rows)
    return out

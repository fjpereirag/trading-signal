import yfinance as yf
import pandas as pd

def _clean(df):
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def get_timeframes(symbol):
    # Yahoo 1-minute data is intended for signal prototyping and may be delayed/limited.
    raw = _clean(yf.download(symbol, period="7d", interval="1m",
                             progress=False, auto_adjust=False, prepost=True))
    if raw.empty:
        raise RuntimeError("No se han recibido datos para el símbolo.")
    raw = raw[["Open","High","Low","Close","Volume"]]
    return {
        "M1": raw,
        "M5": raw.resample("5min").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna(),
        "M15": raw.resample("15min").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()
    }

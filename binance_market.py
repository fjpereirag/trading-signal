"""Completed XRP/USDT candles from Binance Spot public market data."""

from datetime import datetime, timezone

import pandas as pd
import requests


URL = "https://data-api.binance.vision/api/v3/klines"


def get_timeframes(symbol="XRPUSDT"):
    frames = {}
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    for name, interval, duration in (("M1", "1m", 60_000), ("M5", "5m", 300_000), ("M15", "15m", 900_000)):
        response = requests.get(URL, params={"symbol": symbol, "interval": interval, "limit": 500}, timeout=15)
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows, list) or len(rows) < 370:
            raise RuntimeError(f"Binance no devolvió suficientes velas {name}")
        completed = [r for r in rows if len(r) >= 7 and int(r[6]) < now_ms]
        if len(completed) < 366:
            raise RuntimeError(f"Velas completas insuficientes {name}")
        frame = pd.DataFrame(completed, columns=["open_time", "Open", "High", "Low", "Close", "Volume", "close_time", "q", "n", "tb", "tq", "ignore"])
        frame.index = pd.to_datetime(frame.pop("open_time"), unit="ms", utc=True)
        frames[name] = frame[["Open", "High", "Low", "Close", "Volume"]].astype(float)
    return frames

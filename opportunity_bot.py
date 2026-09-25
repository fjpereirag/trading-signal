"""Encrypted, read-only opportunity snapshot for the Streamlit dashboard."""

import json
import os
from datetime import datetime, timedelta, timezone
from math import ceil, floor, isfinite

import pandas as pd
import requests
import yfinance as yf

from quantfury_account import snapshot
from result_codec import seal


PLANS = (
    ("AVGO", 359.0, "Acción Nasdaq", 5),
    ("ETHUSDT", 2700.0, "Cripto", 5),
    ("SOLUSDT", 120.0, "Cripto", 5),
)
TARGET = 50.0
MAX_AGE = timedelta(minutes=12)


def candles(symbol, now):
    if symbol == "AVGO":
        frame = yf.download(symbol, period="1d", interval="5m", auto_adjust=False,
                            progress=False, prepost=False, threads=False)
        if frame.empty:
            raise RuntimeError("AVGO sin velas actuales")
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
        frame.index = pd.to_datetime(frame.index, utc=True)
        # Yahoo timestamps refer to the beginning of each bar.
        frame = frame[frame.index + timedelta(minutes=5) <= now]
    else:
        response = requests.get("https://data-api.binance.vision/api/v3/klines",
                                params={"symbol": symbol, "interval": "5m", "limit": 30}, timeout=15)
        response.raise_for_status()
        rows = [r for r in response.json() if int(r[6]) < now.timestamp() * 1000]
        frame = pd.DataFrame({"Close": [float(r[4]) for r in rows]},
                             index=pd.to_datetime([int(r[6]) for r in rows], unit="ms", utc=True))
    if len(frame) < 4 or now - frame.index[-1].to_pydatetime() > MAX_AGE:
        raise RuntimeError(f"Velas de {symbol} insuficientes o desactualizadas")
    close = [float(v) for v in frame["Close"].tail(4)]
    if any(not isfinite(v) or v <= 0 for v in close):
        raise RuntimeError(f"Precios de {symbol} inválidos")
    return close, frame.index[-1].isoformat()


def evaluate(symbol, level, kind, decimals, close, observed, power, positions):
    latest = close[-1]
    # Two prior closed bars above the level, followed by a shallow retest and recovery.
    confirmed = close[-4] > level and close[-3] > level
    retest = level <= close[-2] <= level * 1.003
    rebound = close[-1] > close[-2] and close[-1] > level
    quantity = floor(power / latest) if kind == "Acción Nasdaq" else floor(power / latest * 10000) / 10000
    open_position = bool(positions)
    ready = confirmed and retest and rebound and quantity > 0 and not open_position
    return {
        "asset": symbol.replace("USDT", ""), "kind": kind, "reference": level,
        "price": round(latest, decimals), "observed": observed,
        "status": "Señal técnica; verificar bid/ask" if ready else
                  "Hay otra posición abierta" if open_position else "Esperar",
        "quantity": quantity, "exposure": round(quantity * latest, 2),
        "target_move": ceil(TARGET / quantity * 10**decimals) / 10**decimals if quantity else None,
        "ready": ready,
    }


def main():
    password = os.environ.get("APP_RESULT_PASSWORD", "")
    request_id = os.environ.get("REQUEST_ID", "")
    if len(password) < 20 or len(request_id) != 32 or any(c not in "0123456789abcdef" for c in request_id):
        raise RuntimeError("Clave o identificador inválido")
    account, positions = snapshot()
    balance = float(account["balance"])
    power = float(account["availableTradingPower"])
    if not isfinite(balance) or balance <= 0 or not isfinite(power) or power < 0:
        raise RuntimeError("Saldo o poder de trading inválido")
    now = datetime.now(timezone.utc)
    plans = []
    for symbol, level, kind, decimals in PLANS:
        try:
            close, observed = candles(symbol, now)
            plans.append(evaluate(symbol, level, kind, decimals, close, observed, power, positions))
        except (RuntimeError, requests.RequestException, ValueError, KeyError):
            plans.append({"asset": symbol.replace("USDT", ""), "kind": kind,
                          "reference": level, "price": None, "observed": None,
                          "status": "Datos no disponibles; señal bloqueada", "quantity": None,
                          "exposure": None, "target_move": None, "ready": False})
    result = {"type": "opportunities-v1", "generated": now.isoformat(),
              "balance": balance, "currency": account["currency"],
              "power": power, "positions": len(positions), "target": TARGET,
              "risk_pct": round(TARGET / balance * 100, 1), "plans": plans}
    with open("result.json.enc", "wb") as handle:
        handle.write(seal(json.dumps(result, ensure_ascii=False), password))


if __name__ == "__main__":
    main()

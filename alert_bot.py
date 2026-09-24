"""XRP/USDT alerts; Quantfury operations remain manual."""

import json
import os
from datetime import datetime, timedelta, timezone

import requests

from binance_market import get_timeframes
from quantfury_account import review_xrp, snapshot
from strategy_mobile import analyze


def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("Faltan credenciales de Telegram")
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": message}, timeout=15,
    )
    response.raise_for_status()


def format_advice(result, review, account):
    """Never infer SL, partial size or profit from absent position fields."""
    positions = review["xrp"]
    action = "Esperar"
    if (result["signal"] == "BUY" and result["zone"] in ("BAJA", "PROFUNDA")
            and result["pullback"] == "REAL" and not review["block_buys"]):
        action = "Comprar"
    sl = "Mantener"
    for position in positions:
        price = position.get("lastPrice")
        stops = position.get("stopOrders")
        direction = position.get("direction")
        if price is None or stops is None or direction not in ("Long", "Short"):
            raise RuntimeError("Posición XRP sin precio, dirección o SL verificables")
        if not stops:
            sl = "Revisar: posición sin SL"
            action = "Esperar"
            continue
        for stop in stops:
            level = stop.get("price")
            if level is None:
                raise RuntimeError("SL XRP sin nivel verificable")
            if (direction == "Long" and price <= level) or (
                direction == "Short" and price >= level
            ):
                sl = f"Revisar ejecución en Quantfury ({level:.4f})"
                action = "Esperar"
        if position.get("targetOrders") is None:
            raise RuntimeError("Objetivos XRP no verificables")
    return "\n".join((
        f"1. Acción: {action}",
        f"2. SL: {sl}",
        "3. Parcial: No actuar",
    ))


def main():
    if os.environ.get("TEST_TELEGRAM", "").lower() == "true":
        send_telegram("Prueba de Telegram. Sin operaciones.")
        return
    if not (os.environ.get("QUANTFURY_ACCESS_TOKEN") or (
        os.environ.get("QUANTFURY_CLIENT_ID") and os.environ.get("QUANTFURY_REFRESH_TOKEN")
    )):
        raise RuntimeError("Cuenta Quantfury sin autorización: indicaciones suspendidas")
    account, positions = snapshot()
    review = review_xrp(account, positions)
    tfs = get_timeframes()
    observed = tfs["M1"].index[-1].to_pydatetime()
    now = datetime.now(timezone.utc)
    if not timedelta(0) <= now - observed <= timedelta(minutes=3):
        raise RuntimeError("Precio de Binance desactualizado: indicaciones suspendidas")
    with open("config.json", encoding="utf-8") as handle:
        result = analyze(tfs, json.load(handle))
    send_telegram(f"XRP/USDT · {now:%d/%m/%Y %H:%M} UTC\n" + format_advice(result, review, account))


if __name__ == "__main__":
    main()

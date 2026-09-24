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
    price = result["price"]
    action = "Esperar"
    if (result["signal"] == "BUY" and result["zone"] in ("BAJA", "PROFUNDA")
            and result["pullback"] == "REAL" and not review["block_buys"]):
        action = "Comprar"
    stops = [p.get("stopLossPrice") for p in positions]
    valid_stops = [float(x) for x in stops if x is not None]
    sl = "Mantener"
    # Binance's quote cannot prove that a stop was touched at Quantfury.
    if any(price <= stop for stop in valid_stops):
        sl = "Revisar en Quantfury"
    if positions and len(valid_stops) != len(positions):
        sl = "Sin verificar"
        action = "Esperar"
    return "\n".join((
        f"1. Acción: {action}",
        f"2. SL: {sl}",
        "3. Parcial: No actuar",
        f"Binance XRP/USDT: {price:.4f} USDT · Quantfury: {account['balance']} {account['currency']} · exposición: {review['exposure_pct']:.1f}%",
        "Acciones manuales en Quantfury. Parciales y subida de SL pendientes de datos y reglas verificables.",
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

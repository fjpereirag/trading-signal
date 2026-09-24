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


def _number(value, label):
    """Reject absent, malformed and nonfinite broker fields."""
    import math
    try:
        number = float(value)
    except (ValueError, TypeError):
        raise RuntimeError(f"{label} no verificable") from None
    if not math.isfinite(number):
        raise RuntimeError(f"{label} no verificable")
    return number


def format_advice(result, review, account):
    """Three lines based on live Quantfury positions and confirmed market bars."""
    positions = review["xrp"]
    if len(positions) != 1:
        raise RuntimeError("Se necesita una sola posición XRP con SL verificable")
    position = positions[0]
    if position.get("direction") != "Long":
        raise RuntimeError("Solo se admiten posiciones XRP largas")
    price = _number(position.get("lastPrice"), "Precio Quantfury")
    quantity = _number(position.get("quantity"), "Cantidad XRP")
    if price <= 0 or quantity <= 0:
        raise RuntimeError("Posición XRP inválida")
    stops = position.get("stopOrders")
    if not isinstance(stops, list) or not stops:
        raise RuntimeError("Posición XRP sin SL verificable")
    levels = [_number(stop.get("price"), "SL XRP") for stop in stops]
    if any(level <= 0 for level in levels):
        raise RuntimeError("SL XRP inválido")
    stop = max(levels)
    action, sl, partial = "Esperar", "Mantener", "No actuar"
    if price <= stop:
        action, sl, partial = "Vender", "Ejecutar", "Venta total por SL"
    elif result.get("breakout"):
        pnl = _number(position.get("unrealizedPnlSystem"), "Beneficio XRP")
        if pnl >= 50:
            sale = quantity * 0.25
            action, sl = "Vender", "Subir"
            partial = f"Venta parcial de {sale:.4f} XRP en {price:.4f} USD"
    elif (
        result.get("signal") == "BUY"
        and result.get("context") == "ALCISTA"
        and result.get("zone") in ("BAJA", "PROFUNDA")
        and result.get("pullback") in ("REAL", "PROFUNDO")
        and not review["block_buys"]
    ):
        action = "Comprar"
        if result["zone"] == "PROFUNDA":
            partial = "Compra parcial"
    return "\n".join((
        f"1. Acción: {action}",
        f"2. SL: {sl}",
        f"3. Parcial: {partial}",
    ))

def main():
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
    send_telegram(format_advice(result, review, account))


if __name__ == "__main__":
    main()

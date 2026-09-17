import os
import json
import requests


from market import get_timeframes
from strategy_mobile import analyze, trade_plan


TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

ASSETS = {
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "EUR/USD": "EURUSD=X",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
}


def send_telegram(message):
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
        },
        timeout=15,
    )

    response.raise_for_status()


def main():
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    for name, ticker in ASSETS.items():
        try:
            tfs = get_timeframes(ticker)
            result = analyze(tfs, cfg)

            signal = result.get("signal", "WAIT")
            score = result.get("score", 0)
            quality = result.get("quality", "BAJA")

            # Solo avisamos cuando existe señal completa 3/3
            # y supera los filtros de calidad.
            if signal not in ("BUY", "SELL") or score != 3:
                continue

            price = float(
                result.get(
                    "price",
                    tfs["M1"]["Close"].iloc[-1]
                )
            )

            if signal == "BUY":
                action = "🟢 COMPRAR"
            else:
                action = "🔴 VENDER"

            message = (
                f"📈 TRADING SIGNAL V3.1\n\n"
                f"{action}\n"
                f"Activo: {name}\n"
                f"Precio externo: {price:.4f}\n"
                f"Reglas: {score}/3\n"
                f"Calidad técnica: {quality}\n\n"
                f"M15 tendencia + M5 confirmación + M1 gatillo."
            )

            send_telegram(message)

        except Exception as e:
            print(f"Error comprobando {name}: {e}")


if __name__ == "__main__":
    main()

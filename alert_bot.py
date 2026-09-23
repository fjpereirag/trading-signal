import os
import json
import requests
from datetime import datetime, timezone


from market import get_timeframes
from strategy_mobile import analyze


TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

ASSETS = {
    "XRP": "XRP-USD",
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
    if os.environ.get("TEST_TELEGRAM", "").lower() == "true":
        send_telegram(
            "✅ Prueba de conexión de Trading Signal V4. "
            "Este es un mensaje de prueba; no se ha realizado ninguna operación."
        )
        print("Mensaje de prueba enviado al chat configurado.")
        return

    if os.environ.get("REPORT_TELEGRAM", "").lower() == "true":
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        lines = [
            "📊 Trading Signal V4 · consulta puntual",
            datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
            "Precios externos de Yahoo Finance; no son precios ejecutables en Quantfury.",
        ]
        for name, ticker in (("XRP", "XRP-USD"), ("BTC", "BTC-USD")):
            try:
                result = analyze(get_timeframes(ticker), cfg)
                lines.append(
                    f"{name}: {result['price']:.4f} USD · "
                    f"contexto {result['context']} · zona {result['zone']} · "
                    f"reglas {result['score']}/3 · acción simulada "
                    f"{result['action'].replace('_', ' ')}"
                )
            except Exception as exc:
                print(f"Error consultando {name}: {exc}")
                lines.append(f"{name}: datos no disponibles en esta consulta.")
        lines.append(
            "La cuenta de Quantfury no está conectada; sus cifras manuales pueden haber cambiado. "
            "Sin órdenes ni recomendación automática."
        )
        send_telegram("\n".join(lines))
        print("Informe puntual enviado al chat configurado.")
        return

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

            action = "🟢 Señal técnica alcista" if signal == "BUY" else "🔴 Señal técnica bajista"

            message = (
                f"📈 TRADING SIGNAL V4 · SIMULACIÓN\n\n"
                f"{action}\n"
                f"Activo: {name}\n"
                f"Precio externo: {price:.4f}\n"
                f"Reglas: {score}/3\n"
                f"Calidad técnica: {quality}\n\n"
                f"M15 tendencia + M5 confirmación + M1 gatillo. "
                f"Sin datos de la cuenta ni órdenes en Quantfury."
            )

            send_telegram(message)

        except Exception as e:
            print(f"Error comprobando {name}: {e}")


if __name__ == "__main__":
    main()

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


from market import get_timeframes
from strategy_mobile import analyze
from quantfury_account import snapshot, review_xrp


TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

ASSETS = {"XRP": "XRP-USD"}


def candle_time(tfs):
    """Return the actual timestamp of the latest Yahoo one-minute candle."""
    last = tfs["M1"].index[-1]
    if last.tzinfo is None:
        raise ValueError("La vela M1 no tiene zona horaria verificable.")
    return last.to_pydatetime().astimezone(timezone.utc)


def fresh_market_data(tfs, now):
    """Reject old or future Yahoo candles before sending any market alert."""
    age = now - candle_time(tfs)
    return timedelta(minutes=-2) <= age <= timedelta(minutes=10)


def data_time_label(tfs, now):
    observed = candle_time(tfs)
    local = observed.astimezone(ZoneInfo("Europe/Madrid"))
    age_minutes = max(0, int((now - observed).total_seconds() // 60))
    return (
        f"Vela Yahoo M1: {observed:%d/%m/%Y %H:%M} UTC "
        f"({local:%H:%M} Madrid); antigüedad {age_minutes} min"
    )


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

    scheduled_report = os.environ.get("REPORT_SCHEDULE", "").lower() == "true"
    account_context = None
    if os.environ.get("QUANTFURY_ACCESS_TOKEN") or (
        os.environ.get("QUANTFURY_CLIENT_ID") and os.environ.get("QUANTFURY_REFRESH_TOKEN")
    ):
        try:
            account, positions = snapshot()
            account_context = (account, review_xrp(account, positions))
        except Exception as exc:
            # Never substitute the old manually entered figures for a failed live read.
            raise RuntimeError("No se pudo verificar la cuenta Quantfury; avisos suspendidos") from exc
    if scheduled_report or os.environ.get("REPORT_TELEGRAM", "").lower() == "true":
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        lines = [
            "📊 XRP · seguimiento" if scheduled_report else "📊 XRP · consulta",
            "Objetivo: acumular USDT para comprar BTC en spot.",
            datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
        ]
        for name, ticker in ASSETS.items():
            try:
                tfs = get_timeframes(ticker)
                now = datetime.now(timezone.utc)
                if not fresh_market_data(tfs, now):
                    lines.append(f"{name}: vela Yahoo desactualizada; sin señal.")
                    continue
                result = analyze(tfs, cfg)
                lines.append(
                    f"{name} (Yahoo): {result['price']:.4f} USD · "
                    f"reglas {result['score']}/3 · "
                    f"{result['action'].replace('_', ' ')}"
                )
            except Exception as exc:
                print(f"Error consultando {name}: {exc}")
                lines.append(f"{name}: datos de mercado no disponibles.")
        if account_context:
            account, review = account_context
            lines.append(
                f"Quantfury: saldo trading {account['balance']:.2f} "
                f"{account['currency']} · exposición {review['exposure_pct']:.1f}% "
                f"· XRP abiertas {len(review['xrp'])}."
            )
            if review["block_buys"]:
                lines.append("Compras XRP bloqueadas en el análisis: exposición ≥30%.")
        else:
            lines.append("Quantfury sin conexión; datos de mercado externos.")
        lines.append("Precios Yahoo no ejecutables. Sin órdenes.")
        send_telegram("\n".join(lines))
        print("Seguimiento XRP enviado al chat configurado.")
        return

    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    for name, ticker in ASSETS.items():
        try:
            tfs = get_timeframes(ticker)
            now = datetime.now(timezone.utc)
            if not fresh_market_data(tfs, now):
                print(f"{name}: vela M1 desactualizada; aviso omitido.")
                continue
            result = analyze(tfs, cfg)

            signal = result.get("signal", "WAIT")
            score = result.get("score", 0)
            quality = result.get("quality", "BAJA")

            # XRP: aviso previo cuando M15 y M5 coinciden, antes del gatillo M1.
            # Una ventana de cinco minutos por cuarto de hora limita repeticiones.
            early_xrp = (
                result.get("trend") == "BUY"
                and result.get("confirm")
                and not result.get("trigger")
                and score == 2
                and now.minute % 15 < 5
            )
            if early_xrp:
                if account_context and account_context[1]["block_buys"]:
                    continue
                send_telegram(
                    "🟡 TRADING SIGNAL V4 · AVISO PREVIO XRP\n"
                    f"{now:%d/%m/%Y %H:%M} UTC\n"
                    f"{data_time_label(tfs, now)}\n"
                    f"Precio externo: {result['price']:.4f} USD\n"
                    "M15 tendencia alcista + M5 confirmación: 2/3. "
                    "Falta el gatillo M1; no hay señal completa.\n"
                    f"Contexto: {result['context']} · zona: {result['zone']}.\n"
                    "Consulta tu posición y el precio ejecutable en Quantfury. " +
                    ("Cuenta Quantfury verificada; sin órdenes." if account_context
                     else "Cuenta no conectada; sin órdenes ni recomendación automática.")
                )

            # Solo avisamos cuando existe señal completa 3/3
            # y supera los filtros de calidad.
            if signal not in ("BUY", "SELL") or score != 3:
                continue
            if signal == "BUY" and account_context and account_context[1]["block_buys"]:
                print("Compra XRP bloqueada por exposición de la cuenta Quantfury.")
                continue

            price = float(result["price"])

            action = "🟢 Señal técnica alcista" if signal == "BUY" else "🔴 Señal técnica bajista"

            message = (
                f"📈 TRADING SIGNAL V4 · SIMULACIÓN\n\n"
                f"{action}\n"
                f"Activo: {name}\n"
                f"{data_time_label(tfs, now)}\n"
                f"Precio externo: {price:.4f}\n"
                f"Reglas: {score}/3\n"
                f"Calidad técnica: {quality}\n\n"
                f"M15 tendencia + M5 confirmación + M1 gatillo. " +
                (f"Exposición Quantfury {account_context[1]['exposure_pct']:.1f}%. "
                 if account_context else "Sin datos de la cuenta Quantfury. ")
                + "Sin órdenes; ejecución manual."
            )

            send_telegram(message)

        except Exception as e:
            raise RuntimeError(f"Error comprobando o notificando {name}") from e


if __name__ == "__main__":
    main()

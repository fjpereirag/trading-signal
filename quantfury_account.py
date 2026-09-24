"""Read-only Quantfury MCP access for scheduled account-aware alerts."""

import os
import requests

MCP_URL = "https://ai.quantfury.com/mcp"


def _token():
    # A ChatGPT connector authorization is scoped to ChatGPT, not GitHub Actions.
    token = os.environ.get("QUANTFURY_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError("Falta QUANTFURY_ACCESS_TOKEN en GitHub Actions")
    return token


def _call(name, request_id):
    response = requests.post(
        MCP_URL,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        },
        json={
            "jsonrpc": "2.0", "id": request_id, "method": "tools/call",
            "params": {"name": name, "arguments": {}},
        },
        timeout=20,
    )
    response.raise_for_status()
    if response.headers.get("content-type", "").startswith("text/event-stream"):
        events = [line[6:] for line in response.text.splitlines() if line.startswith("data: ")]
        if not events:
            raise RuntimeError("Respuesta MCP vacía")
        import json
        payload = json.loads(events[-1])
    else:
        payload = response.json()
    if payload.get("error"):
        raise RuntimeError("Quantfury rechazó la consulta MCP")
    result = payload["result"]
    if result.get("isError"):
        raise RuntimeError("Quantfury no pudo consultar la cuenta")
    if "structuredContent" in result:
        return result["structuredContent"]
    import json
    return json.loads(next(item["text"] for item in result["content"] if item["type"] == "text"))


def snapshot():
    account = _call("quantfury_trading_account", 1)
    positions = _call("quantfury_open_positions", 2)
    if account.get("message") or positions.get("message"):
        raise RuntimeError("No hay cuenta de trading disponible")
    required = ("balance", "currency", "tradingPower", "availableTradingPower")
    if any(account.get(key) is None for key in required) or positions.get("positions") is None:
        raise RuntimeError("Respuesta incompleta de Quantfury")
    return account, positions["positions"]


def review_xrp(account, positions, max_exposure_pct=30):
    power = float(account["tradingPower"])
    available = float(account["availableTradingPower"])
    if power <= 0 or not 0 <= available <= power:
        raise ValueError("Poder de trading inválido")
    exposure = (power - available) / power * 100
    xrp = [p for p in positions if p.get("shortNameDisplay", "").upper() in ("XRP", "XRP/USDT")]
    return {
        "exposure_pct": exposure,
        "block_buys": exposure >= max_exposure_pct,
        "xrp": xrp,
    }

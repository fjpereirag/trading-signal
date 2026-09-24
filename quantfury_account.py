"""Read-only Quantfury MCP access for scheduled account-aware alerts."""

import os
import base64
import asyncio
import json
import requests
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from nacl.public import PublicKey, SealedBox

MCP_URL = "https://ai.quantfury.com/mcp"


_cached_token = None


def _save_rotated_refresh_token(value):
    """Persist a rotated token before using it; never print token material."""
    pat = os.environ.get("GH_SECRETS_PAT")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not pat or repo != "fjpereirag/trading-signal":
        raise RuntimeError(
            "Quantfury rotó el refresh token y falta GH_SECRETS_PAT para guardarlo. "
            "Se requiere nueva autorización local."
        )
    url = f"https://api.github.com/repos/{repo}/actions/secrets"
    headers = {"Authorization": f"Bearer {pat}", "Accept": "application/vnd.github+json"}
    key_response = requests.get(f"{url}/public-key", headers=headers, timeout=15)
    key_response.raise_for_status()
    key = key_response.json()
    encrypted = SealedBox(PublicKey(base64.b64decode(key["key"]))).encrypt(value.encode())
    update = requests.put(
        f"{url}/QUANTFURY_REFRESH_TOKEN", headers=headers,
        json={"encrypted_value": base64.b64encode(encrypted).decode(), "key_id": key["key_id"]},
        timeout=15,
    )
    update.raise_for_status()


def _token():
    global _cached_token
    if _cached_token:
        return _cached_token
    client_id = os.environ.get("QUANTFURY_CLIENT_ID")
    refresh = os.environ.get("QUANTFURY_REFRESH_TOKEN")
    if client_id and refresh:
        response = requests.post(
            "https://ai.quantfury.com/token",
            data={"grant_type": "refresh_token", "client_id": client_id,
                  "refresh_token": refresh, "resource": MCP_URL},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        access = payload.get("access_token")
        if not access:
            raise RuntimeError("Quantfury no devolvió un access token")
        rotated = payload.get("refresh_token")
        if rotated and rotated != refresh:
            _save_rotated_refresh_token(rotated)
        _cached_token = access
        return access
    token = os.environ.get("QUANTFURY_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError("Falta autorización Quantfury para GitHub Actions")
    _cached_token = token
    return token


def _call(name, _request_id):
    async def invoke():
        async with streamablehttp_client(
            MCP_URL, headers={"Authorization": f"Bearer {_token()}"}
        ) as (read_stream, write_stream, _session_id):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                available = await session.list_tools()
                matches = [t.name for t in available.tools if t.name == name or t.name.endswith(name)]
                if len(matches) != 1:
                    raise RuntimeError(f"La herramienta MCP {name} no está disponible de forma inequívoca")
                result = await session.call_tool(matches[0], arguments={})
                if result.isError:
                    raise RuntimeError("Quantfury no pudo consultar la cuenta")
                if result.structuredContent is not None:
                    return result.structuredContent
                return json.loads(next(item.text for item in result.content if item.type == "text"))
    return asyncio.run(invoke())


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

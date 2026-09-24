"""One-time local OAuth setup. Run on your own computer, never in GitHub Actions."""

import base64
import hashlib
import json
import secrets
import subprocess
import threading
import webbrowser
from getpass import getpass
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

REPO = "fjpereirag/trading-signal"
SERVER = "https://ai.quantfury.com"
RESOURCE = f"{SERVER}/mcp"


def save_secret(name, value):
    subprocess.run(
        ["gh", "secret", "set", name, "-R", REPO],
        input=value, text=True, check=True, capture_output=True,
    )


def main():
    subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
    state = secrets.token_urlsafe(24)
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    received = {}
    finished = threading.Event()

    class Callback(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlparse(self.path)
            if url.path != "/callback":
                self.send_error(404)
                return
            params = parse_qs(url.query)
            if params.get("state", [None])[0] != state:
                self.send_error(400, "Estado OAuth incorrecto")
                return
            received["code"] = params.get("code", [None])[0]
            received["error"] = params.get("error", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Autorizacion recibida. Puedes cerrar esta pagina.")
            finished.set()

        def log_message(self, *_args):
            pass  # Never log authorization codes.

    with HTTPServer(("127.0.0.1", 0), Callback) as server:
        redirect = f"http://127.0.0.1:{server.server_port}/callback"
        client_response = requests.post(
            f"{SERVER}/register",
            json={
                "client_name": "Trading Signal account alerts",
                "redirect_uris": [redirect],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
                "scope": "quantfury.agent",
            },
            timeout=20,
        )
        client_response.raise_for_status()
        client_id = client_response.json()["client_id"]
        url = f"{SERVER}/authorize?" + urlencode({
            "response_type": "code", "client_id": client_id,
            "redirect_uri": redirect, "scope": "quantfury.agent",
            "resource": RESOURCE, "state": state,
            "code_challenge": challenge, "code_challenge_method": "S256",
        })
        print("Abriendo Quantfury en el navegador de este ordenador...")
        threading.Thread(target=server.serve_forever, daemon=True).start()
        webbrowser.open(url)
        if not finished.wait(180):
            raise TimeoutError("No se recibió autorización en tres minutos")
        server.shutdown()

    if received.get("error") or not received.get("code"):
        raise RuntimeError("Quantfury no autorizó la conexión")
    response = requests.post(
        f"{SERVER}/token",
        data={
            "grant_type": "authorization_code", "client_id": client_id,
            "redirect_uri": redirect, "code": received["code"],
            "code_verifier": verifier, "resource": RESOURCE,
        },
        timeout=20,
    )
    response.raise_for_status()
    tokens = response.json()
    refresh = tokens.get("refresh_token")
    if not refresh:
        raise RuntimeError("Quantfury no devolvió refresh_token; no se configuró GitHub")
    # GitHub CLI sends each value over TLS into encrypted Actions secrets.
    save_secret("QUANTFURY_CLIENT_ID", client_id)
    save_secret("QUANTFURY_REFRESH_TOKEN", refresh)
    pat = getpass(
        "Token GitHub limitado a Secrets: write para renovar credenciales (Intro para omitir): "
    ).strip()
    if pat:
        save_secret("GH_SECRETS_PAT", pat)
    print("Secretos guardados. Si omites el token GitHub, una rotación del refresh token detendrá el bot.")


if __name__ == "__main__":
    main()

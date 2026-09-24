"""Launch and retrieve an encrypted, read-only XRP review."""

from io import BytesIO
import uuid
import zipfile

import requests

from result_codec import open_message


REPOSITORY = "fjpereirag/trading-signal"
WORKFLOW = "main.yml"
API = f"https://api.github.com/repos/{REPOSITORY}"


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


def dispatch(token):
    if not token:
        raise ValueError("Falta el token de GitHub")
    request_id = uuid.uuid4().hex
    response = requests.post(
        f"{API}/actions/workflows/{WORKFLOW}/dispatches",
        headers=_headers(token), json={"ref": "main", "inputs": {"request_id": request_id}}, timeout=15,
    )
    response.raise_for_status()
    if response.status_code != 204:
        raise RuntimeError(f"GitHub no aceptó la consulta: HTTP {response.status_code}")
    return request_id


def check_result(token, request_id, password):
    """Return (state, message, run_url); never return data from another run."""
    if not token or len(request_id) != 32 or any(c not in "0123456789abcdef" for c in request_id):
        raise ValueError("Identificador de consulta inválido")
    response = requests.get(
        f"{API}/actions/workflows/{WORKFLOW}/runs",
        headers=_headers(token), params={"event": "workflow_dispatch", "per_page": 30}, timeout=15,
    )
    response.raise_for_status()
    runs = response.json().get("workflow_runs", [])
    run = next((item for item in runs if item.get("display_title") == f"Consulta XRP/USDT {request_id}"), None)
    if run is None:
        return "pending", "Esperando a que GitHub inicie la consulta…", None
    url = run["html_url"]
    if run.get("status") != "completed":
        return "pending", "Consultando Quantfury y Binance…", url
    if run.get("conclusion") != "success":
        return "failed", "La consulta falló. Abre los detalles de GitHub para ver el motivo.", url
    response = requests.get(f"{API}/actions/runs/{run['id']}/artifacts", headers=_headers(token), timeout=15)
    response.raise_for_status()
    artifact = next((a for a in response.json().get("artifacts", []) if a.get("name") == f"signal-{request_id}" and not a.get("expired")), None)
    if artifact is None:
        return "failed", "GitHub terminó sin guardar el resultado.", url
    response = requests.get(f"{API}/actions/artifacts/{artifact['id']}/zip", headers=_headers(token), timeout=15)
    response.raise_for_status()
    if len(response.content) > 128_000:
        raise ValueError("Resultado demasiado grande")
    with zipfile.ZipFile(BytesIO(response.content)) as archive:
        if archive.namelist() != ["result.json.enc"] or archive.getinfo("result.json.enc").file_size > 16_000:
            raise ValueError("Archivo de resultado inválido")
        payload = archive.read("result.json.enc")
    return "success", open_message(payload, password), url

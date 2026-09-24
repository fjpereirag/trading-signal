"""Dispatch the existing GitHub Actions workflow without exposing trading secrets."""

import requests

REPOSITORY = "fjpereirag/trading-signal"
WORKFLOW = "main.yml"


def dispatch(token):
    if not token:
        raise ValueError("Falta el token de GitHub para iniciar el workflow")
    response = requests.post(
        f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/{WORKFLOW}/dispatches",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"ref": "main", "inputs": {"test_telegram": "false", "report_telegram": "true"}},
        timeout=15,
    )
    response.raise_for_status()
    if response.status_code != 204:
        raise RuntimeError(f"GitHub no aceptó la ejecución: HTTP {response.status_code}")

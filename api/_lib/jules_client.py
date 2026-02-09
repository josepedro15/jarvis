"""
Jarvis - Cliente Jules API
Gerencia sessoes de coding do Jules (Google DeepMind).
"""
import httpx
from .config import JULES_API_KEY, JULES_API_URL


HEADERS = {
    "X-Goog-Api-Key": JULES_API_KEY,
    "Content-Type": "application/json"
}


async def list_repos() -> list:
    """Lista repositorios disponiveis no Jules."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{JULES_API_URL}/sources",
                headers=HEADERS
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("sources", [])
        except Exception as e:
            print(f"[JULES] Erro ao listar repos: {e}")
            return []


async def create_session(task: str, repo: str, branch: str = "main") -> dict:
    """Cria nova sessao de coding no Jules."""
    payload = {
        "prompt": task,
        "sourceContext": {
            "source": repo,
            "githubRepoContext": {"startingBranch": branch}
        },
        "automationMode": "AUTO_CREATE_PR",
        "title": f"Jarvis: {task[:50]}"
    }

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(
                f"{JULES_API_URL}/sessions",
                headers=HEADERS,
                json=payload
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": str(e)}


async def get_session_status(session_name: str) -> dict:
    """Verifica status de uma sessao Jules."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{JULES_API_URL}/{session_name}",
                headers=HEADERS
            )
            resp.raise_for_status()
            data = resp.json()

            # Determinar status
            state = data.get("state", "UNKNOWN")
            if state == "UNKNOWN" and data.get("outputs"):
                state = "COMPLETED"

            # Extrair PR URL se disponivel
            pr_url = None
            outputs = data.get("outputs", {})
            if isinstance(outputs, dict):
                pr_url = outputs.get("pullRequestUrl", None)

            return {
                "state": state,
                "pr_url": pr_url,
                "raw": data
            }
        except Exception as e:
            return {"state": "ERROR", "error": str(e)}


def format_repos_list(repos: list) -> str:
    """Formata lista de repos para exibicao no WhatsApp."""
    if not repos:
        return "Nenhum repositorio encontrado."

    lines = ["📂 *Seus Repositorios:*\n"]
    for i, repo in enumerate(repos, 1):
        name = repo.get("source", repo.get("name", "desconhecido"))
        # Extrair nome legivel
        display_name = name.replace("github/", "").replace("josepedro15/", "")
        lines.append(f"{i}. {display_name}")

    lines.append("\nResponda com o *numero* do repositorio que deseja usar.")
    return "\n".join(lines)

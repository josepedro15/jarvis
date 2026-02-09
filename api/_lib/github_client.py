"""
Jarvis - Cliente GitHub API
Gerencia repositorios e commits via GitHub API.
"""
import httpx
import base64
import json
from .config import GITHUB_TOKEN, GITHUB_OWNER


HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
BASE_URL = "https://api.github.com"


async def list_repos(per_page: int = 30) -> list:
    """Lista repositorios do usuario."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/user/repos",
                headers=HEADERS,
                params={"per_page": per_page, "sort": "updated", "direction": "desc"}
            )
            resp.raise_for_status()
            repos = resp.json()
            return [{"name": r["name"], "full_name": r["full_name"],
                      "url": r["html_url"], "description": r.get("description", ""),
                      "updated_at": r["updated_at"]} for r in repos]
        except Exception as e:
            print(f"[GITHUB] Erro ao listar repos: {e}")
            return []


async def create_repo(name: str, description: str = "", private: bool = False) -> dict:
    """Cria novo repositorio."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{BASE_URL}/user/repos",
                headers=HEADERS,
                json={
                    "name": name,
                    "description": description,
                    "private": private,
                    "auto_init": True
                }
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": str(e)}


async def create_or_update_file(repo: str, path: str, content: str,
                                  message: str, branch: str = "main") -> dict:
    """Cria ou atualiza arquivo no repositorio."""
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{BASE_URL}/repos/{GITHUB_OWNER}/{repo}/contents/{path}"

        # Verificar se arquivo ja existe (pegar sha)
        sha = None
        try:
            existing = await client.get(url, headers=HEADERS, params={"ref": branch})
            if existing.status_code == 200:
                sha = existing.json().get("sha")
        except Exception:
            pass

        # Criar/atualizar arquivo
        try:
            payload = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": branch
            }
            if sha:
                payload["sha"] = sha

            resp = await client.put(url, headers=HEADERS, json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


async def save_workflow_to_repo(repo_name: str, workflow_name: str,
                                 workflow_content: dict) -> dict:
    """Salva workflow N8N como arquivo JSON num repositorio."""
    # Sanitizar nome do arquivo
    safe_name = workflow_name.replace(" ", "_").replace("/", "_").lower()
    file_path = f"workflows/{safe_name}.json"
    content = json.dumps(workflow_content, indent=2, ensure_ascii=False)
    message = f"Sync workflow: {workflow_name}"

    return await create_or_update_file(repo_name, file_path, content, message)


async def get_repo_info(repo: str) -> dict:
    """Retorna informacoes de um repositorio."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/repos/{GITHUB_OWNER}/{repo}",
                headers=HEADERS
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

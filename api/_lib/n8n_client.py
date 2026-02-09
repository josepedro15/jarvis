"""
Jarvis - Cliente N8N API (SOMENTE LEITURA)
IMPORTANTE: Este modulo so faz operacoes GET.
Nunca fazer PUT, POST, DELETE ou PATCH na API do N8N.
"""
import httpx
from .config import N8N_API_KEY, N8N_BASE_URL


HEADERS = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Accept": "application/json"
}


async def get_workflows() -> list:
    """Lista todos os workflows do N8N. SOMENTE GET."""
    if not N8N_BASE_URL or not N8N_API_KEY:
        return []

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{N8N_BASE_URL}/api/v1/workflows",
                headers=HEADERS
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception as e:
            print(f"[N8N] Erro ao listar workflows: {e}")
            return []


async def get_workflow(workflow_id: str) -> dict:
    """Retorna detalhes de um workflow especifico. SOMENTE GET."""
    if not N8N_BASE_URL or not N8N_API_KEY:
        return {"error": "N8N nao configurado"}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}",
                headers=HEADERS
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


async def get_executions(workflow_id: str = None, status: str = None,
                          limit: int = 20) -> list:
    """Lista execucoes de workflows. SOMENTE GET."""
    if not N8N_BASE_URL or not N8N_API_KEY:
        return []

    params = {"limit": limit}
    if workflow_id:
        params["workflowId"] = workflow_id
    if status:
        params["status"] = status

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{N8N_BASE_URL}/api/v1/executions",
                headers=HEADERS,
                params=params
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception as e:
            print(f"[N8N] Erro ao listar execucoes: {e}")
            return []


async def get_error_executions(limit: int = 20) -> list:
    """Lista execucoes com erro. SOMENTE GET."""
    return await get_executions(status="error", limit=limit)


async def get_workflow_stats() -> dict:
    """Retorna estatisticas dos workflows. SOMENTE GET."""
    try:
        workflows = await get_workflows()
        all_executions = await get_executions(limit=100)
        error_executions = await get_error_executions(limit=100)

        # Contar workflows ativos
        active_count = sum(1 for w in workflows if w.get("active", False))

        return {
            "total_workflows": len(workflows),
            "active_workflows": active_count,
            "recent_executions": len(all_executions),
            "recent_errors": len(error_executions),
            "error_rate": round(len(error_executions) / max(len(all_executions), 1) * 100, 1)
        }
    except Exception as e:
        return {"error": str(e)}


def format_workflows_list(workflows: list) -> str:
    """Formata lista de workflows para exibicao no WhatsApp."""
    if not workflows:
        return "Nenhum workflow encontrado no N8N."

    lines = ["⚡ *Workflows N8N:*\n"]
    for i, wf in enumerate(workflows, 1):
        name = wf.get("name", "Sem nome")
        active = "✅" if wf.get("active", False) else "⏸️"
        lines.append(f"{i}. {active} {name}")

    return "\n".join(lines)


def format_errors_list(errors: list) -> str:
    """Formata lista de erros para exibicao no WhatsApp."""
    if not errors:
        return "✅ Nenhum erro recente no N8N!"

    lines = ["❌ *Erros Recentes no N8N:*\n"]
    for err in errors[:10]:
        wf_name = err.get("workflowData", {}).get("name", "?")
        finished = err.get("stoppedAt", "?")
        lines.append(f"• {wf_name} - {finished}")

    return "\n".join(lines)

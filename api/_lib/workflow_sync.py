"""
Jarvis - Workflow Sync Service
Sincroniza workflows do N8N com GitHub automaticamente.
IMPORTANTE: N8N API e SOMENTE LEITURA (GET).
"""
from . import n8n_client as n8n
from . import github_client as github
from . import supabase_client as db


# Nome do repo onde os workflows serao salvos
WORKFLOWS_REPO = "n8n-workflows-backup"


async def sync_workflows() -> dict:
    """
    Busca workflows novos no N8N e salva no GitHub.
    Retorna estatisticas da sincronizacao.
    """
    stats = {"checked": 0, "new": 0, "synced": 0, "errors": 0}

    try:
        # 1. Buscar todos workflows do N8N (GET)
        workflows = await n8n.get_workflows()
        stats["checked"] = len(workflows)

        if not workflows:
            db.log("n8n", "Nenhum workflow encontrado no N8N")
            return stats

        # 2. Para cada workflow, verificar se ja esta salvo
        for wf in workflows:
            wf_id = str(wf.get("id", ""))
            wf_name = wf.get("name", "sem-nome")

            if not wf_id:
                continue

            # Verificar se ja existe no banco
            existing = db.get_all_workflows()
            existing_ids = {w["n8n_workflow_id"] for w in existing}

            if wf_id not in existing_ids:
                # Workflow novo! Buscar detalhes completos (GET)
                full_workflow = await n8n.get_workflow(wf_id)
                if "error" in full_workflow:
                    db.log("n8n", f"Erro ao buscar workflow {wf_id}: {full_workflow['error']}",
                           level="error")
                    stats["errors"] += 1
                    continue

                # Salvar no banco
                db.save_n8n_workflow(wf_id, wf_name, full_workflow)
                stats["new"] += 1

                db.log("n8n", f"Novo workflow detectado: {wf_name} (ID: {wf_id})")

        # 3. Sincronizar workflows nao-syncados com GitHub
        unsynced = db.get_unsynced_workflows()
        for wf in unsynced:
            try:
                # Garantir que o repo existe
                repo_info = await github.get_repo_info(WORKFLOWS_REPO)
                if "error" in repo_info or not repo_info.get("name"):
                    # Criar repo
                    create_result = await github.create_repo(
                        WORKFLOWS_REPO,
                        description="Backup automatico dos workflows N8N pelo Jarvis",
                        private=True
                    )
                    if "error" in create_result:
                        db.log("github", f"Erro ao criar repo: {create_result['error']}",
                               level="error")
                        stats["errors"] += 1
                        continue

                # Salvar workflow no repo
                result = await github.save_workflow_to_repo(
                    WORKFLOWS_REPO,
                    wf["name"],
                    wf["content"]
                )

                if "error" not in result:
                    db.mark_workflow_synced(wf["n8n_workflow_id"], WORKFLOWS_REPO)
                    stats["synced"] += 1
                    db.log("github",
                           f"Workflow sincronizado: {wf['name']} -> {WORKFLOWS_REPO}",
                           details={"workflow_id": wf["n8n_workflow_id"]})
                else:
                    db.log("github", f"Erro ao salvar workflow: {result['error']}",
                           level="error")
                    stats["errors"] += 1

            except Exception as e:
                db.log("github", f"Erro na sincronizacao: {str(e)}", level="error")
                stats["errors"] += 1

    except Exception as e:
        db.log("n8n", f"Erro geral na sincronizacao: {str(e)}", level="error")
        stats["errors"] += 1

    return stats


async def check_n8n_errors() -> list:
    """Verifica erros recentes no N8N."""
    errors = await n8n.get_error_executions(limit=10)
    if errors:
        db.log("n8n", f"Encontrados {len(errors)} erros recentes",
               level="warn", details={"count": len(errors)})
    return errors

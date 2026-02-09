"""
Jarvis - Task Manager
Monitora sessoes Jules e envia notificacoes de status.
"""
from . import jules_client as jules
from . import whatsapp_gateway as whatsapp
from . import supabase_client as db


async def monitor_pending_sessions() -> dict:
    """
    Verifica status de todas as sessoes Jules pendentes.
    Envia notificacao WhatsApp quando uma sessao muda de status.
    """
    stats = {"checked": 0, "completed": 0, "failed": 0}

    pending = db.get_pending_sessions()
    if not pending:
        return stats

    for session in pending:
        session_id = session["session_id"]
        repo = session["repo_name"]
        phone = session.get("phone_number")

        stats["checked"] += 1

        try:
            # Verificar status no Jules
            status_data = await jules.get_session_status(session_id)
            state = status_data.get("state", "UNKNOWN")
            pr_url = status_data.get("pr_url")

            if state in ["SUCCEEDED", "COMPLETED"]:
                # Tarefa concluida com sucesso
                db.update_jules_session(session_id, state, pr_url)
                stats["completed"] += 1

                # Notificar via WhatsApp
                repo_name = repo.replace("github/", "").replace("josepedro15/", "")
                msg = f"✅ *Jules Concluiu!*\n\n📂 Repo: {repo_name}\n📊 Status: {state}"
                if pr_url:
                    msg += f"\n🔗 PR: {pr_url}"

                if phone:
                    await whatsapp.send_text(phone, msg)

                db.log("jules", f"Sessao concluida: {session_id}",
                       details={"repo": repo, "state": state, "pr_url": pr_url})

            elif state in ["FAILED", "CANCELLED"]:
                # Tarefa falhou
                db.update_jules_session(session_id, state)
                stats["failed"] += 1

                repo_name = repo.replace("github/", "").replace("josepedro15/", "")
                msg = f"❌ *Jules Falhou*\n\n📂 Repo: {repo_name}\n📊 Status: {state}"

                if phone:
                    await whatsapp.send_text(phone, msg)

                db.log("jules", f"Sessao falhou: {session_id}",
                       level="error", details={"repo": repo, "state": state})

            elif state == "ERROR":
                db.log("jules", f"Erro ao checar sessao: {session_id}",
                       level="warn", details=status_data)

        except Exception as e:
            db.log("jules", f"Erro ao monitorar sessao {session_id}: {str(e)}",
                   level="error")

    return stats

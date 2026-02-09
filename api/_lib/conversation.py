"""
Jarvis - Conversation Engine (State Machine)
Gerencia o fluxo de conversacao via WhatsApp.
Processa mensagens, identifica intencoes e executa acoes.
"""
import json
from . import supabase_client as db
from . import gemini_client as ai
from . import jules_client as jules
from . import github_client as github
from . import n8n_client as n8n
from . import whatsapp_gateway as whatsapp
from .config import ALLOWED_PHONE


async def process_message(phone: str, text: str) -> str:
    """
    Processa uma mensagem recebida e retorna a resposta.
    Este e o ponto central de toda a logica conversacional.
    """
    # 1. Verificar whitelist
    if not db.is_number_allowed(phone):
        db.log("whatsapp", f"Mensagem rejeitada de numero nao autorizado: {phone}",
               level="warn", details={"phone": phone, "text": text})
        return None  # Nao responder

    # 2. Log da mensagem recebida
    db.log("whatsapp", f"Mensagem recebida de {phone}: {text[:100]}",
           details={"phone": phone})

    # 3. Verificar estado atual da conversa
    state = db.get_conversation_state(phone)
    current_state = state.get("current_state", "idle")
    state_data = state.get("state_data", {})

    # 4. Processar de acordo com o estado
    try:
        if current_state == "waiting_repo_confirm":
            return await handle_repo_confirmation(phone, text, state_data)
        elif current_state == "waiting_task_description":
            return await handle_task_description(phone, text, state_data)
        else:
            return await handle_general_message(phone, text)
    except Exception as e:
        db.log("ai", f"Erro ao processar mensagem: {str(e)}",
               level="error", details={"phone": phone, "error": str(e)})
        return "Desculpe, ocorreu um erro. Tente novamente."


async def handle_general_message(phone: str, text: str) -> str:
    """Processa mensagem geral usando o Gemini para classificar intencao."""
    # Adicionar contexto sobre o estado atual
    pending = db.get_pending_sessions()
    extra_context = ""
    if pending:
        pending_info = [f"- {s['repo_name']}: {s['status']}" for s in pending[:5]]
        extra_context = f"Tarefas em andamento:\n" + "\n".join(pending_info)

    # Enviar para o Gemini
    response = await ai.chat(phone, text, extra_context=extra_context)

    # Tentar extrair intent do response
    intent_data, clean_text = ai.parse_intent(response)

    if intent_data:
        intent_type = intent_data.get("intent", "general")
        params = intent_data.get("params", {})

        if intent_type == "jules_task":
            return await start_jules_flow(phone, params.get("task_description", text))
        elif intent_type == "list_repos":
            return await list_repos_flow(phone)
        elif intent_type == "jules_status":
            return await check_status_flow(phone)
        elif intent_type == "n8n_query":
            return await n8n_query_flow(phone, params.get("query_type", "workflows"))
        elif intent_type == "cancel":
            db.update_conversation_state(phone, "idle", {})
            return clean_text or "Acao cancelada! Como posso ajudar?"

    # Retornar resposta limpa (sem JSON)
    return clean_text or response


async def start_jules_flow(phone: str, task_description: str) -> str:
    """Inicia fluxo de criacao de tarefa Jules - lista repos primeiro."""
    db.log("jules", f"Iniciando fluxo Jules para {phone}: {task_description}")

    # Buscar repos do Jules
    repos = await jules.list_repos()

    if not repos:
        # Fallback: buscar do GitHub
        gh_repos = await github.list_repos(per_page=15)
        repos = [{"source": f"github/{r['full_name']}"} for r in gh_repos]

    if not repos:
        return "Nao encontrei repositorios disponiveis. Verifique suas configuracoes."

    # Salvar estado
    db.update_conversation_state(phone, "waiting_repo_confirm", {
        "task_description": task_description,
        "repos": [r.get("source", r.get("name", "")) for r in repos]
    })

    return jules.format_repos_list(repos)


async def list_repos_flow(phone: str) -> str:
    """Lista repositorios disponiveis."""
    repos = await jules.list_repos()
    if not repos:
        gh_repos = await github.list_repos(per_page=15)
        repos = [{"source": f"github/{r['full_name']}"} for r in gh_repos]

    return jules.format_repos_list(repos)


async def handle_repo_confirmation(phone: str, text: str, state_data: dict) -> str:
    """Processa confirmacao de repositorio pelo usuario."""
    repos = state_data.get("repos", [])
    task = state_data.get("task_description", "")

    # Tentar interpretar como numero
    selected_repo = None
    try:
        index = int(text.strip()) - 1
        if 0 <= index < len(repos):
            selected_repo = repos[index]
    except ValueError:
        # Tentar match por nome
        text_lower = text.strip().lower()
        for repo in repos:
            if text_lower in repo.lower():
                selected_repo = repo
                break

    if text.strip().lower() in ["cancelar", "cancel", "sair", "0"]:
        db.update_conversation_state(phone, "idle", {})
        return "Acao cancelada! Como posso ajudar?"

    if not selected_repo:
        return f"Nao entendi. Envie o *numero* (1-{len(repos)}) do repositorio ou 'cancelar'."

    # Repositorio confirmado - pedir descricao detalhada da tarefa se necessario
    if not task or task in ["editar codigo", "editar", "codigo"]:
        db.update_conversation_state(phone, "waiting_task_description", {
            "repo": selected_repo
        })
        repo_name = selected_repo.replace("github/", "").replace("josepedro15/", "")
        return f"Repositorio selecionado: *{repo_name}*\n\nAgora descreva a tarefa que deseja que o Jules execute nesse repositorio:"

    # Criar sessao Jules
    return await execute_jules_task(phone, selected_repo, task)


async def handle_task_description(phone: str, text: str, state_data: dict) -> str:
    """Processa descricao da tarefa apos confirmacao do repo."""
    repo = state_data.get("repo", "")

    if text.strip().lower() in ["cancelar", "cancel", "sair"]:
        db.update_conversation_state(phone, "idle", {})
        return "Acao cancelada! Como posso ajudar?"

    return await execute_jules_task(phone, repo, text)


async def execute_jules_task(phone: str, repo: str, task: str) -> str:
    """Executa criacao de tarefa no Jules."""
    repo_name = repo.replace("github/", "").replace("josepedro15/", "")

    # Notificar que esta criando
    db.log("jules", f"Criando sessao Jules: {repo} - {task}")

    # Criar sessao no Jules
    result = await jules.create_session(task, repo)

    if "error" in result:
        db.update_conversation_state(phone, "idle", {})
        db.log("jules", f"Erro ao criar sessao: {result['error']}",
               level="error", details=result)
        return f"Erro ao criar tarefa no Jules: {result['error']}"

    session_name = result.get("name", "")

    # Salvar no banco
    db.create_jules_session(session_name, repo, task, phone)
    db.update_conversation_state(phone, "idle", {})
    db.log("jules", f"Sessao criada: {session_name}", details={"repo": repo, "task": task})

    return (
        f"🚀 *Tarefa enviada para o Jules!*\n\n"
        f"📂 Repo: {repo_name}\n"
        f"📝 Tarefa: {task}\n"
        f"🔖 Sessao: {session_name}\n\n"
        f"Vou te avisar quando terminar!"
    )


async def check_status_flow(phone: str) -> str:
    """Verifica status de tarefas em andamento."""
    pending = db.get_pending_sessions()

    if not pending:
        recent = db.get_jules_sessions(limit=5)
        if not recent:
            return "Nenhuma tarefa encontrada."

        lines = ["📋 *Tarefas Recentes:*\n"]
        for s in recent:
            emoji = {"COMPLETED": "✅", "SUCCEEDED": "✅", "FAILED": "❌",
                     "CANCELLED": "🚫", "PENDING": "⏳"}.get(s["status"], "❓")
            repo_name = s["repo_name"].replace("github/", "").replace("josepedro15/", "")
            lines.append(f"{emoji} {repo_name} - {s['status']}")
            if s.get("pr_url"):
                lines.append(f"   PR: {s['pr_url']}")
        return "\n".join(lines)

    lines = ["⏳ *Tarefas em Andamento:*\n"]
    for s in pending:
        repo_name = s["repo_name"].replace("github/", "").replace("josepedro15/", "")
        task = s.get("task_description", "")[:50]
        lines.append(f"• {repo_name}: {task}")

    lines.append(f"\n_Total: {len(pending)} tarefa(s) pendente(s)_")
    return "\n".join(lines)


async def n8n_query_flow(phone: str, query_type: str) -> str:
    """Processa consultas sobre N8N."""
    if query_type == "errors":
        errors = await n8n.get_error_executions()
        return n8n.format_errors_list(errors)
    elif query_type == "executions":
        stats = await n8n.get_workflow_stats()
        if "error" in stats:
            return f"Erro ao consultar N8N: {stats['error']}"
        return (
            f"📊 *Estatisticas N8N:*\n\n"
            f"Total workflows: {stats['total_workflows']}\n"
            f"Ativos: {stats['active_workflows']}\n"
            f"Execucoes recentes: {stats['recent_executions']}\n"
            f"Erros recentes: {stats['recent_errors']}\n"
            f"Taxa de erro: {stats['error_rate']}%"
        )
    else:
        workflows = await n8n.get_workflows()
        return n8n.format_workflows_list(workflows)

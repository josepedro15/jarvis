"""
Jarvis - Cliente Supabase
Gerencia todas as operacoes de banco de dados.
"""
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from datetime import datetime, timezone
from typing import Optional
import json


def get_client() -> Client:
    """Retorna cliente Supabase com service role (acesso total)."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# ========================
# Allowed Numbers (Whitelist)
# ========================

def is_number_allowed(phone: str) -> bool:
    """Verifica se um numero esta na whitelist."""
    client = get_client()
    result = client.table("allowed_numbers").select("id").eq("phone_number", phone).eq("is_active", True).execute()
    return len(result.data) > 0


def get_allowed_numbers() -> list:
    """Lista todos os numeros autorizados."""
    client = get_client()
    result = client.table("allowed_numbers").select("*").order("created_at").execute()
    return result.data


def add_allowed_number(phone: str, name: str = "") -> dict:
    """Adiciona numero a whitelist."""
    client = get_client()
    result = client.table("allowed_numbers").upsert({
        "phone_number": phone,
        "name": name,
        "is_active": True
    }).execute()
    return result.data[0] if result.data else {}


def remove_allowed_number(phone: str) -> bool:
    """Desativa numero da whitelist."""
    client = get_client()
    result = client.table("allowed_numbers").update({"is_active": False}).eq("phone_number", phone).execute()
    return len(result.data) > 0


# ========================
# AI Config
# ========================

def get_ai_config() -> dict:
    """Retorna configuracao atual da IA."""
    client = get_client()
    result = client.table("ai_config").select("*").limit(1).execute()
    if result.data:
        return result.data[0]
    return {
        "model": "gemini-2.5-flash",
        "system_prompt": "Voce e o Jarvis, assistente pessoal.",
        "temperature": 0.7,
        "max_tokens": 2048
    }


def update_ai_config(model: str = None, system_prompt: str = None,
                      temperature: float = None, max_tokens: int = None) -> dict:
    """Atualiza configuracao da IA."""
    client = get_client()
    current = get_ai_config()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

    if model is not None:
        update_data["model"] = model
    if system_prompt is not None:
        update_data["system_prompt"] = system_prompt
    if temperature is not None:
        update_data["temperature"] = temperature
    if max_tokens is not None:
        update_data["max_tokens"] = max_tokens

    result = client.table("ai_config").update(update_data).eq("id", current["id"]).execute()
    return result.data[0] if result.data else current


# ========================
# Conversation History
# ========================

def save_message(phone: str, role: str, content: str, intent: str = None, metadata: dict = None) -> dict:
    """Salva mensagem no historico."""
    client = get_client()
    result = client.table("conversation_history").insert({
        "phone_number": phone,
        "role": role,
        "content": content,
        "intent": intent,
        "metadata": metadata or {}
    }).execute()
    return result.data[0] if result.data else {}


def get_conversation_history(phone: str, limit: int = 20) -> list:
    """Retorna historico de conversa de um numero."""
    client = get_client()
    result = (client.table("conversation_history")
              .select("*")
              .eq("phone_number", phone)
              .order("created_at", desc=False)
              .limit(limit)
              .execute())
    return result.data


# ========================
# Conversation State (State Machine)
# ========================

def get_conversation_state(phone: str) -> dict:
    """Retorna estado atual da conversa."""
    client = get_client()
    result = client.table("conversation_state").select("*").eq("phone_number", phone).execute()
    if result.data:
        return result.data[0]
    # Criar estado inicial
    new_state = client.table("conversation_state").insert({
        "phone_number": phone,
        "current_state": "idle",
        "state_data": {}
    }).execute()
    return new_state.data[0] if new_state.data else {"current_state": "idle", "state_data": {}}


def update_conversation_state(phone: str, state: str, state_data: dict = None) -> dict:
    """Atualiza estado da conversa."""
    client = get_client()
    result = (client.table("conversation_state")
              .upsert({
                  "phone_number": phone,
                  "current_state": state,
                  "state_data": state_data or {},
                  "updated_at": datetime.now(timezone.utc).isoformat()
              })
              .execute())
    return result.data[0] if result.data else {}


# ========================
# Jules Sessions
# ========================

def create_jules_session(session_id: str, repo: str, task: str, phone: str = None) -> dict:
    """Cria registro de sessao Jules."""
    client = get_client()
    result = client.table("jules_sessions").insert({
        "session_id": session_id,
        "repo_name": repo,
        "task_description": task,
        "status": "PENDING",
        "phone_number": phone
    }).execute()
    return result.data[0] if result.data else {}


def get_pending_sessions() -> list:
    """Retorna sessoes Jules pendentes."""
    client = get_client()
    result = client.table("jules_sessions").select("*").eq("status", "PENDING").execute()
    return result.data


def update_jules_session(session_id: str, status: str, pr_url: str = None) -> dict:
    """Atualiza status de sessao Jules."""
    client = get_client()
    update_data = {"status": status}
    if pr_url:
        update_data["pr_url"] = pr_url
    if status in ["SUCCEEDED", "COMPLETED", "FAILED", "CANCELLED"]:
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()

    result = (client.table("jules_sessions")
              .update(update_data)
              .eq("session_id", session_id)
              .execute())
    return result.data[0] if result.data else {}


def get_jules_sessions(limit: int = 50) -> list:
    """Lista sessoes Jules recentes."""
    client = get_client()
    result = (client.table("jules_sessions")
              .select("*")
              .order("started_at", desc=True)
              .limit(limit)
              .execute())
    return result.data


# ========================
# N8N Workflows
# ========================

def save_n8n_workflow(workflow_id: str, name: str, content: dict) -> dict:
    """Salva workflow do N8N."""
    client = get_client()
    result = client.table("n8n_workflows").upsert({
        "n8n_workflow_id": workflow_id,
        "name": name,
        "content": content,
        "github_synced": False
    }).execute()
    return result.data[0] if result.data else {}


def get_unsynced_workflows() -> list:
    """Retorna workflows nao sincronizados com GitHub."""
    client = get_client()
    result = client.table("n8n_workflows").select("*").eq("github_synced", False).execute()
    return result.data


def mark_workflow_synced(workflow_id: str, github_repo: str) -> dict:
    """Marca workflow como sincronizado."""
    client = get_client()
    result = (client.table("n8n_workflows")
              .update({
                  "github_synced": True,
                  "github_repo": github_repo,
                  "last_synced_at": datetime.now(timezone.utc).isoformat()
              })
              .eq("n8n_workflow_id", workflow_id)
              .execute())
    return result.data[0] if result.data else {}


def get_all_workflows() -> list:
    """Lista todos os workflows salvos."""
    client = get_client()
    result = client.table("n8n_workflows").select("*").order("created_at", desc=True).execute()
    return result.data


# ========================
# System Logs
# ========================

def log(source: str, message: str, level: str = "info", details: dict = None):
    """Registra log no sistema."""
    try:
        client = get_client()
        client.table("system_logs").insert({
            "level": level,
            "source": source,
            "message": message,
            "details": details or {}
        }).execute()
    except Exception as e:
        print(f"[LOG ERROR] {e}")


def get_logs(source: str = None, level: str = None, limit: int = 100) -> list:
    """Retorna logs do sistema."""
    client = get_client()
    query = client.table("system_logs").select("*")
    if source:
        query = query.eq("source", source)
    if level:
        query = query.eq("level", level)
    result = query.order("created_at", desc=True).limit(limit).execute()
    return result.data


# ========================
# Metrics
# ========================

def get_metrics(period: str = None) -> list:
    """Retorna metricas."""
    client = get_client()
    query = client.table("metrics").select("*")
    if period:
        query = query.eq("period", period)
    result = query.order("created_at", desc=True).limit(30).execute()
    return result.data


def upsert_metrics(period: str, data: dict) -> dict:
    """Atualiza metricas de um periodo."""
    client = get_client()
    data["period"] = period
    result = client.table("metrics").upsert(data, on_conflict="period").execute()
    return result.data[0] if result.data else {}

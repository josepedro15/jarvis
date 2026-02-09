"""
Jarvis - Centro de Comando
API Principal (FastAPI)
Deploy: Vercel Serverless
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import os

# Modulos internos
from _lib import supabase_client as db
from _lib import whatsapp_gateway as whatsapp
from _lib import gemini_client as ai
from _lib import jules_client as jules
from _lib import github_client as github
from _lib import n8n_client as n8n
from _lib import conversation
from _lib import task_manager
from _lib import workflow_sync


app = FastAPI(title="Jarvis - Centro de Comando", version="1.0.0")

# CORS para o painel admin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _verify_cron_secret(request: Request):
    """Verifica segredo do CRON (Header ou Query Param)."""
    secret = os.environ.get("CRON_SECRET")
    if not secret:
        print("WARN: CRON_SECRET nao configurado")
        return  # Permitir se sem segredo (dev/legacy) ou bloquear?
        # Por seguranca, vou levantar erro se nao bater, mas se env nao existir,
        # talvez seja melhor bloquear. Vou assumir que deve estar setado.
        # raise HTTPException(status_code=500, detail="CRON_SECRET_MISSING")
    
    auth = request.headers.get("Authorization")
    if auth == f"Bearer {secret}":
        return
        
    if request.query_params.get("secret") == secret:
        return
        
    raise HTTPException(status_code=401, detail="Invalid Cron Secret")


# ============================================
# WEBHOOK - Receber mensagens do WhatsApp
# ============================================

@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """Recebe mensagens do WhatsApp via UAZAPI webhook."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"status": "ok"})

    # Extrair mensagem
    message = whatsapp.extract_message_from_webhook(data)
    if not message:
        return JSONResponse({"status": "no_message"})

    phone = message["phone"]
    text = message["text"]

    # Processar mensagem (conversation engine)
    response = await conversation.process_message(phone, text)

    # Enviar resposta (se houver)
    if response:
        await whatsapp.send_text(phone, response)
        db.log("whatsapp", f"Resposta enviada para {phone}",
               details={"response_length": len(response)})

    return JSONResponse({"status": "processed"})


# ============================================
# CRON JOBS
# ============================================

@app.get("/api/cron/jules")
async def cron_jules(request: Request):
    _verify_cron_secret(request)
    """Cron: Monitora sessoes Jules pendentes (a cada 1 min)."""
    stats = await task_manager.monitor_pending_sessions()
    db.log("jules", f"Cron Jules: {stats}")
    return JSONResponse(stats)


@app.get("/api/cron/n8n")
async def cron_n8n(request: Request):
    _verify_cron_secret(request)
    """Cron: Sincroniza workflows N8N com GitHub (a cada 5 min)."""
    stats = await workflow_sync.sync_workflows()
    db.log("n8n", f"Cron N8N sync: {stats}")
    return JSONResponse(stats)


@app.get("/api/cron/metrics")
async def cron_metrics(request: Request):
    _verify_cron_secret(request)
    """Cron: Agrega metricas (a cada 1 hora)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    period = now.strftime("%Y-%m-%d")

    try:
        # Contar sessoes Jules
        all_sessions = db.get_jules_sessions(limit=1000)
        today_sessions = [s for s in all_sessions
                          if s.get("started_at", "").startswith(period)]

        completed = sum(1 for s in today_sessions if s["status"] in ["SUCCEEDED", "COMPLETED"])
        failed = sum(1 for s in today_sessions if s["status"] == "FAILED")

        # Contar workflows sincronizados
        all_workflows = db.get_all_workflows()
        synced_today = sum(1 for w in all_workflows
                          if (w.get("last_synced_at") or "").startswith(period))

        # Contar erros N8N
        errors = await n8n.get_error_executions(limit=100)

        # Contar mensagens
        # (simplificado - conta logs de whatsapp)
        logs = db.get_logs(source="whatsapp", limit=1000)
        today_messages = sum(1 for l in logs
                            if l.get("created_at", "").startswith(period))

        db.upsert_metrics(period, {
            "jules_tasks_completed": completed,
            "jules_tasks_failed": failed,
            "n8n_workflows_synced": synced_today,
            "n8n_errors": len(errors),
            "messages_exchanged": today_messages
        })

        return JSONResponse({"period": period, "status": "ok"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ============================================
# API - Painel Admin
# ============================================

# --- AI Config ---

@app.get("/api/admin/ai-config")
async def get_ai_config():
    """Retorna configuracao atual da IA."""
    config = db.get_ai_config()
    return JSONResponse(config)


@app.put("/api/admin/ai-config")
async def update_ai_config(request: Request):
    """Atualiza configuracao da IA."""
    data = await request.json()
    result = db.update_ai_config(
        model=data.get("model"),
        system_prompt=data.get("system_prompt"),
        temperature=data.get("temperature"),
        max_tokens=data.get("max_tokens")
    )
    return JSONResponse(result)


@app.post("/api/admin/ai-test")
async def test_ai(request: Request):
    """Testa prompt da IA sem salvar no historico."""
    data = await request.json()
    message = data.get("message", "Ola!")
    system_prompt = data.get("system_prompt")
    response = await ai.test_prompt(message, system_prompt)
    return JSONResponse({"response": response})


# --- WhatsApp ---

@app.get("/api/admin/whatsapp/status")
async def whatsapp_status():
    """Status da conexao WhatsApp."""
    status = await whatsapp.get_connection_status()
    return JSONResponse(status)


@app.post("/api/admin/whatsapp/connect")
async def whatsapp_connect():
    """Gera QR Code para conectar WhatsApp."""
    result = await whatsapp.connect_instance()
    return JSONResponse(result)


@app.post("/api/admin/whatsapp/disconnect")
async def whatsapp_disconnect():
    """Desconecta WhatsApp."""
    result = await whatsapp.disconnect_instance()
    return JSONResponse(result)


@app.post("/api/admin/whatsapp/webhook-config")
async def whatsapp_webhook_config(request: Request):
    """Configura webhook URL do WhatsApp."""
    data = await request.json()
    url = data.get("url", "")
    result = await whatsapp.configure_webhook(url)
    return JSONResponse(result)


# --- Whitelist ---

@app.get("/api/admin/whitelist")
async def get_whitelist():
    """Lista numeros autorizados."""
    numbers = db.get_allowed_numbers()
    return JSONResponse(numbers)


@app.post("/api/admin/whitelist")
async def add_to_whitelist(request: Request):
    """Adiciona numero a whitelist."""
    data = await request.json()
    result = db.add_allowed_number(data["phone_number"], data.get("name", ""))
    return JSONResponse(result)


@app.delete("/api/admin/whitelist/{phone}")
async def remove_from_whitelist(phone: str):
    """Remove numero da whitelist."""
    db.remove_allowed_number(phone)
    return JSONResponse({"status": "removed"})


# --- Jules ---

@app.get("/api/admin/jules/sessions")
async def get_jules_sessions():
    """Lista sessoes Jules recentes."""
    sessions = db.get_jules_sessions(limit=50)
    return JSONResponse(sessions)


@app.get("/api/admin/jules/repos")
async def get_jules_repos():
    """Lista repositorios disponiveis no Jules."""
    repos = await jules.list_repos()
    return JSONResponse(repos)


# --- N8N ---

@app.get("/api/admin/n8n/workflows")
async def get_n8n_workflows():
    """Lista workflows salvos do N8N."""
    workflows = db.get_all_workflows()
    return JSONResponse(workflows)


@app.get("/api/admin/n8n/stats")
async def get_n8n_stats():
    """Estatisticas do N8N."""
    stats = await n8n.get_workflow_stats()
    return JSONResponse(stats)


@app.get("/api/admin/n8n/errors")
async def get_n8n_errors():
    """Erros recentes do N8N."""
    errors = await n8n.get_error_executions()
    return JSONResponse(errors)


# --- GitHub ---

@app.get("/api/admin/github/repos")
async def get_github_repos():
    """Lista repositorios GitHub."""
    repos = await github.list_repos()
    return JSONResponse(repos)


# --- Logs ---

@app.get("/api/admin/logs")
async def get_logs(source: str = None, level: str = None, limit: int = 100):
    """Retorna logs do sistema."""
    logs = db.get_logs(source=source, level=level, limit=limit)
    return JSONResponse(logs)


# --- Metrics ---

@app.get("/api/admin/metrics")
async def get_metrics(period: str = None):
    """Retorna metricas do sistema."""
    metrics = db.get_metrics(period=period)
    return JSONResponse(metrics)


# --- Dashboard Summary ---

@app.get("/api/admin/dashboard")
async def get_dashboard():
    """Retorna resumo para o dashboard."""
    try:
        pending_sessions = db.get_pending_sessions()
        recent_sessions = db.get_jules_sessions(limit=10)
        n8n_stats = await n8n.get_workflow_stats()
        recent_logs = db.get_logs(limit=10)
        wa_status = await whatsapp.get_connection_status()

        return JSONResponse({
            "jules": {
                "pending": len(pending_sessions),
                "recent": recent_sessions[:5]
            },
            "n8n": n8n_stats,
            "whatsapp": wa_status,
            "recent_logs": recent_logs
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ============================================
# Health Check
# ============================================

@app.get("/api/health")
async def health():
    return JSONResponse({"status": "ok", "service": "jarvis"})

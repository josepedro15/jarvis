"""
Jarvis - WhatsApp Gateway (UAZAPI)
Gerencia conexao, envio e recebimento de mensagens via UAZAPI.
Baseado nos padroes do projeto Batepapo.
"""
import httpx
from .config import UAZAPI_BASE_URL, UAZAPI_ADMIN_TOKEN, UAZAPI_INSTANCE_TOKEN


async def send_text(phone: str, text: str, instance_token: str = None) -> dict:
    """Envia mensagem de texto via WhatsApp."""
    token = instance_token or UAZAPI_INSTANCE_TOKEN
    if not token:
        print("[WHATSAPP] Token nao configurado")
        return {"error": "Token nao configurado"}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{UAZAPI_BASE_URL}/send/text",
                headers={"token": token},
                json={"number": phone, "text": text}
            )
            return resp.json()
        except Exception as e:
            print(f"[WHATSAPP] Erro ao enviar: {e}")
            return {"error": str(e)}


async def create_instance(name: str = "jarvis") -> dict:
    """Cria nova instancia WhatsApp na UAZAPI."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{UAZAPI_BASE_URL}/instance/init",
                headers={"admintoken": UAZAPI_ADMIN_TOKEN},
                json={"name": name}
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


async def connect_instance(instance_token: str = None) -> dict:
    """Gera QR Code para conectar WhatsApp."""
    token = instance_token or UAZAPI_INSTANCE_TOKEN
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{UAZAPI_BASE_URL}/instance/connect",
                headers={"token": token}
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


async def get_connection_status(instance_token: str = None) -> dict:
    """Verifica status da conexao WhatsApp."""
    token = instance_token or UAZAPI_INSTANCE_TOKEN
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{UAZAPI_BASE_URL}/instance/status",
                headers={"token": token}
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


async def disconnect_instance(instance_token: str = None) -> dict:
    """Desconecta instancia WhatsApp."""
    token = instance_token or UAZAPI_INSTANCE_TOKEN
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{UAZAPI_BASE_URL}/instance/disconnect",
                headers={"token": token}
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


async def configure_webhook(webhook_url: str, instance_token: str = None) -> dict:
    """Configura webhook para receber mensagens."""
    token = instance_token or UAZAPI_INSTANCE_TOKEN
    config = {
        "enabled": True,
        "url": webhook_url,
        "events": ["messages", "connection", "messages_update"],
        "excludeMessages": ["wasSentByApi"]
    }
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{UAZAPI_BASE_URL}/webhook",
                headers={"token": token},
                json=config
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


async def list_instances() -> dict:
    """Lista todas as instancias."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{UAZAPI_BASE_URL}/instance/all",
                headers={"admintoken": UAZAPI_ADMIN_TOKEN}
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


def extract_message_from_webhook(data: dict) -> dict | None:
    """
    Extrai dados relevantes de um webhook de mensagem recebida.
    Retorna None se nao for uma mensagem de texto valida.
    """
    if not data:
        return None

    # Formato UAZAPI webhook
    event = data.get("event", "")

    if event == "messages":
        messages = data.get("data", {})
        if isinstance(messages, dict):
            message_data = messages
        elif isinstance(messages, list) and len(messages) > 0:
            message_data = messages[0]
        else:
            return None

        # Ignorar mensagens enviadas pelo proprio bot
        if message_data.get("fromMe", False):
            return None

        # Extrair numero do remetente
        remote_jid = message_data.get("remoteJid", "") or message_data.get("key", {}).get("remoteJid", "")
        phone = remote_jid.replace("@s.whatsapp.net", "").replace("@g.us", "")

        # Extrair texto da mensagem
        text = ""
        msg = message_data.get("message", {})
        if isinstance(msg, dict):
            text = (msg.get("conversation", "") or
                    msg.get("extendedTextMessage", {}).get("text", "") or
                    msg.get("text", ""))
        elif isinstance(msg, str):
            text = msg

        # Fallback: campo body direto
        if not text:
            text = message_data.get("body", "") or message_data.get("text", "")

        if not phone or not text:
            return None

        return {
            "phone": phone,
            "text": text.strip(),
            "message_id": message_data.get("key", {}).get("id", ""),
            "timestamp": message_data.get("messageTimestamp", ""),
            "raw": message_data
        }

    return None

import os
import requests
import json
from dotenv import load_dotenv

# Load env variables
load_dotenv()

API_URL = os.getenv("WHATSAPP_API_URL")
API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
TARGET_NUMBER = os.getenv("WHATSAPP_NUMBER")

def send_whatsapp_message(text):
    """
    Sends a text message via WhatsApp using the configured API.
    """
    if not all([API_URL, API_TOKEN, TARGET_NUMBER]):
        print("⚠️  Aviso: Credenciais do WhatsApp não configuradas no .env. Notificação pulada.")
        return

    headers = {
        "token": API_TOKEN
    }
    
    payload = {
        "number": TARGET_NUMBER,
        "text": text
    }

    try:
        print(f"📨 Enviando notificação para {TARGET_NUMBER}...")
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        print("✅ Notificação enviada com sucesso!")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar notificação: {e}")
        if response is not None:
             print(f"Detalhes: {response.text}")

if __name__ == "__main__":
    # Test execution
    send_whatsapp_message("🔔 Teste do Jules Command Center: O sistema de notificação está funcionando!")

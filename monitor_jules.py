import os
import sys
import time
import requests
from dotenv import load_dotenv

# Fix name collision with local 'convex' folder
# We must ensure we import the installed library, not the local folder.
# sys.path[0] is usually the script's directory.
params_path = sys.path[0]
if os.path.exists(os.path.join(params_path, "convex")):
    # If we are in the directory containing the 'convex' folder,
    # temporarily remove it from path to allow importing the library.
    sys.path.pop(0)

try:
    from convex import ConvexClient
except ImportError:
    # If that fails, restore path and try again (fallback, though unlikely to help if lib is missing)
    sys.path.insert(0, params_path)
    # Re-raise or handle
    raise

# Restore path for other imports if needed (though we only need notify which is local)
sys.path.insert(0, params_path)

from notify import send_whatsapp_message

# Load environment variables
load_dotenv()

JULES_API_KEY = os.getenv("JULES_API_KEY")
JULES_API_URL = "https://jules.googleapis.com/v1alpha"

def get_convex():
    url = os.getenv("CONVEX_URL")
    if not url:
        print("❌ Erro: CONVEX_URL não configurada.")
        return None
    return ConvexClient(url)

def check_status():
    """Checks for pending sessions and updates their status."""
    client = get_convex()
    if not client:
        return

    print("🔎 Verificando tarefas pendentes...")
    
    try:
        # 1. Get Pending Sessions from Convex
        pending_sessions = client.query("tasks:getPending")
    except Exception as e:
        print(f"❌ Erro ao consultar Convex: {e}")
        return

    if not pending_sessions:
        print("   Nenhuma tarefa pendente.")
        return

    headers = {"X-Goog-Api-Key": JULES_API_KEY}

    for session in pending_sessions:
        session_name = session.get('session_id')
        row_id = session.get('_id')
        repo = session.get('repo_name')
        
        if not session_name:
            continue

        print(f"   Analizando sessão: {session_name} ({repo})")

        # 2. Check Jules Status
        # The API URL for a specific session is .../sessions/{session_id} or just .../{session_name} 
        # api/index.py uses: f"https://jules.googleapis.com/v1alpha/{session_name}"
        real_url = f"{JULES_API_URL}/{session_name}"
        
        try:
            r = requests.get(real_url, headers=headers)
            if r.status_code == 200:
                jules_data = r.json()
                status = jules_data.get('state', 'UNKNOWN')
                
                # Check for outputs/PR to confirm completion even if state assumes otherwise?
                # api/index.py logic: if status == "UNKNOWN" and jules_data.get('outputs'): status = "COMPLETED"
                if status == "UNKNOWN" and jules_data.get('outputs'):
                     status = "COMPLETED"

                print(f"      Status: {status}")

                if status in ["SUCCEEDED", "COMPLETED", "FAILED", "CANCELLED"]:
                    print(f"      ---> Marcando como finalizado no Convex...")
                    # 3. Update Convex
                    client.mutation("tasks:markDone", {"id": row_id, "status": status})
                    
                    # 4. Notify
                    emoji = "✅" if status in ["SUCCEEDED", "COMPLETED"] else "❌"
                    msg = f"{emoji} *Jules Finalizou!*\n\nRepo: {repo}\nStatus: {status}\nVerifique o PR no GitHub."
                    send_whatsapp_message(msg)

            else:
                print(f"      Erro na API Jules: {r.status_code} - {r.text}")

        except Exception as e:
            print(f"      Erro ao verificar status: {e}")

def main():
    print("🚀 Iniciando Monitor Jules (Local Loop)")
    print("Pressione Ctrl+C para parar.")
    
    while True:
        try:
            check_status()
            # Wait 30 seconds before next check
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n🛑 Monitor parado pelo usuário.")
            break
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()

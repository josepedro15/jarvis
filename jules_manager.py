import os
import requests
import json
import time
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

JULES_API_KEY = os.getenv("JULES_API_KEY")
JULES_API_URL = "https://jules.googleapis.com/v1alpha"

if not JULES_API_KEY:
    print("❌ Erro: JULES_API_KEY não encontrada no arquivo .env")
    exit(1)

HEADERS = {
    "X-Goog-Api-Key": JULES_API_KEY,
    "Content-Type": "application/json"
}

def list_sources():
    """Lists all available repositories (sources) connected to Jules."""
    url = f"{JULES_API_URL}/sources"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        print("\n📂 Repositórios Disponíveis:")
        sources = data.get("sources", [])
        if not sources:
            print("   Nenhum repositório encontrado.")
        else:
            for source in sources:
                print(f"   - {source.get('name')} (ID: {source.get('id')})")
        return sources
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao listar sources: {e}")
        if response is not None:
             print(f"Detalhes: {response.text}")
        return []

def create_session(source_id, task_description):
    """Creates a coding session in Jules for a specific repo."""
    url = f"{JULES_API_URL}/sessions"
    
    # Correct structure based on documentation provided by user
    payload = {
        "prompt": task_description,
        "sourceContext": {
            "source": source_id,
            "githubRepoContext": {
                "startingBranch": "main" # Defaulting to main, could be parametrized
            }
        },
        "automationMode": "AUTO_CREATE_PR", # Enable PR creation by default
        "title": f"Task: {task_description[:30]}..." # Simple title
    }
    
    print(f"\n🚀 Iniciando Sessão no Jules...")
    print(f"   Repo ID: {source_id}")
    print(f"   Tarefa: {task_description}")

    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        session_data = response.json()
        print(f"✅ Sessão Criada com Sucesso! ID: {session_data.get('name')}")
        return session_data
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao criar sessão: {e}")
        if response is not None:
             print(f"Detalhes: {response.text}")
        return None

def get_session(session_name):
    """Retrieves the current status of a session."""
    url = f"{JULES_API_URL}/{session_name}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def main():
    parser = argparse.ArgumentParser(description="Jules Command Center CLI")
    subparsers = parser.add_subparsers(dest="command", help="Comando a executar")

    # Command: list
    subparsers.add_parser("list", help="Listar repositórios disponíveis")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Iniciar uma tarefa no Jules")
    run_parser.add_argument("--repo", required=True, help="Nome ou ID do repositório (Source)")
    run_parser.add_argument("--task", required=True, help="Descrição da tarefa a ser executada")

    args = parser.parse_args()

    if args.command == "list":
        list_sources()
    elif args.command == "run":
        from notify import send_whatsapp_message
        
        # 1. Start the session
        session = create_session(args.repo, args.task)
        
        if session:
            session_name = session.get('name')
            repo_name = args.repo
            
            # Notify Start
            print("⏳ Monitorando status da tarefa...")
            send_whatsapp_message(f"🚀 *Jules Iniciado*\n\nTarefa enviada para: {repo_name}\nStatus: Em andamento...")

            # 2. Polling Loop
            while True:
                time.sleep(10) # Check every 10 seconds
                current_session = get_session(session_name)
                
                if not current_session:
                    continue

                status = current_session.get("state", "UNKNOWN") # Assuming 'state' or 'status' field
                print(f"   Status atual: {status}")

                if status in ["SUCCEEDED", "COMPLETED", "FAILED", "CANCELLED"]:
                    # Final Notification
                    emoji = "✅" if status in ["SUCCEEDED", "COMPLETED"] else "❌"
                    
                    final_msg = (
                        f"{emoji} *Jules Finalizado*\n\n"
                        f"Repo: {repo_name}\n"
                        f"Status Final: {status}\n"
                        f"Verifique o PR no GitHub!"
                    )
                    send_whatsapp_message(final_msg)
                    break
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

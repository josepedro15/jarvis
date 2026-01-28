from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv
from convex import ConvexClient

# Load env variables (Vercel injects these automatically)
load_dotenv()

app = Flask(__name__)

# --- Configuration ---
JULES_API_URL = "https://jules.googleapis.com/v1alpha/sessions"
JULES_API_KEY = os.getenv("JULES_API_KEY")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")

# --- Helpers ---
def get_convex():
    url = os.getenv("CONVEX_URL")
    if not url:
        return None
    return ConvexClient(url)

def send_whatsapp(number, message):
    if not WHATSAPP_API_URL or not WHATSAPP_API_TOKEN:
        print("WhatsApp not configured")
        return
    
    headers = {"token": WHATSAPP_API_TOKEN}
    payload = {"number": number, "text": message}
    try:
        requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
    except Exception as e:
        print(f"Error sending WhatsApp: {e}")

# --- Routes ---

@app.route('/api/webhook', methods=['POST'])
def webhook_start():
    data = request.json
    task = data.get('task', 'Nova Tarefa')
    repo = data.get('repo', 'github/josepedro15/default') 
    phone = data.get('phone', WHATSAPP_NUMBER)

    # 1. Start Jules Session
    headers = {"X-Goog-Api-Key": JULES_API_KEY, "Content-Type": "application/json"}
    payload = {
        "prompt": task,
        "sourceContext": {
            "source": repo,
            "githubRepoContext": {"startingBranch": "main"}
        },
        "automationMode": "AUTO_CREATE_PR",
        "title": f"Task: {task[:30]}"
    }

    try:
        resp = requests.post(JULES_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        session_data = resp.json()
        session_name = session_data.get('name')
    except Exception as e:
        return jsonify({"error": f"Jules API Error: {str(e)}"}), 500

    # 2. Save to Convex
    client = get_convex()
    if client:
        # Calls the mutation defined in convex/tasks.ts
        client.mutation("tasks:createSession", {
            "session_name": session_name,
            "repo_name": repo,
            "phone_number": phone
        })

    # 3. Notify
    msg = f"🚀 Jules Iniciado!\nRepo: {repo}\nSessão: {session_name}\nStatus: PENDING"
    send_whatsapp(phone, msg)

    return jsonify({"status": "started", "session": session_name})

@app.route('/api/cron', methods=['GET'])
def cron_check():
    client = get_convex()
    if not client:
        return jsonify({"error": "Convex not configured"}), 500

    # 1. Get Pending Sessions from Convex
    pending_sessions = client.query("tasks:getPending")

    checked_count = 0
    completed_count = 0
    
    headers = {"X-Goog-Api-Key": JULES_API_KEY}

    for session in pending_sessions:
        session_name = session['session_id'] # Note schema field name
        row_id = session['_id']
        repo = session['repo_name']
        phone = session['phone_number']

        # 2. Check Jules Status
        real_url = f"https://jules.googleapis.com/v1alpha/{session_name}"
        
        try:
            r = requests.get(real_url, headers=headers)
            if r.status_code == 200:
                jules_data = r.json()
                status = jules_data.get('state', 'UNKNOWN')
                
                # Check for outputs/PR
                if status == "UNKNOWN" and jules_data.get('outputs'):
                     status = "COMPLETED"

                if status in ["SUCCEEDED", "COMPLETED", "FAILED", "CANCELLED"]:
                    # 3. Update Convex
                    client.mutation("tasks:markDone", {"id": row_id, "status": status})
                    
                    # 4. Notify
                    emoji = "✅" if status in ["SUCCEEDED", "COMPLETED"] else "❌"
                    msg = f"{emoji} Jules Finalizou!\nRepo: {repo}\nStatus: {status}"
                    send_whatsapp(phone, msg)
                    completed_count += 1
        except Exception as e:
            print(f"Error checking {session_name}: {e}")

    return jsonify({"checked": checked_count, "completed": completed_count})

if __name__ == '__main__':
    app.run(debug=True, port=3000)

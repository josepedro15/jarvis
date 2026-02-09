import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
PROJECT_NAME = "jules-command-center"
HEADERS = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}

def create_project():
    print(f"Creating project '{PROJECT_NAME}'...")
    url = "https://api.vercel.com/v9/projects"
    # Link to GitHub immediately during creation if possible, or update later
    data = {
        "name": PROJECT_NAME,
        "gitRepository": {
            "type": "github",
            "repo": "josepedro15/jules-command-center"
        }
    }
    resp = requests.post(url, headers=HEADERS, json=data)
    if resp.status_code == 200:
        print("✅ Project created and linked.")
        return resp.json().get("id")
    elif resp.status_code == 409:
        print("ℹ️ Project exists. Linking repo...")
        # Get ID? We need to look it up.
        # But simpler: just try to link endpoint
        # We need the ID.
        get_resp = requests.get(f"https://api.vercel.com/v9/projects/{PROJECT_NAME}", headers=HEADERS)
        if get_resp.status_code == 200:
            pid = get_resp.json().get("id")
            link_repo(pid)
            return pid
    else:
        print(f"❌ Error creating project: {resp.text}")
        return None

def link_repo(project_id):
    url = f"https://api.vercel.com/v9/projects/{project_id}/link"
    data = {
        "type": "github",
        "repo": "josepedro15/jules-command-center"
    }
    resp = requests.post(url, headers=HEADERS, json=data)
    if resp.status_code == 200:
        print("✅ GitHub Linked.")
    else:
        print(f"⚠️ Link failed (might need Vercel App installed on GitHub): {resp.text}")


def set_env_vars(project_id):
    print("Setting environment variables...")
    # Load all envs ensuring we don't upload the VERCEL_TOKEN itself if not needed (optional)
    envs = {k: v for k, v in os.environ.items() if k in [
        "JULES_API_KEY", "CONVEX_URL", "CONVEX_ACCESS_TOKEN", 
        "GITHUB_TOKEN", "WHATSAPP_API_URL", "WHATSAPP_API_TOKEN", "WHATSAPP_NUMBER"
    ]}
    
    url = f"https://api.vercel.com/v10/projects/{PROJECT_NAME}/env"
    
    # First, list existing to avoid dupes? Vercel API allows duplicates for different targets, but usually we want one.
    # We'll just try to add.
    
    target = ["production", "preview", "development"]
    
    for key, value in envs.items():
        payload = {
            "key": key,
            "value": value,
            "type": "encrypted",
            "target": target
        }
        resp = requests.post(url, headers=HEADERS, json=payload)
        if resp.status_code == 200:
             print(f"   Set {key}")
        else:
             # Ignore if already exists (400? 422?)
             print(f"   Skipped {key} (might exist)")

def trigger_deploy():
    print("🚀 Linking Project...")
    # Link: Needs org? Usually auto-detected from token if only one scope.
    # Note: 'link' command behavior varies without .vercel dir.
    # We will try to pull project settings.
    os.system(f"npx vercel link --yes --project {PROJECT_NAME} --token {VERCEL_TOKEN}")
    
    print("🚀 Triggering Deploy via CLI...")
    cmd = f"npx vercel deploy --prod --token {VERCEL_TOKEN} --yes"
    os.system(cmd)


if __name__ == "__main__":
    pid = create_project()
    if pid:
        set_env_vars(pid)
        trigger_deploy()

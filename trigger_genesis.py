import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JULES_API_KEY = os.getenv("JULES_API_KEY")
JULES_API_URL = "https://jules.googleapis.com/v1alpha/sessions"

# Context: The keys Jules needs to do the job.
# WARNING: Passing keys in prompt/context is sensitive, but required for this "bootstrap" agent pattern.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
CONVEX_TOKEN = os.getenv("CONVEX_ACCESS_TOKEN")

prompt = f"""
TASK: GENESIS - CREATE NEW PROJECT 'finance-flow'

Objective:
1. Create a new GitHub repository 'josepedro15/finance-flow'.
2. Initialize a Convex project 'finance-flow' and generate the schema.
3. Scaffold a Next.js + Convex starter.

CREDENTIALS:
- GitHub Token: {GITHUB_TOKEN}
- Convex Admin Key: {CONVEX_TOKEN}

INSTRUCTIONS:
- Use the 'gh' CLI or curl along with the GitHub Token to create the repo.
- Use 'npx convex' with the Admin Key to provision the DB.
- Push the initial code to main.
"""

payload = {
    "prompt": prompt,
    "sourceContext": {
        "source": "https://github.com/josepedro15/jules-command-center",
        "githubRepoContext": {"startingBranch": "main"}
    },
    "automationMode": "AUTO_CREATE_PR",
    "title": "Genesis: Finance Flow"
}

headers = {
    "X-Goog-Api-Key": JULES_API_KEY,
    "Content-Type": "application/json"
}

print("🚀 Sending Genesis Order to Jules...")
try:
    resp = requests.post(JULES_API_URL, headers=headers, json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Session Created: {data.get('name')}")
        print("Jules is now working on creating your new project.")
    else:
        print(f"❌ Error: {resp.status_code} - {resp.text}")
except Exception as e:
    print(f"Error: {e}")

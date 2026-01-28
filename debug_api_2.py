import os
import requests
from dotenv import load_dotenv

load_dotenv()
JULES_API_KEY = os.getenv("JULES_API_KEY")
HEADERS = {"X-Goog-Api-Key": JULES_API_KEY, "Content-Type": "application/json"}
BASE_URL = "https://jules.googleapis.com/v1alpha"
REPO_ID = "sources/github/josepedro15/lpcomunidade"

# Try POST /sources/{id}/sessions
print(f"--- Testing POST /sources/{{id}}/sessions ---")
url = f"{BASE_URL}/{REPO_ID}/sessions"
print(f"URL: {url}")
payload = {"task": "test task"} 
# Also try 'description' or just empty
resp = requests.post(url, headers=HEADERS, json=payload)
print(resp.status_code)
print(resp.text)

if resp.status_code != 200:
    # Try with 'session' wrapper in this URL
    print("\n--- Testing wrapper with this URL ---")
    resp = requests.post(url, headers=HEADERS, json={"session": {"task": "test"}})
    print(resp.status_code)
    print(resp.text)

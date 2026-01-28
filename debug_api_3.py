import os
import requests
from dotenv import load_dotenv

load_dotenv()
JULES_API_KEY = os.getenv("JULES_API_KEY")
HEADERS = {"X-Goog-Api-Key": JULES_API_KEY, "Content-Type": "application/json"}
URL = "https://jules.googleapis.com/v1alpha/sessions"

SOURCE = "sources/github/josepedro15/lpcomunidade"

def test_payload(name, payload):
    print(f"\n--- Testing variant: {name} ---")
    wrapper = {"session": payload}
    print(f"Payload: {wrapper}")
    resp = requests.post(URL, headers=HEADERS, json=wrapper)
    print(resp.status_code)
    print(resp.text)

# Test 1: sourceName
test_payload("camelCase sourceName", {"sourceName": SOURCE, "description": "test task"})

# Test 2: source (nested object?)
test_payload("Nested Source Object", {"source": {"name": SOURCE}, "description": "test task"})

# Test 3: parent
test_payload("parent field", {"parent": SOURCE, "description": "test task"})

# Test 4: repository
test_payload("repository field", {"repository": SOURCE, "description": "test task"})

import os
import requests
from dotenv import load_dotenv

load_dotenv()
JULES_API_KEY = os.getenv("JULES_API_KEY")
HEADERS = {"X-Goog-Api-Key": JULES_API_KEY, "Content-Type": "application/json"}
URL = "https://jules.googleapis.com/v1alpha/sessions"

print("--- Testing Empty Payload ---")
resp = requests.post(URL, headers=HEADERS, json={})
print(resp.status_code)
print(resp.text)

print("\n--- Testing 'source_name' and 'description' ---")
resp = requests.post(URL, headers=HEADERS, json={"source_name": "github/josepedro15/lpcomunidade", "description": "test"})
print(resp.status_code)
print(resp.text)

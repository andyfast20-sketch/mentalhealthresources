import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()

CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_D1_DATABASE_ID = os.getenv("CF_D1_DATABASE_ID")

BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database/{CF_D1_DATABASE_ID}/query"

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "sql": "INSERT INTO charities (name, description, logo_url, site_url) VALUES (?, ?, ?, ?);",
    "params": ["Test Charity", "Hello", "logo.png", "https://test.com"]
}

print("Sending request...")
response = requests.post(BASE_URL, headers=HEADERS, json=payload)

print("Status:", response.status_code)
print("Response:")
print(response.text)

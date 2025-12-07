import os
import requests
from dotenv import load_dotenv

load_dotenv()

CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_D1_DATABASE_ID = os.getenv("CF_D1_DATABASE_ID")

url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database/{CF_D1_DATABASE_ID}/query"

headers = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "sql": "INSERT INTO charities (name, description, logo_url, site_url) VALUES (?, ?, ?, ?);",
    "params": [
        "TEST CHARITY",
        "This is only a test",
        "https://example.com/logo.png",
        "https://example.com"
    ]
}

print("Sending INSERT...")
response = requests.post(url, headers=headers, json=payload)

print("Status:", response.status_code)
print("Response:", response.text)

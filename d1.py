import os
import requests
import json

CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_D1_DATABASE_ID = os.getenv("CF_D1_DATABASE_ID")

BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database/{CF_D1_DATABASE_ID}/query"

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json"
}

def d1_query(sql, params=None):
    payload = {
        "sql": sql,
        "params": params or []
    }

    response = requests.post(BASE_URL, headers=HEADERS, json=payload)

    try:
        data = response.json()
    except:
        print("Error decoding response")
        print(response.text)
        return None

    if not data.get("success"):
        print("D1 Error:", data)
        return None

    return data.get("result", [])

import requests
from config import ASANA_API_URL, HEADERS
import os
def create_webhook():
    project_id = '1208840851929433'
    url = f"{ASANA_API_URL}/webhooks"
    payload = {
        "data": {
            "resource": project_id,
            "target": "https://Shailesh-Sharma-K-dynamic-deadline.onrender.com/webhook"
        }
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    if response.status_code == 201:
        print("Webhook created successfully!")
    else:
        print(f"Failed to create webhook: {response.text}")

if __name__ == "__main__":
    create_webhook()
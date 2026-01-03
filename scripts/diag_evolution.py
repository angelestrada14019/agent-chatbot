import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("EVOLUTION_URL", "https://evoapi.tbrflows.transborder.com.co")
INSTANCE = os.getenv("EVOLUTION_INSTANCE", "test")
API_KEY = os.getenv("EVOLUTION_API_KEY")

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

def check_instance():
    print(f"\n--- Checking Instance Connection: {INSTANCE} ---")
    try:
        res = requests.get(f"{URL}/instance/connectionState/{INSTANCE}", headers=headers)
        print(f"Status: {res.status_code}")
        print(f"Data: {json.dumps(res.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def check_webhook():
    print(f"\n--- Checking Webhook Config (Instance) ---")
    try:
        res = requests.get(f"{URL}/webhook/find/{INSTANCE}", headers=headers)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print(json.dumps(res.json(), indent=2))
        else:
            print(f"Response: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("[ERROR] EVOLUTION_API_KEY no encontrado en .env")
    else:
        print(f"URL: {URL}")
        print(f"Instance: {INSTANCE}")
        check_instance()
        check_webhook()

import sys
from pathlib import Path

# Add project root to sys.path to allow importing config
sys.path.append(str(Path(__file__).parent.parent))

import config

headers = {
    "apikey": config.EVOLUTION_API_KEY,
    "Content-Type": "application/json"
}

def check_instance():
    print(f"\n--- Checking Instance Connection: {config.EVOLUTION_INSTANCE} ---")
    try:
        res = requests.get(f"{config.EVOLUTION_URL}/instance/connectionState/{config.EVOLUTION_INSTANCE}", headers=headers)
        print(f"Status: {res.status_code}")
        print(f"Data: {json.dumps(res.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def check_webhook():
    print(f"\n--- Checking Webhook Config (Instance) ---")
    try:
        res = requests.get(f"{config.EVOLUTION_URL}/webhook/find/{config.EVOLUTION_INSTANCE}", headers=headers)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print(json.dumps(res.json(), indent=2))
        else:
            print(f"Response: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if not config.EVOLUTION_API_KEY:
        print("[ERROR] EVOLUTION_API_KEY no encontrado en .env")
    else:
        print(f"URL: {config.EVOLUTION_URL}")
        print(f"Instance: {config.EVOLUTION_INSTANCE}")
        check_instance()
        check_webhook()

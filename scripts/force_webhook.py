import sys
from pathlib import Path

# Add project root to sys.path to allow importing config
sys.path.append(str(Path(__file__).parent.parent))

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

import config

# URL de ngrok extraida de la captura del usuario
NGROK_URL = "https://d5f7321225b1.ngrok-free.app/webhook/evolution".strip()

headers = {
    "apikey": config.EVOLUTION_API_KEY,
    "Content-Type": "application/json"
}

def configure_webhook():
    print(f"--- Forzando configuracion del Webhook ---")
    print(f"URL: '{NGROK_URL}'")
    
    # Payload v2 compatible (probando ambos formatos si uno falla)
    payload_v1 = {
        "url": NGROK_URL,
        "enabled": True,
        "webhookBase64": True,
        "events": [
            "MESSAGES_UPSERT", "MESSAGES_UPDATE", "MESSAGES_DELETE", 
            "SEND_MESSAGE", "CONTACTS_UPSERT", "PRESENCE_UPDATE", "QRCODE_UPDATED"
        ]
    }
    
    # Algunas versiones de v2 esperan un objeto "webhook"
    payload_v2 = {
        "webhook": {
            "url": NGROK_URL,
            "enabled": True,
            "webhookBase64": True,
            "events": [
                "MESSAGES_UPSERT", "MESSAGES_UPDATE", "MESSAGES_DELETE", 
                "SEND_MESSAGE", "CONTACTS_UPSERT", "PRESENCE_UPDATE", "QRCODE_UPDATED"
            ]
        }
    }
    
    for payload in [payload_v1, payload_v2]:
        try:
            print(f"\nProbando con payload: {json.dumps(payload)[:100]}...")
            res = requests.post(f"{config.EVOLUTION_URL}/webhook/set/{config.EVOLUTION_INSTANCE}", headers=headers, json=payload)
            print(f"Status: {res.status_code}")
            print(f"Response: {res.text}")
            
            if res.status_code in [200, 201]:
                print("\n[SUCCESS] Webhook configurado exitosamente!")
                return
        except Exception as e:
            print(f"[ERROR] Intento fallido: {e}")

if __name__ == "__main__":
    if not config.EVOLUTION_API_KEY:
        print("[ERROR] EVOLUTION_API_KEY no encontrado en .env")
    else:
        configure_webhook()

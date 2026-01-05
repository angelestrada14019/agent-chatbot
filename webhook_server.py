"""
🔗 Webhook Server for EvoDataAgent (FastAPI)
Recibe mensajes de EvolutionAPI y los procesa con el Agente Nativo (SDK).
"""
import json
import uuid
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
from evodata_agent import EvoDataAgent
from utils.logger import get_logger

logger = get_logger("WebhookServer")

app = FastAPI(title=f"{config.AGENT_NAME} API", version=config.AGENT_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class EvolutionPayload(BaseModel):
    event: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    # Soporte para v1/v2 mixed
    key: Optional[Dict[str, Any]] = None
    message: Optional[Dict[str, Any]] = None
    messageType: Optional[str] = None

def get_agent() -> EvoDataAgent:
    """Singleton del agente para FastAPI"""
    if not hasattr(app, "agent"):
        app.agent = EvoDataAgent()
    return app.agent

@app.post("/webhook/evolution")
async def handle_webhook(
    payload: EvolutionPayload, 
    background_tasks: BackgroundTasks,
    agent: EvoDataAgent = Depends(get_agent)
):
    """Procesador principal de Webhooks"""
    data = payload.data or payload.model_dump()
    key = data.get("key", {})
    msg_type = data.get("messageType")
    from_me = key.get("fromMe", False)

    if from_me:
        return {"status": "ignored", "reason": "fromMe"}

    remote_jid = key.get("remoteJid")
    if not remote_jid:
        return {"status": "ignored", "reason": "no_jid"}

    phone_number = remote_jid.replace("@s.whatsapp.net", "@c.us")
    
    # Extraer texto o audio
    if msg_type in ["conversation", "extendedTextMessage"]:
        msg_content = data.get("message", {})
        text = msg_content.get("conversation") or (msg_content.get("extendedTextMessage") or {}).get("text", "")
        if text:
            background_tasks.add_task(process_text, agent, phone_number, text)
            return {"status": "processing", "type": "text"}
            
    elif msg_type == "audioMessage":
        # Se asume que el audio requiere descarga o fetch previo
        background_tasks.add_task(process_audio, agent, phone_number, key)
        return {"status": "processing", "type": "audio"}

    return {"status": "ignored", "type": msg_type}

async def process_text(agent: EvoDataAgent, phone_number: str, text: str):
    try:
        response = await agent.process_message(text, phone_number=phone_number)
        await agent.send_whatsapp_message(phone_number, response)
    except Exception as e:
        logger.log_error_with_context(e, {"phone_number": phone_number, "action": "process_text", "text": text[:50]})

async def process_audio(agent: EvoDataAgent, phone_number: str, key: dict):
    try:
        # Fetch base64 from Evolution
        base64_audio = await agent.whatsapp_service.fetch_media(key)
        if not base64_audio:
            return
            
        # Guardar temporal
        temp_path = Path(config.TEMP_DIR) / f"voice_{uuid.uuid4().hex}.mp3"
        import base64
        with open(temp_path, "wb") as f:
            f.write(base64.b64decode(base64_audio))
            
        response = await agent.process_message("", phone_number=phone_number, is_voice=True, audio_path=str(temp_path))
        await agent.send_whatsapp_message(phone_number, response)
        
        # Cleanup
        if temp_path.exists(): temp_path.unlink()
    except Exception as e:
        logger.log_error_with_context(e, {"phone_number": phone_number, "action": "process_audio"})

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza de recursos al apagar el servidor"""
    agent = get_agent()
    await agent.whatsapp_service.close()
    logger.info("🔌 Conexiones cerradas correctamente")

@app.get("/health")
def health():
    return {"status": "ok", "agent": config.AGENT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.WEBHOOK_SERVER_PORT)

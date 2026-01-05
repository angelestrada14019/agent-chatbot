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
from services.whatsapp_service import WhatsAppService
from utils.logger import get_logger

logger = get_logger("WebhookServer")

app = FastAPI(title=f"{config.AGENT_NAME} API", version=config.AGENT_VERSION)

@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar el servidor"""
    import os
    for directory in [config.TEMP_DIR, config.EXPORTS_DIR, config.LOGS_DIR]:
        os.makedirs(directory, exist_ok=True)
    logger.info("📁 Directorios de sistema inicializados")

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

# Singletons
agent = EvoDataAgent()
whatsapp = WhatsAppService()

@app.post("/webhook/evolution")
async def handle_webhook(
    payload: EvolutionPayload, 
    background_tasks: BackgroundTasks
):
    """Procesador principal de Webhooks"""
    data = payload.data or payload.model_dump()
    key = data.get("key", {})
    from_me = key.get("fromMe", False)
    
    if from_me: return {"status": "ignored"}

    remote_jid = key.get("remoteJid")
    if not remote_jid: return {"status": "no_jid"}
    
    phone_number = whatsapp.normalize_phone_number(remote_jid)
    msg_type = data.get("messageType")

    # Orquestación de tareas en segundo plano
    if msg_type in ["conversation", "extendedTextMessage"]:
        msg_content = data.get("message", {})
        text = msg_content.get("conversation") or (msg_content.get("extendedTextMessage") or {}).get("text", "")
        if text:
            background_tasks.add_task(process_chat_flow, phone_number, text)
            return {"status": "processing"}
            
    elif msg_type == "audioMessage":
        background_tasks.add_task(process_chat_flow, phone_number, "", is_voice=True, msg_key=key)
        return {"status": "processing"}

    return {"status": "unsupported_type"}

async def process_chat_flow(phone_number: str, text: str, is_voice: bool = False, msg_key: dict = None):
    """Flujo completo: Procesamiento -> Agente -> WhatsApp"""
    try:
        audio_path = None
        if is_voice and msg_key:
            # 1. Obtener audio de Evolution
            base64_audio = await whatsapp.fetch_media(msg_key)
            if base64_audio:
                audio_path = Path(config.TEMP_DIR) / f"voice_{uuid.uuid4().hex}.mp3"
                import base64
                with open(audio_path, "wb") as f:
                    f.write(base64.b64decode(base64_audio))

        # 2. El Agente procesa (incluye Whisper si hay audio_path)
        logger.info(f"🤖 Procesando solicitud de {phone_number}")
        result = await agent.process_message(text, phone_number=phone_number, is_voice=is_voice, audio_path=str(audio_path) if audio_path else None)
        
        # 3. Entrega de resultados
        if result.get("success"):
            await whatsapp.send_message_with_response(phone_number, result)
        
        # Cleanup
        if audio_path and audio_path.exists(): audio_path.unlink()
        
    except Exception as e:
        from utils.logger import log_error_with_context
        log_error_with_context(logger, e, {"phone_number": phone_number})

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza de recursos"""
    await whatsapp.close()
    logger.info("🔌 Conexiones cerradas")

@app.get("/health")
def health():
    return {"status": "ok", "agent": config.AGENT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.WEBHOOK_SERVER_PORT)

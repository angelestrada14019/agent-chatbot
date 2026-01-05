"""
🔗 Webhook Server for EvoDataAgent (FastAPI)
Recibe mensajes de EvolutionAPI y los procesa con el Agente Nativo (SDK).
"""
import json
import uuid
import logging
import httpx
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
    """Payload flexible para evitar errores 422 con eventos no suscritos o cambios en la API"""
    event: Optional[str] = None
    instance: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    # Soporte para v1/v2 mixed
    key: Optional[Dict[str, Any]] = None
    message: Optional[Dict[str, Any]] = None
    messageType: Optional[str] = None
    
    class Config:
        extra = "allow" # Permite campos adicionales sin fallar

# Singletons
agent = EvoDataAgent()
whatsapp = WhatsAppService()

@app.post("/webhook/evolution")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Procesador principal de Webhooks (Máxima Flexibilidad)"""
    try:
        body = await request.json()
    except Exception:
        return {"status": "invalid_json"}

    # Extraer data de diferentes versiones/eventos
    data = body.get("data") or body
    instance = body.get("instance") or config.EVOLUTION_INSTANCE
    event = body.get("event")
    
    # Soporte para array de mensajes (v2 standard)
    if isinstance(data, dict) and "messages" in data:
        messages = data.get("messages", [])
        if messages: data = messages[0]

    # Solo procesar mensajes (evitar ruidos de conexión/presencia)
    if event and "messages" not in event and "MESSAGES" not in event:
        return {"status": "ignored_event", "event": event}

    key = data.get("key", {})
    from_me = key.get("fromMe", False)
    if from_me: return {"status": "ignored_self"}

    remote_jid = key.get("remoteJid")
    if not remote_jid: return {"status": "no_jid"}
    
    phone_number = whatsapp.normalize_phone_number(remote_jid)
    msg_type = data.get("messageType")
    
    logger.info(f"📩 Evento: {event or 'legacy'} | Instancia: {instance} | Tipo: {msg_type} | De: {phone_number}")

    # Orquestación de tareas en segundo plano
    if msg_type in ["conversation", "extendedTextMessage"]:
        msg_content = data.get("message", {})
        text = msg_content.get("conversation") or (msg_content.get("extendedTextMessage") or {}).get("text", "")
        if text:
            background_tasks.add_task(process_chat_flow, phone_number, text)
            return {"status": "processing"}
            
    elif msg_type in ["audioMessage", "audio"]:
        message = data.get("message", {})
        audio_msg = message.get("audioMessage") or message.get("audio") or {}
        audio_url = audio_msg.get("url")
        
        # SI es una URL de WhatsApp CDN (.enc), forzar fetch_media para descifrar
        force_fetch = False
        if audio_url and ("mmg.whatsapp.net" in audio_url or ".enc" in audio_url):
            logger.info("🔐 URL encriptada detectada, usando proxy de Evolution para descifrar")
            force_fetch = True
            
        background_tasks.add_task(
            process_chat_flow, 
            phone_number, 
            "", 
            is_voice=True, 
            msg_key=key, 
            audio_url=audio_url if not force_fetch else None,
            instance_name=instance
        )
        return {"status": "processing"}

    return {"status": "unsupported_type"}

async def process_chat_flow(phone_number: str, text: str, is_voice: bool = False, msg_key: dict = None, audio_url: str = None, instance_name: str = None):
    """Flujo completo: Procesamiento -> Agente -> WhatsApp"""
    try:
        audio_path = None
        if is_voice:
            audio_path = Path(config.TEMP_DIR) / f"voice_{uuid.uuid4().hex}.mp3"
            success = False
            
            # 1. Intentar descargar por URL si existe (v2)
            if audio_url:
                logger.info(f"🔗 Descargando audio desde URL: {audio_url}")
                async with httpx.AsyncClient() as client:
                    resp = await client.get(audio_url)
                    if resp.status_code == 200:
                        with open(audio_path, "wb") as f:
                            f.write(resp.content)
                        success = True
            
            # 2. Si falló o no había URL, intentar base64 estándar
            if not success and msg_key:
                logger.info(f"🎤 Solicitando media base64 para {phone_number}...")
                base64_audio = await whatsapp.fetch_media(msg_key, instance_name=instance_name)
                if base64_audio:
                    import base64
                    with open(audio_path, "wb") as f:
                        f.write(base64.b64decode(base64_audio))
                    success = True

            if success:
                logger.info(f"✅ Audio listo: {audio_path}")
            else:
                audio_path = None
                logger.warning(f"⚠️ No se pudo obtener el audio por ningún método para {phone_number}")

        # 2. El Agente procesa (incluye Whisper si hay audio_path)
        logger.info(f"🤖 Agente procesando solicitud de {phone_number} (voice={is_voice})")
        result = await agent.process_message(
            text, 
            phone_number=phone_number, 
            is_voice=is_voice, 
            audio_path=str(audio_path) if audio_path else None
        )
        
        # 3. Entrega de resultados
        if result.get("success"):
            logger.info(f"📤 Enviando respuesta a {phone_number}")
            await whatsapp.send_message_with_response(phone_number, result)
        else:
            error_msg = result.get("error", "Error desconocido")
            logger.error(f"❌ El agente no pudo procesar la solicitud: {error_msg}")
            # Opcional: Notificar al usuario del error
            await whatsapp.send_text_message(phone_number, "Lo siento, tuve un problema procesando tu mensaje. ¿Podrías repetirlo?")
        
        # Cleanup
        if audio_path and audio_path.exists(): 
            audio_path.unlink()
            logger.info(f"🗑️ Archivo temporal eliminado: {audio_path}")
        
    except Exception as e:
        from utils.logger import log_error_with_context
        log_error_with_context(logger, e, {"phone_number": phone_number, "flow": "voice" if is_voice else "text"})

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

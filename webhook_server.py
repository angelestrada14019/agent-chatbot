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
    
    # Cleanup automático de archivos antiguos
    if config.STORAGE_SAVE_FILES:
        from services.storage_provider import get_storage_provider
        storage = get_storage_provider()
        cleanup_count = storage.cleanup_old_files(config.STORAGE_CLEANUP_DAYS)
        if cleanup_count > 0:
            logger.info(f"🧺 Limpieza: {cleanup_count} archivo(s) antiguo(s) eliminado(s)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    is_message_event = event and ("messages" in event or "MESSAGES" in event or "upsert" in event.lower())
    if event and not is_message_event:
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
        
        background_tasks.add_task(
            process_chat_flow, 
            phone_number, 
            "", 
            is_voice=True, 
            msg_key=key,
            audio_url=audio_url,
            instance_name=instance,
            full_data=data
        )
        return {"status": "processing"}

    return {"status": "unsupported_type"}

async def process_chat_flow(
    phone_number: str, 
    text: str, 
    is_voice: bool = False, 
    msg_key: dict = None, 
    audio_url: str = None, 
    instance_name: str = None,
    full_data: dict = None
):
    """Flujo completo: Procesamiento -> Agente -> WhatsApp"""
    try:
        audio_path = None
        if is_voice:
            audio_path = Path(config.TEMP_DIR) / f"voice_{uuid.uuid4().hex}.mp3"
            success = False
            
            # 1. Recuperación de Media (Estrategia única vía Evolution API)
            logger.info(f"🎤 Solicitando media vía Evolution API (ID: {msg_key.get('id') if msg_key else 'N/A'})...")
            base64_audio = await whatsapp.fetch_media(
                msg_key, 
                instance_name=instance_name,
                message_data=full_data
            )
            if base64_audio:
                import base64
                with open(audio_path, "wb") as f:
                    f.write(base64.b64decode(base64_audio))
                success = True
                logger.info(f"✅ Audio obtenido y descifrado")

            if not success:
                audio_path = None
                logger.error(f"❌ Fallo total al recuperar audio para {phone_number}")
                await whatsapp.send_text_message(
                    phone_number, 
                    "Lo siento, no pude procesar tu audio. ¿Podrías intentar de nuevo o escribir tu mensaje?"
                )
                return

        # 2. Procesamiento del Agente
        logger.info(f"🤖 Procesando solicitud de {phone_number} (voice={is_voice})")
        result = await agent.process_message(
            text, 
            phone_number=phone_number, 
            is_voice=is_voice, 
            audio_path=str(audio_path) if audio_path else None
        )
        
        # 3. Respuesta
        if result.get("success"):
            logger.info(f"📤 Respuesta lista para {phone_number}")
            
            # Prioridad: Si hay nota de voz, enviarla primero (usuario envió voz)
            voice_note = result.get("voice_note")
            if voice_note:
                await whatsapp.send_voice_note(phone_number, voice_note)
                # Limpiar archivo temporal de voz
                Path(voice_note).unlink(missing_ok=True)
                logger.debug(f"🗑️ Audio temporal eliminado: {voice_note}")
            
            # Enviar texto y archivos (siempre, como complemento o principal)
            await whatsapp.send_message_with_response(phone_number, result)
            
            # Borrar archivos si STORAGE_SAVE_FILES=false
            if not config.STORAGE_SAVE_FILES:
                files = result.get("files", [])
                for file_path in files:
                    try:
                        Path(file_path).unlink(missing_ok=True)
                        logger.debug(f"🗑️ Archivo temporal eliminado: {file_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo borrar {file_path}: {e}")
        else:
            error_msg = result.get("error", "Error desconocido")
            logger.error(f"❌ Error del agente: {error_msg}")
            await whatsapp.send_text_message(
                phone_number, 
                "Tuve un problema al procesar tu solicitud. Por favor intenta de nuevo."
            )
        
        # Cleanup
        if audio_path and audio_path.exists(): 
            audio_path.unlink()
            logger.info(f"🗑️ Temporales limpios")
        
    except Exception as e:
        from utils.logger import log_error_with_context
        log_error_with_context(logger, e, {"phone_number": phone_number, "flow": "voice" if is_voice else "text"})
        try:
            await whatsapp.send_text_message(phone_number, "Ocurrió un error inesperado. Por favor intenta de nuevo.")
        except: pass

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

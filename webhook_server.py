"""
🔗 Webhook Server for EvoDataAgent (FastAPI)
Recibe mensajes de EvolutionAPI y los procesa con el agente
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
import requests
from pathlib import Path
from functools import lru_cache
import time
import json
import os

from evodata_agent import EvoDataAgent
from utils.logger import get_logger
from utils.response_formatter import MessageTemplates
import config

# Configurar logger
logger = get_logger("WebhookServer")

# Crear aplicación FastAPI con metadatos
app = FastAPI(
    title=f"{config.AGENT_NAME} Webhook API",
    description="Webhook para recibir y procesar mensajes de EvolutionAPI",
    version=config.AGENT_VERSION,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# 📦 MODELOS PYDANTIC PARA VALIDACIÓN
# ============================================

class WhatsAppKey(BaseModel):
    """Modelo para key de WhatsApp"""
    remoteJid: str = Field(..., description="Número del remitente con formato @s.whatsapp.net")
    fromMe: Optional[bool] = False
    id: Optional[str] = None

class AudioMessageData(BaseModel):
    """Datos de mensaje de audio"""
    url: Optional[str] = None
    mimetype: Optional[str] = None

class ExtendedTextMessageData(BaseModel):
    """Datos de mensaje de texto extendido"""
    text: Optional[str] = None

class WhatsAppMessage(BaseModel):
    """Modelo para mensaje de WhatsApp"""
    conversation: Optional[str] = None
    extendedTextMessage: Optional[Dict[str, Any]] = None
    audioMessage: Optional[Dict[str, Any]] = None

class EvolutionWebhookPayload(BaseModel):
    """Payload del webhook de EvolutionAPI (v2 compatible)"""
    event: Optional[str] = None
    instance: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    # Soporte para v1 (retrocompatibilidad)
    key: Optional[WhatsAppKey] = None
    message: Optional[WhatsAppMessage] = None
    messageType: Optional[str] = None
    
    class Config:
        extra = "allow"

class WebhookResponse(BaseModel):
    """Respuesta del webhook"""
    status: str
    request_id: Optional[str] = None
    action: Optional[str] = None

class HealthResponse(BaseModel):
    """Respuesta de health check"""
    status: str
    agent: str
    version: str
    database_connected: bool = False
    timestamp: str

# ============================================
# 🔧 DEPENDENCY INJECTION
# ============================================

@lru_cache()
def get_agent() -> EvoDataAgent:
    """Obtiene instancia singleton del agente"""
    logger.info("Inicializando EvoDataAgent...")
    return EvoDataAgent()

# ============================================
# 📡 ENDPOINTS
# ============================================

@app.post("/webhook/evolution", response_model=WebhookResponse, tags=["Webhook"])
async def evolution_webhook(
    payload: EvolutionWebhookPayload,
    background_tasks: BackgroundTasks,
    agent: EvoDataAgent = Depends(get_agent)
) -> WebhookResponse:
    """
    Webhook principal para recibir mensajes de EvolutionAPI
    
    - **Soporta**: Mensajes de texto y voz
    - **Procesa**: En background para respuesta rápida
    - **Validación**: Automática con Pydantic
    """
    logger.info("📩 Webhook recibido")
    
    # Debug: Guardar payload raw para diagnóstico
    try:
        debug_file = Path(config.LOGS_DIR) / "webhook_debug.json"
        with open(debug_file, "a") as f:
            f.write(json.dumps(payload.dict(), default=str) + "\n")
    except Exception as e:
        logger.error(f"❌ Error al escribir log debug: {str(e)}")

    # Extraer datos (manejar anidamiento de v2)
    data = payload.data if payload.data else payload.dict()
    
    # Extraer campos clave del objeto de datos
    key = data.get('key', {})
    message_content = data.get('message', {})
    message_type = data.get('messageType')
    from_me = key.get('fromMe', False) if isinstance(key, dict) else getattr(key, 'fromMe', False)

    # Ignorar mensajes enviados por el propio bot para evitar bucles infinitos
    if from_me:
        logger.debug(f"⏭️ Ignorando mensaje enviado por el bot (ID: {key.get('id')})")
        return WebhookResponse(status="ignored", action="message_from_me")
    
    # Fallback si el anidamiento es diferente (algunas versiones de v2)
    if not key and 'key' in payload.dict():
        key = payload.key.dict() if hasattr(payload.key, 'dict') else payload.key
        message_content = payload.message.dict() if hasattr(payload.message, 'dict') else payload.message
        message_type = payload.messageType

    # Extraer número de teléfono
    remote_jid = key.get('remoteJid') if isinstance(key, dict) else getattr(key, 'remoteJid', None)
    
    if not remote_jid:
        logger.warning(f"⚠️ Webhook sin remoteJid. Evento: {payload.event}")
        return WebhookResponse(status="ignored", action="no_remote_jid")
    
    # Convertir formato de número
    phone_number = remote_jid.replace('@s.whatsapp.net', '@c.us')
    
    logger.info(f"📱 Mensaje de {phone_number} (tipo: {message_type})")
    
    # Procesar mensaje según tipo
    if message_type == 'audioMessage':
        # Audio
        audio_data = message_content.get('audioMessage') if isinstance(message_content, dict) else getattr(message_content, 'audioMessage', {})
        audio_url = audio_data.get('url') if audio_data else None
        
        if not audio_url:
            raise HTTPException(status_code=400, detail="Audio sin URL")
        
        logger.info(f"🎤 Procesando mensaje de voz (ID: {key.get('id')})")
        
        # Procesar en background
        background_tasks.add_task(
            process_voice_message,
            agent,
            phone_number,
            key # Pasar el key completo para fetch_media
        )
        
        return WebhookResponse(status="processing", action="voice_to_text")
    
    elif message_type in ['conversation', 'extendedTextMessage']:
        # Texto
        if isinstance(message_content, dict):
            text = message_content.get('conversation') or (message_content.get('extendedTextMessage') or {}).get('text', '')
        else:
            text = getattr(message_content, 'conversation', '') or getattr(getattr(message_content, 'extendedTextMessage', {}), 'text', '')
        
        if not text:
            return WebhookResponse(status="ignored", action="no_text")
        
        logger.info(f"💬 Texto: {text[:50]}...")
        
        # Comandos especiales
        if text.lower() in ['hola', 'help', 'ayuda', 'inicio']:
            # Responder inmediatamente con greeting
            greeting = MessageTemplates.greeting()
            agent.send_whatsapp_message(phone_number, {
                "success": True,
                "response_type": "text",
                "content": greeting,
                "attachments": []
            })
            return WebhookResponse(status="ok", action="greeting")
        
        # Procesar mensaje normal en background
        background_tasks.add_task(
            process_text_message,
            agent,
            phone_number,
            text
        )
        
        return WebhookResponse(status="processing", action="text_processing")
    
    else:
        logger.warning(f"⚠️ Tipo de mensaje no soportado: {message_type}")
        return WebhookResponse(status="ignored", action=f"unsupported_type_{message_type}")


async def process_voice_message(agent: EvoDataAgent, phone_number: str, message_key: dict):
    """Procesa mensaje de voz en background"""
    try:
        # 1. Obtener audio decodificado desde EvolutionAPI (Base64)
        logger.info(f"🔄 Solicitando audio decodificado para {message_key.get('id')}...")
        base64_audio = agent.whatsapp_service.fetch_media(message_key)
        
        if not base64_audio:
            error_msg = "❌ No pude recuperar el audio desde EvolutionAPI. Verifica la configuración."
            agent.send_whatsapp_message(phone_number, {
                "success": False,
                "response_type": "error",
                "content": error_msg,
                "attachments": []
            })
            return
        
        # 2. Guardar base64 a archivo temporal (mp3 force)
        import base64
        temp_dir = Path(config.TEMP_DIR)
        temp_dir.mkdir(exist_ok=True)
        filename = f"voice_{uuid.uuid4().hex}.mp3" # Evolution fetchMedia with convertToMp3: True
        audio_path = temp_dir / filename
        
        with open(audio_path, 'wb') as f:
            f.write(base64.b64decode(base64_audio))
            
        logger.info(f"✅ Audio guardado: {audio_path}")
        
        # 3. Procesar con Whisper (Async)
        response = await agent.process_message(
            "",
            is_voice=True,
            audio_path=str(audio_path)
        )
        
        # 4. Enviar respuesta
        agent.send_whatsapp_message(phone_number, response)
        logger.info(f"✅ Mensaje de voz procesado y respondido")
    
    except Exception as e:
        logger.error(f"❌ Error procesando voz: {str(e)}")


async def process_text_message(agent: EvoDataAgent, phone_number: str, text: str):
    """Procesa mensaje de texto en background"""
    try:
        # Procesar mensaje (Async)
        response = await agent.process_message(text)
        
        # Enviar respuesta
        agent.send_whatsapp_message(phone_number, response)
        logger.info(f"✅ Mensaje de texto procesado y respondido")
    
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje: {str(e)}")


async def download_audio_async(audio_url: str) -> Optional[str]:
    """
    Descarga archivo de audio desde URL de EvolutionAPI
    
    Args:
        audio_url: URL del audio
        
    Returns:
        str: Path del archivo descargado o None si falla
    """
    try:
        # Crear directorio temporal si no existe
        temp_dir = Path(config.TEMP_DIR)
        temp_dir.mkdir(exist_ok=True)
        
        # Descargar (TODO: usar httpx async en vez de requests)
        logger.info(f"⬇️ Descargando audio desde {audio_url}")
        response = requests.get(audio_url, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ Error al descargar audio: {response.status_code}")
            return None
        
        # Determinar extensión real
        content_type = response.headers.get('Content-Type', '')
        ext = '.ogg' # Default
        if 'audio/mpeg' in content_type or 'audio/mp3' in content_type:
            ext = '.mp3'
        elif 'audio/mp4' in content_type:
            ext = '.m4a'
        elif 'audio/wav' in content_type:
            ext = '.wav'
        elif 'audio/oga' in content_type or 'audio/ogg' in content_type:
            ext = '.ogg'
        
        # Generar nombre único con la extensión correcta
        filename = f"audio_{uuid.uuid4().hex}{ext}"
        file_path = temp_dir / filename
        
        # Guardar
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"✅ Audio descargado ({ext}): {file_path}")
        return str(file_path)
    
    except Exception as e:
        logger.error(f"❌ Error al descargar audio: {str(e)}")
        return None


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Returns:
        HealthResponse con estado del sistema
    """
    return HealthResponse(
        status="healthy",
        agent=config.AGENT_NAME,
        version=config.AGENT_VERSION,
        database_connected=False,  # TODO: Implementar check real cuando tengamos MCP activo
        timestamp=f"{time.time()}"
    )


@app.get("/stats", tags=["Monitoring"])
async def stats():
    """Endpoint de estadísticas del agente"""
    return {
        "agent": config.AGENT_NAME,
        "version": config.AGENT_VERSION,
        "db_connected": False,  # TODO: Implementar check MCP
        "tools": ["Calculator", "Visualizer", "Excel Generator", "MCP Client"]
    }


@app.get("/", tags=["Info"])
async def root():
    """Página de información del API"""
    return {
        "name": f"{config.AGENT_NAME} Webhook API",
        "version": config.AGENT_VERSION,
        "status": "active",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "webhook_endpoint": "/webhook/evolution"
    }


# ============================================
# 🔍 MIDDLEWARE PARA LOGGING
# ============================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests"""
    start_time = time.time()
    
    # Procesar request
    response = await call_next(request)
    
    # Calcular tiempo
    process_time = time.time() - start_time
    
    # Log
    logger.info(
        "Request procesado",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=int(process_time * 1000)
    )
    
    return response


# ============================================
# 🚀 ENTRY POINT
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 Iniciando {config.AGENT_NAME} Webhook Server (FastAPI)")
    logger.info(f"🌐 Puerto: {config.WEBHOOK_SERVER_PORT}")
    logger.info(f"📡 Endpoint: /webhook/evolution")
    logger.info(f"📚 Docs: http://localhost:{config.WEBHOOK_SERVER_PORT}/docs")
    logger.info(f"🗄️ Base de datos: {config.DB_TYPE}")
    logger.info(f"🎤 Whisper: OpenAI API")
    
    # Iniciar servidor con Uvicorn
    uvicorn.run(
        "webhook_server:app",
        host="0.0.0.0",
        port=config.WEBHOOK_SERVER_PORT,
        reload=config.DEBUG_MODE,
        log_level="info"
    )

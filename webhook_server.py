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
    """Payload del webhook de EvolutionAPI"""
    key: WhatsAppKey
    message: WhatsAppMessage
    messageType: str
    
    class Config:
        schema_extra = {
            "example": {
                "key": {"remoteJid": "573124488445@s.whatsapp.net"},
                "message": {"conversation": "Muéstrame las ventas"},
                "messageType": "conversation"
            }
        }

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
    
    # Extraer número de teléfono
    remote_jid = payload.key.remoteJid
    if not remote_jid:
        raise HTTPException(status_code=400, detail="remoteJid faltante")
    
    # Convertir formato de número
    phone_number = remote_jid.replace('@s.whatsapp.net', '@c.us')
    message_type = payload.messageType
    
    logger.info(f"📱 Mensaje de {phone_number} (tipo: {message_type})")
    
    # Procesar mensaje según tipo
    if message_type == 'audioMessage':
        # Audio
        audio_data = payload.message.audioMessage or {}
        audio_url = audio_data.get('url')
        
        if not audio_url:
            raise HTTPException(status_code=400, detail="Audio sin URL")
        
        logger.info(f"🎤 Procesando mensaje de voz desde {audio_url}")
        
        # Procesar en background
        background_tasks.add_task(
            process_voice_message,
            agent,
            phone_number,
            audio_url
        )
        
        return WebhookResponse(status="processing", action="voice_to_text")
    
    elif message_type in ['conversation', 'extendedTextMessage']:
        # Texto
        text = (
            payload.message.conversation or
            (payload.message.extendedTextMessage or {}).get('text', '')
        )
        
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


async def process_voice_message(agent: EvoDataAgent, phone_number: str, audio_url: str):
    """Procesa mensaje de voz en background"""
    try:
        # Descargar audio
        audio_path = await download_audio_async(audio_url)
        
        if not audio_path:
            error_msg = "❌ No pude descargar el audio. Intenta de nuevo."
            agent.send_whatsapp_message(phone_number, {
                "success": False,
                "response_type": "error",
                "content": error_msg,
                "attachments": []
            })
            return
        
        # Procesar con Whisper
        response = agent.process_message(
            "",
            is_voice=True,
            audio_path=audio_path
        )
        
        # Enviar respuesta
        agent.send_whatsapp_message(phone_number, response)
        logger.info(f"✅ Mensaje de voz procesado y respondido")
    
    except Exception as e:
        logger.error(f"❌ Error procesando voz: {str(e)}")


async def process_text_message(agent: EvoDataAgent, phone_number: str, text: str):
    """Procesa mensaje de texto en background"""
    try:
        # Procesar mensaje
        response = agent.process_message(text)
        
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
        
        # Generar nombre único
        filename = f"audio_{uuid.uuid4().hex}.ogg"
        file_path = temp_dir / filename
        
        # Descargar (TODO: usar httpx async en vez de requests)
        logger.info(f"⬇️ Descargando audio desde {audio_url}")
        response = requests.get(audio_url, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ Error al descargar audio: {response.status_code}")
            return None
        
        # Guardar
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"✅ Audio descargado: {file_path}")
        return str(file_path)
    
    except Exception as e:
        logger.error(f"❌ Error al descargar audio: {str(e)}")
        return None


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check(agent: EvoDataAgent = Depends(get_agent)) -> HealthResponse:
    """
    Health check endpoint
    
    - Verifica estado del agente
    - Valida conexión a base de datos
    - Retorna timestamp
    """
    from datetime import datetime
    
    return HealthResponse(
        status="healthy",
        agent=config.AGENT_NAME,
        version=config.AGENT_VERSION,
        database_connected=agent.db_connector.validate_connection(),
        timestamp=datetime.now().isoformat()
    )


@app.get("/stats", tags=["Monitoring"])
async def stats(agent: EvoDataAgent = Depends(get_agent)):
    """Endpoint de estadísticas del agente"""
    return {
        "agent": config.AGENT_NAME,
        "version": config.AGENT_VERSION,
        "db_connected": agent.db_connector.validate_connection(),
        "tools": ["MCP Database Connector", "Visualizer", "Excel Generator"]
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

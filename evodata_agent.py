"""
🤖 EvoDataAgent - Main Orchestrator (Refactorizado)
Agente principal - Ahora SOLO orquesta, delegando responsabilidades a servicios
"""
from typing import Dict, Any, Optional
import uuid

import config
from utils.logger import get_logger
from utils.response_formatter import ResponseFormatter

# Servicios (SRP)
from services.message_processor import MessageProcessor
from services.whatsapp_service import WhatsAppService
from services.intent_router import IntentRouter

logger = get_logger("EvoDataAgent")


class EvoDataAgent:
    """
    Agente principal de análisis y automatización
    
    REFACTORIZADO para cumplir con SRP (Single Responsibility Principle)
    
    Responsabilidad ÚNICA: Orquestar servicios
    
    Delega a:
    - MessageProcessor: Procesamiento de texto/voz
    - WhatsAppService: Comunicación WhatsApp
    - IntentRouter: Clasificación y routing de mensajes
    """
    
    def __init__(self):
        """Inicializa el agente y sus servicios"""
        # Servicios
        self.message_processor = MessageProcessor()
        self.whatsapp_service = WhatsAppService()
        self.intent_router = IntentRouter(message_processor=self.message_processor)
        self.response_formatter = ResponseFormatter()
        
        logger.info(f"🤖 {config.AGENT_NAME} v{config.AGENT_VERSION} inicializado")
        logger.info("✅ Arquitectura refactorizada con servicios (SOLID)")
    
    async def process_message(
        self,
        message: str,
        is_voice: bool = False,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa mensaje del usuario (texto o voz) (Async)
        
        REFACTORIZADO: Delega validación y procesamiento a servicios
        """
        # Generar ID único para esta solicitud
        request_id = str(uuid.uuid4())
        
        try:
            # Si es voz, delegar a MessageProcessor
            if is_voice and audio_path:
                logger.info(f"🎤 Procesando mensaje de voz (request_id: {request_id})")
                # MessageProcessor sigue siendo síncrono (OpenAI calls), no problem
                message = self.message_processor.process_voice_message(audio_path)
            
            # Validar mensaje de texto
            elif not self.message_processor.validate_text_message(message):
                logger.warning(f"⚠️ Mensaje vacío recibido (request_id: {request_id})")
                return self.response_formatter.format_error_response(
                    error_message="El mensaje no puede estar vacío",
                    error_type="validation",
                    request_id=request_id
                )
            
            # Normalizar texto
            message = self.message_processor.normalize_text(message)
            
            logger.log_request(request_id, "user", message)
            
            # Delegar routing a IntentRouter (Async)
            response = await self.intent_router.route_message(message, request_id)
            
            logger.log_response(
                request_id,
                response.get("response_type", "unknown"),
                response.get("success", False)
            )
            
            return response
        
        except ValueError as e:
            # Errores de validación
            logger.warning(f"⚠️ Validación falló: {str(e)}")
            return self.response_formatter.format_error_response(
                error_message=str(e),
                error_type="validation",
                request_id=request_id
            )
        
        except Exception as e:
            # Errores inesperados
            logger.log_error_with_context(e, {"request_id": request_id, "message": message})
            return self.response_formatter.format_error_response(
                error_message=f"Error inesperado: {str(e)}",
                error_type="system",
                request_id=request_id
            )
    
    def send_whatsapp_message(
        self,
        phone_number: str,
        response: Dict[str, Any]
    ) -> bool:
        """
        Envía respuesta por WhatsApp
        
        REFACTORIZADO: Delega a WhatsAppService
        
        Args:
            phone_number: Número de destino (formato: 573124488445@c.us)
            response: Respuesta formateada del agente
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Normalizar número
            phone_number = self.whatsapp_service.normalize_phone_number(phone_number)
            
            # Delegar envío al servicio
            return self.whatsapp_service.send_message_with_response(
                phone_number=phone_number,
                response_data=response
            )
        
        except Exception as e:
            logger.error(f"❌ Error al enviar mensaje: {str(e)}")
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Retorna las capacidades del agente
        
        Returns:
            Dict con información de capacidades
        """
        return {
            "agent_name": config.AGENT_NAME,
            "version": config.AGENT_VERSION,
            "services": {
                "message_processor": "MessageProcessor",
                "whatsapp_service": "WhatsAppService",
                "intent_router": "IntentRouter"
            },
            "tools": {
                "database": "MCPConnector",
                "visualization": "Visualizer",
                "excel": "ExcelGenerator",
                "calculator": "Calculator (NUEVO)"
            },
            "features": [
                "Text message processing",
                "Voice message transcription (Whisper)",
                "WhatsApp integration (EvolutionAPI)",
                "SQL queries (PostgreSQL)",
                "Data visualization (matplotlib/plotly)",
                "Excel export (openpyxl)",
                "Statistical calculations (scipy)",
                "Intent classification (Strategy Pattern)",
                "Async processing (FastAPI)",
                "Dual file delivery (attachment + URL)"
            ]
        }


# Entry point removed - use webhook_server.py for production
# Use examples/example_queries.py for testing

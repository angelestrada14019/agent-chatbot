"""
🤖 EvoDataAgent - OpenAI Agents SDK
Orquestador principal basado en el SDK oficial de OpenAI Agents.
"""
import json
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from agents import Agent, Runner
import config
from utils.logger import get_logger

# Herramientas (Refactorizadas a function_tool)
from tools.mcp_client import query_database
from tools.visualizer import generate_chart
from tools.excel_generator import generate_excel_report
from tools.calculator import calculate_expression

# Servicios de apoyo
from services.message_processor import MessageProcessor
from services.whatsapp_service import WhatsAppService

logger = get_logger("EvoDataAgent")

@dataclass
class UserContext:
    """Contexto de usuario inyectado en herramientas si fuera necesario"""
    phone_number: str
    request_id: str

class EvoDataAgent:
    """
    Agente experto en Análisis de Datos de M.C.T. SAS
    Implementado con OpenAI Agents SDK
    """
    
    def __init__(self):
        self.message_processor = MessageProcessor()
        self.whatsapp_service = WhatsAppService()
        
        # Definición del Agente Nativo
        self.agent = Agent(
            name=config.AGENT_NAME,
            instructions=(
                f"Eres {config.AGENT_NAME}, un analista de datos experto de la empresa M.C.T. SAS. "
                "Tu objetivo es ayudar a los usuarios a entender sus datos de ventas, productos y clientes. "
                "Cuentas con herramientas para consultar la base de datos (SQL), generar gráficas y reportes en Excel. "
                "Sé profesional, amable y siempre verifica los datos antes de dar una conclusión. "
                "Si el usuario pide una gráfica pero no hay datos, primero ejecuta una consulta SQL."
            ),
            model=config.CHAT_MODEL,
            tools=[query_database, generate_chart, generate_excel_report, calculate_expression]
        )
        
        logger.info(f"🤖 Agente '{config.AGENT_NAME}' (SDK) inicializado correctamente")

    async def process_message(
        self,
        message: str,
        phone_number: str = "user",
        is_voice: bool = False,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa el mensaje usando el Runner del SDK
        """
        request_id = str(uuid.uuid4())
        
        try:
            # 1. Pre-procesamiento
            if is_voice and audio_path:
                message = await self.message_processor.process_voice_message(audio_path)
            
            if not self.message_processor.validate_text_message(message):
                return {"success": False, "error": "Mensaje vacío", "type": "validation"}
            
            message = self.message_processor.normalize_text(message)
            logger.log_request(request_id, phone_number, message)
            
            # 2. Ejecutar Runner del SDK
            logger.info(f"🚀 Iniciando Runner para {request_id}")
            
            context = UserContext(phone_number=phone_number, request_id=request_id)
            
            # El Runner maneja el loop de herramientas automáticamente
            result = await Runner.run(
                self.agent,
                [{"role": "user", "content": message}],
                context=context
            )
            
            # 3. Extraer resultados y archivos
            final_content = result.final_output if hasattr(result, "final_output") else ""
            attachments = []
            
            # Obtener el historial completo para buscar resultados de herramientas
            history = result.to_input_list()
            
            for msg in history:
                if msg.get("role") == "tool":
                    try:
                        # Los resultados de nuestras herramientas son JSON strings
                        content = msg.get("content", "")
                        if content:
                            tool_data = json.loads(content)
                            if isinstance(tool_data, dict) and "file_path" in tool_data:
                                attachments.append(tool_data["file_path"])
                    except (json.JSONDecodeError, TypeError):
                        pass 
            
            return {
                "success": True,
                "response": final_content or "Operación completada.",
                "response_type": "files" if attachments else "text",
                "files": attachments,
                "request_id": request_id
            }

        except Exception as e:
            logger.log_error_with_context(e, {"phone_number": phone_number, "request_id": request_id})
            return {
                "success": False,
                "error": str(e),
                "request_id": request_id
            }

    async def send_whatsapp_message(self, phone_number: str, response: Dict[str, Any]) -> bool:
        """Delega a WhatsAppService"""
        phone_number = self.whatsapp_service.normalize_phone_number(phone_number)
        return await self.whatsapp_service.send_message_with_response(phone_number, response)

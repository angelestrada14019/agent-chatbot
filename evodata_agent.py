"""
🤖 EvoDataAgent - OpenAI Agents SDK
Orquestador principal basado en el SDK oficial de OpenAI Agents.
Cumplimiento 100% con SOLID y Clean Code.
"""
import uuid
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from agents import Agent, Runner
import config
from utils.logger import get_logger
from utils.whisper_util import transcribe_audio

# Herramientas (Refactorizadas a Pydantic Results)
from tools.mcp_client import query_database, QueryResult
from tools.visualizer import generate_chart, ChartResult
from tools.excel_generator import generate_excel_report, ExcelResult
from tools.calculator import calculate_expression

logger = get_logger("EvoDataAgent")

class EvoDataAgent:
    """
    Agente experto en Análisis de Datos de M.C.T. SAS.
    Implementación nativa con OpenAI Agents SDK.
    """
    
    def __init__(self):
        # Definición del Agente Nativo
        self.agent = Agent(
            name=config.AGENT_NAME,
            instructions=(
                f"Eres {config.AGENT_NAME}, el analista de datos oficial de M.C.T. SAS. "
                "Tu misión es proporcionar insights precisos sobre ventas, productos y clientes. "
                "Cuentas con herramientas para SQL, gráficas y Excel. "
                "RESPUESTAS: Tus respuestas deben ser SIEMPRE claras y profesionales en español. "
                "Si usas una herramienta que genera un archivo, menciónalo en tu respuesta final. "
                "Si la consulta SQL falla o no hay datos, informa al usuario amablemente."
            ),
            model=config.CHAT_MODEL,
            tools=[query_database, generate_chart, generate_excel_report, calculate_expression]
        )
        logger.info(f"🤖 Agente '{config.AGENT_NAME}' inicializado")

    async def process_message(
        self,
        message: str,
        phone_number: str = "user",
        is_voice: bool = False,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa el mensaje usando el Runner del SDK.
        No usa MessageProcessor (Redundante); usa Whisper directamente si es voz.
        """
        request_id = str(uuid.uuid4())
        attachments = []
        
        try:
            # 1. Voz a Texto (Si aplica)
            if is_voice and audio_path:
                message = await transcribe_audio(audio_path)
            
            if not message or not message.strip():
                return {"success": False, "error": "Mensaje vacío", "request_id": request_id}

            logger.info(f"📩 [{phone_number}] -> {message[:50]}...")
            
            # 2. Ejecutar Runner del SDK
            result = await Runner.run(self.agent, message)
            
            # 3. Extracción Inteligente de Resultados (SOLID: SDK Native)
            # El Runner.run() devuelve un RunResult que contiene 'new_items' (mensajes, tool_calls, etc.)
            for item in getattr(result, "new_items", []):
                # En el SDK, los tool calls suelen estar en objetos Message o ToolCall
                if hasattr(item, "tool_calls") and item.tool_calls:
                    for tool_call in item.tool_calls:
                        # Acceder al resultado de la herramienta si está disponible en el item
                        # O buscar el mensaje de respuesta de la herramienta en new_items
                        pass
                
                # Si el item es un ToolResponseMessage, contiene el objeto de salida
                if hasattr(item, "role") and item.role == "tool":
                    # En algunas versiones el objeto real está en 'output' o 'content'
                    output = getattr(item, "output", None)
                    if output and hasattr(output, "file_path") and output.file_path:
                        attachments.append(output.file_path)

            return {
                "success": True,
                "response": result.final_output,
                "files": attachments,
                "request_id": request_id
            }

        except Exception as e:
            from utils.logger import log_error_with_context
            log_error_with_context(logger, e, {"phone_number": phone_number, "request_id": request_id})
            return {"success": False, "error": str(e), "request_id": request_id}

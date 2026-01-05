"""
🤖 EvoDataAgent - OpenAI Agents SDK
Orquestador principal basado en el SDK oficial de OpenAI Agents.
Cumplimiento 100% con SOLID y Clean Code.
"""
import uuid
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from agents import Agent, Runner
from agents.mcp import MCPServerSse, MCPServerSseParams
import config
from utils.logger import get_logger
from utils.whisper_util import transcribe_audio
from agents.memory import SQLiteSession

# Herramientas Core (Visualización y Reportes)
from tools.visualizer import generate_chart
from tools.excel_generator import generate_excel_report
from tools.calculator import calculate_expression

logger = get_logger("EvoDataAgent")

class EvoDataAgent:
    """
    Agente experto en Análisis de Datos de M.C.T. SAS.
    Implementación nativa con OpenAI Agents SDK.
    """
    
    def __init__(self):
        # 🔌 Configuración Dinámica de MCP (Standard SDK)
        self.mcp_server = MCPServerSse(
            name="mcp_database",
            params=MCPServerSseParams(
                url=config.MCP_SERVER_URL,
                timeout=30.0
            )
        )

        # Definición del Agente Nativo
        self.agent = Agent(
            name=config.AGENT_NAME,
            instructions=(
                f"Eres {config.AGENT_NAME}, el analista de datos oficial de M.C.T. SAS. "
                "Tu misión es proporcionar insights profesionales sobre cualquier base de datos conectada vía MCP. "
                "\n\nESTRATEGIA:"
                "\n1. Explora las herramientas disponibles en el servidor MCP para entender qué datos puedes consultar (ventas, stock, clientes, etc.)."
                "\n2. Ejecuta consultas SQL SELECT precisas según la necesidad del usuario."
                "\n3. Genera gráficas o excels según la solicitud del usuario usando tus herramientas locales."
                "\n4. Sé profesional y estructurado en español."
            ),
            model=config.CHAT_MODEL,
            mcp_servers=[self.mcp_server],
            tools=[
                generate_chart, 
                generate_excel_report, 
                calculate_expression
            ]
        )
        # Memoria persistente basada en SQLite
        self.sessions: Dict[str, SQLiteSession] = {}
        logger.info(f" Agente '{config.AGENT_NAME}' inicializado con soporte de Memoria")

    async def _ensure_mcp_connected(self):
        """Garantiza que la conexión MCP esté activa antes de procesar"""
        # MCPServerSse tiene estado interno; intentamos conectar si no está activo
        try:
            # En el SDK, connect() es el punto de entrada para inicializar la sesión
            logger.info("📡 Verificando conexión MCP...")
            await self.mcp_server.connect()
        except Exception as e:
            # Si ya está conectado, el SDK suele lanzar una excepción o ignorar
            logger.debug(f"Aviso de conexión MCP: {e}")

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
            # 0. Asegurar Conexión MCP (Fix: Server not initialized)
            await self._ensure_mcp_connected()

            # 1. Voz a Texto (Si aplica)
            if is_voice and audio_path:
                message = await transcribe_audio(audio_path)
            
            if not message or not message.strip():
                return {"success": False, "error": "Mensaje vacío", "request_id": request_id}

            logger.info(f"📩 [{phone_number}] -> {message[:50]}...")
            
            # 2. Obtener o crear sesión para el usuario (Memoria)
            if phone_number not in self.sessions:
                db_path = f"logs/memory_{phone_number}.db"
                self.sessions[phone_number] = SQLiteSession(session_id=phone_number, db_path=db_path)
            
            session = self.sessions[phone_number]

            # 3. Ejecutar Runner del SDK con Memoria
            result = await Runner.run(self.agent, message, session=session)
            
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

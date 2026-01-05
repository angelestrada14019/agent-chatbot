"""
🔌 MCP Client - Integración con OpenAI Agents SDK
Este módulo proporciona herramientas para interactuar con servidores MCP.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from contextlib import AsyncExitStack

from agents import function_tool
from mcp import ClientSession
from mcp.client.sse import sse_client
import config

logger = logging.getLogger("MCPTool")

class MCPManager:
    """Gestiona la conexión con el servidor MCP"""
    _instance = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.url = config.MCP_SERVER_URL
        
    @classmethod
    async def get_instance(cls):
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    async def connect(self):
        """Asegura la conexión con el servidor MCP"""
        if self.session:
            return self.session
            
        logger.info(f"🔌 Conectando a MCP via SSE: {self.url}")
        try:
            read, write = await self.exit_stack.enter_async_context(sse_client(self.url))
            session = ClientSession(read, write)
            await session.initialize()
            self.session = session
            logger.info("✅ Conexión MCP establecida")
            return self.session
        except Exception as e:
            logger.error(f"❌ Error conectando a MCP: {str(e)}")
            await self.exit_stack.aclose()
            self.session = None
            raise

manager = MCPManager()

@function_tool
async def query_database(sql: str) -> str:
    """
    Ejecuta una consulta SQL en la base de datos de la empresa para obtener información sobre ventas, productos, clientes, etc.
    Solo soporta sentencias SELECT.
    
    Args:
        sql: Sentencia SQL válida. Ejemplo: "SELECT * FROM ventas LIMIT 5"
    """
    try:
        mcp = await manager.connect()
        logger.info(f"📊 Ejecutando SQL: {sql}")
        
        # Llamar a la herramienta 'query' del servidor MCP
        result = await mcp.call_tool("query", arguments={"sql": sql})
        
        # Extraer el contenido de la respuesta
        if hasattr(result, 'content') and result.content:
            data = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content)
            return data
        return json.dumps({"success": False, "error": "No se obtuvo respuesta del servidor MCP"})
        
    except Exception as e:
        logger.error(f"❌ Error en query_database: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})

# Singleton para compatibilidad si fuera necesario (aunque el SDK usa la función directa)
def get_mcp_client():
    return manager

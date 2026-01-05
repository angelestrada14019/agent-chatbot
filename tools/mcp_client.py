"""
🔌 MCP Client - Integración con OpenAI Agents SDK
Implementación asíncrona para consultas SQL en base de datos.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from contextlib import AsyncExitStack
from pydantic import BaseModel, Field

from agents import function_tool
from mcp import ClientSession
from mcp.client.sse import sse_client
import config

logger = logging.getLogger("MCPTool")

class QueryResult(BaseModel):
    """Resultado estructurado de una consulta SQL"""
    success: bool = Field(..., description="Indica si la consulta fue exitosa")
    data_json: Optional[str] = Field(None, description="Datos en formato JSON string")
    error: Optional[str] = Field(None, description="Mensaje de error si falló")
    row_count: int = Field(0, description="Número de filas obtenidas")

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
        if self.session: return self.session
            
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
async def query_database(sql: str) -> QueryResult:
    """
    Ejecuta una consulta SQL SELECT en la base de datos para obtener información de ventas, productos o clientes.
    """
    try:
        mcp = await manager.connect()
        logger.info(f"📊 SQL: {sql}")
        
        result = await mcp.call_tool("query", arguments={"sql": sql})
        
        if hasattr(result, 'content') and result.content:
            data_str = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content)
            # Intentar parsear para contar filas
            try:
                data_list = json.loads(data_str)
                row_count = len(data_list) if isinstance(data_list, list) else 0
            except:
                row_count = 0
                
            return QueryResult(success=True, data_json=data_str, row_count=row_count)
            
        return QueryResult(success=False, error="No se obtuvo respuesta del servidor MCP")
        
    except Exception as e:
        logger.error(f"❌ Error en query_database: {str(e)}")
        return QueryResult(success=False, error=str(e))

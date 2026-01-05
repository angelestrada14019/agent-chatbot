"""
🔌 MCP Client - Gestión Robusta de Conexión
Implementación siguiendo el diagnóstico de buenas prácticas para evitar 'Server not initialized'.
"""
import asyncio
import json
import logging
import httpx
from contextlib import AsyncExitStack
from typing import Dict, Any, Optional

from agents import function_tool
from mcp import ClientSession
from mcp.client.sse import sse_client
from pydantic import BaseModel, Field
import config

logger = logging.getLogger("MCPManager")

class QueryResult(BaseModel):
    """Resultado estructurado de una consulta SQL"""
    success: bool = Field(..., description="Indica si la consulta fue exitosa")
    data_json: Optional[str] = Field(None, description="Datos en formato JSON string")
    error: Optional[str] = Field(None, description="Mensaje de error si falló")
    row_count: int = Field(0, description="Número de filas obtenidas")

class MCPManager:
    """Gestiona la conexión con el servidor MCP con reintentos y validación"""
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.url = (config.MCP_SERVER_URL or "").strip()
        if not self.url:
            raise RuntimeError("MCP_SERVER_URL no configurado")

    async def connect(self):
        """Conecta al servidor MCP con lógica de reintentos y backoff"""
        if self.session:
            return self.session

        logger.info(f"🔌 Conectando a MCP via SSE: {self.url}")

        # 1. Validación rápida de accesibilidad del host
        try:
            # Comprobar host básico para detectar errores de red/DNS rápidos
            base_check = self.url.split('/sse')[0]
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(base_check)
                logger.debug(f"Check base URL {base_check} -> {r.status_code}")
        except Exception as exc:
            logger.warning(f"⚠️ Aviso: No se pudo verificar el host {self.url} antes de conectar: {exc}")

        # 2. Reintentos con Backoff Exponencial
        max_attempts = 4
        for attempt in range(1, max_attempts + 1):
            try:
                read, write = await self.exit_stack.enter_async_context(sse_client(self.url))
                session = ClientSession(read, write)
                await session.initialize()
                self.session = session
                logger.info(f"✅ Conexión MCP establecida (Intento {attempt})")
                return self.session
            except Exception as e:
                logger.error(f"❌ Intento {attempt} falló conectando a MCP: {e}")
                # Limpiar stack parcial antes del siguiente intento
                await self.exit_stack.aclose()
                self.exit_stack = AsyncExitStack()
                self.session = None
                
                if attempt < max_attempts:
                    wait_time = 1 * attempt
                    logger.info(f"⏳ Reintentando en {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("❌ No se pudo conectar al MCP tras agotar los intentos.")
                    raise

    async def disconnect(self):
        """Cierra la conexión de forma segura"""
        await self.exit_stack.aclose()
        self.session = None
        logger.info("🔌 Conexión MCP cerrada")

# Instancia global del manager
manager = MCPManager()

@function_tool
async def query_database(sql: str) -> QueryResult:
    """
    Ejecuta una consulta SQL SELECT en la base de datos conectada.
    """
    try:
        mcp = await manager.connect()
        logger.info(f"📊 Ejecutando SQL: {sql}")
        # Ajustado a nombre corto según estandarización
        result = await mcp.call_tool("query", arguments={"sql": sql})
        return _parse_mcp_result(result)
    except Exception as e:
        logger.error(f"❌ Error en query_database: {str(e)}")
        return QueryResult(success=False, error=str(e))

def _parse_mcp_result(result) -> QueryResult:
    """Helper para normalizar la respuesta de herramientas MCP"""
    if hasattr(result, 'content') and result.content:
        data_str = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content)
        try:
            data_list = json.loads(data_str)
            row_count = len(data_list) if isinstance(data_list, list) else 0
        except:
            row_count = 0
        return QueryResult(success=True, data_json=data_str, row_count=row_count)
    return QueryResult(success=False, error="Sin respuesta del servidor MCP")

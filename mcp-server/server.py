import os
import asyncio
import logging
import json
from contextlib import asynccontextmanager
from typing import Any, List

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent

import psycopg2
from psycopg2.extras import RealDictCursor
from starlette.applications import Starlette
from starlette.routing import Route

# ==========================================
# 📝 CONFIGURACIÓN Y LOGGING
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MCPServer-Standard")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "analytics"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres")
}

# ==========================================
# 🔌 MCP SERVER CORE
# ==========================================
mcp = Server("evodata-mcp-server")
sse_transport = SseServerTransport("/messages")

def get_db_connection():
    """Conexión robusta a PostgreSQL"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"❌ Error DB: {e}")
        raise

@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """Define las herramientas disponibles para el Agent SDK"""
    return [
        Tool(
            name="query",
            description="Ejecuta una consulta SQL SELECT para obtener datos de compras, productos o clientes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "Consulta SQL SELECT válida"}
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="list_tables",
            description="Lista las tablas disponibles para entender la estructura de datos.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_schema",
            description="Obtiene las columnas y tipos de datos de una tabla específica.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Nombre de la tabla"}
                },
                "required": ["table_name"]
            }
        )
    ]

@mcp.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Manejador universal de herramientas siguiendo el protocolo MCP"""
    logger.info(f"🛠️ Ejecutando herramienta: {name} | Args: {arguments}")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if name == "query":
            sql = arguments.get("sql", "")
            if not sql.lower().strip().startswith("select"):
                return [TextContent(type="text", text="Error: Solo se permiten consultas SELECT por seguridad.")]
            
            cursor.execute(sql)
            results = cursor.fetchall()
            return [TextContent(type="text", text=json.dumps(results, default=str))]
            
        elif name == "list_tables":
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [row['table_name'] for row in cursor.fetchall()]
            return [TextContent(type="text", text=json.dumps(tables))]
            
        elif name == "get_schema":
            table_name = arguments.get("table_name")
            cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s", (table_name,))
            columns = cursor.fetchall()
            return [TextContent(type="text", text=json.dumps(columns))]
            
        else:
            return [TextContent(type="text", text=f"Error: Herramienta '{name}' no encontrada.")]
            
    except Exception as e:
        logger.error(f"❌ Error en tool {name}: {e}")
        return [TextContent(type="text", text=f"Error en base de datos: {str(e)}")]
    finally:
        if conn:
            conn.close()

# ==========================================
# 🌐 STARLETTE ASGI INTERFACE
# ==========================================

async def handle_sse(scope, receive, send):
    """Handler ASGI puro para la conexión de streaming SSE"""
    try:
        async with sse_transport.connect_sse(scope, receive, send) as (read_stream, write_stream):
            await mcp.run(
                read_stream, 
                write_stream, 
                mcp.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"❌ Error SSE: {e}")

async def handle_messages(scope, receive, send):
    """Handler ASGI para recibir mensajes POST del cliente"""
    try:
        await sse_transport.handle_post_message(scope, receive, send)
    except Exception as e:
        logger.error(f"❌ Error POST: {e}")

@asynccontextmanager
async def lifespan(app: Starlette):
    logger.info("🚀 Servidor MCP (SSE Mode) iniciado")
    yield
    logger.info("🛑 Servidor MCP detenido")

# Definición de la aplicación Starlette para máxima compatibilidad ASGI
app = Starlette(
    debug=True,
    lifespan=lifespan
)

# Registramos las rutas como aplicaciones ASGI puras para evitar conflictos de respuesta
app.add_route("/sse", handle_sse, methods=["GET"])
app.add_route("/messages", handle_messages, methods=["POST"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

import os
import asyncio
import logging
import json
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from mcp.server.sse import SseServerTransport
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import psycopg2
from psycopg2.extras import RealDictCursor

# Configurar Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MCPServer-SSE")

# Configuración de BD desde Variables de Entorno
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "analytics"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres")
}

# Inicializar Servidor MCP
mcp = Server("postgres-mcp-server")

# Transport para SSE
sse_transport = SseServerTransport("/messages")

def get_db_connection():
    """Obtiene conexión a la base de datos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("✅ Conexión a BD establecida")
        return conn
    except Exception as e:
        logger.error(f"❌ Error conectando a BD: {e}")
        raise

@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """Lista las herramientas disponibles"""
    return [
        Tool(
            name="query",
            description="Ejecuta una consulta SQL segura (SELECT) en la base de datos de análisis (Tablas: ventas, productos, clientes)",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "Consulta SQL SELECT a ejecutar"
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="list_tables",
            description="Lista las tablas disponibles en la base de datos",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_schema",
            description="Obtiene el esquema de una tabla específica",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"}
                },
                "required": ["table_name"]
            }
        )
    ]

@mcp.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Ejecuta una herramienta"""
    logger.info(f"🛠️ Ejecutando herramienta: {name} con args: {arguments}")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if name == "query":
            sql = arguments.get("sql")
            if not sql.lower().strip().startswith("select"):
                raise ValueError("Solo se permiten consultas SELECT por seguridad")
                
            cursor.execute(sql)
            results = cursor.fetchall()
            
            # Convertir resultados a JSON string para enviarlos como texto
            return [TextContent(type="text", text=json.dumps(results, default=str, indent=2))]
            
        elif name == "list_tables":
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [row['table_name'] for row in cursor.fetchall()]
            return [TextContent(type="text", text=json.dumps(tables, indent=2))]
            
        elif name == "get_schema":
            table_name = arguments.get("table_name")
            cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
            columns = cursor.fetchall()
            return [TextContent(type="text", text=json.dumps(columns, indent=2))]
            
        else:
            raise ValueError(f"Herramienta desconocida: {name}")
            
    except Exception as e:
        logger.error(f"❌ Error ejecutando tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    finally:
        if conn:
            conn.close()

# ==========================================
# Configuración FastAPI + SSE
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Iniciando Servidor MCP (SSE Mode)...")
    yield
    # Shutdown
    logger.info("🛑 Deteniendo Servidor MCP...")

app = FastAPI(lifespan=lifespan)

@app.get("/sse")
async def handle_sse(request: Request):
    """Endpoint para la conexión SSE"""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp.run(
            streams[0], streams[1], mcp.create_initialization_options()
        )

@app.post("/messages")
async def handle_messages(request: Request):
    """Endpoint para recibir mensajes del cliente (POST)"""
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)

if __name__ == "__main__":
    import uvicorn
    # Escuchar en todas las interfaces dentro del contenedor
    uvicorn.run(app, host="0.0.0.0", port=8002)

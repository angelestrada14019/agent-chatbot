#!/usr/bin/env python3
"""
🚀 MCP Server Simulator para PostgreSQL
Servidor MCP que implementa el protocolo Model Context Protocol
Simula conexión a PostgreSQL y expone recursos/herramientas
"""
import asyncio
import json
import sys
import os
from typing import Any, Sequence
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp-server.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("MCPServer")

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.error("MCP Server SDK no instalado. Instalar con: pip install mcp")
    sys.exit(1)


class PostgreSQLMCPServer:
    """
    Servidor MCP que simula PostgreSQL
    
    Expone:
    - Recursos: Tablas y vistas de PostgreSQL
    - Herramientas: query, list_tables, get_schema
    """
    
    def __init__(self):
        self.server = Server("postgres-mcp-server")
        self.db_config = self._load_db_config()
        
        # Datos simulados (en producción, conectar a PostgreSQL real)
        self.simulated_data = self._create_simulated_data()
        
        # Registrar handlers
        self._register_handlers()
        
        logger.info("✅ PostgreSQL MCP Server inicializado")
    
    def _load_db_config(self) -> dict:
        """Carga configuración de DB desde variables de entorno"""
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "analytics"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres")
        }
    
    def _create_simulated_data(self) -> dict:
        """Crea datos simulados para testing"""
        return {
            "ventas": [
                {"id": 1, "producto": "Laptop", "cantidad": 10, "precio": 1200.00, "fecha": "2024-01-15"},
                {"id": 2, "producto": "Mouse", "cantidad": 50, "precio": 25.00, "fecha": "2024-01-16"},
                {"id": 3, "producto": "Teclado", "cantidad": 30, "precio": 75.00, "fecha": "2024-01-17"},
                {"id": 4, "producto": "Monitor", "cantidad": 15, "precio": 350.00, "fecha": "2024-01-18"},
                {"id": 5, "producto": "Webcam", "cantidad": 20, "precio": 85.00, "fecha": "2024-01-19"},
            ],
            "productos": [
                {"id": 1, "nombre": "Laptop", "categoria": "Computadoras", "stock": 50},
                {"id": 2, "nombre": "Mouse", "categoria": "Accesorios", "stock": 200},
                {"id": 3, "nombre": "Teclado", "categoria": "Accesorios", "stock": 150},
                {"id": 4, "nombre": "Monitor", "categoria": "Pantallas", "stock": 75},
                {"id": 5, "nombre": "Webcam", "categoria": "Video", "stock": 100},
            ],
            "clientes": [
                {"id": 1, "nombre": "Juan Pérez", "email": "juan@example.com", "ciudad": "Bogotá"},
                {"id": 2, "nombre": "María García", "email": "maria@example.com", "ciudad": "Medellín"},
                {"id": 3, "nombre": "Carlos López", "email": "carlos@example.com", "ciudad": "Cali"},
            ]
        }
    
    def _register_handlers(self):
        """Registra handlers de recursos y herramientas"""
        
        # Handler de recursos
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """Lista recursos disponibles (tablas)"""
            logger.info("📋 Listando recursos disponibles")
            
            resources = []
            for table_name in self.simulated_data.keys():
                resources.append(
                    Resource(
                        uri=f"postgres://analytics/{table_name}",
                        name=f"Tabla: {table_name}",
                        mimeType="application/json",
                        description=f"Datos de la tabla {table_name}"
                    )
                )
            
            return resources
        
        # Handler para leer recurso
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Lee contenido de un recurso (tabla)"""
            logger.info(f"📖 Leyendo recurso: {uri}")
            
            # Parsear URI: postgres://analytics/tabla
            parts = uri.replace("postgres://", "").split("/")
            if len(parts) < 2:
                raise ValueError(f"URI inválida: {uri}")
            
            table_name = parts[1]
            
            if table_name not in self.simulated_data:
                raise ValueError(f"Tabla '{table_name}' no encontrada")
            
            data = self.simulated_data[table_name]
            
            return json.dumps({
                "table": table_name,
                "rows": data,
                "count": len(data)
            }, indent=2)
        
        # Handler de herramientas
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """Lista herramientas disponibles"""
            logger.info("🛠️ Listando herramientas disponibles")
            
            return [
                Tool(
                    name="query",
                    description="Ejecuta una query SQL (simulada)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "Query SQL a ejecutar"
                            },
                            "params": {
                                "type": "object",
                                "description": "Parámetros de la query"
                            }
                        },
                        "required": ["sql"]
                    }
                ),
                Tool(
                    name="list_tables",
                    description="Lista todas las tablas disponibles",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_schema",
                    description="Obtiene el schema de una tabla",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Nombre de la tabla"
                            }
                        },
                        "required": ["table_name"]
                    }
                )
            ]
        
        # Handler para ejecutar herramientas
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            """Ejecuta una herramienta"""
            logger.info(f"🔧 Ejecutando herramienta: {name}")
            
            if name == "query":
                return await self._handle_query(arguments)
            elif name == "list_tables":
                return await self._handle_list_tables()
            elif name == "get_schema":
                return await self._handle_get_schema(arguments)
            else:
                raise ValueError(f"Herramienta '{name}' no encontrada")
    
    async def _handle_query(self, arguments: dict) -> Sequence[TextContent]:
        """Simula ejecución de query SQL"""
        sql = arguments.get("sql", "")
        params = arguments.get("params", {})
        
        logger.info(f"📊 Ejecutando query: {sql[:100]}...")
        
        # Simulación simple: detectar tabla en FROM
        sql_lower = sql.lower()
        
        result_data = []
        columns = []
        
        # Detectar tabla
        for table_name in self.simulated_data.keys():
            if table_name in sql_lower:
                data = self.simulated_data[table_name]
                result_data = data
                if data:
                    columns = list(data[0].keys())
                break
        
        result = {
            "success": True,
            "rows": result_data,
            "columns": columns,
            "row_count": len(result_data),
            "query": sql
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _handle_list_tables(self) -> Sequence[TextContent]:
        """Lista todas las tablas"""
        logger.info("📋 Listando tablas")
        
        tables = list(self.simulated_data.keys())
        
        result = {
            "tables": tables,
            "count": len(tables)
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _handle_get_schema(self, arguments: dict) -> Sequence[TextContent]:
        """Obtiene schema de una tabla"""
        table_name = arguments.get("table_name")
        
        logger.info(f"📐 Obteniendo schema de: {table_name}")
        
        if table_name not in self.simulated_data:
            raise ValueError(f"Tabla '{table_name}' no encontrada")
        
        data = self.simulated_data[table_name]
        
        if not data:
            schema = []
        else:
            # Inferir schema desde primer row
            first_row = data[0]
            schema = [
                {
                    "column": col,
                    "type": type(val).__name__
                }
                for col, val in first_row.items()
            ]
        
        result = {
            "table": table_name,
            "columns": schema,
            "row_count": len(data)
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def run(self):
        """Inicia el servidor MCP"""
        logger.info("🚀 Iniciando servidor MCP...")
        logger.info(f"📊 Base de datos: {self.db_config['database']}")
        logger.info(f"📋 Tablas simuladas: {list(self.simulated_data.keys())}")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Entry point del servidor"""
    try:
        server = PostgreSQLMCPServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("🛑 Servidor detenido por usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

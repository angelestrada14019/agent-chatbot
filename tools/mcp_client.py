"""
🔌 MCP Client - Implementación Real del Protocolo MCP
Cliente que se conecta a servidores MCP externos
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP SDK no instalado. Instalar con: pip install mcp")

from tools.base import Tool, ToolResult, ToolStatus
import config

logger = logging.getLogger(__name__)


class MCPClient(Tool):
    """
    Cliente MCP que implementa el protocolo Model Context Protocol
    
    Se conecta a servidores MCP externos que exponen:
    - Recursos: Datos (ej: postgres://database/table)
    - Herramientas: Funciones (ej: query, list_tables)
    - Prompts: Plantillas reutilizables
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa cliente MCP
        
        Args:
            config_path: DEPRECATED - Se construye config desde variables de entorno
        """
        super().__init__("MCPClient")
        
        if not MCP_AVAILABLE:
            raise ImportError(
                "MCP SDK no está instalado. "
                "Instalar con: pip install mcp"
            )
        
        self.sessions: Dict[str, ClientSession] = {}
        self.server_configs: Dict[str, Dict] = {}
        self._exit_stack = []  # Para almacenar los context managers (sse/stdio components)
        
        # Construir configuración desde variables de entorno
        self._build_server_configs_from_env()
    
    def _build_server_configs_from_env(self):
        """Construye configuración de servidores MCP desde variables de entorno"""
        import config as cfg
        
        # Configuración del servidor PostgreSQL MCP
        self.server_configs = {
            "postgres": {
                "command": "python",
                "args": ["mcp-server/server.py"],
                "env": {
                    "DB_HOST": cfg.DB_HOST,
                    "DB_PORT": str(cfg.DB_PORT),
                    "DB_NAME": cfg.DB_NAME,
                    "DB_USER": cfg.DB_USER or "postgres",
                    "DB_PASSWORD": cfg.DB_PASSWORD or "postgres"
                }
            }
        }
        
        self.logger.info(f"✅ Configuración MCP construida desde variables de entorno")
        self.logger.info(f"📋 Servidores disponibles: {list(self.server_configs.keys())}")
    
    async def connect_to_server(self, server_name: str) -> Dict[str, Any]:
        """
        Conecta a un servidor MCP
        
        Args:
            server_name: Nombre del servidor (debe estar en config)
            
        Returns:
            Dict con recursos y herramientas disponibles
        """
        if server_name in self.sessions:
            self.logger.info(f"✅ Ya conectado a servidor '{server_name}'")
            return await self._get_server_capabilities(server_name)
        
        if server_name not in self.server_configs:
            raise ValueError(
                f"Servidor '{server_name}' no encontrado en configuración. "
                f"Disponibles: {list(self.server_configs.keys())}"
            )
        
        config = self.server_configs[server_name]
        
        try:
            self.logger.info(f"🔌 Conectando a servidor MCP '{server_name}'...")
            
            # Configurar parámetros del servidor
            server_params = StdioServerParameters(
                command=config["command"],
                args=config.get("args", []),
                env=config.get("env", {})
            )
            
            # Iniciar servidor y obtener streams
            read, write = await stdio_client(server_params)
            
            # Crear sesión
            session = ClientSession(read, write)
            await session.initialize()
            
            self.sessions[server_name] = session
            
            # Obtener capacidades
            capabilities = await self._get_server_capabilities(server_name)
            
            self.logger.info(
                f"✅ Conectado a '{server_name}'",
                resources=len(capabilities.get("resources", [])),
                tools=len(capabilities.get("tools", []))
            )
            
            return capabilities
        
        except Exception as e:
            self.logger.error(f"❌ Error conectando a servidor '{server_name}': {str(e)}")
            raise
    
    async def _get_server_capabilities(self, server_name: str) -> Dict[str, Any]:
        """Obtiene capacidades del servidor (recursos, herramientas, prompts)"""
        session = self.sessions[server_name]
        
        try:
            resources = await session.list_resources()
            tools = await session.list_tools()
            prompts = await session.list_prompts()
            
            return {
                "resources": [r.dict() for r in resources.resources],
                "tools": [t.dict() for t in tools.tools],
                "prompts": [p.dict() for p in prompts.prompts]
            }
        except Exception as e:
            self.logger.warning(f"⚠️ Error obteniendo capacidades: {str(e)}")
            return {"resources": [], "tools": [], "prompts": []}
    
    async def call_tool_async(
        self,
        server_name: str,
        tool_name: str,
        **arguments
    ) -> Any:
        """
        Llama una herramienta del servidor MCP
        
        Args:
            server_name: Nombre del servidor
            tool_name: Nombre de la herramienta
            **arguments: Argumentos de la herramienta
            
        Returns:
            Resultado de la herramienta
        """
        if server_name not in self.sessions:
            await self.connect_to_server(server_name)
        
        session = self.sessions[server_name]
        
        try:
            self.logger.info(f"🔧 Llamando herramienta '{tool_name}' en '{server_name}'")
            
            result = await session.call_tool(tool_name, arguments=arguments)
            
            self.logger.info(f"✅ Herramienta '{tool_name}' ejecutada")
            
            return result
        
        except Exception as e:
            self.logger.error(f"❌ Error llamando herramienta '{tool_name}': {str(e)}")
            raise
    
    async def read_resource_async(self, server_name: str, uri: str) -> Any:
        """
        Lee un recurso del servidor MCP
        
        Args:
            server_name: Nombre del servidor
            uri: URI del recurso (ej: "postgres://analytics/ventas")
            
        Returns:
            Contenido del recurso
        """
        if server_name not in self.sessions:
            await self.connect_to_server(server_name)
        
        session = self.sessions[server_name]
        
        try:
            self.logger.info(f"📖 Leyendo recurso '{uri}' de '{server_name}'")
            
            resource = await session.read_resource(uri)
            
            self.logger.info(f"✅ Recurso leído: {uri}")
            
            return resource
        
        except Exception as e:
            self.logger.error(f"❌ Error leyendo recurso '{uri}': {str(e)}")
            raise
    
    # ============================================
    # Interfaz Síncrona (Tool interface)
    # ============================================
    
    def execute(self, operation: str, **params) -> ToolResult:
        """
        Ejecuta operación MCP (interfaz síncrona para compatibilidad)
        
        Operations:
        - connect: Conectar a servidor
        - call_tool: Llamar herramienta
        - read_resource: Leer recurso
        - list_capabilities: Listar capacidades
        """
        try:
            if operation == "connect":
                result = asyncio.run(self.connect_to_server(params["server_name"]))
                return ToolResult(status=ToolStatus.SUCCESS, data=result)
            
            elif operation == "call_tool":
                server = params.pop("server_name")
                tool = params.pop("tool_name")
                result = asyncio.run(self.call_tool_async(server, tool, **params))
                
                # Convertir resultado MCP a ToolResult
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=self._parse_mcp_result(result)
                )
            
            elif operation == "read_resource":
                result = asyncio.run(
                    self.read_resource_async(
                        params["server_name"],
                        params["uri"]
                    )
                )
                return ToolResult(status=ToolStatus.SUCCESS, data=result)
            
            elif operation == "list_capabilities":
                result = asyncio.run(
                    self._get_server_capabilities(params["server_name"])
                )
                return ToolResult(status=ToolStatus.SUCCESS, data=result)
            
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Operación '{operation}' no soportada"
                )
        
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    def _parse_mcp_result(self, result: Any) -> Any:
        """Parsea resultado de herramienta MCP a formato estándar"""
        if hasattr(result, 'content'):
            # MCP result tiene content
            content = result.content
            if isinstance(content, list) and len(content) > 0:
                return content[0].text if hasattr(content[0], 'text') else content
            return content
        return result
    
    def get_supported_operations(self) -> List[str]:
        """Lista de operaciones soportadas"""
        return ["connect", "call_tool", "read_resource", "list_capabilities"]
    
    async def close_all(self):
        """Cierra todas las conexiones a servidores MCP"""
        for server_name, session in self.sessions.items():
            try:
                await session.close()
                self.logger.info(f"✅ Desconectado de '{server_name}'")
            except Exception as e:
                self.logger.warning(f"⚠️ Error cerrando '{server_name}': {str(e)}")
        
        self.sessions.clear()


# ============================================
# Adaptador para compatibilidad con código existente
# ============================================

class MCPDatabaseAdapter:
    """
    Adaptador que expone la interfaz del antiguo MCPConnector
    pero usa MCP real por debajo
    """
    
    def __init__(self, server_name: str = "postgres"):
        """
        Args:
            server_name: Nombre del servidor MCP a usar
        """
        self.mcp_client = MCPClient()
        self.server_name = server_name
        
        # Conectar al servidor
        asyncio.run(self.mcp_client.connect_to_server(server_name))
        
        logger.info(f"✅ MCPDatabaseAdapter inicializado con servidor '{server_name}'")
    
    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta query SQL usando servidor MCP
        
        Interfaz compatible con el antiguo mcp_connector.py
        """
        try:
            # Llamar herramienta 'query' del servidor MCP
            result = self.mcp_client.execute(
                "call_tool",
                server_name=self.server_name,
                tool_name="query",
                sql=sql,
                params=params or {},
                timeout=timeout or config.MAX_QUERY_TIMEOUT
            )
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error,
                    "data": [],
                    "columns": [],
                    "row_count": 0
                }
            
            # Formatear resultado
            data = result.data
            
            return {
                "success": True,
                "data": data.get("rows", []),
                "columns": data.get("columns", []),
                "row_count": len(data.get("rows", [])),
                "execution_time": result.metadata.get("execution_time", 0)
            }
        
        except Exception as e:
            logger.error(f"❌ Error en execute_query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "columns": [],
                "row_count": 0
            }
    
    def validate_connection(self) -> bool:
        """Valida que la conexión al servidor MCP esté activa"""
        return self.server_name in self.mcp_client.sessions


# Singleton instance (para compatibilidad)
_mcp_adapter_instance = None


def get_mcp_client() -> MCPDatabaseAdapter:
    """
    Obtiene instancia singleton del cliente MCP
    
    Returns:
        MCPDatabaseAdapter configurado
    """
    global _mcp_adapter_instance
    if _mcp_adapter_instance is None:
        _mcp_adapter_instance = MCPDatabaseAdapter()
    return _mcp_adapter_instance

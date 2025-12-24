"""
🗄️ MCP Database Connector Tool
Herramienta para conectar y consultar PostgreSQL de manera segura
"""
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError, TimeoutError as SQLTimeoutError
import time
import re
import config
from utils.logger import get_logger

logger = get_logger("MCPConnector")


class MCPConnector:
    """Conector a base de datos PostgreSQL con seguridad y pooling"""
    
    def __init__(self):
        """Inicializa el conector con pool de conexiones"""
        self.engine = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Crea el engine de SQLAlchemy con pooling"""
        try:
            self.engine = create_engine(
                config.DATABASE_URL,
                poolclass=QueuePool,
                pool_size=config.DB_POOL_SIZE,
                max_overflow=config.DB_MAX_OVERFLOW,
                pool_timeout=config.DB_POOL_TIMEOUT,
                pool_pre_ping=True,  # Verifica conexiones antes de usar
                echo=config.VERBOSE_LOGGING
            )
            
            # Test de conexión inicial
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("✅ Conexión a PostgreSQL establecida correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error al conectar a PostgreSQL: {str(e)}")
            raise
    
    def validate_connection(self) -> bool:
        """
        Valida que la conexión esté activa
        
        Returns:
            bool: True si la conexión es válida
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"❌ Conexión inválida: {str(e)}")
            return False
    
    def _validate_sql_safety(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        Valida que la consulta SQL sea segura (solo SELECT)
        
        Args:
            sql: Consulta SQL a validar
            
        Returns:
            tuple: (es_valida, mensaje_error)
        """
        sql_upper = sql.upper().strip()
        
        # Verificar palabras prohibidas
        for forbidden in config.FORBIDDEN_SQL_KEYWORDS:
            # Buscar como palabra completa, no como substring
            pattern = r'\b' + re.escape(forbidden) + r'\b'
            if re.search(pattern, sql_upper):
                return False, f"Operación prohibida: {forbidden}"
        
        # Debe comenzar con SELECT o WITH (CTEs)
        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
            return False, "Solo se permiten consultas SELECT"
        
        # Verificar límite de longitud (prevenir queries muy largas)
        if len(sql) > 10000:
            return False, "Consulta demasiado larga"
        
        return True, None
    
    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta una consulta SQL parametrizada
        
        Args:
            sql: Consulta SQL (solo SELECT)
            params: Parámetros para la consulta (diccionario)
            timeout: Timeout en segundos (opcional)
            
        Returns:
            Dict con resultados:
            {
                "success": bool,
                "data": List[Dict],
                "columns": List[str],
                "row_count": int,
                "execution_time": float
            }
        """
        start_time = time.time()
        
        # Validar seguridad de la consulta
        is_safe, error_msg = self._validate_sql_safety(sql)
        if not is_safe:
            logger.warning(f"⚠️ Consulta insegura bloqueada: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "data": [],
                "columns": [],
                "row_count": 0
            }
        
        try:
            # Usar timeout si se proporciona
            execution_timeout = timeout or config.MAX_QUERY_TIMEOUT
            
            with self.engine.connect() as conn:
                # Configurar timeout para esta sesión
                conn.execute(text(f"SET statement_timeout = {execution_timeout * 1000}"))
                
                # Ejecutar consulta con parámetros
                result = conn.execute(text(sql), params or {})
                
                # Obtener columnas
                columns = list(result.keys())
                
                # Obtener datos
                rows = result.fetchall()
                
                # Convertir a lista de diccionarios
                data = [dict(zip(columns, row)) for row in rows]
                
                execution_time = time.time() - start_time
                
                logger.info(
                    f"✅ Consulta ejecutada exitosamente",
                    row_count=len(data),
                    execution_time=execution_time
                )
                
                return {
                    "success": True,
                    "data": data,
                    "columns": columns,
                    "row_count": len(data),
                    "execution_time": execution_time
                }
        
        except SQLTimeoutError as e:
            logger.error(f"⏱️ Timeout en consulta: {str(e)}")
            return {
                "success": False,
                "error": f"La consulta excedió el límite de tiempo ({execution_timeout}s)",
                "data": [],
                "columns": [],
                "row_count": 0
            }
        
        except SQLAlchemyError as e:
            logger.error(f"❌ Error SQL: {str(e)}")
            return {
                "success": False,
                "error": f"Error en la consulta: {str(e)}",
                "data": [],
                "columns": [],
                "row_count": 0
            }
        
        except Exception as e:
            logger.error(f"❌ Error inesperado: {str(e)}")
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}",
                "data": [],
                "columns": [],
                "row_count": 0
            }
    
    def call_stored_procedure(
        self,
        procedure_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Llama a un procedimiento almacenado
        
        Args:
            procedure_name: Nombre del procedimiento
            params: Parámetros del procedimiento
            
        Returns:
            Dict con resultados
        """
        start_time = time.time()
        
        try:
            # Construir llamada al procedimiento
            param_placeholders = ", ".join([f":{key}" for key in (params or {}).keys()])
            sql = f"SELECT * FROM {procedure_name}({param_placeholders})"
            
            logger.info(f"🔧 Llamando procedimiento: {procedure_name}")
            
            # Ejecutar usando execute_query (hereda validaciones de seguridad)
            result = self.execute_query(sql, params)
            
            if result["success"]:
                execution_time = time.time() - start_time
                logger.info(
                    f"✅ Procedimiento ejecutado",
                    procedure=procedure_name,
                    execution_time=execution_time
                )
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Error al llamar procedimiento: {str(e)}")
            return {
                "success": False,
                "error": f"Error en procedimiento: {str(e)}",
                "data": [],
                "columns": [],
                "row_count": 0
            }
    
    def get_schema_info(self, table_name: str) -> Dict[str, Any]:
        """
        Obtiene información del esquema de una tabla
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Dict con información de columnas
        """
        try:
            inspector = inspect(self.engine)
            
            # Verificar si la tabla existe
            if table_name not in inspector.get_table_names():
                return {
                    "success": False,
                    "error": f"Tabla '{table_name}' no encontrada",
                    "columns": []
                }
            
            # Obtener columnas
            columns = inspector.get_columns(table_name)
            
            # Formatear información
            column_info = [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": str(col["default"]) if col["default"] else None
                }
                for col in columns
            ]
            
            logger.info(f"📋 Esquema obtenido para tabla: {table_name}")
            
            return {
                "success": True,
                "table_name": table_name,
                "columns": column_info,
                "column_count": len(column_info)
            }
        
        except Exception as e:
            logger.error(f"❌ Error al obtener esquema: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "columns": []
            }
    
    def get_table_list(self) -> Dict[str, Any]:
        """
        Obtiene lista de todas las tablas en la base de datos
        
        Returns:
            Dict con lista de tablas
        """
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            logger.info(f"📋 Obtenidas {len(tables)} tablas")
            
            return {
                "success": True,
                "tables": tables,
                "count": len(tables)
            }
        
        except Exception as e:
            logger.error(f"❌ Error al obtener tablas: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tables": []
            }
    
    def close(self):
        """Cierra las conexiones del pool"""
        if self.engine:
            self.engine.dispose()
            logger.info("🔌 Pool de conexiones cerrado")


# Singleton instance
_connector_instance = None

def get_connector() -> MCPConnector:
    """
    Obtiene instancia del conector (singleton)
    
    Returns:
        MCPConnector instance
    """
    global _connector_instance
    if _connector_instance is None:
        _connector_instance = MCPConnector()
    return _connector_instance

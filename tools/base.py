"""
🔧 Base Tool Interface
Define la interfaz común para todas las herramientas del agente
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ToolStatus(Enum):
    """Estados posibles de ejecución de una tool"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    TIMEOUT = "timeout"


@dataclass
class ToolResult:
    """
    Resultado estandarizado de ejecución de una tool
    
    Attributes:
        status: Estado de la ejecución
        data: Datos resultantes
        error: Mensaje de error si falló
        metadata: Información adicional (tiempo, rows, etc)
    """
    status: ToolStatus
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def success(self) -> bool:
        """Retorna True si la operación fue exitosa"""
        return self.status == ToolStatus.SUCCESS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para compatibilidad"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            **self.metadata
        }


class Tool(ABC):
    """
    Interfaz base para todas las herramientas del agente
    
    Implementa Template Method pattern para ejecución estandarizada
    """
    
    def __init__(self, name: str):
        self.name = name
        self._logger = None
    
    @property
    def logger(self):
        """Lazy loading del logger"""
        if self._logger is None:
            from utils.logger import get_logger
            self._logger = get_logger(self.name)
        return self._logger
    
    @abstractmethod
    def execute(self, operation: str, **params) -> ToolResult:
        """
        Ejecuta una operación de la tool
        
        Args:
            operation: Nombre de la operación a ejecutar
            **params: Parámetros de la operación
            
        Returns:
            ToolResult con el resultado de la operación
        """
        pass
    
    def validate_params(self, required_params: list, params: dict) -> Optional[str]:
        """
        Valida que los parámetros required estén presentes
        
        Args:
            required_params: Lista de parámetros requeridos
            params: Parámetros recibidos
            
        Returns:
            None si es válido, mensaje de error si falta algún parámetro
        """
        missing = [p for p in required_params if p not in params]
        if missing:
            return f"Parámetros faltantes: {', '.join(missing)}"
        return None
    
    def execute_with_logging(self, operation: str, **params) -> ToolResult:
        """
        Template Method: Ejecuta con logging automático
        
        Args:
            operation: Operación a ejecutar
            **params: Parámetros
            
        Returns:
            ToolResult
        """
        import time
        
        start_time = time.time()
        self.logger.info(f"🔧 Ejecutando {self.name}.{operation}")
        
        try:
            result = self.execute(operation, **params)
            
            execution_time = time.time() - start_time
            result.metadata["execution_time"] = execution_time
            
            if result.success:
                self.logger.info(
                    f"✅ {self.name}.{operation} completado",
                    execution_time=execution_time
                )
            else:
                self.logger.warning(
                    f"⚠️ {self.name}.{operation} falló: {result.error}"
                )
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(
                f"❌ Error en {self.name}.{operation}: {str(e)}",
                execution_time=execution_time
            )
            
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Error inesperado: {str(e)}",
                metadata={"execution_time": execution_time}
            )
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Retorna las capacidades/operaciones soportadas por esta tool
        
        Returns:
            Dict con información de capacidades
        """
        return {
            "name": self.name,
            "operations": self.get_supported_operations(),
            "description": self.__doc__
        }
    
    @abstractmethod
    def get_supported_operations(self) -> list:
        """
        Lista de operaciones soportadas por esta tool
        
        Returns:
            Lista de nombres de operaciones
        """
        pass

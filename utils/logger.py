"""
📝 EvoDataAgent Logging System
Sistema de logging estructurado con soporte para JSON y archivos rotativos
"""
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from pythonjsonlogger import jsonlogger
import config

class AgentLogger:
    """Logger personalizado para EvoDataAgent"""
    
    def __init__(self, name: str = "EvoDataAgent"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # Evitar duplicados
        if self.logger.handlers:
            return
            
        # Handler para consola
        self._setup_console_handler()
        
        # Handler para archivo
        self._setup_file_handler()
    
    def _setup_console_handler(self):
        """Configura handler para salida en consola"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        if config.LOG_FORMAT == "json":
            formatter = jsonlogger.JsonFormatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """Configura handler rotativo para archivos"""
        log_file = Path(config.LOGS_DIR) / f"{self.name}.log"
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        if config.LOG_FORMAT == "json":
            formatter = jsonlogger.JsonFormatter(
                '%(asctime)s %(name)s %(levelname)s %(pathname)s %(lineno)d %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=kwargs)
    
    def log_request(self, request_id: str, user_number: str, message: str):
        """Log incoming request"""
        self.info(
            f"📩 Nueva solicitud recibida",
            request_id=request_id,
            user_number=user_number,
            message_preview=message[:100]
        )
    
    def log_response(self, request_id: str, response_type: str, success: bool):
        """Log outgoing response"""
        status = "✅" if success else "❌"
        self.info(
            f"{status} Respuesta enviada",
            request_id=request_id,
            response_type=response_type,
            success=success
        )
    
    def log_tool_execution(self, tool_name: str, duration: float, success: bool):
        """Log tool execution"""
        status = "✅" if success else "❌"
        self.info(
            f"{status} Tool ejecutado: {tool_name}",
            tool=tool_name,
            duration_seconds=duration,
            success=success
        )
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]):
        """Log error with additional context"""
        # Create a copy to not modify original context
        ctx = context.copy()
        # Rename 'message' if it exists to avoid collision with self.error positioning
        if 'message' in ctx:
            ctx['original_message'] = ctx.pop('message')
            
        self.error(
            f"❌ Error: {str(error)}",
            error_type=type(error).__name__,
            error_message=str(error),
            **ctx
        )


# Thread-safe singleton
import threading
_logger_instance = None
_logger_lock = threading.Lock()

def get_logger(name: str = "EvoDataAgent") -> AgentLogger:
    """
    Obtiene instancia del logger (singleton thread-safe)
    
    Args:
        name: Nombre del logger
        
    Returns:
        AgentLogger instance
    """
    global _logger_instance
    
    # Double-checked locking para thread safety
    if _logger_instance is None:
        with _logger_lock:
            if _logger_instance is None:
                _logger_instance = AgentLogger(name)
    
    return _logger_instance

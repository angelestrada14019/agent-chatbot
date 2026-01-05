"""
📝 EvoDataAgent Logging System
Sistema de logging estructurado y profesional.
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any
import config

def get_logger(name: str = "EvoDataAgent") -> logging.Logger:
    """
    Obtiene un logger configurado con rotación y salida a consola.
    Limpia el código de clases logger personalizadas redundantes.
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicados si el logger ya tiene handlers
    if logger.handlers:
        return logger
        
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Formateador profesional
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Consola
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # Archivo rotativo (si el directorio existe)
    log_dir = Path(config.LOGS_DIR)
    if log_dir.exists():
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{name.lower()}.log",
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

def log_error_with_context(logger: logging.Logger, error: Exception, context: Dict[str, Any]):
    """Helper para registrar errores con contexto adicional de forma limpia"""
    msg = f"❌ Error: {str(error)} | Context: {context}"
    logger.error(msg)

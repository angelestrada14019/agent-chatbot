"""
🎯 Intent Router Service  
Enruta mensajes basado en la intención detectada usando Strategy Pattern
"""
from typing import Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
import pandas as pd

from utils.logger import get_logger
from utils.response_formatter import ResponseFormatter, MessageTemplates
from tools.mcp_connector import get_connector
from tools.visualizer import get_visualizer
from tools.excel_generator import get_excel_generator
from tools.calculator import get_calculator
import config

logger = get_logger("IntentRouter")


class IntentStrategy(Protocol):
    """Protocolo para estrategias de clasificación de intenciones"""
    
    def classify(self, message: str) -> str:
        """Clasifica la intención del mensaje"""
        ...


class KeywordBasedIntentStrategy:
    """Estrategia de clasificación basada en keywords"""
    
    INTENT_KEYWORDS = {
        "query": ["consulta", "muestra", "dame", "obtén", "cuánto", "cuántos", "lista", "ver"],
        "visualization": ["gráfico", "gráfica", "chart", "visualiza", "plotea", "grafica"],
        "export": ["excel", "exporta", "descarga", "archivo", "reporte"],
        "analysis": ["análisis", "analiza", "calcula", "promedio", "suma", "total", "estadística"],
        "calculation": ["calcula", "suma", "promedio", "mediana", "correlación", "crecimiento"]
    }
    
    def classify(self, message: str) -> str:
        """
        Clasifica la intención usando keywords
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            str: Intención detectada
        """
        message_lower = message.lower()
        
        # Contar coincidencias por tipo de intención
        scores = {intent: 0 for intent in self.INTENT_KEYWORDS}
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    scores[intent] += 1
        
        # Retornar la intención con mayor puntuación
        max_intent = max(scores, key=scores.get)
        
        # Si no hay coincidencias, asumir consulta
        if scores[max_intent] == 0:
            return "query"
        
        logger.info(f"🎯 Intención clasificada: {max_intent}", scores=scores)
        return max_intent


class IntentRouter:
    """
    Enruta mensajes a los handlers apropiados según la intención
    
    Implementa Strategy Pattern para clasificación
    """
    
    def __init__(self, classification_strategy: Optional[IntentStrategy] = None):
        """
        Inicializa el router
        
        Args:
            classification_strategy: Estrategia de clasificación (default: KeywordBased)
        """
        self.strategy = classification_strategy or KeywordBasedIntentStrategy()
        self.db_connector = get_connector()
        self.visualizer = get_visualizer()
        self.excel_generator = get_excel_generator()
        self.calculator = get_calculator()
        self.response_formatter = ResponseFormatter()
        
        logger.info("✅ IntentRouter inicializado")
    
    def route_message(self, message: str, request_id: str) -> Dict[str, Any]:
        """
        Enruta mensaje a su handler apropiado
        
        Args:
            message: Mensaje del usuario
            request_id: ID único de la solicitud
            
        Returns:
            Dict: Respuesta formateada
        """
        # Clasificar intención
        intent = self.strategy.classify(message)
        
        # Enrutar a handler
        handlers = {
            "query": self._handle_query,
            "visualization": self._handle_visualization,
            "export": self._handle_export,
            "calculation": self._handle_calculation,
            "analysis": self._handle_analysis
        }
        
        handler = handlers.get(intent, self._handle_query)
        
        try:
            return handler(message, request_id)
        except Exception as e:
            logger.error(f"❌ Error en handler de {intent}: {str(e)}")
            return self.response_formatter.format_error_response(
                error_message=f"Error procesando {intent}: {str(e)}",
                error_type=intent,
                request_id=request_id
            )
    
    def _handle_query(self, message: str, request_id: str) -> Dict[str, Any]:
        """Handler para consultas de datos"""
        logger.info("📊 Procesando consulta de datos...")
        
        # TODO: Implementar NLP->SQL conversion
        return self.response_formatter.format_error_response(
            error_message="Funcionalidad de consulta SQL desde lenguaje natural pendiente. Use ejemplos directos con tools.",
            error_type="not_implemented",
            details={"message": message},
            request_id=request_id
        )
    
    def _handle_visualization(self, message: str, request_id: str) -> Dict[str, Any]:
        """Handler para visualizaciones"""
        logger.info("📈 Procesando solicitud de visualización...")
        
        # TODO: Obtener datos relevantes
        return self.response_formatter.format_error_response(
            error_message="Use examples/example_queries.py para crear visualizaciones. Conversión automática pendiente.",
            error_type="not_implemented",
            request_id=request_id
        )
    
    def _handle_export(self, message: str, request_id: str) -> Dict[str, Any]:
        """Handler para exportación Excel"""
        logger.info("📁 Procesando exportación a Excel...")
        
        # TODO: Obtener datos relevantes
        return self.response_formatter.format_error_response(
            error_message="Use examples/example_queries.py para exportar a Excel. Conversión automática pendiente.",
            error_type="not_implemented",
            request_id=request_id
        )
    
    def _handle_calculation(self, message: str, request_id: str) -> Dict[str, Any]:
        """Handler para cálculos"""
        logger.info("🧮 Procesando solicitud de cálculo...")
        
        # TODO: Extraer operación y parámetros del mensaje
        return self.response_formatter.format_error_response(
            error_message="Use Calculator tool directamente. Ejemplo en examples/. Conversión NLP pendiente.",
            error_type="not_implemented",
            request_id=request_id
        )
    
    def _handle_analysis(self, message: str, request_id: str) -> Dict[str, Any]:
        """Handler para análisis estadístico"""
        logger.info("📊 Procesando análisis estadístico...")
        
        # TODO: Combinar DB query + Calculator
        return self.response_formatter.format_error_response(
            error_message="Use MCP Connector + Calculator directamente. Ver examples/. NLP pendiente.",
            error_type="not_implemented",
            request_id=request_id
        )
    
    def set_classification_strategy(self, strategy: IntentStrategy):
        """
        Cambia la estrategia de clasificación en runtime
        
        Args:
            strategy: Nueva estrategia a usar
        """
        self.strategy = strategy
        logger.info(f"🔄 Estrategia de clasificación cambiada: {type(strategy).__name__}")

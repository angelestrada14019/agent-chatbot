"""
🎯 Intent Router Service  
Enruta mensajes basado en la intención detectada usando Strategy Pattern
"""
from typing import Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime
import json

from utils.logger import get_logger
from utils.response_formatter import ResponseFormatter, MessageTemplates
# Usar el cliente MCP en lugar del conector directo para arquitectura desacoplada
from tools.mcp_client import get_mcp_client
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
        "query": ["consulta", "muestra", "dame", "obtén", "cuánto", "cuántos", "lista", "ver", "ventas", "productos", "clientes"],
        "visualization": ["gráfico", "gráfica", "chart", "visualiza", "plotea", "grafica"],
        "export": ["excel", "exporta", "descarga", "archivo", "reporte"],
        # Analysis combina todo: query + graficas + excel/analisis
        "analysis": ["análisis", "analiza", "tendencia", "reporte de ventas", "trimestre", "balance"],
        "calculation": ["calcula", "suma", "promedio", "mediana", "correlación", "crecimiento", "sqrt", "+", "-", "*", "/"]
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
        
        # Prioridad a Analysis si menciona reporte complejo
        if "ventas" in message_lower and ("grafica" in message_lower or "excel" in message_lower or "tendencia" in message_lower):
            return "analysis"
        
        # Contar coincidencias por tipo de intención
        scores = {intent: 0 for intent in self.INTENT_KEYWORDS}
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    scores[intent] += 1
        
        # Retornar la intención con mayor puntuación
        max_intent = max(scores, key=scores.get)
        
        # Si no hay coincidencias, asumir consulta genérica
        if scores[max_intent] == 0:
            return "query"
        
        logger.info(f"🎯 Intención clasificada: {max_intent}", scores=scores)
        return max_intent


class IntentRouter:
    """
    Enruta mensajes a los handlers apropiados según la intención
    
    Implementa Strategy Pattern para clasificación
    """
    
    def __init__(self, message_processor: Any, classification_strategy: Optional[IntentStrategy] = None):
        """
        Inicializa el router
        
        Args:
            message_processor: Instancia de MessageProcessor para tareas de IA
            classification_strategy: Estrategia de clasificación (default: KeywordBased)
        """
        self.message_processor = message_processor
        self.strategy = classification_strategy or KeywordBasedIntentStrategy()
        # Usar adapter que usa MCPClient por debajo
        self.db_connector = get_mcp_client() 
        self.visualizer = get_visualizer()
        self.excel_generator = get_excel_generator()
        self.calculator = get_calculator()
        self.response_formatter = ResponseFormatter()
        
        logger.info("✅ IntentRouter inicializado con soporte de IA")
    
    async def route_message(self, message: str, request_id: str) -> Dict[str, Any]:
        """
        Enruta mensaje a su handler apropiado (Async)
        
        Args:
            message: Mensaje del usuario
            request_id: ID único de la solicitud
            
        Returns:
            Dict: Respuesta formateada
        """
        # Clasificar intención usando IA si es posible, de lo contrario keywords
        if hasattr(self.message_processor, 'get_intent_classification'):
            intent = await self.message_processor.get_intent_classification(message)
        else:
            intent = self.strategy.classify(message)
            
        logger.info(f"🎯 Intención final: {intent}")
        
        # Enrutar a handler
        handlers = {
            "query": self._handle_query,
            "visualization": self._handle_visualization,
            "export": self._handle_export,
            "calculation": self._handle_calculation,
            "analysis": self._handle_analysis,
            "chat": self._handle_chat
        }
        
        handler = handlers.get(intent, self._handle_chat)
        
        try:
            return await handler(message, request_id)
        except Exception as e:
            logger.error(f"❌ Error en handler de {intent}: {str(e)}")
            return self.response_formatter.format_error_response(
                error_message=f"Error procesando {intent}: {str(e)}",
                error_type=intent,
                request_id=request_id
            )

    async def _handle_chat(self, message: str, request_id: str) -> Dict[str, Any]:
        """Handler para conversación general usando IA (Async)"""
        logger.info("💬 Procesando respuesta de chat con IA...")
        
        response_text = await self.message_processor.get_chat_completion(message)
        
        return {
            "success": True,
            "response": response_text,
            "response_type": "text",
            "request_id": request_id
        }
    
    async def _handle_query(self, message: str, request_id: str) -> Dict[str, Any]:
        """Handler para consultas de datos simples (Async)"""
        logger.info("📊 Procesando consulta de datos...")
        
        # Mapeo simple NLP -> SQL (para demo)
        if "ventas" in message.lower():
            sql = "SELECT * FROM ventas ORDER BY fecha DESC LIMIT 10"
            result = await self.db_connector.execute_query(sql)
            
            if result["success"]:
                # Formatear tabla simple
                df = pd.DataFrame(result["data"])
                table_str = df.to_markdown(index=False)
                return {
                    "success": True,
                    "response": f"Aquí están las últimas ventas:\n\n{table_str}",
                    "response_type": "text",
                    "request_id": request_id
                }
        
        elif "productos" in message.lower():
            sql = "SELECT * FROM productos LIMIT 10"
            result = await self.db_connector.execute_query(sql)
             
            if result["success"]:
                 df = pd.DataFrame(result["data"])
                 table_str = df.to_markdown(index=False)
                 return {
                    "success": True,
                    "response": f"Catálogo de productos:\n\n{table_str}",
                    "response_type": "text",
                    "request_id": request_id
                }
                 
        return self.response_formatter.format_error_response(
            error_message="No entendí qué datos quieres. Prueba 'muéstrame las ventas' o 'lista productos'.",
            error_type="not_understanding",
            request_id=request_id
        )
    
    async def _handle_visualization(self, message: str, request_id: str) -> Dict[str, Any]:
        """Handler para visualizaciones"""
        return await self._handle_analysis(message, request_id)  # Reutilizar lógica de análisis
    
    async def _handle_export(self, message: str, request_id: str) -> Dict[str, Any]:
        """Handler para exportación Excel"""
        return await self._handle_analysis(message, request_id)
    
    async def _handle_calculation(self, message: str, request_id: str) -> Dict[str, Any]:
        """Handler para cálculos"""
        logger.info("🧮 Procesando solicitud de cálculo...")
        
        try:
            # Calculator es síncrono (tool local pura), no requiere await
            result = self.calculator.calculate(message)
            return {
                "success": True,
                "response": f"El resultado es: {result}",
                "response_type": "text",
                "request_id": request_id
            }
        except Exception as e:
            return self.response_formatter.format_error_response(
                error_message=f"No pude calcular eso: {str(e)}",
                error_type="calculation_error",
                request_id=request_id
            )
    
    async def _handle_analysis(self, message: str, request_id: str) -> Dict[str, Any]:
        """
        Handler completo para análisis (Query -> Chart -> Excel) (Async)
        Workflow solicitado por usuario: "ventas trimestre + grafica tendencia + excel"
        """
        logger.info("📊 Procesando flujo completo de análisis (MCP -> Viz -> Excel)...")
        
        # 1. Obtención de Datos (Vía MCP)
        # -----------------------------
        sql = "SELECT fecha, producto, cantidad, precio, (cantidad * precio) as total FROM ventas WHERE fecha >= '2024-01-01' ORDER BY fecha ASC"
        
        result = await self.db_connector.execute_query(sql)
        
        if not result["success"]:
            return self.response_formatter.format_error_response(
                error_message=f"Error consultando datos: {result.get('error')}",
                error_type="db_error",
                request_id=request_id
            )
            
        data = result["data"]
        df = pd.DataFrame(data)
        
        if df.empty:
            return {
                "success": True,
                "response": "No encontré ventas en este periodo.",
                "response_type": "text",
                "request_id": request_id
            }
            
        # 2. Generación de Gráficos (Visualizer)
        # ------------------------------------
        files = []
        
        # Gráfico de Tendencia (Línea de tiempo)
        # Visualizer es síncrono (CPU bound, se podría envolver en loop.run_in_executor pero por ahora ok)
        chart_result = self.visualizer.create_line_chart(
            data=df,
            x_column="fecha",
            y_columns=["total"],
            title="Tendencia de Ventas (Trimestre Actual)"
        )
        
        if chart_result["success"]:
            files.append(chart_result["file_path"])
            
        # 3. Generación de Excel (ExcelGenerator)
        # -------------------------------------
        # ExcelGenerator es síncrono (Disk/CPU bound)
        excel_result = self.excel_generator.create_excel_from_data(
            data=df,
            filename=f"reporte_ventas_{datetime.now().strftime('%Y%m%d')}",
            sheet_name="Ventas Trimestre"
        )
        
        if excel_result["success"]:
            # Insertar el gráfico en el Excel también
            if chart_result["success"]:
                self.excel_generator.add_chart_to_excel(
                    file_path=excel_result["file_path"],
                    sheet_name="Ventas Trimestre",
                    chart_type="line",
                    data_range=f"E2:E{len(df)+1}",
                    chart_title="Tendencia Ventas",
                    position="G2"
                )
            files.append(excel_result["file_path"])
            
        # 4. Respuesta Final
        # ----------------
        return {
            "success": True,
            "response": "✅ Aquí tienes el análisis solicitado:\n\n1. 📊 Gráfico de tendencia de ventas\n2. 📁 Reporte Excel detallado",
            "response_type": "files",
            "files": files,
            "request_id": request_id
        }
    
    def set_classification_strategy(self, strategy: IntentStrategy):
        """
        Cambia la estrategia de clasificación en runtime
        
        Args:
            strategy: Nueva estrategia a usar
        """
        self.strategy = strategy
        logger.info(f"🔄 Estrategia de clasificación cambiada: {type(strategy).__name__}")

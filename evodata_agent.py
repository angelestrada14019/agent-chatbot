"""
🤖 EvoDataAgent - Main Orchestrator
Agente inteligente de análisis y automatización integrado con EvolutionAPI
"""
from typing import Dict, Any, Optional, List
import requests
import pandas as pd
import uuid
from datetime import datetime
from openai import OpenAI
import config
from utils.logger import get_logger
from utils.response_formatter import ResponseFormatter
from tools.mcp_connector import get_connector
from tools.visualizer import get_visualizer
from tools.excel_generator import get_excel_generator

logger = get_logger("EvoDataAgent")


class IntentClassifier:
    """Clasificador de intenciones del usuario"""
    
    INTENT_KEYWORDS = {
        "query": ["consulta", "muestra", "dame", "obtén", "cuánto", "cuántos", "lista", "ver"],
        "visualization": ["gráfico", "gráfica", "chart", "visualiza", "plotea", "grafica"],
        "export": ["excel", "exporta", "descarga", "archivo", "reporte"],
        "analysis": ["análisis", "analiza", "calcula", "promedio", "suma", "total", "estadística"]
    }
    
    @staticmethod
    def classify(message: str) -> str:
        """
        Clasifica la intención del mensaje del usuario
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            str: Tipo de intención (query, visualization, export, analysis)
        """
        message_lower = message.lower()
        
        # Contar coincidencias por tipo de intención
        scores = {intent: 0 for intent in IntentClassifier.INTENT_KEYWORDS}
        
        for intent, keywords in IntentClassifier.INTENT_KEYWORDS.items():
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


class EvoDataAgent:
    """Agente principal de análisis y automatización"""
    
    def __init__(self):
        """Inicializa el agente y sus herramientas"""
        self.db_connector = get_connector()
        self.visualizer = get_visualizer()
        self.excel_generator = get_excel_generator()
        self.response_formatter = ResponseFormatter()
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        logger.info(f"🤖 {config.AGENT_NAME} v{config.AGENT_VERSION} inicializado")
    
    def process_voice_message(self, audio_file_path: str) -> str:
        """
        Convierte audio a texto usando OpenAI Whisper API
        
        Args:
            audio_file_path: Path del archivo de audio
            
        Returns:
            str: Texto transcrito
        """
        try:
            logger.info("🎤 Procesando mensaje de voz...")
            
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model=config.WHISPER_MODEL,
                    file=audio_file,
                    language=config.WHISPER_LANGUAGE
                )
            
            text = transcript.text
            logger.info(f"✅ Audio transcrito: {text[:100]}...")
            return text
        
        except Exception as e:
            logger.error(f"❌ Error al transcribir audio: {str(e)}")
            raise
    
    def handle_query_intent(
        self,
        message: str,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Maneja intención de consulta de datos
        
        Args:
            message: Mensaje del usuario
            request_id: ID de la solicitud
            
        Returns:
            Dict: Respuesta formateada
        """
        logger.info("📊 Procesando consulta de datos...")
        
        # Aquí deberías tener lógica para convertir lenguaje natural a SQL
        # Por ahora, un ejemplo simple
        sql_query = "SELECT * FROM ventas LIMIT 10"  # Placeholder
        
        # Ejecutar consulta
        result = self.db_connector.execute_query(sql_query)
        
        if not result["success"]:
            return self.response_formatter.format_error_response(
                error_message=result["error"],
                error_type="query",
                request_id=request_id
            )
        
        # Formatear resumen
        summary = f"📊 Encontré {result['row_count']} registros.\n\n"
        
        if result["row_count"] > 0:
            # Mostrar primeras filas como texto
            df = pd.DataFrame(result["data"])
            summary += f"```\n{df.head(5).to_string()}\n```"
        
        return self.response_formatter.format_data_response(
            data=result,
            summary=summary,
            request_id=request_id
        )
    
    def handle_visualization_intent(
        self,
        message: str,
        data: pd.DataFrame,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Maneja intención de crear visualización
        
        Args:
            message: Mensaje del usuario
            data: DataFrame con datos a visualizar
            request_id: ID de la solicitud
            
        Returns:
            Dict: Respuesta formateada con gráfico
        """
        logger.info("📈 Generando visualización...")
        
        # Detectar tipo de gráfico sugerido
        chart_type = self.visualizer.auto_suggest_chart_type(data)
        
        # Obtener columnas
        columns = data.columns.tolist()
        
        # Crear gráfico (ejemplo con primeras 2 columnas)
        if len(columns) >= 2:
            result = self.visualizer.create_bar_chart(
                data=data,
                x_column=columns[0],
                y_column=columns[1],
                title="Análisis de Datos"
            )
        else:
            return self.response_formatter.format_error_response(
                error_message="Datos insuficientes para crear gráfico",
                error_type="visualization",
                request_id=request_id
            )
        
        if not result["success"]:
            return self.response_formatter.format_error_response(
                error_message=result["error"],
                error_type="visualization",
                request_id=request_id
            )
        
        # Convertir a base64 para adjunto
        chart_base64 = self.visualizer.export_as_base64(result["file_path"])
        
        # Generar URL pública (si se configura un servidor)
        chart_url = None
        if config.FILE_DELIVERY_METHOD in ["both", "url"]:
            filename = result["file_path"].split("\\")[-1]
            chart_url = f"{config.FILE_SERVER_URL}/{filename}"
        
        description = f"📊 Aquí está tu gráfico de {chart_type} con {len(data)} registros."
        
        return self.response_formatter.format_visualization_response(
            chart_path=result["file_path"],
            chart_url=chart_url,
            chart_base64=chart_base64 if config.FILE_DELIVERY_METHOD in ["both", "attachment"] else None,
            description=description,
            data_summary={"row_count": len(data), "chart_type": chart_type},
            request_id=request_id
        )
    
    def handle_export_intent(
        self,
        message: str,
        data: pd.DataFrame,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Maneja intención de exportar a Excel
        
        Args:
            message: Mensaje del usuario
            data: DataFrame con datos a exportar
            request_id: ID de la solicitud
            
        Returns:
            Dict: Respuesta formateada con archivo Excel
        """
        logger.info("📁 Generando archivo Excel...")
        
        # Crear Excel
        result = self.excel_generator.create_excel_from_data(
            data=data,
            filename=f"export_{request_id}",
            apply_styling=True
        )
        
        if not result["success"]:
            return self.response_formatter.format_error_response(
                error_message=result["error"],
                error_type="excel",
                request_id=request_id
            )
        
        # Convertir a base64 para adjunto
        file_base64 = self.excel_generator.export_as_base64(result["file_path"])
        
        # Generar URL pública
        file_url = None
        if config.FILE_DELIVERY_METHOD in ["both", "url"]:
            file_url = f"{config.FILE_SERVER_URL}/{result['filename']}"
        
        description = "Tu archivo Excel está listo"
        
        return self.response_formatter.format_excel_response(
            file_path=result["file_path"],
            file_url=file_url,
            file_base64=file_base64 if config.FILE_DELIVERY_METHOD in ["both", "attachment"] else None,
            description=description,
            row_count=result["row_count"],
            sheet_count=result["sheet_count"],
            request_id=request_id
        )
    
    def process_message(
        self,
        message: str,
        is_voice: bool = False,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa mensaje del usuario (texto o voz)
        
        Args:
            message: Mensaje de texto del usuario
            is_voice: Si True, es mensaje de voz
            audio_path: Path del audio (si is_voice=True)
            
        Returns:
            Dict: Respuesta formateada
        """
        # Generar ID único para esta solicitud
        request_id = str(uuid.uuid4())
        
        logger.log_request(request_id, "user", message)
        
        try:
            # Si es voz, transcribir primero
            if is_voice and audio_path:
                message = self.process_voice_message(audio_path)
            
            # Clasificar intención
            intent = IntentClassifier.classify(message)
            
            # Obtener datos (ejemplo simple - deberías mejorar esto)
            # En producción, aquí convertirías el mensaje a SQL
            sql_query = "SELECT * FROM ventas LIMIT 100"  # Placeholder
            query_result = self.db_connector.execute_query(sql_query)
            
            if not query_result["success"]:
                return self.response_formatter.format_error_response(
                    error_message=query_result["error"],
                    error_type="database",
                    request_id=request_id
                )
            
            data = pd.DataFrame(query_result["data"])
            
            # Procesar según intención
            if intent == "visualization":
                response = self.handle_visualization_intent(message, data, request_id)
            elif intent == "export":
                response = self.handle_export_intent(message, data, request_id)
            elif intent in ["query", "analysis"]:
                response = self.handle_query_intent(message, request_id)
            else:
                response = self.handle_query_intent(message, request_id)
            
            logger.log_response(request_id, response["response_type"], response["success"])
            return response
        
        except Exception as e:
            logger.log_error_with_context(e, {"request_id": request_id, "message": message})
            return self.response_formatter.format_error_response(
                error_message=str(e),
                error_type="general",
                request_id=request_id
            )
    
    def send_whatsapp_message(
        self,
        phone_number: str,
        response: Dict[str, Any]
    ) -> bool:
        """
        Envía mensaje por WhatsApp vía EvolutionAPI
        
        Args:
            phone_number: Número de destino (formato: 573124488445@c.us)
            response: Respuesta formateada del agente
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            url = f"{config.EVOLUTION_URL}/message/sendText/{config.EVOLUTION_INSTANCE}"
            headers = {
                "Content-Type": "application/json",
                "apikey": config.EVOLUTION_API_KEY
            }
            
            # Enviar mensaje de texto
            payload = {
                "number": phone_number,
                "options": {"delay": 1000, "presence": "composing"},
                "text": response["content"]
            }
            
            resp = requests.post(url, json=payload, headers=headers)
            
            if resp.status_code not in (200, 201):
                logger.error(f"❌ Error al enviar mensaje: {resp.status_code}")
                return False
            
            # Si hay adjuntos, enviarlos
            if response.get("attachments"):
                for attachment in response["attachments"]:
                    self._send_attachment(phone_number, attachment)
            
            logger.info(f"✅ Mensaje enviado a {phone_number}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error al enviar WhatsApp: {str(e)}")
            return False
    
    def _send_attachment(self, phone_number: str, attachment: Dict[str, Any]) -> bool:
        """
        Envía archivo adjunto por WhatsApp
        
        Args:
            phone_number: Número de destino
            attachment: Dict con info del adjunto
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Determinar endpoint según tipo
            if attachment["type"] == "image":
                endpoint = "sendBase64"
            elif attachment["type"] == "document":
                endpoint = "sendBase64"
            else:
                return False
            
            url = f"{config.EVOLUTION_URL}/message/{endpoint}/{config.EVOLUTION_INSTANCE}"
            headers = {
                "Content-Type": "application/json",
                "apikey": config.EVOLUTION_API_KEY
            }
            
            payload = {
                "number": phone_number,
                "options": {"delay": 1000},
                "base64": attachment["data"],
                "fileName": attachment["filename"]
            }
            
            resp = requests.post(url, json=payload, headers=headers)
            
            if resp.status_code not in (200, 201):
                logger.error(f"❌ Error al enviar adjunto: {resp.status_code}")
                return False
            
            logger.info(f"✅ Adjunto enviado: {attachment['filename']}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error al enviar adjunto: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    # Inicializar agente
    agent = EvoDataAgent()
    
    # Procesar mensaje de ejemplo
    response = agent.process_message("Muéstrame las ventas de este mes")
    
    # Mostrar respuesta
    print(ResponseFormatter.to_json(response, pretty=True))

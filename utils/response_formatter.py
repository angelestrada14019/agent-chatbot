"""
📤 EvoDataAgent Response Formatter
Formatea respuestas de manera estandarizada para EvolutionAPI
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import config

class ResponseFormatter:
    """Formateador de respuestas estandarizado"""
    
    @staticmethod
    def format_success_response(
        response_type: str,
        content: str,
        data: Optional[Dict] = None,
        attachments: Optional[List[Dict]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formatea respuesta exitosa
        
        Args:
            response_type: Tipo de respuesta (text, graph, excel, etc.)
            content: Contenido textual de la respuesta
            data: Datos adicionales (opcional)
            attachments: Lista de archivos adjuntos (opcional)
            request_id: ID de la solicitud (opcional)
            
        Returns:
            Dict con respuesta formateada
        """
        return {
            "success": True,
            "response_type": response_type,
            "content": content,
            "data": data or {},
            "attachments": attachments or [],
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id,
                "agent_name": config.AGENT_NAME,
                "agent_version": config.AGENT_VERSION
            }
        }
    
    @staticmethod
    def format_error_response(
        error_message: str,
        error_type: str = "general",
        details: Optional[Dict] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formatea respuesta de error
        
        Args:
            error_message: Mensaje de error
            error_type: Tipo de error
            details: Detalles adicionales (opcional)
            request_id: ID de la solicitud (opcional)
            
        Returns:
            Dict con respuesta de error
        """
        # Mensajes de error amigables en español
        friendly_messages = {
            "database": "❌ No pude conectarme a la base de datos. Por favor intenta más tarde.",
            "query": "❌ Hubo un problema al ejecutar la consulta. Verifica los parámetros.",
            "visualization": "❌ No pude generar el gráfico. Verifica que los datos sean correctos.",
            "excel": "❌ Error al generar el archivo Excel. Intenta de nuevo.",
            "file_delivery": "❌ No pude enviar el archivo. Intenta más tarde.",
            "voice": "❌ No pude procesar el audio. Envía un mensaje de texto o intenta de nuevo.",
            "general": f"❌ Ocurrió un error: {error_message}"
        }
        
        user_message = friendly_messages.get(error_type, friendly_messages["general"])
        
        return {
            "success": False,
            "response_type": "error",
            "content": user_message,
            "error": {
                "type": error_type,
                "message": error_message,
                "details": details or {}
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id,
                "agent_name": config.AGENT_NAME
            }
        }
    
    @staticmethod
    def format_data_response(
        data: Dict,
        summary: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formatea respuesta con datos de consulta
        
        Args:
            data: Datos obtenidos de la consulta
            summary: Resumen descriptivo
            request_id: ID de la solicitud
            
        Returns:
            Dict con respuesta formateada
        """
        return ResponseFormatter.format_success_response(
            response_type="data",
            content=summary,
            data=data,
            request_id=request_id
        )
    
    @staticmethod
    def format_visualization_response(
        chart_path: str,
        chart_url: Optional[str],
        chart_base64: Optional[str],
        description: str,
        data_summary: Dict,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formatea respuesta con visualización
        
        Args:
            chart_path: Path local del gráfico
            chart_url: URL pública del gráfico (si aplica)
            chart_base64: Gráfico en base64 (para adjuntos)
            description: Descripción del gráfico
            data_summary: Resumen de los datos visualizados
            request_id: ID de la solicitud
            
        Returns:
            Dict con respuesta formateada
        """
        attachments = []
        
        # Agregar como adjunto si hay base64
        if chart_base64:
            attachments.append({
                "type": "image",
                "format": "png",
                "data": chart_base64,
                "filename": chart_path.split("/")[-1] if "/" in chart_path else chart_path.split("\\")[-1]
            })
        
        # Agregar URL si está disponible
        if chart_url:
            description += f"\n\n🔗 También puedes verlo aquí: {chart_url}"
        
        return ResponseFormatter.format_success_response(
            response_type="graph",
            content=description,
            data=data_summary,
            attachments=attachments,
            request_id=request_id
        )
    
    @staticmethod
    def format_excel_response(
        file_path: str,
        file_url: Optional[str],
        file_base64: Optional[str],
        description: str,
        row_count: int,
        sheet_count: int,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formatea respuesta con archivo Excel
        
        Args:
            file_path: Path local del archivo
            file_url: URL pública del archivo (si aplica)
            file_base64: Archivo en base64 (para adjuntos)
            description: Descripción del archivo
            row_count: Número de filas
            sheet_count: Número de hojas
            request_id: ID de la solicitud
            
        Returns:
            Dict con respuesta formateada
        """
        attachments = []
        
        # Agregar como adjunto si hay base64
        if file_base64:
            filename = file_path.split("/")[-1] if "/" in file_path else file_path.split("\\")[-1]
            attachments.append({
                "type": "document",
                "format": "xlsx",
                "data": file_base64,
                "filename": filename
            })
        
        # Construir mensaje
        message = f"📊 {description}\n\n"
        message += f"📄 Hojas: {sheet_count}\n"
        message += f"📝 Registros: {row_count}\n"
        
        # Agregar URL si está disponible
        if file_url:
            message += f"\n🔗 Descargar aquí: {file_url}"
        
        return ResponseFormatter.format_success_response(
            response_type="excel",
            content=message,
            data={
                "row_count": row_count,
                "sheet_count": sheet_count,
                "file_path": file_path
            },
            attachments=attachments,
            request_id=request_id
        )
    
    @staticmethod
    def create_whatsapp_message(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convierte respuesta formateada a mensaje de WhatsApp para EvolutionAPI
        
        Args:
            response: Respuesta formateada
            
        Returns:
            Dict compatible con EvolutionAPI
        """
        # Mensaje de texto base
        message = {
            "text": response["content"]
        }
        
        return message
    
    @staticmethod
    def to_json(response: Dict[str, Any], pretty: bool = False) -> str:
        """
        Convierte respuesta a JSON string
        
        Args:
            response: Respuesta formateada
            pretty: Si True, formatea con indentación
            
        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(response, indent=2, ensure_ascii=False)
        return json.dumps(response, ensure_ascii=False)

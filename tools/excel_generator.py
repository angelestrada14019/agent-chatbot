"""
📁 Excel Generator Tool - Integración con OpenAI Agents SDK
Generador de reportes profesionales en Excel con Pydantic.
"""
import pandas as pd
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from agents import function_tool
import config

logger = logging.getLogger("ExcelTool")

class ExcelResult(BaseModel):
    """Resultado estructurado de la generación de un Excel"""
    success: bool = Field(..., description="Indica si el reporte se generó con éxito")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    file_path: Optional[str] = Field(None, description="Ruta local al archivo Excel generado")
    filename: str = Field(..., description="Nombre del archivo generado")

class ExcelManager:
    """Gestiona la creación de archivos Excel usando Storage Provider"""
    def __init__(self):
        from services.storage_provider import get_storage_provider
        self.storage = get_storage_provider()

    def generate(self, data: pd.DataFrame, filename: str) -> str:
        """
        Genera archivo Excel usando Storage Provider.
        
        Args:
            data: DataFrame con los datos
            filename: Nombre del archivo
        
        Returns:
            Path del archivo generado
        """
        from io import BytesIO
        
        if not filename.endswith(".xlsx"):
            filename += ".xlsx"
        
        # Generar Excel en memoria
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            data.to_excel(writer, index=False, sheet_name="Reporte")
            
            # Ajustar anchos de columnas
            workbook = writer.book
            worksheet = writer.sheets["Reporte"]
            for idx, col in enumerate(data.columns):
                max_len = max(data[col].astype(str).map(len).max(), len(col)) + 2
                col_letter = chr(65 + idx) if idx < 26 else f"A{chr(65 + idx - 26)}"
                worksheet.column_dimensions[col_letter].width = min(max_len, 50)

        buf.seek(0)
        excel_data = buf.read()
        
        # Usar storage provider para guardar
        path = self.storage.save(excel_data, filename)
        logger.info(f"✅ Excel generado: {path}")
        return path

excel_manager = ExcelManager()

@function_tool
def generate_excel_report(data_json: str, filename: str) -> ExcelResult:
    """
    Crea un archivo Excel profesional a partir de una lista de datos JSON.
    
    Args:
        data_json: Datos en formato JSON (lista de objetos).
        filename: Nombre sugerido para el archivo (ej: 'ventas_reporte.xlsx').
    """
    try:
        data = json.loads(data_json)
        df = pd.DataFrame(data)
        
        if df.empty:
            return ExcelResult(success=False, message="No hay datos para generar el Excel.", filename=filename)

        path = excel_manager.generate(df, filename)
        
        return ExcelResult(
            success=True,
            message=f"Archivo Excel '{filename}' generado correctamente.",
            file_path=path,
            filename=filename
        )

    except Exception as e:
        logger.error(f"❌ Error generando Excel: {str(e)}")
        return ExcelResult(success=False, message=f"Error: {str(e)}", filename=filename)

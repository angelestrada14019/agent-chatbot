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
    """Gestiona la creación de archivos Excel"""
    def __init__(self):
        self.output_dir = Path(config.EXPORTS_DIR)

    def generate(self, data: pd.DataFrame, filename: str) -> str:
        if not filename.endswith(".xlsx"):
            filename += ".xlsx"
        
        path = self.output_dir / filename
        
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            data.to_excel(writer, index=False, sheet_name="Reporte")
            
            # Ajustar anchos
            workbook = writer.book
            worksheet = writer.sheets["Reporte"]
            for idx, col in enumerate(data.columns):
                max_len = max(data[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_len, 50)

        logger.info(f"✅ Excel generado en: {path}")
        return str(path)

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

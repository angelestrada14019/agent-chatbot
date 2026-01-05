"""
📁 Excel Generator Tool - Integración con OpenAI Agents SDK
Generahor de reportes profesionales en Excel.
"""
import pandas as pd
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from agents import function_tool
import config

logger = logging.getLogger("ExcelTool")

class ExcelManager:
    """Gestiona la creación de archivos Excel"""
    def __init__(self):
        self.output_dir = Path(config.EXPORTS_DIR)
        self.output_dir.mkdir(exist_ok=True)

    def generate(self, data: pd.DataFrame, filename: str) -> str:
        if not filename.endswith(".xlsx"):
            filename += ".xlsx"
        
        path = self.output_dir / filename
        
        # Guardar con estilo profesional básico usando pandas
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            data.to_excel(writer, index=False, sheet_name="Reporte")
            
            # Ajustar anchos de columna (opcional pero recomendado para Clean Code)
            workbook = writer.book
            worksheet = writer.sheets["Reporte"]
            for idx, col in enumerate(data.columns):
                max_len = max(data[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_len, 50)

        logger.info(f"✅ Excel generado en: {path}")
        return str(path)

excel_manager = ExcelManager()

@function_tool
def generate_excel_report(data_json: str, filename: str) -> str:
    """
    Crea un archivo Excel profesional a partir de una lista de datos JSON.
    
    Args:
        data_json: Datos en formato JSON (lista de objetos).
        filename: Nombre sugerido para el archivo (ej: 'ventas_enero.xlsx').
    """
    try:
        data = json.loads(data_json)
        df = pd.DataFrame(data)
        
        if df.empty:
            return "No hay datos para generar el Excel."

        path = excel_manager.generate(df, filename)
        
        return json.dumps({
            "success": True,
            "message": f"Archivo Excel '{filename}' generado correctamente.",
            "file_path": path
        })

    except Exception as e:
        logger.error(f"❌ Error generando Excel: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})

def get_excel_generator():
    return excel_manager

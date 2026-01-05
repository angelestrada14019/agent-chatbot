"""
📊 Visualizer Tool - Integración con OpenAI Agents SDK
Generador de visualizaciones profesionales usando matplotlib y seaborn.
Retorna resultados estructurados con Pydantic.
"""
import pandas as pd
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from agents import function_tool
import config

logger = logging.getLogger("VisualizerTool")

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')

class ChartResult(BaseModel):
    """Resultado estructurado de la generación de un gráfico"""
    success: bool = Field(..., description="Indica si el gráfico se generó con éxito")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    file_path: Optional[str] = Field(None, description="Ruta local al archivo de imagen generado")
    chart_type: str = Field(..., description="Tipo de gráfico generado")

class VisualizerManager:
    """Gestiona la generación de archivos de imagen"""
    def __init__(self):
        self.output_dir = Path(config.EXPORTS_DIR)
        # Directorio asegurado en el startup del servidor

    def save_fig(self, fig, prefix: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.png"
        path = self.output_dir / filename
        fig.savefig(path, dpi=config.PLOT_DPI, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"✅ Gráfico guardado en: {path}")
        return str(path)

viz_manager = VisualizerManager()

@function_tool
def generate_chart(
    data_json: str, 
    title: str, 
    chart_type: str = "bar", 
    x_axis: Optional[str] = None, 
    y_axis: Optional[str] = None
) -> ChartResult:
    """
    Genera un gráfico profesional a partir de datos en formato JSON.
    
    Args:
        data_json: Lista de objetos JSON con los datos.
        title: Título descriptivo del gráfico.
        chart_type: Tipo de gráfico ('bar', 'line', 'pie', 'scatter').
        x_axis: Nombre de la columna para el eje X.
        y_axis: Nombre de la columna para el eje Y.
    """
    try:
        data = json.loads(data_json)
        df = pd.DataFrame(data)
        
        if df.empty:
            return ChartResult(success=False, message="No hay datos para graficar.", chart_type=chart_type)

        # Auto-selección de ejes si no se proveen
        if not x_axis: x_axis = df.columns[0]
        if not y_axis and len(df.columns) > 1: y_axis = df.columns[1]

        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == "bar":
            sns.barplot(data=df, x=x_axis, y=y_axis, ax=ax, palette="viridis")
        elif chart_type == "line":
            sns.lineplot(data=df, x=x_axis, y=y_axis, ax=ax, marker='o')
        elif chart_type == "pie":
            ax.pie(df[y_axis], labels=df[x_axis], autopct='%1.1f%%', startangle=90)
            ax.set_ylabel('')
        elif chart_type == "scatter":
            sns.scatterplot(data=df, x=x_axis, y=y_axis, ax=ax)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        path = viz_manager.save_fig(fig, f"chart_{chart_type}")
        
        return ChartResult(
            success=True,
            message=f"Gráfica '{title}' generada correctamente.",
            file_path=path,
            chart_type=chart_type
        )

    except Exception as e:
        logger.error(f"❌ Error generando gráfica: {str(e)}")
        return ChartResult(success=False, message=f"Error: {str(e)}", chart_type=chart_type)

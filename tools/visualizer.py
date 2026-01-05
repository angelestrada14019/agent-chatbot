"""
📊 Visualizer Tool - Integración con OpenAI Agents SDK
Generador de visualizaciones profesionales usando matplotlib y plotly.
"""
import pandas as pd
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from agents import function_tool
import config

logger = logging.getLogger("VisualizerTool")

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')

class VisualizerManager:
    """Gestiona la generación de archivos de imagen"""
    def __init__(self):
        self.output_dir = Path(config.EXPORTS_DIR)
        self.output_dir.mkdir(exist_ok=True)

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
) -> str:
    """
    Genera un gráfico profesional a partir de datos en formato JSON.
    
    Args:
        data_json: Lista de objetos JSON con los datos.
        title: Título descriptivo del gráfico.
        chart_type: Tipo de gráfico ('bar', 'line', 'pie', 'scatter').
        x_axis: Nombre de la columna para el eje X (opcional, se usará la primera si no se provee).
        y_axis: Nombre de la columna para el eje Y (opcional, se usará la segunda si no se provee).
    """
    try:
        data = json.loads(data_json)
        df = pd.DataFrame(data)
        
        if df.empty:
            return "No hay datos para graficar."

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
        
        return json.dumps({
            "success": True,
            "message": f"Gráfica '{title}' generada correctamente.",
            "file_path": path
        })

    except Exception as e:
        logger.error(f"❌ Error generando gráfica: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})

def get_visualizer():
    return viz_manager

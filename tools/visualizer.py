"""
📊 Visualizer Tool
Generador de visualizaciones con matplotlib, plotly y seaborn
"""
from typing import Dict, Any, List, Optional
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns
import pandas as pd
import numpy as np
import base64
from io import BytesIO
from pathlib import Path
from datetime import datetime
import config
from utils.logger import get_logger

logger = get_logger("Visualizer")

# Configurar estilo de matplotlib
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette(config.COLOR_PALETTE_PRIMARY)


class Visualizer:
    """Generador de visualizaciones profesionales"""
    
    def __init__(self):
        """Inicializa el visualizador"""
        self.output_dir = Path(config.EXPORTS_DIR)
        self.output_dir.mkdir(exist_ok=True)
    
    def auto_suggest_chart_type(self, data: pd.DataFrame) -> str:
        """
        Sugiere el tipo de gráfico más apropiado según los datos
        
        Args:
            data: DataFrame con los datos
            
        Returns:
            str: Tipo de gráfico sugerido
        """
        num_cols = data.select_dtypes(include=[np.number]).columns
        cat_cols = data.select_dtypes(include=['object', 'category']).columns
        
        # Si hay 1 categórica y 1 numérica -> barras
        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            return "bar"
        
        # Si hay 2 numéricas -> dispersión
        if len(num_cols) >= 2:
            return "scatter"
        
        # Si solo hay 1 numérica -> histograma
        if len(num_cols) == 1:
            return "histogram"
        
        return "table"
    
    def create_bar_chart(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str = "Gráfico de Barras",
        horizontal: bool = False,
        stacked: bool = False,
        color_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea gráfico de barras con matplotlib
        
        Args:
            data: DataFrame con los datos
            x_column: Columna para eje X
            y_column: Columna para eje Y
            title: Título del gráfico
            horizontal: Si True, barras horizontales
            stacked: Si True, barras apiladas
            color_column: Columna para colorear (opcional)
            
        Returns:
            Dict con información del gráfico generado
        """
        try:
            fig, ax = plt.subplots(figsize=(config.CHART_DEFAULT_WIDTH, config.CHART_DEFAULT_HEIGHT))
            
            if color_column and color_column in data.columns:
                # Gráfico agrupado o apilado
                pivot_data = data.pivot_table(
                    values=y_column,
                    index=x_column,
                    columns=color_column,
                    aggfunc='sum'
                )
                
                if horizontal:
                    pivot_data.plot(kind='barh', stacked=stacked, ax=ax)
                else:
                    pivot_data.plot(kind='bar', stacked=stacked, ax=ax)
            else:
                # Gráfico simple
                if horizontal:
                    ax.barh(data[x_column], data[y_column], color=config.COMPANY_COLOR_PRIMARY)
                else:
                    ax.bar(data[x_column], data[y_column], color=config.COMPANY_COLOR_PRIMARY)
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel(x_column if not horizontal else y_column, fontsize=12)
            ax.set_ylabel(y_column if not horizontal else x_column, fontsize=12)
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Guardar
            return self._save_figure(fig, "bar_chart")
        
        except Exception as e:
            logger.error(f"❌ Error al crear gráfico de barras: {str(e)}")
            plt.close('all')
            return {"success": False, "error": str(e)}
    
    def create_line_chart(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str = "Gráfico de Líneas",
        markers: bool = True
    ) -> Dict[str, Any]:
        """
        Crea gráfico de líneas
        
        Args:
            data: DataFrame con los datos
            x_column: Columna para eje X
            y_columns: Lista de columnas para eje Y
            title: Título del gráfico
            markers: Si True, agrega marcadores
            
        Returns:
            Dict con información del gráfico
        """
        try:
            fig, ax = plt.subplots(figsize=(config.CHART_DEFAULT_WIDTH, config.CHART_DEFAULT_HEIGHT))
            
            for i, y_col in enumerate(y_columns):
                marker = 'o' if markers else None
                ax.plot(
                    data[x_column],
                    data[y_col],
                    marker=marker,
                    label=y_col,
                    linewidth=2,
                    color=config.COLOR_PALETTE_PRIMARY[i % len(config.COLOR_PALETTE_PRIMARY)]
                )
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel(x_column, fontsize=12)
            ax.set_ylabel("Valores", fontsize=12)
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            return self._save_figure(fig, "line_chart")
        
        except Exception as e:
            logger.error(f"❌ Error al crear gráfico de líneas: {str(e)}")
            plt.close('all')
            return {"success": False, "error": str(e)}
    
    def create_pie_chart(
        self,
        data: pd.DataFrame,
        label_column: str,
        value_column: str,
        title: str = "Gráfico de Torta"
    ) -> Dict[str, Any]:
        """
        Crea gráfico de torta
        
        Args:
            data: DataFrame con los datos
            label_column: Columna para etiquetas
            value_column: Columna para valores
            title: Título del gráfico
            
        Returns:
            Dict con información del gráfico
        """
        try:
            fig, ax = plt.subplots(figsize=(config.CHART_DEFAULT_WIDTH, config.CHART_DEFAULT_HEIGHT))
            
            colors = config.COLOR_PALETTE_PRIMARY[:len(data)]
            
            wedges, texts, autotexts = ax.pie(
                data[value_column],
                labels=data[label_column],
                autopct='%1.1f%%',
                startangle=90,
                colors=colors
            )
            
            # Mejorar legibilidad
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            return self._save_figure(fig, "pie_chart")
        
        except Exception as e:
            logger.error(f"❌ Error al crear gráfico de torta: {str(e)}")
            plt.close('all')
            return {"success": False, "error": str(e)}
    
    def create_scatter_plot(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str = "Gráfico de Dispersión",
        color_column: Optional[str] = None,
        size_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea gráfico de dispersión
        
        Args:
            data: DataFrame con los datos
            x_column: Columna para eje X
            y_column: Columna para eje Y
            title: Título del gráfico
            color_column: Columna para colorear puntos (opcional)
            size_column: Columna para tamaño de puntos (opcional)
            
        Returns:
            Dict con información del gráfico
        """
        try:
            fig, ax = plt.subplots(figsize=(config.CHART_DEFAULT_WIDTH, config.CHART_DEFAULT_HEIGHT))
            
            colors = data[color_column] if color_column and color_column in data.columns else config.COMPANY_COLOR_PRIMARY
            sizes = data[size_column] * 100 if size_column and size_column in data.columns else 50
            
            scatter = ax.scatter(
                data[x_column],
                data[y_column],
                c=colors,
                s=sizes,
                alpha=0.6,
                edgecolors='w',
                linewidth=0.5
            )
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel(x_column, fontsize=12)
            ax.set_ylabel(y_column, fontsize=12)
            ax.grid(True, alpha=0.3)
            
            if color_column and color_column in data.columns:
                plt.colorbar(scatter, ax=ax, label=color_column)
            
            plt.tight_layout()
            
            return self._save_figure(fig, "scatter_plot")
        
        except Exception as e:
            logger.error(f"❌ Error al crear gráfico de dispersión: {str(e)}")
            plt.close('all')
            return {"success": False, "error": str(e)}
    
    def create_interactive_plotly(
        self,
        data: pd.DataFrame,
        chart_type: str,
        x_column: str,
        y_column: str,
        title: str = "Gráfico Interactivo"
    ) -> Dict[str, Any]:
        """
        Crea gráfico interactivo con Plotly
        
        Args:
            data: DataFrame con los datos
            chart_type: Tipo de gráfico ('bar', 'line', 'scatter', 'pie')
            x_column: Columna para eje X
            y_column: Columna para eje Y
            title: Título del gráfico
            
        Returns:
            Dict con información del gráfico (HTML)
        """
        try:
            if chart_type == "bar":
                fig = px.bar(data, x=x_column, y=y_column, title=title)
            elif chart_type == "line":
                fig = px.line(data, x=x_column, y=y_column, title=title, markers=True)
            elif chart_type == "scatter":
                fig = px.scatter(data, x=x_column, y=y_column, title=title)
            elif chart_type == "pie":
                fig = px.pie(data, names=x_column, values=y_column, title=title)
            else:
                return {"success": False, "error": f"Tipo de gráfico '{chart_type}' no soportado"}
            
            # Personalizar
            fig.update_layout(
                template="plotly_white",
                font=dict(size=12),
                title_font=dict(size=16, family="Arial Black")
            )
            
            # Guardar como HTML e imagen estática
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interactive_{chart_type}_{timestamp}"
            
            # HTML
            html_path = self.output_dir / f"{filename}.html"
            fig.write_html(str(html_path))
            
            # PNG estático
            png_path = self.output_dir / f"{filename}.png"
            fig.write_image(str(png_path), width=1200, height=600)
            
            logger.info(f"✅ Gráfico interactivo creado: {filename}")
            
            return {
                "success": True,
                "file_path": str(png_path),
                "html_path": str(html_path),
                "chart_type": chart_type,
                "format": "png"
            }
        
        except Exception as e:
            logger.error(f"❌ Error al crear gráfico Plotly: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _save_figure(self, fig, chart_type: str) -> Dict[str, Any]:
        """
        Guarda la figura de matplotlib como PNG y genera info
        
        Args:
            fig: Figura de matplotlib
            chart_type: Tipo de gráfico
            
        Returns:
            Dict con información del archivo guardado
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{chart_type}_{timestamp}.png"
            file_path = self.output_dir / filename
            
            # Guardar como PNG
            fig.savefig(
                file_path,
                dpi=config.PLOT_DPI,
                bbox_inches='tight',
                facecolor='white'
            )
            
            plt.close(fig)
            
            logger.info(f"✅ Gráfico guardado: {filename}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "chart_type": chart_type,
                "format": "png"
            }
        
        except Exception as e:
            logger.error(f"❌ Error al guardar gráfico: {str(e)}")
            plt.close('all')
            return {"success": False, "error": str(e)}
    
    def export_as_base64(self, file_path: str) -> Optional[str]:
        """
        Convierte imagen a base64 para envío
        
        Args:
            file_path: Path de la imagen
            
        Returns:
            String base64 o None si hay error
        """
        try:
            with open(file_path, 'rb') as f:
                img_data = f.read()
            
            base64_str = base64.b64encode(img_data).decode('utf-8')
            logger.info(f"✅ Imagen convertida a base64")
            return base64_str
        
        except Exception as e:
            logger.error(f"❌ Error al convertir a base64: {str(e)}")
            return None


# Singleton instance
_visualizer_instance = None

def get_visualizer() -> Visualizer:
    """
    Obtiene instancia del visualizador (singleton)
    
    Returns:
        Visualizer instance
    """
    global _visualizer_instance
    if _visualizer_instance is None:
        _visualizer_instance = Visualizer()
    return _visualizer_instance

"""
🧮 Calculator Tool
Herramienta de cálculos y análisis estadísticos
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from scipy import stats

from tools.base import Tool, ToolResult, ToolStatus
import config


class Calculator(Tool):
    """
    Herramienta de cálculos avanzados y análisis estadístico
    
    Operaciones soportadas:
    - metrics: Cálculo de métricas básicas (sum, avg, max, min, count, std)
    - growth_rate: Tasa de crecimiento período a período
    - moving_average: Promedio móvil
    - outliers: Detección de valores atípicos
    - correlation: Matriz de correlación
    - percentiles: Cálculo de percentiles
    - aggregates: Agregaciones grupales
    """
    
    def __init__(self):
        super().__init__("Calculator")
    
    def execute(self, operation: str, **params) -> ToolResult:
        """
        Ejecuta una operación de cálculo
        
        Args:
            operation: Nombre de la operación
            **params: Parámetros específicos de cada operación
            
        Returns:
            ToolResult con los resultados
        """
        operations = {
            "metrics": self._calculate_metrics,
            "growth_rate": self._calculate_growth_rate,
            "moving_average": self._calculate_moving_average,
            "outliers": self._detect_outliers,
            "correlation": self._calculate_correlation,
            "percentiles": self._calculate_percentiles,
            "aggregates": self._calculate_aggregates
        }
        
        if operation not in operations:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Operación '{operation}' no soportada. Disponibles: {list(operations.keys())}"
            )
        
        try:
            return operations[operation](**params)
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Error en {operation}: {str(e)}"
            )
    
    def get_supported_operations(self) -> list:
        """Lista de operaciones soportadas"""
        return [
            "metrics",
            "growth_rate",
            "moving_average",
            "outliers",
            "correlation",
            "percentiles",
            "aggregates"
        ]
    
    def _calculate_metrics(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None
    ) -> ToolResult:
        """
        Calcula métricas estadísticas básicas
        
        Args:
            data: DataFrame con los datos
            columns: Columnas a calcular (None = todas numéricas)
            metrics: Métricas a calcular (None = todas)
            
        Returns:
            ToolResult con diccionario de métricas
        """
        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()
        
        available_metrics = {
            "sum": lambda col: data[col].sum(),
            "mean": lambda col: data[col].mean(),
            "median": lambda col: data[col].median(),
            "min": lambda col: data[col].min(),
            "max": lambda col: data[col].max(),
            "std": lambda col: data[col].std(),
            "var": lambda col: data[col].var(),
            "count": lambda col: data[col].count()
        }
        
        if metrics is None:
            metrics = list(available_metrics.keys())
        
        results = {}
        for col in columns:
            if col not in data.columns:
                continue
            
            results[col] = {}
            for metric in metrics:
                if metric in available_metrics:
                    results[col][metric] = available_metrics[metric](col)
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=results,
            metadata={
                "columns_analyzed": len(columns),
                "metrics_calculated": len(metrics)
            }
        )
    
    def _calculate_growth_rate(
        self,
        data: pd.DataFrame,
        value_column: str,
        period_column: Optional[str] = None,
        periods: int = 1
    ) -> ToolResult:
        """
        Calcula tasa de crecimiento
        
        Args:
            data: DataFrame con los datos
            value_column: Columna con los valores
            period_column: Columna de período (None = índice)
            periods: Número de períodos para calcular crecimiento
            
        Returns:
            ToolResult con tasas de crecimiento
        """
        # Validar parámetros
        error = self.validate_params(["data", "value_column"], locals())
        if error:
            return ToolResult(status=ToolStatus.ERROR, error=error)
        
        if value_column not in data.columns:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Columna '{value_column}' no existe"
            )
        
        # Calcular crecimiento
        if period_column:
            sorted_data = data.sort_values(period_column)
            values = sorted_data[value_column]
        else:
            values = data[value_column]
        
        growth_rates = values.pct_change(periods=periods) * 100
        
        result_data = pd.DataFrame({
            value_column: values,
            "growth_rate_%": growth_rates
        })
        
        avg_growth = growth_rates.mean()
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=result_data.to_dict('records'),
            metadata={
                "average_growth_rate": avg_growth,
                "periods": periods,
                "total_periods": len(values)
            }
        )
    
    def _calculate_moving_average(
        self,
        data: pd.DataFrame,
        column: str,
        window: int = 3,
        ma_type: str = "simple"
    ) -> ToolResult:
        """
        Calcula promedio móvil
        
        Args:
            data: DataFrame con los datos
            column: Columna a calcular
            window: Tamaño de la ventana
            ma_type: Tipo ('simple' o 'exponential')
            
        Returns:
            ToolResult con promedios móviles
        """
        error = self.validate_params(["data", "column"], locals())
        if error:
            return ToolResult(status=ToolStatus.ERROR, error=error)
        
        if column not in data.columns:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Columna '{column}' no existe"
            )
        
        if ma_type == "simple":
            ma = data[column].rolling(window=window).mean()
        elif ma_type == "exponential":
            ma = data[column].ewm(span=window).mean()
        else:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Tipo '{ma_type}' no soportado. Use 'simple' o 'exponential'"
            )
        
        result_data = pd.DataFrame({
            column: data[column],
            f"ma_{window}": ma
        })
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=result_data.to_dict('records'),
            metadata={
                "window": window,
                "type": ma_type,
                "values_calculated": ma.notna().sum()
            }
        )
    
    def _detect_outliers(
        self,
        data: pd.DataFrame,
        column: str,
        method: str = "iqr",
        threshold: float = 1.5
    ) -> ToolResult:
        """
        Detecta valores atípicos (outliers)
        
        Args:
            data: DataFrame con los datos
            column: Columna a analizar
            method: Método ('iqr' o 'zscore')
            threshold: Umbral (1.5 para IQR, 3 para z-score)
            
        Returns:
            ToolResult con outliers detectados
        """
        error = self.validate_params(["data", "column"], locals())
        if error:
            return ToolResult(status=ToolStatus.ERROR, error=error)
        
        if column not in data.columns:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Columna '{column}' no existe"
            )
        
        values = data[column].dropna()
        
        if method == "iqr":
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            outliers = data[(data[column] < lower_bound) | (data[column] > upper_bound)]
        
        elif method == "zscore":
            z_scores = np.abs(stats.zscore(values))
            outliers = data[z_scores > threshold]
        
        else:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Método '{method}' no soportado. Use 'iqr' o 'zscore'"
            )
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=outliers.to_dict('records'),
            metadata={
                "total_values": len(data),
                "outliers_count": len(outliers),
                "outliers_percentage": (len(outliers) / len(data)) * 100,
                "method": method,
                "threshold": threshold
            }
        )
    
    def _calculate_correlation(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "pearson"
    ) -> ToolResult:
        """
        Calcula matriz de correlación
        
        Args:
            data: DataFrame con los datos
            columns: Columnas a correlacionar (None = todas numéricas)
            method: Método ('pearson', 'spearman', 'kendall')
            
        Returns:
            ToolResult con matriz de correlación
        """
        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(columns) < 2:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Se necesitan al menos 2 columnas numéricas"
            )
        
        correlation_matrix = data[columns].corr(method=method)
        
        # Encontrar correlaciones fuertes (> 0.7 o < -0.7)
        strong_correlations = []
        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:
                    strong_correlations.append({
                        "col1": columns[i],
                        "col2": columns[j],
                        "correlation": corr_value
                    })
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "correlation_matrix": correlation_matrix.to_dict(),
                "strong_correlations": strong_correlations
            },
            metadata={
                "columns_analyzed": len(columns),
                "method": method,
                "strong_correlations_count": len(strong_correlations)
            }
        )
    
    def _calculate_percentiles(
        self,
        data: pd.DataFrame,
        column: str,
        percentiles: List[float] = [0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
    ) -> ToolResult:
        """
        Calcula percentiles
        
        Args:
            data: DataFrame con los datos
            column: Columna a analizar
            percentiles: Lista de percentiles a calcular (0-1)
            
        Returns:
            ToolResult con percentiles
        """
        error = self.validate_params(["data", "column"], locals())
        if error:
            return ToolResult(status=ToolStatus.ERROR, error=error)
        
        if column not in data.columns:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Columna '{column}' no existe"
            )
        
        results = {}
        for p in percentiles:
            percentile_value = data[column].quantile(p)
            results[f"p{int(p*100)}"] = percentile_value
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=results,
            metadata={
                "column": column,
                "percentiles_calculated": len(percentiles)
            }
        )
    
    def _calculate_aggregates(
        self,
        data: pd.DataFrame,
        group_by: str,
        agg_column: str,
        agg_functions: List[str] = ["sum", "mean", "count"]
    ) -> ToolResult:
        """
        Calcula agregaciones por grupo
        
        Args:
            data: DataFrame con los datos
            group_by: Columna para agrupar
            agg_column: Columna a agregar
            agg_functions: Funciones de agregación
            
        Returns:
            ToolResult con agregaciones
        """
        error = self.validate_params(["data", "group_by", "agg_column"], locals())
        if error:
            return ToolResult(status=ToolStatus.ERROR, error=error)
        
        if group_by not in data.columns:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Columna de grupo '{group_by}' no existe"
            )
        
        if agg_column not in data.columns:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Columna de agregación '{agg_column}' no existe"
            )
        
        # Mapear nombres de funciones
        func_map = {
            "sum": "sum",
            "mean": "mean",
            "avg": "mean",
            "count": "count",
            "min": "min",
            "max": "max",
            "std": "std"
        }
        
        valid_functions = [func_map.get(f, f) for f in agg_functions]
        
        aggregated = data.groupby(group_by)[agg_column].agg(valid_functions)
        aggregated = aggregated.reset_index()
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=aggregated.to_dict('records'),
            metadata={
                "groups_count": len(aggregated),
                "group_by_column": group_by,
                "aggregated_column": agg_column,
                "functions_applied": valid_functions
            }
        )


# Singleton instance
_calculator_instance = None


def get_calculator() -> Calculator:
    """
    Obtiene instancia singleton del Calculator
    
    Returns:
        Calculator instance
    """
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = Calculator()
    return _calculator_instance

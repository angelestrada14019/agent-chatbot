"""
📚 Example: Using Calculator Tool
Ejemplos de uso de la herramienta de cálculos estadísticos
"""
import pandas as pd
from tools.calculator import get_calculator


def example_1_basic_metrics():
    """Ejemplo 1: Métricas básicas"""
    print("\n" + "="*60)
    print("🧮 EJEMPLO 1: Métricas Básicas")
    print("="*60)
    
    # Datos de ejemplo
    data = pd.DataFrame({
        "producto": ["A", "B", "C", "D", "E"],
        "ventas": [1000, 1500, 1200, 900, 1100],
        "cantidad": [50, 75, 60, 45, 55]
    })
    
    calc = get_calculator()
    
    # Calcular métricas
    result = calc.execute_with_logging(
        "metrics",
        data=data,
        columns=["ventas", "cantidad"],
        metrics=["sum", "mean", "std", "min", "max"]
    )
    
    if result.success:
        print("\n✅ Métricas calculadas:")
        for col, metrics in result.data.items():
            print(f"\n{col}:")
            for metric, value in metrics.items():
                print(f"  - {metric}: {value:.2f}")
    else:
        print(f"❌ Error: {result.error}")


def example_2_growth_rate():
    """Ejemplo 2: Tasa de crecimiento"""
    print("\n" + "="*60)
    print("📈 EJEMPLO 2: Tasa de Crecimiento")
    print("="*60)
    
    # Datos de ventas mensuales
    data = pd.DataFrame({
        "mes": ["Ene", "Feb", "Mar", "Abr", "May"],
        "ventas": [10000, 12000, 11500, 13000, 14500]
    })
    
    calc = get_calculator()
    
    result = calc.execute_with_logging(
        "growth_rate",
        data=data,
        value_column="ventas",
        period_column="mes",
        periods=1
    )
    
    if result.success:
        print("\n✅ Crecimiento calculado:")
        print(f"Tasa promedio: {result.metadata['average_growth_rate']:.2f}%")
        print("\nDetalle por período:")
        for row in result.data:
            growth = row.get('growth_rate_%')
            if pd.notna(growth):
                print(f"  {row['ventas']:.0f} → {growth:+.2f}%")


def example_3_moving_average():
    """Ejemplo 3: Promedio móvil"""
    print("\n" + "="*60)
    print("📊 EJEMPLO 3: Promedio Móvil")
    print("="*60)
    
    # Datos con fluctuaciones
    data = pd.DataFrame({
        "dia": range(1, 11),
        "ventas": [100, 120, 110, 130, 125, 140, 135, 150, 145, 160]
    })
    
    calc = get_calculator()
    
    result = calc.execute_with_logging(
        "moving_average",
        data=data,
        column="ventas",
        window=3,
        ma_type="simple"
    )
    
    if result.success:
        print("\n✅ Promedio móvil calculado:")
        for row in result.data:
            ma = row.get('ma_3')
            if pd.notna(ma):
                print(f"  Día {row.get('dia', 'N/A')}: Venta={row['ventas']}, MA(3)={ma:.2f}")


def example_4_outliers():
    """Ejemplo 4: Detección de outliers"""
    print("\n" + "="*60)
    print("🔍 EJEMPLO 4: Detección de Outliers")
    print("="*60)
    
    # Datos con algunos valores atípicos
    data = pd.DataFrame({
        "cliente_id": range(1, 21),
        "compra": [100, 95, 110, 105, 98, 102, 500, 103, 99, 107,  # 500 es outlier
                   104, 96, 101, 108, 1000, 99, 103, 97, 105, 102]  # 1000 es outlier
    })
    
    calc = get_calculator()
    
    result = calc.execute_with_logging(
        "outliers",
        data=data,
        column="compra",
        method="iqr",
        threshold=1.5
    )
    
    if result.success:
        print(f"\n✅ Outliers detectados: {result.metadata['outliers_count']}")
        print(f"Porcentaje: {result.metadata['outliers_percentage']:.1f}%")
        print("\nValores atípicos:")
        for row in result.data:
            print(f"  Cliente {row['cliente_id']}: ${row['compra']}")


def example_5_correlation():
    """Ejemplo 5: Matriz de correlación"""
    print("\n" + "="*60)
    print("🔗 EJEMPLO 5: Correlación")
    print("="*60)
    
    # Datos de múltiples variables
    data = pd.DataFrame({
        "ventas": [100, 150, 120, 180, 160, 140, 200, 170],
        "publicidad": [10, 15, 12, 20, 18, 14, 25, 19],
        "precio": [50, 48, 52, 45, 47, 51, 44, 46],
        "temperatura": [25, 28, 24, 30, 29, 26, 32, 28]
    })
    
    calc = get_calculator()
    
    result = calc.execute_with_logging(
        "correlation",
        data=data,
        method="pearson"
    )
    
    if result.success:
        print("\n✅ Correlaciones fuertes encontradas:")
        for corr in result.data["strong_correlations"]:
            print(f"  {corr['col1']} ↔ {corr['col2']}: {corr['correlation']:.3f}")


def example_6_aggregates():
    """Ejemplo 6: Agregaciones por grupo"""
    print("\n" + "="*60)
    print("📊 EJEMPLO 6: Agregaciones por Grupo")
    print("="*60)
    
    # Datos de ventas por categoría
    data = pd.DataFrame({
        "categoria": ["Electrónica", "Ropa", "Electrónica", "Alimentos", 
                      "Ropa", "Electrónica", "Alimentos", "Ropa"],
        "ventas": [1000, 500, 1200, 300, 450, 900, 350, 550],
        "unidades": [10, 25, 12, 40, 22, 9, 45, 28]
    })
    
    calc = get_calculator()
    
    result = calc.execute_with_logging(
        "aggregates",
        data=data,
        group_by="categoria",
        agg_column="ventas",
        agg_functions=["sum", "mean", "count"]
    )
    
    if result.success:
        print("\n✅ Agregaciones por categoría:")
        for row in result.data:
            print(f"\n{row['categoria']}:")
            print(f"  Total: ${row.get('sum', 0):.0f}")
            print(f"  Promedio: ${row.get('mean', 0):.0f}")
            print(f"  Cantidad: {row.get('count', 0)}")


def example_7_percentiles():
    """Ejemplo 7: Cálculo de percentiles"""
    print("\n" + "="*60)
    print("📊 EJEMPLO 7: Percentiles")
    print("="*60)
    
    # Datos de salarios
    data = pd.DataFrame({
        "empleado_id": range(1, 51),
        "salario": [30000 + i*1000 + (i%7)*500 for i in range(50)]
    })
    
    calc = get_calculator()
    
    result = calc.execute_with_logging(
        "percentiles",
        data=data,
        column="salario",
        percentiles=[0.25, 0.5, 0.75, 0.9, 0.95]
    )
    
    if result.success:
        print("\n✅ Percentiles de salarios:")
        for percentile, value in result.data.items():
            print(f"  {percentile}: ${value:,.0f}")


if __name__ == "__main__":
    print("""
    🧮 Calculator Tool - Ejemplos de Uso
    ====================================
    
    Ejecutando 7 ejemplos de cálculos estadísticos...
    """)
    
    try:
        example_1_basic_metrics()
        example_2_growth_rate()
        example_3_moving_average()
        example_4_outliers()
        example_5_correlation()
        example_6_aggregates()
        example_7_percentiles()
        
        print("\n" + "="*60)
        print("✅ Todos los ejemplos ejecutados correctamente")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n⚠️ Asegúrate de:")
        print("1. Tener scipy instalado: pip install scipy")
        print("2. Tener pandas y numpy instalados")

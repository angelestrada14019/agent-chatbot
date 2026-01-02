"""
📚 Example: Using Calculator Tool (Expression Evaluator)
Ejemplos de uso de la calculadora como evaluador de expresiones
"""
from tools.calculator import get_calculator, calc


def example_1_basic_arithmetic():
    """Ejemplo 1: Aritmética básica"""
    print("\n" + "="*60)
    print("🧮 EJEMPLO 1: Aritmética Básica")
    print("="*60)
    
    calculator = get_calculator()
    
    expressions = [
        "2 + 2",
        "10 - 3",
        "4 * 5",
        "20 / 4",
        "17 // 5",  # División entera
        "17 % 5",   # Módulo
        "2 ** 8",   # Potencia
    ]
    
    for expr in expressions:
        result = calculator.execute_with_logging("evaluate", expression=expr)
        if result.success:
            print(f"  {result.metadata['formatted']}")


def example_2_complex_expressions():
    """Ejemplo 2: Expresiones complejas"""
    print("\n" + "="*60)
    print("🔢 EJEMPLO 2: Expresiones Complejas")
    print("="*60)
    
    expressions = [
        "(10 + 5) * 2",
        "100 / (5 + 5)",
        "(2 ** 3) + (4 ** 2)",
        "-(5 + 3) * 2",
        "((8 + 2) * 3) / 6",
    ]
    
    for expr in expressions:
        result = calc(expr)  # Función de conveniencia
        print(f"  {expr} = {result}")


def example_3_trigonometry():
    """Ejemplo 3: Funciones trigonométricas"""
    print("\n" + "="*60)
    print("📐 EJEMPLO 3: Trigonometría")
    print("="*60)
    
    expressions = [
        "sin(0)",
        "sin(pi/2)",
        "cos(0)",
        "tan(pi/4)",
        "asin(1)",
        "acos(0)",
    ]
    
    for expr in expressions:
        result = calc(expr)
        print(f"  {expr} = {result}")


def example_4_logarithms():
    """Ejemplo 4: Logaritmos y exponenciales"""
    print("\n" + "="*60)
    print("📊 EJEMPLO 4: Logaritmos y Exponenciales")
    print("="*60)
    
    expressions = [
        "log(100, 10)",  # log base 10 de 100
        "log10(1000)",
        "log2(8)",
        "exp(1)",  # e^1
        "exp(2)",
        "log(e)",  # ln(e)
    ]
    
    for expr in expressions:
        result = calc(expr)
        print(f"  {expr} = {result}")


def example_5_roots_and_powers():
    """Ejemplo 5: Raíces y potencias"""
    print("\n" + "="*60)
    print("🔺 EJEMPLO 5: Raíces y Potencias")
    print("="*60)
    
    expressions = [
        "sqrt(16)",
        "sqrt(2)",
        "cbrt(27)",  # Raíz cúbica
        "pow(2, 10)",
        "sqrt(144) + sqrt(25)",
    ]
    
    for expr in expressions:
        result = calc(expr)
        print(f"  {expr} = {result}")


def example_6_rounding():
    """Ejemplo 6: Redondeo"""
    print("\n" + "="*60)
    print("🎯 EJEMPLO 6: Funciones de Redondeo")
    print("="*60)
    
    expressions = [
        "round(3.7)",
        "round(3.14159, 2)",  # Python permite pero nuestra calc no pasarparams adicionales así
        "floor(3.7)",
        "ceil(3.2)",
        "trunc(3.9)",
        "abs(-15)",
    ]
    
    for expr in expressions:
        try:
            result = calc(expr)
            print(f"  {expr} = {result}")
        except Exception as e:
            print(f"  {expr} → Error: {e}")


def example_7_special_functions():
    """Ejemplo 7: Funciones especiales"""
    print("\n" + "="*60)
    print("⭐ EJEMPLO 7: Funciones Especiales")
    print("="*60)
    
    expressions = [
        "factorial(5)",
        "factorial(10)",
        "gcd(48, 18)",
        "lcm(12, 18)",
        "max(10, 25, 5, 30)",
        "min(10, 25, 5, 30)",
    ]
    
    for expr in expressions:
        result = calc(expr)
        print(f"  {expr} = {result}")


def example_8_constants():
    """Ejemplo 8: Uso de constantes"""
    print("\n" + "="*60)
    print("🔢 EJEMPLO 8: Constantes Matemáticas")
    print("="*60)
    
    expressions = [
        "pi",
        "e",
        "tau",  # 2*pi
        "pi * 2",
        "e ** 2",
        "sin(pi)",
        "cos(2*pi)",
    ]
    
    for expr in expressions:
        result = calc(expr)
        print(f"  {expr} = {result}")


def example_9_real_world():
    """Ejemplo 9: Casos de uso real"""
    print("\n" + "="*60)
    print("🌍 EJEMPLO 9: Casos de Uso Reales")
    print("="*60)
    
    # Calcular área de círculo
    radius = 5
    area = calc(f"pi * {radius} ** 2")
    print(f"  Área de círculo (r={radius}): {area:.2f}")
    
    # Calcular hipotenusa
    a, b = 3, 4
    hypotenuse = calc(f"sqrt({a}**2 + {b}**2)")
    print(f"  Hipotenusa (catetos {a}, {b}): {hypotenuse}")
    
    # Convertir grados a radianes y calcular seno
    degrees = 30
    radians_expr = f"({degrees} * pi) / 180"
    radians = calc(radians_expr)
    sin_30 = calc(f"sin({radians})")
    print(f"  sin(30°) = {sin_30}")
    
    # Calcular interés compuesto
    principal = 1000
    rate = 0.05  # 5%
    years = 10
    final = calc(f"{principal} * (1 + {rate}) ** {years}")
    print(f"  Interés compuesto (P=${principal}, r=5%, t={years} años): ${final:.2f}")


def example_10_help():
    """Ejemplo 10: Ver funciones disponibles"""
    print("\n" + "="*60)
    print("❓ EJEMPLO 10: Ayuda - Funciones Disponibles")
    print("="*60)
    
    calculator = get_calculator()
    result = calculator.execute("help")
    
    if result.success:
        data = result.data
        
        print("\n📌 Operadores:")
        print(f"  Aritméticos: {', '.join(data['operators']['arithmetic'])}")
        print(f"  Unarios: {', '.join(data['operators']['unary'])}")
        
        print("\n🔧 Funciones:")
        for category, functions in data['functions'].items():
            print(f"  {category.capitalize()}: {', '.join(functions)}")
        
        print(f"\n🔢 Constantes: {', '.join(data['constants'])}")
        
        print("\n📚 Ejemplos:")
        for example in data['examples']:
            print(f"  {example}")


def example_11_error_handling():
    """Ejemplo 11: Manejo de errores"""
    print("\n" + "="*60)
    print("⚠️ EJEMPLO 11: Manejo de Errores")
    print("="*60)
    
    calculator = get_calculator()
    
    invalid_expressions = [
        "2 / 0",  # División por cero
        "sqrt(-1)",  # Raíz de negativo
        "invalid_function(5)",  # Función no existente
        "2 +",  # Sintaxis incorrecta
        "import os",  # Código malicioso (no permitido)
    ]
    
    for expr in invalid_expressions:
        result = calculator.execute("evaluate", expression=expr)
        if result.success:
            print(f"  ✅ {expr} = {result.data['result']}")
        else:
            print(f"  ❌ {expr} → {result.error}")


if __name__ == "__main__":
    print("""
    🧮 Calculator Tool - Evaluador de Expresiones
    ==============================================
    
    Calculadora que evalúa expresiones matemáticas dinámicamente
    Similar a una calculadora científica
    """)
    
    try:
        example_1_basic_arithmetic()
        example_2_complex_expressions()
        example_3_trigonometry()
        example_4_logarithms()
        example_5_roots_and_powers()
        example_6_rounding()
        example_7_special_functions()
        example_8_constants()
        example_9_real_world()
        example_10_help()
        example_11_error_handling()
        
        print("\n" + "="*60)
        print("✅ Todos los ejemplos ejecutados correctamente")
        print("="*60)
        print("\n💡 Uso rápido:")
        print("  from tools.calculator import calc")
        print("  result = calc('2 + 2')")
        print("  print(result)  # 4")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

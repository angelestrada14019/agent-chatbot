"""
🧮 Calculator Tool - Evaluador de Expresiones Matemáticas
Calculadora que evalúa expresiones matemáticas dinámicamente
"""
from typing import Dict, Any, List, Optional, Union
import math
import re
import ast
import operator

from tools.base import Tool, ToolResult, ToolStatus


class MathExpressionEvaluator:
    """
    Evaluador seguro de expresiones matemáticas
    
    Soporta:
    - Operaciones básicas: +, -, *, /, //, %, **
    - Funciones matemáticas: sin, cos, tan, sqrt, log, exp, abs, etc
    - Constantes: pi, e
    - Paréntesis para orden de operaciones
    """
    
    # Operadores permitidos
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos
    }
    
    # Funciones matemáticas permitidas
    FUNCTIONS = {
        # Trigonométricas
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'sinh': math.sinh,
        'cosh': math.cosh,
        'tanh': math.tanh,
        
        # Logarítmicas y exponenciales
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        'exp': math.exp,
        'pow': pow,
        
        # Raíces y potencias
        'sqrt': math.sqrt,
        'cbrt': lambda x: x ** (1/3),
        
        # Redondeo
        'round': round,
        'floor': math.floor,
        'ceil': math.ceil,
        'trunc': math.trunc,
        
        # Valor absoluto y signo
        'abs': abs,
        'fabs': math.fabs,
        
        # Otras
        'factorial': math.factorial,
        'gcd': math.gcd,
        'lcm': lambda a, b: abs(a * b) // math.gcd(a, b) if a and b else 0,
        
        # Funciones de dos parámetros
        'max': max,
        'min': min,
        'sum': sum,
    }
    
    # Constantes permitidas
    CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
        'tau': math.tau,
        'inf': math.inf,
    }
    
    def __init__(self):
        self.allowed_names = {**self.FUNCTIONS, **self.CONSTANTS}
    
    def evaluate(self, expression: str) -> Union[float, int]:
        """
        Evalúa una expresión matemática de forma segura
        
        Args:
            expression: Expresión matemática como string
            
        Returns:
            Resultado numérico
            
        Raises:
            ValueError: Si la expresión es inválida
            SyntaxError: Si la sintaxis es incorrecta
        """
        # Limpiar expresión
        expression = expression.strip()
        
        # Reemplazar constantes textuales
        expression = self._replace_constants(expression)
        
        try:
            # Parsear expresión a AST
            node = ast.parse(expression, mode='eval')
            
            # Evaluar de forma segura
            result = self._eval_node(node.body)
            
            return result
        
        except Exception as e:
            raise ValueError(f"Error evaluando expresión: {str(e)}")
    
    def _replace_constants(self, expression: str) -> str:
        """Reemplaza nombres de constantes por sus valores"""
        for name, value in self.CONSTANTS.items():
            # Reemplazar solo palabras completas
            expression = re.sub(rf'\b{name}\b', str(value), expression)
        return expression
    
    def _eval_node(self, node):
        """Evalúa un nodo del AST de forma recursiva"""
        
        # Número literal
        if isinstance(node, ast.Num):
            return node.n
        
        # Constante (None, True, False)
        elif isinstance(node, ast.Constant):
            return node.value
        
        # Operación binaria (ej: 2 + 3)
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Operador {op_type.__name__} no permitido")
            
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            
            return self.OPERATORS[op_type](left, right)
        
        # Operación unaria (ej: -5, +3)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Operador unario {op_type.__name__} no permitido")
            
            operand = self._eval_node(node.operand)
            return self.OPERATORS[op_type](operand)
        
        # Llamada a función (ej: sin(0.5))
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Solo se permiten llamadas a funciones nombradas")
            
            func_name = node.func.id
            if func_name not in self.FUNCTIONS:
                raise ValueError(f"Función '{func_name}' no permitida")
            
            # Evaluar argumentos
            args = [self._eval_node(arg) for arg in node.args]
            
            # Ejecutar función
            func = self.FUNCTIONS[func_name]
            return func(*args)
        
        # Nombre (variable o constante)
        elif isinstance(node, ast.Name):
            if node.id in self.CONSTANTS:
                return self.CONSTANTS[node.id]
            raise ValueError(f"Variable '{node.id}' no definida")
        
        # Lista (para funciones como sum, max, min)
        elif isinstance(node, ast.List):
            return [self._eval_node(item) for item in node.elts]
        
        # Tupla
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(item) for item in node.elts)
        
        else:
            raise ValueError(f"Tipo de nodo {type(node).__name__} no soportado")


class Calculator(Tool):
    """
    Calculadora que evalúa expresiones matemáticas dinámicamente
    
    Ejemplos:
    - "2 + 2" → 4
    - "sqrt(16) * 5" → 20.0
    - "sin(pi/2)" → 1.0
    - "(10 + 5) * 2 / 3" → 10.0
    - "log(100, 10)" → 2.0
    - "factorial(5)" → 120
    """
    
    def __init__(self):
        super().__init__("Calculator")
        self.evaluator = MathExpressionEvaluator()
    
    def execute(self, operation: str, **params) -> ToolResult:
        """
        Ejecuta operación de calculadora
        
        Operations:
        - evaluate: Evalúa expresión matemática
        - help: Muestra funciones disponibles
        """
        if operation == "evaluate":
            return self._evaluate_expression(params.get("expression", ""))
        
        elif operation == "help":
            return self._get_help()
        
        else:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Operación '{operation}' no soportada. Use 'evaluate' o 'help'"
            )
    
    def _evaluate_expression(self, expression: str) -> ToolResult:
        """Evalúa una expresión matemática"""
        if not expression:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Expresión vacía. Proporcione una expresión matemática."
            )
        
        try:
            self.logger.info(f"🧮 Evaluando: {expression}")
            
            result = self.evaluator.evaluate(expression)
            
            # Formatear resultado
            if isinstance(result, float):
                # Si es entero, mostrarlo sin decimales
                if result.is_integer():
                    result = int(result)
            
            self.logger.info(f"✅ Resultado: {result}")
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "expression": expression,
                    "result": result,
                    "type": type(result).__name__
                },
                metadata={
                    "formatted": f"{expression} = {result}"
                }
            )
        
        except (ValueError, SyntaxError, ZeroDivisionError) as e:
            self.logger.error(f"❌ Error en expresión: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Error evaluando '{expression}': {str(e)}"
            )
        
        except Exception as e:
            self.logger.error(f"❌ Error inesperado: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Error inesperado: {str(e)}"
            )
    
    def _get_help(self) -> ToolResult:
        """Retorna ayuda con funciones disponibles"""
        help_data = {
            "operators": {
                "arithmetic": ["+", "-", "*", "/", "//", "%", "**"],
                "unary": ["-", "+"]
            },
            "functions": {
                "trigonometric": ["sin", "cos", "tan", "asin", "acos", "atan"],
                "logarithmic": ["log", "log10", "log2", "exp"],
                "roots": ["sqrt", "cbrt"],
                "rounding": ["round", "floor", "ceil", "trunc"],
                "other": ["abs", "factorial", "max", "min", "sum", "gcd", "lcm"]
            },
            "constants": ["pi", "e", "tau", "inf"],
            "examples": [
                "2 + 2 → 4",
                "sqrt(16) * 5 → 20.0",
                "sin(pi/2) → 1.0",
                "(10 + 5) * 2 / 3 → 10.0",
                "log(100, 10) → 2.0",
                "factorial(5) → 120",
                "max(5, 10, 3) → 10",
                "abs(-15) → 15"
            ]
        }
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=help_data
        )
    
    def get_supported_operations(self) -> List[str]:
        """Lista de operaciones soportadas"""
        return ["evaluate", "help"]
    
    def calculate(self, expression: str) -> Union[float, int, None]:
        """
        Método de conveniencia para evaluar directamente
        
        Args:
            expression: Expresión matemática
            
        Returns:
            Resultado o None si hay error
        """
        result = self.execute("evaluate", expression=expression)
        if result.success:
            return result.data["result"]
        return None


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


# Función de conveniencia
def calc(expression: str) -> Union[float, int, None]:
    """
    Función de conveniencia para cálculos rápidos
    
    Args:
        expression: Expresión matemática
        
    Returns:
        Resultado del cálculo
        
    Example:
        >>> calc("2 + 2")
        4
        >>> calc("sqrt(16) * 5")
        20.0
    """
    calculator = get_calculator()
    return calculator.calculate(expression)

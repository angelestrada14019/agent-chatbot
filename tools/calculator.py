"""
🧮 Calculator Tool - Integración con OpenAI Agents SDK
Evaluador seguro de expresiones matemáticas.
"""
import math
import ast
import operator
import logging
from typing import Union

from agents import function_tool

logger = logging.getLogger("CalculatorTool")

class MathEvaluator:
    """Evaluador seguro de AST para matemáticas"""
    OPERATORS = {
        ast.Add: operator.add, ast.Sub: operator.sub, 
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg
    }
    
    FUNCTIONS = {
        'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 
        'tan': math.tan, 'log': math.log, 'exp': math.exp,
        'abs': abs, 'round': round
    }

    def eval_node(self, node):
        if isinstance(node, ast.Num): return node.n
        if isinstance(node, ast.BinOp):
            return self.OPERATORS[type(node.op)](self.eval_node(node.left), self.eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            return self.OPERATORS[type(node.op)](self.eval_node(node.operand))
        if isinstance(node, ast.Call):
            return self.FUNCTIONS[node.func.id](*[self.eval_node(arg) for arg in node.args])
        raise ValueError(f"Operación no permitida: {type(node).__name__}")

@function_tool
def calculate_expression(expression: str) -> str:
    """
    Evalúa una expresión matemática de forma segura.
    Soporta operaciones básicas (+, -, *, /, **) y funciones (sqrt, sin, cos, log, etc).
    
    Args:
        expression: La expresión matemática a evaluar (ej: "sqrt(25) + 10").
    """
    try:
        evaluator = MathEvaluator()
        node = ast.parse(expression, mode='eval')
        result = evaluator.eval_node(node.body)
        return str(result)
    except Exception as e:
        logger.error(f"❌ Error en calculadora: {str(e)}")
        return f"Error: {str(e)}"

def get_calculator():
    return MathEvaluator()

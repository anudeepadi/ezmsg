"""Safe AST-based conditional expression evaluator.

Evaluates boolean expressions like:
    slip_count >= 3
    language == "en" AND quit_date != ""
    slip_count > 0 AND slip_count < 3

Variables are resolved from a dict of participant variable values.
Only supports: ==, !=, >, <, >=, <=, AND, OR, NOT, parentheses,
string literals, and numeric literals.
"""

import ast
import logging
import operator
import re
from typing import Any

logger = logging.getLogger(__name__)

# Supported comparison operators
_COMPARE_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Gt: operator.gt,
    ast.Lt: operator.lt,
    ast.GtE: operator.ge,
    ast.LtE: operator.le,
}


class ConditionEvalError(Exception):
    """Raised when a condition expression cannot be evaluated."""


def _preprocess(expression: str) -> str:
    """Convert human-friendly syntax to Python-parseable syntax."""
    expr = re.sub(r'\bAND\b', 'and', expression, flags=re.IGNORECASE)
    expr = re.sub(r'\bOR\b', 'or', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bNOT\b', 'not', expr, flags=re.IGNORECASE)
    return expr


def _coerce_numeric(value: str | None) -> int | float | str:
    """Try to coerce a string to a number for comparisons."""
    if value is None:
        return ""
    try:
        return int(value)
    except (ValueError, TypeError):
        pass
    try:
        return float(value)
    except (ValueError, TypeError):
        pass
    return value


def _resolve_node(node: ast.AST, variables: dict[str, Any]) -> Any:
    """Recursively evaluate an AST node against the variable dict."""

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(_resolve_node(v, variables) for v in node.values)
        elif isinstance(node.op, ast.Or):
            return any(_resolve_node(v, variables) for v in node.values)
        raise ConditionEvalError(f"Unsupported boolean op: {type(node.op).__name__}")

    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return not _resolve_node(node.operand, variables)
        raise ConditionEvalError(f"Unsupported unary op: {type(node.op).__name__}")

    if isinstance(node, ast.Compare):
        left = _resolve_node(node.left, variables)
        for op_node, comparator in zip(node.ops, node.comparators):
            op_type = type(op_node)
            if op_type not in _COMPARE_OPS:
                raise ConditionEvalError(f"Unsupported comparison: {op_type.__name__}")
            right = _resolve_node(comparator, variables)
            left_c = _coerce_numeric(left) if isinstance(left, str) else left
            right_c = _coerce_numeric(right) if isinstance(right, str) else right
            if type(left_c) == type(right_c):
                if not _COMPARE_OPS[op_type](left_c, right_c):
                    return False
            else:
                if not _COMPARE_OPS[op_type](str(left), str(right)):
                    return False
            left = right
        return True

    if isinstance(node, ast.Name):
        name = node.id
        if name in ("True", "true"):
            return True
        if name in ("False", "false"):
            return False
        if name in ("None", "null", "none"):
            return ""
        if name not in variables:
            logger.warning("Variable %r not found, defaulting to empty string", name)
            return ""
        return variables[name]

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Expression):
        return _resolve_node(node.body, variables)

    raise ConditionEvalError(f"Unsupported AST node: {type(node).__name__}")


def evaluate_condition(
    condition_text: str,
    variables: dict[str, Any],
) -> bool:
    """Evaluate a conditional expression against participant variables.

    Args:
        condition_text: The expression string, e.g. 'slip_count >= 3'
        variables: Dict mapping variable names to their current values

    Returns:
        True if the condition is satisfied, False otherwise

    Raises:
        ConditionEvalError: If the expression is malformed or uses
            unsupported syntax
    """
    if not condition_text or not condition_text.strip():
        return True

    preprocessed = _preprocess(condition_text.strip())

    try:
        tree = ast.parse(preprocessed, mode="eval")
    except SyntaxError as e:
        raise ConditionEvalError(f"Invalid condition syntax: {e}") from e

    return bool(_resolve_node(tree, variables))

from __future__ import annotations
import ast
from typing import Any, Mapping, Literal, overload

Mode = Literal["number", "predicate", "auto"]

@overload
def eval_safe(expr: str, ctx: Mapping[str, Any], *, mode: Literal["number"]) -> int: ...
@overload
def eval_safe(expr: str, ctx: Mapping[str, Any], *, mode: Literal["predicate"]) -> bool: ...
@overload
def eval_safe(expr: str, ctx: Mapping[str, Any], *, mode: Literal["auto"]) -> int | bool: ...

def eval_safe(expr: str, ctx: Mapping[str, Any], *, mode: Mode = "auto") -> int | bool:
    """
    Safe evaluator for rule expressions.
    - Numeric: ints, dotted lookups, + - * //, unary -
    - Predicate: comparisons (== != > < >= <=) over numeric subexpressions
    - No function calls, subscripts, comprehensions, etc.
    """
    node = ast.parse(expr, mode="eval").body

    def resolve_path(path: str) -> Any:
        obj: Any = ctx
        for part in path.split("."):
            obj = obj[part] if isinstance(obj, dict) else getattr(obj, part)
        return obj

    def as_int(val: Any) -> int:
        if isinstance(val, int) and not isinstance(val, bool):
            return val
        raise ValueError(f"non-integer value in expression: {val!r}")

    def num(n: ast.AST) -> int:
        if isinstance(n, ast.Constant):
            v = n.value
            if isinstance(v, int) and not isinstance(v, bool):
                return v
            raise ValueError("only integer literals allowed")
        if isinstance(n, ast.Name):
            return as_int(resolve_path(n.id))
        if isinstance(n, ast.Attribute):
            parts: list[str] = []
            cur: ast.AST = n
            while isinstance(cur, ast.Attribute):
                parts.insert(0, cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.insert(0, cur.id)
            return as_int(resolve_path(".".join(parts)))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -num(n.operand)
        if isinstance(n, ast.BinOp):
            if   isinstance(n.op, ast.Add):      return num(n.left) +  num(n.right)
            elif isinstance(n.op, ast.Sub):      return num(n.left) -  num(n.right)
            elif isinstance(n.op, ast.Mult):     return num(n.left) *  num(n.right)
            elif isinstance(n.op, ast.FloorDiv): return num(n.left) // num(n.right)
        raise ValueError(f"disallowed node in numeric expr: {ast.dump(n)}")

    def pred(n: ast.AST) -> bool:
        # comparisons over numeric sub-expressions, supports chains (a < b < c)
        if isinstance(n, ast.Compare):
            left_val = num(n.left)
            cur = left_val
            for op_node, rhs in zip(n.ops, n.comparators):
                rv = num(rhs)
                if   isinstance(op_node, ast.Eq):    ok = (cur == rv)
                elif isinstance(op_node, ast.NotEq): ok = (cur != rv)
                elif isinstance(op_node, ast.Gt):    ok = (cur >  rv)
                elif isinstance(op_node, ast.Lt):    ok = (cur <  rv)
                elif isinstance(op_node, ast.GtE):   ok = (cur >= rv)
                elif isinstance(op_node, ast.LtE):   ok = (cur <= rv)
                else:
                    raise ValueError(f"disallowed comparison operator: {type(op_node).__name__}")
                if not ok: return False
                cur = rv
            return True
        # allow bare booleans in predicates
        if isinstance(n, ast.Constant) and isinstance(n.value, bool):
            return bool(n.value)
        # treat a bare numeric expression as truthy if != 0
        try:
            return num(n) != 0
        except Exception:
            pass
        raise ValueError(f"disallowed node in predicate: {ast.dump(n)}")

    # Mode dispatch (and auto-infer on top-level node)
    if mode == "number":
        return num(node)
    if mode == "predicate":
        return pred(node)
    # auto
    if isinstance(node, ast.Compare) or (isinstance(node, ast.Constant) and isinstance(node.value, bool)):
        return pred(node)
    return num(node)

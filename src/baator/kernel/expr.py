from __future__ import annotations
import re
import ast
from typing import Any, Callable, Mapping, Literal, overload

Mode = Literal["number", "predicate", "auto"]

from baator.kernel.rng import RNG

DiceResolver = Callable[[str, RNG, Mapping[str, Any]], int]

@overload
def eval_safe(expr: str, ctx: Mapping[str, Any], *, mode: Literal["number"], rng: RNG | None = ..., dice_resolver: DiceResolver | None = ...) -> int: ...
@overload
def eval_safe(expr: str, ctx: Mapping[str, Any], *, mode: Literal["predicate"], rng: RNG | None = ..., dice_resolver: DiceResolver | None = ...) -> bool: ...
@overload
def eval_safe(expr: str, ctx: Mapping[str, Any], *, mode: Literal["auto"], rng: RNG | None = ..., dice_resolver: DiceResolver | None = ...) -> int | bool: ...

_DICE_RE = re.compile(r"^\s*\d+[dD]\d+")
def _parse_expr(expr: str) -> ast.AST:
    if not isinstance(expr, str):
        raise TypeError(f"exected str expression, got {type(expr).__name__}")
    s = expr.strip()
    if _DICE_RE.match(s):
        raise ValueError("dice syntax detected; use roll_expr for NdM expressions")
    try:
        tree = ast.parse(s, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"bad expression syntax {expr!r}") from e
    # Python 3.13+ use ast.Expression
    if not isinstance(tree, ast.Expression):
        raise ValueError("AST parse did not produce an Expression node")
    return tree.body

def eval_safe(expr: str, ctx: Mapping[str, Any], *, mode: Mode = "auto", rng: Any | None = ..., dice_resolver: DiceResolver | None = None) -> int | bool:
    s = expr.strip()
    """
    Safe evaluator for rule expressions.
    - Numeric: ints, dotted lookups, + - * //, unary -
    - Predicate: comparisons (== != > < >= <=) over numeric subexpressions
    - No function calls, subscripts, comprehensions, etc.
    """
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

    if mode in ("number", "auto") and _DICE_RE.match(s):
        if dice_resolver is None:
            raise ValueError("dice syntax detected; provide dice_resolver (e.g. roll_expr)")
        if rng is None:
            raise ValueError("dice evaluation requires rng: pass eval_safe(..., rng=RNG)")
        return int(dice_resolver(s, rng, ctx))

    node = _parse_expr(expr.strip())

    # Mode dispatch (and auto-infer on top-level node)
    if mode == "number":
        return num(node)
    if mode == "predicate":
        return pred(node)

    # auto
    if isinstance(node, ast.Compare):
        return pred(node)
    try:
        return num(node)
    except ValueError:
        return pred(node)

from __future__ import annotations
from typing import Dict, Any, List, Optional
import ast

# --- Tiny safe evaluator for rule steps ---

_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
_ALLOWED_CMPOPS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)
_ALLOWED_UNARYOPS = (ast.USub, ast.UAdd, ast.Not)
_SAFE_FUNCS = {
    "max": max,
    "min": min,
    "abs": abs,
    "round": round,
    "int": int,
    "float": float,
    # clamp(x, lo, hi) -> within [lo, hi]
    "clamp": lambda x, lo, hi: max(lo, min(hi, x)),
}
class UnsafeExpression(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

def _eval_expr(node: ast.AST, ctx: Dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return ctx[node.id]
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        # short-circuiting boolean evaluation
        if isinstance(node.op, ast.And):
            last = False
            for v in node.values:
                res = _eval_expr(v, ctx)
                if not res:
                    return res
                last = res
            return last
        else:  # ast.Or
            last = False
            for v in node.values:
                res = _eval_expr(v, ctx)
                if res:
                    return res
                last = res
            return last
    if isinstance(node, ast.BinOp) and isinstance(node.op, _ALLOWED_BINOPS):
        return _eval_expr(node.left, ctx) + _eval_expr(node.right, ctx) if isinstance(node.op, ast.Add) else \
               _eval_expr(node.left, ctx) - _eval_expr(node.right, ctx) if isinstance(node.op, ast.Sub) else \
               _eval_expr(node.left, ctx) * _eval_expr(node.right, ctx) if isinstance(node.op, ast.Mult) else \
               _eval_expr(node.left, ctx) / _eval_expr(node.right, ctx) if isinstance(node.op, ast.Div) else \
               _eval_expr(node.left, ctx) // _eval_expr(node.right, ctx) if isinstance(node.op, ast.FloorDiv) else \
               _eval_expr(node.left, ctx) % _eval_expr(node.right, ctx) if isinstance(node.op, ast.Mod) else \
               (_eval_expr(node.left, ctx) ** _eval_expr(node.right, ctx))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, _ALLOWED_UNARYOPS):

        v = _eval_expr(node.operand, ctx)
        return -v if isinstance(node.op, ast.USub) else (+v if isinstance(node.op, ast.UAdd) else (not v))
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], _ALLOWED_CMPOPS):
        left = _eval_expr(node.left, ctx)
        right = _eval_expr(node.comparators[0], ctx)
        op = node.ops[0]
        return (left == right) if isinstance(op, ast.Eq) else \
               (left != right) if isinstance(op, ast.NotEq) else \
               (left < right)  if isinstance(op, ast.Lt) else \
               (left <= right) if isinstance(op, ast.LtE) else \
               (left > right)  if isinstance(op, ast.Gt) else \
               (left >= right) # ast.GtE
    if isinstance(node, ast.Attribute):
        # disallow access to private/dunder attributes
        if node.attr.startswith("_"):
            raise UnsafeExpression(f"access to private attribute not allowed: {node.attr}")
        base = _eval_expr(node.value, ctx)
        return getattr(base, node.attr)
    if isinstance(node, ast.Subscript):
        base = _eval_expr(node.value, ctx)
        if isinstance(node.slice, ast.Slice):
            key = slice(
                _eval_expr(node.slice.lower, ctx) if node.slice.lower is not None else None,
                _eval_expr(node.slice.upper, ctx) if node.slice.upper is not None else None,
                _eval_expr(node.slice.step, ctx) if node.slice.step is not None else None,
            )
        else:
            key = _eval_expr(node.slice, ctx)
        return base[key]
    if isinstance(node, ast.Call):
        # allow calls to a small whitelist of pure functions
        if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCS:
            fn = _SAFE_FUNCS[node.func.id]
            args = [_eval_expr(a, ctx) for a in node.args]
            if node.keywords: raise UnsafeExpression('keyword args not allowed')
            return fn(*args)
        raise UnsafeExpression('function call not allowed: ' + getattr(node.func, 'id', '<expr>'))
    raise UnsafeExpression(f"Unsupported expression: {type(node).__name__}")


def _assign(target: ast.AST, value: Any, ctx: Dict[str, Any]) -> None:
    if isinstance(target, ast.Name):
        ctx[target.id] = value
        return
    if isinstance(target, ast.Attribute):
        # disallow assignment to private/dunder attributes
        if target.attr.startswith("_"):
            raise UnsafeExpression(f"assignment to private attribute not allowed: {target.attr}")
        obj = _eval_expr(target.value, ctx)
        setattr(obj, target.attr, value)
        return
    if isinstance(target, ast.Subscript):
        base = _eval_expr(target.value, ctx)
        if isinstance(target.slice, ast.Slice):
            key = slice(
                _eval_expr(target.slice.lower, ctx) if target.slice.lower is not None else None,
                _eval_expr(target.slice.upper, ctx) if target.slice.upper is not None else None,
                _eval_expr(target.slice.step, ctx) if target.slice.step is not None else None,
            )
        else:
            key = _eval_expr(target.slice, ctx)
        base[key] = value
        return
    raise UnsafeExpression(f"Unsupported assignment target: {type(target).__name__}")

def exec_step(step: str, ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Execute a single rule step string in a safe subset of Python.

    Supported forms:
      - assignment:    x = <expr>    or   obj.attr = <expr>
      - augmented:     x += <expr>   (+=, -= only)
      - if conditional: if <expr>: x = <expr>   or x += <expr>
    Returns optional side-effect note dict for logging.
    """
    tree = ast.parse(step, mode='exec')
    if len(tree.body) != 1:
        raise UnsafeExpression("one statement per step")
    stmt = tree.body[0]
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
        val = _eval_expr(stmt.value, ctx)
        _assign(stmt.targets[0], val, ctx)
        return None
    if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, (ast.Add, ast.Sub)):
        cur = _eval_expr(stmt.target, ctx)
        delta = _eval_expr(stmt.value, ctx)
        new = cur + delta if isinstance(stmt.op, ast.Add) else cur - delta
        _assign(stmt.target, new, ctx)
        return None
    if isinstance(stmt, ast.If):
        cond = _eval_expr(stmt.test, ctx)
        if cond:
            if len(stmt.body) != 1:
                raise UnsafeExpression("if body must be one simple statement")
            # recursively handle a simple inner statement
            inner_src = ast.unparse(stmt.body[0]) if hasattr(ast, "unparse") else step.split(":",1)[1].strip()
            return exec_step(inner_src, ctx)
        return None
    raise UnsafeExpression(f"Unsupported statement: {type(stmt).__name__}")

# --- Rule application helpers ---

def apply_yaml_rule(rule: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    log: List[Dict[str, Any]] = []
    for s in rule.get("steps", []):
        exec_step(s, ctx)
        log.append({"step": s})
    return {"rule_id": rule.get("id"), "log": log}

# Back-compat example: simple programmatic resolver used if no YAML rule exists
def resolve_attack(attacker, defender, env: Dict[str, Any]) -> Dict[str, Any]:
    bonus = 1 if env.get("mana", 0) > 0.7 else 0
    dmg = max(0, attacker.power + bonus)
    return {"damage": dmg}

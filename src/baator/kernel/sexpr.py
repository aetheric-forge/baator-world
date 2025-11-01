# baator/kernel/sexpr.py
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Tuple
import ast, re
from .rolls import DICE_REGEX  # your full dice regex

DICE_NAME = "__DICE"

DiceResolver = Callable[[str, str, Mapping[str, Any]], int]

@dataclass(frozen=True)
class ParsedExpr:
    tree: ast.AST                 # ast.Expression.body
    dice_slots: Dict[str, str]    # {"__DICE0": "1d20+STR", ...}

def parse_expression(expr: str) -> ParsedExpr:
    s = expr.strip()
    dice_slots: Dict[str, str] = {}
    out, last, i = [], 0, 0
    for m in DICE_REGEX.finditer(s):
        out.append(s[last:m.start()])
        slot = f"{DICE_NAME}{i}"
        dice_slots[slot] = m.group(0)
        out.append(slot)
        last = m.end(); i += 1
    out.append(s[last:])
    numeric_expr = "".join(out)

    tree = ast.parse(numeric_expr, mode="eval")
    if not isinstance(tree, ast.Expression):
        raise ValueError("parse did not produce Expression")
    return ParsedExpr(tree.body, dice_slots)

def eval_number(request_id: str, parsed: ParsedExpr, ctx: Mapping[str, Any],
                *, resolve_dice: DiceResolver) -> int:
    def resolve_path(path: str) -> Any:
        obj: Any = ctx
        for part in path.split("."):
            obj = obj[part] if isinstance(obj, dict) else getattr(obj, part)
        return obj

    def as_int(v: Any) -> int:
        if isinstance(v, bool): raise ValueError("booleans not allowed in numbers")
        if isinstance(v, int):  return v
        raise ValueError(f"non-int value: {v!r}")

    def num(n: ast.AST) -> int:
        if isinstance(n, ast.Constant): return as_int(n.value)
        if isinstance(n, ast.Name):
            if n.id in parsed.dice_slots:       # ← dice placeholder
                return int(resolve_dice(request_id, parsed.dice_slots[n.id], ctx))
            return as_int(resolve_path(n.id))
        if isinstance(n, ast.Attribute):
            parts=[]; cur=n
            while isinstance(cur, ast.Attribute):
                parts.insert(0, cur.attr); cur = cur.value
            if isinstance(cur, ast.Name): parts.insert(0, cur.id)
            return as_int(resolve_path(".".join(parts)))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub): return -num(n.operand)
        if isinstance(n, ast.BinOp):
            if   isinstance(n.op, ast.Add):      return num(n.left) +  num(n.right)
            elif isinstance(n.op, ast.Sub):      return num(n.left) -  num(n.right)
            elif isinstance(n.op, ast.Mult):     return num(n.left) *  num(n.right)
            elif isinstance(n.op, ast.FloorDiv): return num(n.left) // num(n.right)
        raise ValueError(f"disallowed node: {ast.dump(n)}")

    return num(parsed.tree)

def eval_predicate(request_id: str, parsed: ParsedExpr, ctx: Mapping[str, Any],
                *, resolve_dice: DiceResolver) -> bool:
    def num(n: ast.AST) -> int:
        # reuse from eval_number but closed over parsed/resolve_dice
        return eval_number(request_id, ParsedExpr(n, parsed.dice_slots), ctx, resolve_dice=resolve_dice)

    node = parsed.tree
    if isinstance(node, ast.Compare):
        cur = num(node.left)
        for op, rhs in zip(node.ops, node.comparators):
            rv = num(rhs)
            ok = (isinstance(op, ast.Eq) and cur == rv) or \
                (isinstance(op, ast.NotEq) and cur != rv) or \
                (isinstance(op, ast.Gt) and cur > rv) or \
                (isinstance(op, ast.Lt) and cur < rv) or \
                (isinstance(op, ast.GtE) and cur >= rv) or \
                (isinstance(op, ast.LtE) and cur <= rv)
            if not ok: return False
            cur = rv
        return True
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return bool(node.value)
    # fallback: treat numeric truthiness
    return num(node) != 0

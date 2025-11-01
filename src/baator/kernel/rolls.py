# baator/kernel/rolls.py
from __future__ import annotations
import ast, re
from typing import Any, Mapping, List, Tuple, overload, Literal, TypedDict, Callable
from .rng import RNG

# ---------- Safe arithmetic / predicate evaluator (no dice in here) ----------

Mode = Literal["number", "predicate", "auto"]

def _parse_expr(expr: str) -> ast.AST:
    if not isinstance(expr, str):
        raise TypeError(f"expected str expression, got {type(expr).__name__}")
    s = expr.strip()
    try:
        tree = ast.parse(s, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"bad expression syntax {expr!r}") from e
    if not isinstance(tree, ast.Expression):
        raise ValueError("AST parse did not produce an Expression node")
    return tree.body

def eval_safe(expr: str, ctx: Mapping[str, Any], *, mode: Mode = "auto") -> int | bool:
    """
    Safe evaluator for rule expressions (no dice tokens).
    - number: ints, dotted lookups, + - * //, unary -
    - predicate: comparisons over numeric subexpressions; bare bools/ints truthiness
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
            parts: List[str] = []
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
        if isinstance(n, ast.Compare):
            cur = num(n.left)
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
        if isinstance(n, ast.Constant) and isinstance(n.value, bool):
            return bool(n.value)
        try:
            return num(n) != 0
        except Exception:
            raise ValueError(f"disallowed node in predicate: {ast.dump(n)}")

    s = str(expr)
    s = s.strip()
    node = _parse_expr(s)
    if mode == "number":     return num(node)
    if mode == "predicate":  return pred(node)
    # auto: try numeric, fall back to predicate
    try: return num(node)
    except ValueError: return pred(node)

# ---------- Dice roller (supports kh/kl + ctx-aware modifiers) ----------

class RollDetail(TypedDict):
    expr: str
    result: int
    faces: List[int]     # all dice rolled
    kept: List[int]      # dice that counted (after kh/kl)
    modifier: int        # resolved modifier

DICE_REGEX = re.compile(
    r"""
    ^\s*
    (?P<count>\d+)[dD](?P<sides>\d+)
    (?:k(?P<keep_mode>[hl])?(?P<keep>\d+))?          # kh1 / kl1 / k3 (default high)
    (?:\s*(?P<sign>[+-])\s*(?P<modifier>(?:\d+|[A-Za-z_][\w.]*)))?
    \s*$
    """,
    re.VERBOSE,
)

def _resolve_modifier(sign: str | None, modraw: str | None, ctx: Mapping[str, Any] | None) -> int:
    if not sign or not modraw:
        return 0
    m = modraw.strip()
    if m.isdigit():
        val = int(m)
    else:
        if ctx is None:
            raise ValueError(f"dice modifier '{m}' requires context")
        val = int(eval_safe(m, ctx, mode="number"))
    return val if sign == "+" else -val

def _roll_expr_detail(expr: str, rng: RNG, *, ctx: Mapping[str, Any] | None
    ) -> Tuple[int, List[int], List[int], int]:
    m = DICE_REGEX.match(expr)
    if not m:
        raise ValueError(f"bad dice expression: {expr!r}")

    n      = int(m.group("count"))
    sides  = int(m.group("sides"))
    keep_s = m.group("keep")
    keep_m = (m.group("keep_mode") or "h")
    sign   = m.group("sign")
    modraw = m.group("modifier")

    faces = [rng.roll(sides) for _ in range(n)]
    if keep_s is not None:
        k = max(0, min(int(keep_s), n))
        kept = sorted(faces, reverse=(keep_m == "h"))[:k] if k else []
    else:
        kept = list(faces)

    subtotal = sum(kept)
    mod      = _resolve_modifier(sign, modraw, ctx)
    return subtotal + mod, faces, kept, mod

from typing import Mapping, Any

def is_dice_expr(expr: str) -> bool:
    return bool(DICE_REGEX.match(expr.strip()))  # _R = your dice regex

@overload
def roll_expr(expr: str, rng: RNG, *, ctx: Mapping[str, Any] | None = None, verbose: Literal[False] = False) -> int: ...

@overload
def roll_expr(expr: str, rng: RNG, *, ctx: Mapping[str, Any] | None = None, verbose: Literal[True]) -> RollDetail: ...

def roll_expr(expr: str, rng: RNG, *, ctx: Mapping[str, Any] | None = None, verbose: bool = False) -> int | RollDetail:
    total, faces, kept, mod = _roll_expr_detail(expr, rng, ctx=ctx)
    if not verbose:
        return total
    return RollDetail(expr=expr, result=total, faces=faces, kept=kept, modifier=mod)

def number_from(expr: str, rng: RNG, *, ctx: Mapping[str, Any] | None = None, verbose: bool = False) -> int:
    """
    Return an integer for either:
      - dice expressions (roll via RNG), or
      - plain numeric/path/arithmetic (eval via eval_safe).
    """
    s = expr.strip()
    if is_dice_expr(s):
        res = roll_expr(s, rng, ctx=ctx or {}, verbose=verbose)
        return res if isinstance(res, int) else int(res["result"])
    # not dice → evaluate safely as number (supports dotted paths)
    return int(eval_safe(s, ctx or {}, mode="number"))


# Sugar helpers: express adv/dis as data
def expr_adv(sides: int) -> str: return f"2d{sides}kh1"
def expr_dis(sides: int) -> str: return f"2d{sides}kl1"

# If you need a resolver type for injection points:
DiceResolver = Callable[[str, RNG, Mapping[str, Any], bool], int | RollDetail]

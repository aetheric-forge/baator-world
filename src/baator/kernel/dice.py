    # ----- imperative API (services can call directly) -----
import re
from typing import Any, Mapping, Optional, Protocol

from .expr import eval_safe
from .rng import RNG

R = re.compile(
    r"""
    ^\s*                             # optional leading spaces
    (?P<count>\d+)                   # number of dice, e.g. 3
    [dD]
    (?P<sides>\d+)                   # die faces, e.g. 6 or 20
    (?:                              # optional modifier group
        (?P<sign>[+-])\s*               # + or -
        (?P<modifier>
            (?:\d+|                  #  ...a plain integer
             [A-Za-z_][\w.]*         #  ...or dotted identifier path
            )
        )
    )?
    \s*$                             # optional trailing spaces
    """,
    re.VERBOSE,
)

def _resolve_modifier(sign: str | None, modraw: str | None, ctx: Mapping[str, Any] | None) -> int:
    if not sign or not modraw:
        return 0
    # numeric literal fast path
    modraw = modraw.strip()
    if modraw.isdigit():
        val = int(modraw)
    else:
        if ctx is None:
            raise ValueError(f"dice modifier '{modraw}' requires context")
        # evaluate dotted path / arithmetic safely as an integer
        val = int(eval_safe(modraw, ctx, mode="number"))
    return val if sign == "+" else -val

def roll_expr_detail(expr: str, rng: RNG, ctx: Mapping[str, Any]={}) -> tuple[int, list[int], int]:
        m = R.match(expr)
        if not m:
            raise ValueError("dice expr like '3d6+2' expected")
        count = int(m.group("count"))
        sides = int(m.group("sides"))
        sign = m.group("sign")
        modraw = m.group("modifier")
        faces = [rng.roll(sides) for _ in range(count)]
        mod = _resolve_modifier(sign, modraw, ctx)
        return sum(faces) + mod, faces, mod

def roll_expr(expr: str, rng: RNG, ctx: Mapping[str, Any] = {}) -> int:
    total, _, _ = roll_expr_detail(expr, rng, ctx)
    return total

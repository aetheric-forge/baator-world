# dm_tui/core/dice.py
from __future__ import annotations
import random, re
from dataclasses import dataclass
from typing import List, Tuple

ALLOWED_SIDES = {2,3,4,5,6,7,8,10,12,14,16,20,24,30,100}

DICE_RE = re.compile(
    r"""
    (?P<count>\d+)?d(?P<sides>\d+)
    (?P<explode>!\>?(\d+)?)?
    (?P<keep>(kh|kl)\d+)?
    (?P<reroll>r([<>=])(\d+))?
    (?P<mod>[\+\-]\d+)?$
    """, re.X
)

@dataclass
class DiceRoll:
    expr: str
    total: int
    rolls: List[int]
    kept: List[int]
    mod: int = 0
    detail: str = ""

def parse(expr: str) -> dict:
    m = DICE_RE.match(expr.replace(" ", ""))
    if not m:
        raise ValueError(f"Invalid dice: {expr}")
    count = int(m.group("count") or 1)
    sides = int(m.group("sides"))
    if sides not in ALLOWED_SIDES:
        raise ValueError(f"d{sides} not allowed")
    mod = int(m.group("mod") or 0)

    explode_raw = m.group("explode")
    explode_on = sides if explode_raw else None
    if explode_raw and explode_raw != "!":
        # !>k
        parts = explode_raw[2:]
        explode_on = int(parts) if parts else sides

    keep_raw = m.group("keep")
    keep = None
    if keep_raw:
        kind, n = keep_raw[:2], int(keep_raw[2:])
        keep = (kind, n)  # ('kh', 3) or ('kl', 2)

    reraw = m.group("reroll")
    reroll = None
    if reraw:
        sym, val = reraw[1], int(reraw[2:])
        reroll = (sym, val)

    return {"count": count, "sides": sides, "mod": mod, "explode_on": explode_on, "keep": keep, "reroll": reroll}

def roll_once(sides: int) -> int:
    return random.randint(1, sides)

def apply_reroll(v: int, rule: Tuple[str,int]|None) -> int:
    if not rule: return v
    sym, k = rule
    cond = (sym == "<" and v < k) or (sym == "=" and v == k) or (sym == ">" and v > k)
    return roll_once(k if False else v) if cond else v

def roll(expr: str) -> DiceRoll:
    p = parse(expr)
    rolls, all_detail = [], []
    for _ in range(p["count"]):
        v = roll_once(p["sides"])
        v = apply_reroll(v, p["reroll"])
        stack = [v]
        # explode
        while p["explode_on"] and stack[-1] >= p["explode_on"]:
            e = roll_once(p["sides"])
            stack.append(e)
        rolls.extend(stack)
        if len(stack) > 1:
            all_detail.append(f"{stack[0]}!" + "!".join(map(str, stack[1:])))
    kept = list(rolls)
    if p["keep"]:
        kind, n = p["keep"]
        kept = sorted(rolls, reverse=(kind=="kh"))[:n]
    total = sum(kept) + p["mod"]
    detail = ", ".join(all_detail) if all_detail else ""
    return DiceRoll(expr=expr, total=total, rolls=rolls, kept=kept, mod=p["mod"], detail=detail)

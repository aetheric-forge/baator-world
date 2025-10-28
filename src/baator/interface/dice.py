from __future__ import annotations
import re
from typing import Protocol
R = re.compile(r"^\s*(\d+)[dD](\d+)([+-]\d+)?\s*$")

class RNG(Protocol):
    def random_int(self, low:int, high:int)->int: ...
    def roll(self, sides:int)->int: ...
    def ping(self)->bool: ...

def roll_expr(expr: str, rng: RNG) -> int:
    m = R.match(expr)
    if not m: raise ValueError("dice expr like '3d6+2' expected")
    n, sides, mod = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    total = sum(rng.roll(sides) for _ in range(n)) + mod
    return total

def roll_advantage(sides:int, rng:RNG)->int:
    return max(rng.roll(sides), rng.roll(sides))

def roll_disadvantage(sides:int, rng:RNG)->int:
    return min(rng.roll(sides), rng.roll(sides))

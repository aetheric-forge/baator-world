from __future__ import annotations
import secrets

class PythonRNG:
    def random_int(self, low: int, high: int) -> int:
        if low > high: low, high = high, low
        # inclusive both ends
        span = (high - low) + 1
        return low + secrets.randbelow(span)

    def roll(self, sides: int) -> int:
        if sides < 1:
            raise ValueError("sides must be >= 1")
        return 1 + secrets.randbelow(sides)

    def ping(self) -> bool:
        return True

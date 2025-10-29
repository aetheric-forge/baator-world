# baator/kernel/rng.py
from typing import Protocol

class RNG(Protocol):
    """Protocol for RNG providers used throughout the Baator engine."""

    def ping(self) -> bool:
        """Optional health check."""
        ...

    def random_int(self, low: int, high: int) -> int:
        """Return an integer in [low, high], inclusive."""
        ...

    def roll(self, sides: int) -> int:
        """Roll a die with the given number of sides, returning a value in [1, sides]."""
        ...

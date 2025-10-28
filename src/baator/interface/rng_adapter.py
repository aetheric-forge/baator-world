# Interface-level adapter wrapping a concrete RNG transport (socket, http, etc.)
from typing import Protocol

class RNG(Protocol):
    def random_int(self, low: int, high: int) -> int:
        ...

# The SocketRNGAdapter from kernel.event_bus can be used here.

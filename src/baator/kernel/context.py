# interface/context.py (or kernel/context.py)
from typing import Protocol, Mapping, Any

class ContextProvider(Protocol):
    def resolve(self, meta: Mapping[str, Any] | None) -> Mapping[str, Any] | None : ...

from typing import Callable, Dict
from .commands import Command


Handler = Callable[[Command], None]

class CommandBus:
    def __init__(self)-> None:
        self._handlers: Dict[str, Handler] = {}

    def register(self, name: str, fn: Handler) -> None:
        if name in self._handlers:
            raise ValueError(f"Command handler already registered for {name}")
        self._handlers[name] = fn

    def dispatch(self, cmd: Command) -> None:
        fn = self._handlers.get(cmd.name)
        if not fn:
            raise KeyError(f"No handler for command {cmd.name}")
        fn(cmd)

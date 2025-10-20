from __future__ import annotations
from typing import List, Callable
from .base import CommandSpec, REGISTRY, CommandFn

def command(name: str, *, help: str = "", usage: str = "", aliases: List[str] | None = None):
    def wrap(fn: CommandFn) -> CommandFn:
        REGISTRY.register(CommandSpec(name=name, fn=fn, help=help, usage=usage, aliases=aliases or []))
        return fn
    return wrap

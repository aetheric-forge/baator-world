from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Protocol

# What the command code sees
@dataclass
class CommandContext:
    app: "DMApp"                      # type: ignore (Textual app)
    ui_log: Callable[[str], None]
    controller: "BaatorController"    # type: ignore

# Command function signature
class CommandFn(Protocol):
    def __call__(self, ctx: CommandContext, args: List[str]) -> None: ...

@dataclass
class CommandSpec:
    name: str
    fn: CommandFn
    help: str = ""
    usage: str = ""
    aliases: List[str] = None

class CommandRegistry:
    def __init__(self) -> None:
        self._by_name: Dict[str, CommandSpec] = {}
        self._alias_to_name: Dict[str, str] = {}

    def register(self, spec: CommandSpec) -> None:
        if spec.name in self._by_name:
            raise ValueError(f"duplicate command: {spec.name}")
        spec.aliases = spec.aliases or []
        self._by_name[spec.name] = spec
        for a in spec.aliases:
            self._alias_to_name[a] = spec.name

    def resolve(self, name: str) -> Optional[CommandSpec]:
        return self._by_name.get(name) or self._by_name.get(self._alias_to_name.get(name, ""))

    def all_specs(self) -> List[CommandSpec]:
        return sorted(self._by_name.values(), key=lambda s: s.name)

# global singleton (simple, effective)
REGISTRY = CommandRegistry()

# dm_tui/command_api.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any, Optional, Dict, Callable
from collections import defaultdict

@dataclass
class CommandContext:
    app: Any
    bus: Any
    cbus: Any
    engine: Any
    sim: Any
    get_state: Callable[[str, str], dict]
    # registry will supply: ctx.get_state(handler_name, state_id)

class CommandHandler(Protocol):
    name: str
    def help(self) -> str: ...
    def parse(self, argv: list[str]) -> tuple[dict, str]: ...
    # returns (parsed_args, state_id) — state_id can be "default"
    def run(self, ctx: CommandContext, args: dict, state: dict) -> str | None: ...

class CommandRegistry:
    def __init__(self):
        self._by_name: Dict[str, CommandHandler] = {}
        self._state: Dict[str, Dict[str, dict]] = defaultdict(dict)  # handler -> state_id -> state
        self._base_ctx: Optional[CommandContext] = None

    def set_base_context(self, *, app, bus, cbus, engine, sim) -> None:
        self._base_ctx = CommandContext(
            app=app, bus=bus, cbus=cbus, engine=engine, sim=sim,
            get_state=self.get_state
        )

    def register(self, handler: CommandHandler) -> None:
        self._by_name[handler.name] = handler

    def get_state(self, handler_name: str, state_id: str = "default") -> dict:
        return self._state[handler_name].setdefault(state_id, {})

    def dispatch_line(self, line: str, base_ctx: Optional[CommandContext] = None) -> str | None:
        ctx = base_ctx or self._base_ctx
        if ctx is None:
            return "command registry not initialized"

        s = line.strip()
        if not s.startswith("/"): return None
        toks = s[1:].split()
        if not toks: return None
        name, argv = toks[0], toks[1:]

        # built-in help command
        if name == "help":
            if argv and argv[0] in self._by_name:
                return self._by_name[argv[0]].help()
            # global help
            lines = ["/help <command>  — show command help", ""]
            for k in sorted(self._by_name):
                lines.append(f"/{k}  — {self._by_name[k].help().splitlines()[0]}")
            return "\n".join(lines)

        h = self._by_name.get(name)
        if not h:
            return f"unknown command: {name}"

        args, state_id = h.parse(argv)
        local_state = self.get_state(h.name, state_id or "default")
        # augment context with state accessor
        return h.run(ctx, args, local_state)

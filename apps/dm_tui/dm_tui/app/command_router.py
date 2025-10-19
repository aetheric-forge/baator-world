from __future__ import annotations
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from dm_tui.ui import DMApp
    from dm_tui.commands import BaseCommand

class CommandRouter:
    def  __init__(self):
        self.handlers: dict[str, Type[BaseCommand]] = {}

    def register_command(self, app: "DMApp", key: str, cmd_cls: Type[BaseCommand]):
        self.handlers[key] = cmd_cls

    def dispatch(self, app: "DMApp", line: str) -> None:
        parts = line.strip().split()
        if not parts:
            return
        cmd_key = parts[0]
        args = parts[1:]

        cmd_cls = self.handlers.get(cmd_key)
        if cmd_cls:
            command = cmd_cls(app, args)
            command.execute()
        else:
            app.ui_log(f"Unknown command: {cmd_key}")

from __future__ import annotations
from typing import TYPE_CHECKING
from .base_command import BaseCommand

if TYPE_CHECKING:
    from dm_tui.ui import DMApp

class HelpCommand(BaseCommand):
    def __init__(self, app: "DMApp", args: list[str]):
        super().__init__(app, args)

    def execute(self) -> None:
        lines = ["Available commands:"]
        for cmd_key in sorted(self.app.router.handlers.keys()):
            lines.append(f"  • {cmd_key}")
        self.app.ui_log("\n".join(lines))

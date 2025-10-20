# apps/dm_tui/dm_tui/commands/rules_command.py
from __future__ import annotations
from .base_command import BaseCommand

class RulesCommand(BaseCommand):
    key = "rules"
    help = "list rule IDs and a peek at their steps"

    def execute(self) -> None:
        try:
            info = self.app.controller.rules_summary()
            self.app.ui_log(info)
        except Exception as e:
            self.app.ui_log(f"rules error: {e}")

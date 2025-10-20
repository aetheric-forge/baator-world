from __future__ import annotations
import shlex
from typing import List
from ..commands.base import CommandContext, REGISTRY

class CommandRouter:
    def __init__(self, app) -> None:
        self.app = app

    def dispatch(self, line: str) -> None:
        line = line.strip()
        if not line:
            return
        # Optional leading slash
        if line.startswith("/"):
            line = line[1:]
        try:
            tokens = shlex.split(line)
        except ValueError as e:
            self.app.ui_log(f"parse error: {e}")
            return
        if not tokens:
            return
        name, args = tokens[0], tokens[1:]
        spec = REGISTRY.resolve(name)
        if not spec:
            self.app.ui_log(f"Unknown command: {name}")
            return
        ctx = CommandContext(app=self.app, ui_log=self.app.ui_log, controller=self.app.controller)
        try:
            spec.fn(ctx, args)
        except Exception as e:
            self.app.ui_log(f"{name} error: {e}")


from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dm_tui.ui import DMApp

class BaseCommand:
    @property
    def app(self) -> DMApp:
        return self._app

    def __init__(self, app: DMApp, args: list[str]):
        self._app = app
        self.args = args

    def execute(self) -> None:
        pass

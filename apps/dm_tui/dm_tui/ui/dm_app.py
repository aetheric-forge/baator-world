from __future__ import annotations
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Log, Static
from textual.reactive import reactive

from ..commands import AutoRunCommand, BaseCommand, HelpCommand, LoadPackCommand, QuitCommand, RollCommand, RuleCommand, RulesCommand, SceneStartCommand, TickCommand
from ..app.command_router import CommandRouter
from ..app.baator_bridge import BaatorController

import os
APP_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, "../../../.."))

class DMApp(App):
    CSS_PATH = "dm_tui.css"
    TITLE = "Baator DM Console"
    SUB_TITLE = "Textual prototype"

    command_line = reactive("")  # current input line

    def __init__(self):
        super().__init__()
        self.commands: dict[str, type[BaseCommand]] = {
            "help": HelpCommand,
            "quit": QuitCommand,
            "roll": RollCommand,
            "loadpack": LoadPackCommand,
            "scene": SceneStartCommand,
            "tick": TickCommand,
            "run": AutoRunCommand,
            "rule": RuleCommand,
            "rules": RulesCommand,
        }
        self.router = CommandRouter()
        self.controller = BaatorController(root=PROJECT_ROOT, world_name="dm_sandbox")
        for key, command in self.commands.items():
            self.router.register_command(self, key, command)

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Horizontal():
                yield Static("🜏", id="prompt")
                yield Input(placeholder="Enter command...", id="cmd_input")
            yield Log(id="log", highlight=True, auto_scroll=True)
        yield Footer()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def ui_log(self, message: str):
        log: Log = self.query_one("#log", Log)
        output: str = f"{message.rstrip()}\n"
        log.write(output)
        log.scroll_end(animate=False)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_mount(self):
        cmd_input = self.query_one("#cmd_input")
        # Ensure it's focused and visible
        cmd_input.focus()
        cmd_input.styles.background = "black"
        cmd_input.styles.color = "white"
        cmd_input.refresh()
        self.ui_log("Welcome to the Baator DM console. Type 'help'.")

    @on(Input.Submitted, "#cmd_input")
    def on_input_submitted(self, event: Input.Submitted):
        cmdline = event.value.strip()
        event.input.value = ""
        if not cmdline:
            return
        self.ui_log(f"> {cmdline}")
        self.router.dispatch(self, cmdline)

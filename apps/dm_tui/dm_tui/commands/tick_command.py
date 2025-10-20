from .base_command import BaseCommand

class TickCommand(BaseCommand):
    key = "tick"
    help = "/tick [n] – advance n ticks (default 1)"

    def execute(self) -> None:
        n = 1
        if self.args:
            try:
                n = max(1, int(self.args[0]))
            except ValueError:
                pass
        try:
            log = self.app.controller.tick(n)
            for e in log:
                self.app.ui_log(str(e))
        except Exception as e:
            self.app.ui_log(f"tick error: {e}")

from .base_command import BaseCommand

class AutoRunCommand(BaseCommand):
    key = "run"
    help = "/run [max_ticks] – run scene with engine auto-resolve"

    def execute(self) -> None:
        mt = 20
        if self.args:
            try:
                mt = max(1, int(self.args[0]))
            except ValueError:
                pass
        try:
            log = self.app.controller.run_auto(max_ticks=mt)
            for e in log:
                self.app.ui_log(str(e))
        except Exception as e:
            self.app.ui_log(f"run error: {e}")

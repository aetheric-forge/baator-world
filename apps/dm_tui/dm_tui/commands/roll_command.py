# dm_tui/commands/roll_command.py
from ..core.dice import roll, DiceRoll
from .base_command import BaseCommand

class RollCommand(BaseCommand):
    """roll 2d6+1, d5, 4d6kh3; supports ! explode, kh/kl keep, r<k reroll"""
    def execute(self) -> None:
        args = " ".join(self.args).replace(" ", "")
        if not args:
            self.app.ui_log("Usage: roll <expr>[,expr...]  e.g. roll 4d6kh3, d5")
            return
        for expr in args.split(","):
            try:
                r: DiceRoll = roll(expr)
                kept = f" kept={r.kept}" if r.kept != r.rolls else ""
                mod = f" {'+' if r.mod>=0 else ''}{r.mod}" if r.mod else ""
                extra = f"  explosions: {r.detail}" if r.detail else ""
                self.app.ui_log(f"{expr} → {r.total}  rolls={r.rolls}{kept}{mod}{extra}")
            except Exception as e:
                self.app.ui_log(f"{expr}: {e}")

from __future__ import annotations
from typing import List
from ..base import CommandContext
from ..decorators import command

@command("run", help="Auto-run scene.", usage="run [max_ticks]")
def run_cmd(ctx: CommandContext, args: List[str]) -> None:
    mt = 20
    if args:
        try: mt = max(1, int(args[0]))
        except ValueError: pass
    for e in ctx.controller.run_auto(mt):
        ctx.ui_log(str(e))

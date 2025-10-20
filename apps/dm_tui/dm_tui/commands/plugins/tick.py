from __future__ import annotations
from typing import List
from ..base import CommandContext
from ..decorators import command

@command("tick", help="Advance N ticks (default 1).", usage="tick [n]")
def tick_cmd(ctx: CommandContext, args: List[str]) -> None:
    n = 1
    if args:
        try: n = max(1, int(args[0]))
        except ValueError: pass
    for e in ctx.controller.tick(n):
        ctx.ui_log(str(e))

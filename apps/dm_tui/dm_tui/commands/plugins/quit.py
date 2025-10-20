from __future__ import annotations
from typing import List
from ..base import CommandContext, REGISTRY
from ..decorators import command

@command("quit", help="Exit the program.", usage="quit", aliases=["exit", "q"])
def quit_cmd(ctx: CommandContext, args: List[str]) -> None:
    ctx.app.exit()

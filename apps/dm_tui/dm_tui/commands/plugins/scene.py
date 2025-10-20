from __future__ import annotations
from typing import List
from ..base import CommandContext
from ..decorators import command

@command("scene", help="Scene operations.", usage="scene start <name> <actor...>", aliases=["/scene"])
def scene_cmd(ctx: CommandContext, args: List[str]) -> None:
    if not args:
        ctx.ui_log("usage: scene start <name> <actor...>"); return
    sub = args[0]
    if sub == "start" and len(args) >= 3:
        name = args[1]; actors = args[2:]
        sid = ctx.controller.start_scene(name, actors)
        ctx.ui_log(f"Scene '{name}' started (id={sid}) with actors: {', '.join(actors)}")
    else:
        ctx.ui_log("usage: scene start <name> <actor...>")

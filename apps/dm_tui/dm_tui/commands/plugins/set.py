from __future__ import annotations
from typing import List
from ..base import CommandContext
from ..decorators import command

@command("set", help="Set actor stats or env mana.", usage="set actor <Name> key=value... | set env mana=<float>")
def set_cmd(ctx: CommandContext, args: List[str]) -> None:
    if not args: ctx.ui_log("usage: set actor <Name> key=value... | set env mana=<float>"); return
    target = args[0]
    if target == "actor" and len(args) >= 3:
        name = args[1]
        a = ctx.controller._actor_by_name(name)
        for pair in args[2:]:
            if "=" in pair:
                k, v = pair.split("=", 1)
                try:
                    v = int(v)
                except ValueError:
                    try: v = float(v)
                    except ValueError: pass
                setattr(a, k, v)
        ctx.ui_log(f"Updated {a.name}: hp={a.hp}, power={a.power}")
    elif target == "env":
        for pair in args[1:]:
            if pair.startswith("mana="):
                try:
                    val = float(pair.split("=",1)[1])
                except ValueError:
                    ctx.ui_log("mana must be a number"); return
                if hasattr(ctx.controller, "set_env_mana"):
                    ctx.controller.set_env_mana(val)
        ctx.ui_log(f"env.mana={ctx.controller.get_env_mana()}")
    else:
        ctx.ui_log("usage: set actor <Name> key=value... | set env mana=<float>")

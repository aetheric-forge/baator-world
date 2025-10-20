from __future__ import annotations
from typing import List
from ..base import CommandContext, REGISTRY
from ..decorators import command

@command("help", help="Show commands and usage.", usage="help [name]")
def help_cmd(ctx: CommandContext, args: List[str]) -> None:
    if args:
        name = args[0]
        spec = REGISTRY.resolve(name)
        if not spec:
            ctx.ui_log(f"No such command: {name}")
            return
        alias_str = f" (aliases: {', '.join(spec.aliases)})" if spec.aliases else ""
        ctx.ui_log(f"{spec.name}{alias_str}\n  {spec.help}\n  usage: {spec.usage or spec.name}")
        return
    lines = ["Commands:"]
    for s in REGISTRY.all_specs():
        alias_str = f" [{', '.join(s.aliases)}]" if s.aliases else ""
        lines.append(f"  • {s.name}{alias_str} – {s.help}")
    ctx.ui_log("\n".join(lines))

from __future__ import annotations
from typing import List
from ..base import CommandContext
from ..decorators import command

@command("rule", help="Apply a rule with bindings.", usage="rule <id> key=value ...")
def rule_cmd(ctx: CommandContext, args: List[str]) -> None:
    if not args:
        ctx.ui_log("usage: rule <id> key=value ..."); return
    rid, kvs = args[0], args[1:]
    bindings = {}
    for pair in kvs:
        if "=" in pair:
            k, v = pair.split("=", 1)
            try:
                v = int(v)
            except ValueError:
                try: v = float(v)
                except ValueError: pass
            bindings[k] = v
    res = ctx.controller.apply_rule(rid, **bindings)
    ctx.ui_log(str(res))

# apps/dm_tui/dm_tui/commands/expect.py
from __future__ import annotations
from typing import List
from ..base import CommandContext
from ..decorators import command

@command("expect", help="Simulate a rule without changing state.",
         usage="expect <rule_id> <attacker> <defender> [mana=0.8]")
def expect_cmd(ctx: CommandContext, args: List[str]) -> None:
    if len(args) < 3:
        ctx.ui_log("usage: expect <rule_id> <attacker> <defender> [mana=0.x]")
        return
    rid, atk, dfd, *rest = args
    env = {}
    for pair in rest:
        if "=" in pair:
            k, v = pair.split("=", 1)
            try:
                v = float(v) if k == "mana" else v
            except ValueError:
                pass
            env[k] = v
    data = ctx.controller.simulate_rule(rid, atk, dfd, env_overrides=env or None)
    # Pretty-ish, but still one line per call
    ctx.ui_log(
        f"{data['rule_id']} {atk}->{dfd}  "
        f"hp {data['before']['defender_hp']}→{data['after']['defender_hp']}  "
        f"pred_damage={data['predicted_damage']}  env={data['before']['env']}"
    )

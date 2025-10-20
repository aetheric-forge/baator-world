# apps/dm_tui/dm_tui/commands/verify.py
from __future__ import annotations
from typing import List
from ..base import CommandContext
from ..decorators import command

@command("verify", help="Compare predicted vs actual damage per tick.",
         usage="verify <rule_id> [ticks]")
def verify_cmd(ctx: CommandContext, args: List[str]) -> None:
    if not args:
        ctx.ui_log("usage: verify <rule_id> [ticks]"); return
    rid = args[0]
    t = 5
    if len(args) > 1:
        try: t = max(1, int(args[1]))
        except ValueError: pass
    rows = ctx.controller.verify_ticks(rid, t)
    for r in rows:
        status = "✓" if r["ok"] else "✗"
        ctx.ui_log(
            f"[{status}] tick {r['tick']}: {r['atk']}→{r['dfd']}  "
            f"pred={r['pred_damage']} actual={r['actual_damage']}  "
            f"hp {r['dfd_hp_before']}→{r['dfd_hp_after']}"
        )

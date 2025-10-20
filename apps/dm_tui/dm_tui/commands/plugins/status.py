from __future__ import annotations
from typing import List
from ..base import CommandContext
from ..decorators import command

@command("status", help="Show active scene, actors, and env.", usage="status")
def status_cmd(ctx: CommandContext, args: List[str]) -> None:
    w = ctx.controller.world
    sid = getattr(w.state, "active_scene_id", None) or getattr(ctx.controller, "_last_scene_id", None)
    if not sid:
        ctx.ui_log("No active scene."); return
    scn = w.state.scenes[sid]
    lines = [f"Scene: {scn.name} (turn {scn.turn})"]
    for aid in scn.actors:
        a = w.state.actors[aid.value]
        lines.append(f" - {a.name}: hp={a.hp}, power={a.power}, faction={a.faction_id.value if a.faction_id else '-'}")
    mana = ctx.controller.get_env_mana() if hasattr(ctx.controller, "get_env_mana") else 0.5
    lines.append(f"env.mana={mana}")
    ctx.ui_log("\n".join(lines))

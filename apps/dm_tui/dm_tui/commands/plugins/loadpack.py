from __future__ import annotations
from typing import List
from ..base import CommandContext
from ..decorators import command

@command("loadpack", help="Load a content pack.", usage="loadpack <pack_name>")
def loadpack_cmd(ctx: CommandContext, args: List[str]) -> None:
    if not args:
        ctx.ui_log("usage: loadpack <pack_name>"); return
    report = ctx.controller.load_pack(args[0])
    ctx.ui_log(f"Loaded pack '{args[0]}': {report['factions']} factions, {report['planes']} planes, {report['rules']} rules.")

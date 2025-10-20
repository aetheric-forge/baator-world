from __future__ import annotations
from typing import List
from ..base import CommandContext
from ..decorators import command

@command("rules", help="List all loaded rule IDs or inspect one rule.", usage="rules [rule_id]")
def rules_cmd(ctx: CommandContext, args: List[str]) -> None:
    meta = getattr(ctx.controller.world, "meta", {})
    rules = meta.get("rules")
    if not rules:
        ctx.ui_log("No rules loaded.")
        return

    # List all rules
    if not args:
        lines = [f"Loaded {len(rules)} rule(s):"]
        for r in rules:
            if not isinstance(r, dict):
                continue
            rid = r.get("id", "<no id>")
            name = r.get("name", "")
            lines.append(f" - {rid} {f'({name})' if name else ''}")
        ctx.ui_log("\n".join(lines))
        return

    # Show details for one rule
    rid = args[0]
    rule = next((r for r in rules if isinstance(r, dict) and r.get("id") == rid), None)
    if not rule:
        ctx.ui_log(f"Rule not found: {rid}")
        return

    lines = [f"Rule: {rule.get('id', '<no id>')}"]
    if "name" in rule:
        lines.append(f"  name: {rule['name']}")
    steps = rule.get("steps", [])
    if isinstance(steps, list):
        lines.append("  steps:")
        for s in steps:
            lines.append(f"    - {s if isinstance(s, str) else str(s)}")
    else:
        lines.append(f"  steps: {steps}")
    ctx.ui_log("\n".join(lines))

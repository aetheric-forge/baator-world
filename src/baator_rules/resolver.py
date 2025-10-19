from __future__ import annotations
from typing import Dict, Any
from baator_core.entities import Actor, Scene

def resolve_attack(attacker: Actor, defender: Actor, env: Dict[str, Any]) -> Dict[str, Any]:
    # Extremely simple: damage = attacker.power (+1 if env['mana'] > 0.7)
    bonus = 1 if env.get("mana", 0) > 0.7 else 0
    dmg = max(0, attacker.power + bonus)
    return {"damage": dmg}
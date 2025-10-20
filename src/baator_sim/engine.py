from __future__ import annotations
import random
from typing import List, Dict, Any, Optional
from baator_services.world import WorldService
from baator_rules.resolver import resolve_attack, apply_yaml_rule

def _find_rule(world: WorldService, rule_id: str) -> Optional[Dict[str, Any]]:
    rules = getattr(world, "_meta", {}).get("rules", [])
    for r in rules:
        if r.get("id") == rule_id:
            return r
    return None

def run_scene(world: WorldService, scene_id: str, *, seed: int = 1337, max_ticks: int = 6) -> List[Dict[str, Any]]:
    rnd = random.Random(seed)
    log: List[Dict[str, Any]] = []
    scene = world.state.scenes[scene_id]
    if len(scene.actors) < 2:
        log.append({"tick": 0, "event": "insufficient_actors"})
        return log

    order = list(scene.actors)
    ticks = 0
    while ticks < max_ticks and len(order) >= 2:
        a_idx = ticks % len(order)
        d_idx = (ticks + 1) % len(order)
        attacker_id = order[a_idx].value
        defender_id = order[d_idx].value
        atk = world.state.actors[attacker_id]
        dfd = world.state.actors[defender_id]

        env = {"mana": 0.5}

        # Prefer YAML rule if available
        yaml_rule = _find_rule(world, "attack_basic")
        if yaml_rule:
            ctx = {"attacker": atk, "defender": dfd, "env": env}
            apply_yaml_rule(yaml_rule, ctx)
            # Derive damage from hp delta if present, else fall back to simple diff
            # If the YAML steps directly modify defender.hp, compute damage:
            # (We capture hp before and after.)
            # Note: in this call path we've already applied, so approximate delta:
            # but to be precise, we'll run the steps with a tracked before/after.
            pass  # handled below
        # Compute damage using programmatic fallback to maintain compatibility
        before_hp = dfd.hp
        if not yaml_rule:
            res = resolve_attack(atk, dfd, env)
            dfd.hp = max(0, dfd.hp - res["damage"])
            damage = res["damage"]
        else:
            # Re-run YAML with before/after capture (safe and deterministic)
            dfd.hp = before_hp  # reset
            ctx = {"attacker": atk, "defender": dfd, "env": env}
            apply_yaml_rule(yaml_rule, ctx)
            after_hp = dfd.hp
            damage = max(0, before_hp - after_hp)

        log.append({"tick": ticks+1, "event": "attack", "attacker": atk.name, "defender": dfd.name, "damage": damage, "defender_hp": dfd.hp})

        if dfd.hp <= 0:
            log.append({"tick": ticks+1, "event": "downed", "actor": dfd.name})
            order.pop(d_idx)
            if len(order) == 1:
                log.append({"tick": ticks+1, "event": "scene_end", "winner": world.state.actors[order[0].value].name})
                break

        ticks += 1
        world.advance_time(scene_id, 1)
    return log
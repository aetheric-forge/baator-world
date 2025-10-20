from __future__ import annotations
import random
from typing import List, Dict, Any, Optional
from baator_services.world import WorldService
from baator_rules.resolver import resolve_attack, apply_yaml_rule

def _current_env(world) -> dict:
    meta = getattr(world, "meta", {}) or {}
    env = meta.get("env")
    return env if isinstance(env, dict) else {"mana": 0.5}

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
        turn = scene.turn
        a_idx = turn % len(order)
        d_idx = (turn + 1) % len(order)
        attacker_id = order[a_idx].value
        defender_id = order[d_idx].value
        atk = world.state.actors[attacker_id]
        dfd = world.state.actors[defender_id]

        # --- Prefer YAML rule; include ENV from world.meta ---
        before_hp = dfd.hp
        rules = getattr(world, "meta", {}).get("rules", [])
        rule = next((r for r in rules if r.get("id") == "attack_basic"), None)  # or your selection logic
        if rule:
            ctx = {"attacker": atk, "defender": dfd, "env": _current_env(world)}
            apply_yaml_rule(rule, ctx)
            damage = max(0, before_hp - dfd.hp)
        else:
            # fallback: deterministic “tickle” damage based on power
            base = max(1, atk.power)
            dfd.hp = max(0, dfd.hp - base)
            damage = base

        log.append({"tick": ticks+1, "event": "attack",
                    "attacker": atk.name, "defender": dfd.name,
                    "damage": damage, "defender_hp": dfd.hp})

        if dfd.hp <= 0:
            log.append({"tick": ticks+1, "event": "downed", "actor": dfd.name})
            order.pop(d_idx)
            if len(order) == 1:
                log.append({"tick": ticks+1, "event": "scene_end", "winner": world.state.actors[order[0].value].name})
                break

        world.advance_time(scene_id, 1)
        ticks += 1

    return log

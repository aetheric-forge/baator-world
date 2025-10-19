from __future__ import annotations
import random
from typing import List, Dict, Any
from baator_services.world import WorldService
from baator_rules.resolver import resolve_attack

def run_scene(world: WorldService, scene_id: str, *, seed: int = 1337, max_ticks: int = 6) -> List[Dict[str, Any]]:
    rnd = random.Random(seed)
    log: List[Dict[str, Any]] = []
    scene = world.state.scenes[scene_id]
    if len(scene.actors) < 2:
        log.append({"tick": 0, "event": "insufficient_actors"})
        return log

    # simplistic alternating initiative
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
        res = resolve_attack(atk, dfd, env)
        dfd.hp = max(0, dfd.hp - res["damage"])
        log.append({"tick": ticks+1, "event": "attack", "attacker": atk.name, "defender": dfd.name, "damage": res["damage"], "defender_hp": dfd.hp})
        if dfd.hp <= 0:
            log.append({"tick": ticks+1, "event": "downed", "actor": dfd.name})
            # remove defender from order
            order.pop(d_idx)
            if len(order) == 1:
                log.append({"tick": ticks+1, "event": "scene_end", "winner": world.state.actors[order[0].value].name})
                break
        ticks += 1
        world.advance_time(scene_id, 1)
    return log
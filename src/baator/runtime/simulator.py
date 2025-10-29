from __future__ import annotations
from typing import Dict, Any, Optional
from uuid import UUID
from baator.kernel import CommandBus, EventBus, Event
from baator.runtime import RulesRegistry, RulesEngine
from baator.domain import Scene, Participant

class Simulator:
    """
    Small orchestration layer: chooses whose turn it is, applies a rule by id,
    and emits trace events for diagnostics.
    """
    def __init__(self, rules: RulesRegistry, eng: RulesEngine,
                 cmd: CommandBus, bus: EventBus):
        self.rules = rules
        self.engine = eng
        self.cmd = cmd
        self.bus = bus

    def apply_rule(self, scene: Scene, rule_key: str,
                   *, actor: Participant, target: Participant | None,
                   ctx_extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
        rule = self.rules.get(rule_key)
        ctx: Dict[str, Any] = {
            "actor": {"name": actor.name},   # extend with stats in your store
            "target": {"name": target.name} if target else {},
        }
        if ctx_extra:
            # merge extra context (stats, AC, etc.)
            for k, v in ctx_extra.items():
                ctx[k] = v

        prov = {"actor_id": str(actor.actor_id), "source": "sim", "layer": rule.layer.value}
        self.bus.publish(Event(name="sim.trace.begin", payload={
            "scene_id": scene.scene_id, "rule": rule_key, "actor": actor.name, "ctx": ctx,
            "target": getattr(target, "name", None), "round": scene.round
        }))

        result = self.engine.apply(rule, ctx=ctx, provenance=prov)

        self.bus.publish(Event(name="sim.trace.end", payload={
            "scene_id": scene.scene_id, "rule": rule_key, "actor": actor.name,
            "target": getattr(target, "name", None), "round": scene.round, **result
        }))
        return result

    def step(self, scene: Scene) -> None:
        cur = scene.current()
        if not cur: return
        # strategy stub: emit a no-op event. The TUI/AI chooses a rule explicitly.
        self.bus.publish(Event(name="sim.turn", payload={
            "scene_id": scene.scene_id, "round": scene.round,
            "actor": cur.name, "actor_id": str(cur.actor_id)
        }))

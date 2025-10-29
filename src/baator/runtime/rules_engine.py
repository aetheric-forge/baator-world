from typing import Any,  Dict
from baator.interface.dice import roll_expr
from baator.kernel import Command, CommandBus, Event, EventBus
from baator.runtime import Effect, Rule
from .rules_eval import eval_safe

class RulesEngine:
    def __init__(self, cmd_bus: CommandBus, evt_bus: EventBus, rng):
        self.cmd = cmd_bus
        self.bus = evt_bus
        self.rng = rng

    def _emit(self, eff: Effect, provenance: Dict[str, Any]) -> None:
        payload = dict(eff.payload)
        payload.update(provenance)  # stamp actor_id/layer/source if provided
        if eff.type == "command":
            self.cmd.dispatch(Command(name=eff.name, payload=payload))
        else:
            self.bus.publish(Event(name=eff.name, payload=payload))

    def apply(self, rule: Rule, *, ctx: Dict[str, Any], provenance: Dict[str, Any]) -> Dict[str, Any]:
        # 1) conditions
        for cond in rule.when:
            if not eval_safe(cond, ctx, mode="predicate"):  # fail fast
                return {"applied": False, "reason": "condition_failed"}

        # 2) cost (if any)
        if rule.cost:
            _ = eval_safe(rule.cost, {}, mode="number")  # compute; your code can deduct resources here

        # 3) roll/DC if present
        success = True
        roll_total = None
        if rule.roll and rule.dc is not None:
            roll_total = roll_expr(rule.roll, self.rng)
            success = (roll_total >= int(rule.dc))

        # 4) effects
        effects = rule.on_success if success else rule.on_failure
        for eff in effects:
            self._emit(eff, provenance)

        return {"applied": True, "success": success, "roll": roll_total}

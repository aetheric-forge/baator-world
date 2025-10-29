from typing import Any,  Dict, Mapping, Protocol
from baator.kernel import Command, CommandBus, Event, EventBus
from baator.runtime import Effect, Rule
from ..kernel.expr import eval_safe
from ..kernel.dice import roll_expr

class RNG(Protocol):
    def random_int(self, low:int, high:int)->int: ...
    def roll(self, sides:int)->int: ...
    def ping(self)->bool: ...

class RulesEngine:
    def __init__(self, cmd_bus: CommandBus, evt_bus: EventBus, rng: RNG):
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

    def apply(self, rule: Rule, *, ctx: Mapping[str, Any], provenance: Dict[str, Any]) -> Dict[str, Any]:
        # 1) conditions
        for cond in rule.when:
            if not eval_safe(cond, ctx):  # type: ignore[arg-type] - PyLance is confused because of return type of assumed auto, but it's fine
                return {"applied": False, "reason": "condition_failed"}

        # 2) cost (if any)
        if rule.cost:
            _ = eval_safe(rule.cost, ctx, mode="number", rng=self.rng, dice_resolver=roll_expr)  # compute; your code can deduct resources here

        # 3) roll/DC if present
        success = True
        roll_total = None
        has_dc = rule.dc not in [None, ""] or False
        dc_val = int(eval_safe(rule.dc, ctx)) # type: ignore[arg-type] - ditto
        if rule.roll and has_dc:
            roll_total = int(eval_safe(rule.roll, ctx, mode="number", rng=self.rng, dice_resolver=roll_expr)) # type: ignore[arg-type] - ditt
            success = (roll_total >= dc_val)

        # 4) effects
        effects = rule.on_success if success else rule.on_failure
        for eff in effects:
            self._emit(eff, provenance)

        # 5) publish detailed calculations
        self.bus.publish(Event(name="rules.trace", payload={
            "rule_id": rule.id, "layer": rule.layer.value,
            "roll": roll_total, "dc": f"{rule.dc}{f"(result: {dc_val})"}" if has_dc else None,
            "success": success
        }))

        return {"applied": True, "success": success, "roll": roll_total}

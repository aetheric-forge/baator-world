import re
from typing import Any,  Dict, Mapping, Protocol
from baator.kernel import Command, CommandBus, Event, EventBus
from baator.runtime import Effect, Rule
from ..kernel.rng import RNG
from ..kernel.rolls import roll_expr, eval_safe

_DICE_START = re.compile(r"^\s*\d+[dD]\d+")  # e.g., "1d8", "2D20", "4d6kh3"


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

    def _materialize(self, obj: Any, ctx: Mapping[str, Any], rng: RNG) -> Any:
        """
        Convert payload literals into concrete values:
        - dict/list: recurse
        - str that looks like dice: roll via roll_expr(...)
        - str that is arithmetic/identifier path: eval via eval_safe(..., mode='number')
        - anything else: return as-is
        """
        if isinstance(obj, dict):
            return {k: self._materialize(v, ctx, rng) for k, v in obj.items()}

        if isinstance(obj, list):
            return [self._materialize(v, ctx, rng) for v in obj]

        if isinstance(obj, str):
            s = obj.strip()
            if _DICE_START.match(s):
                # supports modifiers like +actor.stats.STR and kh/kl
                return roll_expr(s, rng, ctx=ctx, verbose=False)
            try:
                # numeric/path math like "target.AC" or "actor.stats.STR + 2"
                return eval_safe(s, ctx, mode="number")
            except Exception:
                # not a computable expression; leave string unchanged
                return obj

        return obj

    def apply(self, rule: Rule, *, ctx: Mapping[str, Any], provenance: Dict[str, Any]) -> Dict[str, Any]:
        # 1) conditions
        for cond in rule.when:
            if not eval_safe(cond, ctx, mode="predicate"):
                return {"applied": False, "reason": "condition_failed"}

        # 2) cost (if any): compute to trigger RNG/events; ignore value for now
        if rule.cost:
            _ = roll_expr(rule.cost, self.rng, ctx=ctx, verbose=False)

        # 3) roll/DC if present
        roll_total: int | None = None
        dc_val: int | None = None
        success = True

        if rule.dc:
            if isinstance(rule.dc, int):
                dc_val = rule.dc
            else:
                dc_val = roll_expr(rule.dc, self.rng, ctx=ctx, verbose=False)

        if rule.roll and dc_val is not None:
            roll_total = roll_expr(rule.roll, self.rng, ctx=ctx, verbose=False)
            success = (roll_total >= dc_val)

        if success and getattr(rule, "on_success", None):
            for eff in rule.on_success:
                if eff.type == "command":
                    payload = self._materialize(eff.payload, ctx, self.rng)
                    self.cmd.dispatch(Command(eff.name, payload))

        # Emit trace elsewhere; return structured result
        return {
            "applied": True,
            "success": success,
            "roll": roll_total,
            "dc": dc_val,
        }

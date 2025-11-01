# baator/runtime/rules_engine.py
from __future__ import annotations
from typing import Any, Dict, Mapping
from uuid import uuid4

from baator.kernel import Command, CommandBus, Event, EventBus
from baator.runtime import Effect, Rule
from ..kernel.rng import RNG
from ..kernel.rolls import eval_safe  # predicates only

class RulesEngine:
    def __init__(self, cmd_bus: CommandBus, evt_bus: EventBus, rng: RNG):
        self.cmd = cmd_bus
        self.bus = evt_bus
        self.rng = rng  # kept for constructor parity; not used directly

    # ---- request/response via buses ---------------------------------------

    def _resolve_number(self, expr: str, *, ctx: Mapping[str, Any], provenance: Dict[str, Any]) -> int:
        """Resolve either dice (1d20+STR) or numeric/path (target.AC) via DiceService."""
        req_id = str(uuid4())
        box: Dict[str, int] = {}

        def on_res(e):
            p = e.payload
            if p.get("request_id") == req_id:
                box["val"] = int(p["result"])

        self.bus.subscribe("dice.resolved", on_res)
        try:
            self.cmd.dispatch(Command(
                name="dice.resolve_number",
                payload={"expr": expr, "ctx": ctx, "meta": provenance, "request_id": req_id},
            ))
            if "val" not in box:  # sync bus should fill immediately
                raise RuntimeError(f"dice.resolve_number did not resolve for {expr!r}")
            return box["val"]
        finally:
            # prefer to clean up if your EventBus implements unsubscribe
            if hasattr(self.bus, "unsubscribe"):
                self.bus.unsubscribe("dice.resolved", on_res)  # type: ignore[attr-defined]

    # ---- helpers -----------------------------------------------------------

    def _emit(self, eff: Effect, provenance: Dict[str, Any]) -> None:
        payload = {**eff.payload, **provenance}
        if eff.type == "command":
            self.cmd.dispatch(Command(name=eff.name, payload=payload))
        else:
            self.bus.publish(Event(name=eff.name, payload=payload))

    def _materialize(self, obj: Any, ctx: Mapping[str, Any], provenance: Dict[str, Any]) -> Any:
        """
        Convert payload literals into concrete values:
        - dict/list: recurse
        - str: try to resolve as number via DiceService (covers dice OR numeric paths);
               if it isn't a computable expression, leave string as-is.
        - anything else: return as-is
        """
        if isinstance(obj, dict):
            return {k: self._materialize(v, ctx, provenance) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._materialize(v, ctx, provenance) for v in obj]
        if isinstance(obj, str):
            try:
                return self._resolve_number(obj, ctx=ctx, provenance=provenance)
            except Exception:
                return obj
        return obj

    # ---- main --------------------------------------------------------------

    def apply(self, rule: Rule, *, ctx: Mapping[str, Any], provenance: Dict[str, Any]) -> Dict[str, Any]:
        # 1) conditions (predicates only!)
        for cond in rule.when:
            if not eval_safe(cond, ctx, mode="predicate"):
                return {"applied": False, "reason": "condition_failed"}

        # 2) cost (compute for side-effects / trace; ignore value)
        if rule.cost not in (None, ""):
            _ = self._resolve_number(str(rule.cost), ctx=ctx, provenance=provenance)

        # 3) DC and Roll (both through DiceService)
        dc_val: int | None = None
        if rule.dc not in (None, ""):
            dc_val = self._resolve_number(str(rule.dc), ctx=ctx, provenance=provenance)

        roll_total: int | None = None
        success = True
        if rule.roll and dc_val is not None:
            roll_total = self._resolve_number(str(rule.roll), ctx=ctx, provenance=provenance)
            success = (roll_total >= dc_val)

        # 4) effects
        if success and getattr(rule, "on_success", None):
            for eff in rule.on_success:
                # materialize AFTER success so dice in payload roll now
                payload = self._materialize(eff.payload, ctx, provenance)
                self._emit(Effect(type=eff.type, name=eff.name, payload=payload), provenance)

        # 5) trace (engine-level)
        self.bus.publish(Event(name="rules.trace", payload={
            "rule_id": rule.id,
            "layer": rule.layer.value,
            "roll": roll_total,
            "dc": dc_val,
            "success": success,
        }))

        return {"applied": True, "success": success, "roll": roll_total, "dc": dc_val}


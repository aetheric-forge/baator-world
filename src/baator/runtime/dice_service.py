from __future__ import annotations
from typing import Protocol, Any, Dict
from uuid import uuid4
from baator.kernel.event_bus import EventBus
from baator.kernel.events import Event
from baator.kernel.commands import Command
from baator.interface.dice import RNG, roll_expr, roll_advantage, roll_disadvantage

class DiceService:
    """
    Turns dice requests into domain events:
      - rng.requested {expr|sides,type, request_id, meta}
      - rng.fulfilled {result, rolls?, request_id, meta}
      - rng.failed    {reason, request_id, meta}
    """
    def __init__(self, rng: RNG, bus: EventBus) -> None:
        self.rng = rng
        self.bus = bus

    def _emit(self, name: str, payload: Dict[str, Any]) -> None:
        self.bus.publish(Event(name=name, payload=payload))

    # ----- imperative API (services can call directly) -----

    def roll_expression(self, expr: str, *, meta: Dict[str, Any] | None = None) -> int:
        rid = str(uuid4())
        meta = meta or {}
        self._emit("rng.requested", {"kind": "expr", "expr": expr, "request_id": rid, "meta": meta})
        try:
            result = roll_expr(expr, self.rng)
            self._emit("rng.fulfilled", {"kind": "expr", "expr": expr, "result": result, "request_id": rid, "meta": meta})
            return result
        except Exception as e:
            self._emit("rng.failed", {"kind": "expr", "expr": expr, "reason": str(e), "request_id": rid, "meta": meta})
            raise

    def roll_adv(self, sides: int, *, meta: Dict[str, Any] | None = None) -> int:
        rid = str(uuid4()); meta = meta or {}
        self._emit("rng.requested", {"kind": "adv", "sides": sides, "request_id": rid, "meta": meta})
        res = roll_advantage(sides, self.rng)
        self._emit("rng.fulfilled", {"kind": "adv", "sides": sides, "result": res, "request_id": rid, "meta": meta})
        return res

    def roll_dis(self, sides: int, *, meta: Dict[str, Any] | None = None) -> int:
        rid = str(uuid4()); meta = meta or {}
        self._emit("rng.requested", {"kind": "dis", "sides": sides, "request_id": rid, "meta": meta})
        res = roll_disadvantage(sides, self.rng)
        self._emit("rng.fulfilled", {"kind": "dis", "sides": sides, "result": res, "request_id": rid, "meta": meta})
        return res

    # ----- command handlers (bus-friendly) -----

    def handle(self, cmd: Command) -> None:
        """
        Expects commands:
          - dice.roll_expr   payload: {expr, meta?}
          - dice.roll_adv    payload: {sides, meta?}
          - dice.roll_dis    payload: {sides, meta?}
        """
        p = cmd.payload
        if cmd.name == "dice.roll_expr":
            self.roll_expression(str(p["expr"]), meta=p.get("meta") or {})
        elif cmd.name == "dice.roll_adv":
            self.roll_adv(int(p["sides"]), meta=p.get("meta") or {})
        elif cmd.name == "dice.roll_dis":
            self.roll_dis(int(p["sides"]), meta=p.get("meta") or {})
        else:
            raise KeyError(cmd.name)

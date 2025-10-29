from __future__ import annotations
from typing import Any, Dict
from uuid import uuid4
from baator.kernel import EventBus, Event, Command
from baator.interface.dice import RNG, roll_expr_detail

PROVENANCE_KEYS = ("actor_id", "layer", "source", "requester")

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
        # Do not mutate caller's dicts
        meta = dict(payload.get("meta") or {})
        ev = {k: v for k, v in payload.items() if k != "meta"}

        # Flatten selected provenance fields
        for k in PROVENANCE_KEYS:
            if k in meta:
                ev[k] = meta[k]
        self.bus.publish(Event(name=name, payload=ev))

    # ----- imperative API (services can call directly) -----

    def roll_expression(self, expr: str, *, meta=None) -> int:
        rid = str(uuid4()); meta = meta or {}
        self._emit("rng.requested", {"kind":"expr","expr":expr,"request_id":rid,"meta":meta})
        total, faces, mod = roll_expr_detail(expr, self.rng)
        self._emit("rng.fulfilled", {
            "kind":"expr","expr":expr,"result":total,"faces":faces,"modifier":mod,
            "request_id":rid,"meta":meta
        })
        return total

    def roll_adv(self, sides: int, *, meta=None) -> int:
        rid = str(uuid4()); meta = meta or {}
        r1 = self.rng.roll(sides); r2 = self.rng.roll(sides)
        res = max(r1, r2)
        self._emit("rng.requested", {"kind":"adv","sides":sides,"request_id":rid,"meta":meta})
        self._emit("rng.fulfilled", {
            "kind":"adv","sides":sides,"result":res,"faces":[r1, r2],
            "picked":"max","request_id":rid,"meta":meta
        })
        return res

    def roll_dis(self, sides: int, *, meta=None) -> int:
        rid = str(uuid4()); meta = meta or {}
        r1 = self.rng.roll(sides); r2 = self.rng.roll(sides)
        res = min(r1, r2)
        self._emit("rng.requested", {"kind":"dis","sides":sides,"request_id":rid,"meta":meta})
        self._emit("rng.fulfilled", {
            "kind":"dis","sides":sides,"result":res,"faces":[r1, r2],
            "picked":"min","request_id":rid,"meta":meta
        })
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

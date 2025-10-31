from __future__ import annotations
import re
from typing import Any, Dict, Mapping, Optional, Protocol
from uuid import uuid4
from baator.kernel.context import ContextProvider
from baator.kernel import EventBus, Event, Command, expr_adv, expr_dis
from ..kernel.rng import RNG
from ..kernel.rolls import roll_expr, expr_adv, expr_dis, RollDetail

PROVENANCE_KEYS = ("actor_id", "layer", "source", "requester")

class DiceService:
    """
    Turns dice requests into domain events:
      - rng.requested {expr|sides,type, request_id, meta}
      - rng.fulfilled {result, rolls?, request_id, meta}
      - rng.failed    {reason, request_id, meta}
    """
    def __init__(self, rng: RNG, bus: EventBus, ctx_provider: ContextProvider, service_name: str = "dice") -> None:
        self.rng = rng
        self.bus = bus
        self.ctx_provider = ctx_provider
        self.service_name = service_name

    def _context(self, meta: dict | None, explicit_ctx: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
        if explicit_ctx is not None:
            return explicit_ctx
        if self.ctx_provider is not None and meta:
            return self.ctx_provider.resolve(meta)
        return None

    def _emit(self, name: str, payload: Dict[str, Any]) -> None:
        # Do not mutate caller's dicts
        meta = dict(payload.get("meta") or {})
        ev = {k: v for k, v in payload.items() if k != "meta"}

        # Flatten selected provenance fields
        for k in PROVENANCE_KEYS:
            if k in meta:
                ev[k] = meta[k]
        self.bus.publish(Event(name=name, payload=ev))


    def roll_expression(self, expr: str, *, ctx: Optional[Mapping[str, Any]] = None, meta=None) -> int:
        rid = str(uuid4()); meta = meta or {}
        self._emit("rng.requested", {"kind":"expr","expr":expr,"request_id":rid,"meta":meta})
        resolved = self._context(meta, ctx)
        roll_detail: RollDetail = roll_expr(expr, self.rng, ctx=resolved, verbose=True)
        self._emit("rng.fulfilled", {
            "kind":"expr","expr":expr,"result":roll_detail["result"] ,"faces":roll_detail["faces"], "kept":roll_detail["kept"],
            "modifier":roll_detail["modifier"], "request_id":rid,"meta":meta
        })
        return roll_detail["result"]

    def handle(self, cmd: Command) -> None:
        """
        Expects commands:
          - dice.roll_expr   payload: {expr, meta?}
          - dice.roll_adv    payload: {sides, meta?}
          - dice.roll_dis    payload: {sides, meta?}
        """
        p = cmd.payload
        ctx = p.get("ctx") or {}
        if cmd.name == "dice.roll_expr":
            self.roll_expression(str(p["expr"]), ctx=ctx, meta=p.get("meta") or {})
        elif cmd.name == "dice.roll_adv":
            self.roll_expression(expr_adv(int(p["sides"])), meta=p.get("meta") or {})
        elif cmd.name == "dice.roll_dis":
            self.roll_expression(expr_dis(int(p["sides"])), meta=p.get("meta") or {})
        else:
            raise KeyError(cmd.name)

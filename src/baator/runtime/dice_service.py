from __future__ import annotations
import re
from typing import Any, Dict, Mapping
from uuid import uuid4
from baator.kernel.context import ContextProvider
from baator.kernel import CommandBus, EventBus, Event, Command
from ..kernel.rng import RNG
from ..kernel.rolls import roll_expr
from ..kernel.sexpr import parse_expression, eval_number

PROVENANCE_KEYS = ("actor_id", "layer", "source", "requester")

class DiceService:
    """
    Turns dice requests into domain events:
      - rng.requested {expr|sides,type, request_id, meta}
      - rng.fulfilled {result, rolls?, request_id, meta}
      - rng.failed    {reason, request_id, meta}
    """
    def __init__(self, rng: RNG, bus: EventBus, cmd_bus: CommandBus, ctx_provider: ContextProvider, service_name: str = "dice") -> None:
        self.rng = rng
        self.bus = bus
        self.cmd = cmd_bus
        self.ctx_provider = ctx_provider
        self.service_name = service_name

    def _context(self, meta: dict | None, explicit_ctx: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
        if explicit_ctx is not None:
            return explicit_ctx
        if self.ctx_provider is not None and meta:
            return self.ctx_provider.resolve(meta)
        return None

    def _resolver(self, request_id: str, expr: str, ctx: Mapping[str, Any]) -> int:
        detail = roll_expr(expr, self.rng, ctx=ctx, verbose=True)
        self.bus.publish(Event("rng.fulfilled", {"request_id": request_id, "kind": "expr", "expr": expr, **detail}))
        return int(detail["result"])

    def roll_expression(self, request_id: str, expr: str, *, ctx: Mapping[str, Any]) -> int:
        return self._resolver(request_id, expr, ctx)

    def resolve_number(self, request_id: str, expr: str, *, ctx: Mapping[str, Any], meta: dict | None = None):
        parsed = parse_expression(expr)
        val = eval_number(request_id, parsed, ctx, resolve_dice=self._resolver)
        self.bus.publish(Event("dice.resolved", {"request_id": request_id, "expr": expr, "result": val, **(meta or {})}))

    def handle(self, cmd: Command) -> None:
        """
        Expects commands:
          - dice.roll_expr   payload: {expr, meta?}
          - dice.roll_adv    payload: {sides, meta?}
          - dice.roll_dis    payload: {sides, meta?}
        """
        p = cmd.payload
        ctx = p.get("ctx") or {}
        meta = p.get("meta") or {}
        request_id = p.get("request_id") or str(uuid4())
        if cmd.name == "dice.roll_expression":
            expr = str(p["expr"])
            self.roll_expression(request_id, expr, ctx=ctx)
        elif cmd.name == "dice.resolve_number":
            expr = str(p["expr"])
            self.resolve_number(request_id, expr, ctx=ctx, meta=meta)
        else:
            raise KeyError(cmd.name)
